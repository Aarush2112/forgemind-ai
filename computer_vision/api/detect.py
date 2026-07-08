"""
ForgeMind AI — Computer Vision Detection API.

Pipeline: Upload → Preprocess → YOLO → OCR → Parse → Pinecone → JSON
"""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from computer_vision.config import (
    MODEL_PATH,
    RESULTS_DIR,
    YOLO_CONFIDENCE,
    YOLO_IMAGE_SIZE,
    YOLO_IOU,
)
from computer_vision.detection.symbol_detection import SymbolDetector
from computer_vision.ocr.ocr_engine import OCREngine
from computer_vision.ocr.text_cleaner import OCRTextCleaner
from computer_vision.parsers.drawing_parser import DrawingParser
from computer_vision.parsers.pid_parser import PidParser
from computer_vision.parsers.table_parser import TableParser
from computer_vision.preprocessing.image_preprocessing import ImagePreprocessor
from computer_vision.rag.hooks import notify_index_updated
from pinecone_store import index_documents, load_index
logger = logging.getLogger(__name__)

router = APIRouter()

_cv_state: Dict[str, Any] = {
    "model_loaded": False,
    "ocr_loaded": False,
    "model_error": None,
}


@lru_cache(maxsize=1)
def _get_preprocessor() -> ImagePreprocessor:
    return ImagePreprocessor()


@lru_cache(maxsize=1)
def _get_detector() -> SymbolDetector:
    return SymbolDetector(
        model_path=str(MODEL_PATH),
        confidence=YOLO_CONFIDENCE,
        iou=YOLO_IOU,
        imgsz=YOLO_IMAGE_SIZE,
    )


@lru_cache(maxsize=1)
def _gpu_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available() or torch.backends.mps.is_available()
    except Exception:
        return False


@lru_cache(maxsize=1)
def _get_ocr() -> OCREngine:
    return OCREngine(gpu=_gpu_available())


@lru_cache(maxsize=1)
def _get_cleaner() -> OCRTextCleaner:
    return OCRTextCleaner()


@lru_cache(maxsize=1)
def _get_pid_parser() -> PidParser:
    return PidParser()


@lru_cache(maxsize=1)
def _get_table_parser() -> TableParser:
    return TableParser()


@lru_cache(maxsize=1)
def _get_drawing_parser() -> DrawingParser:
    return DrawingParser()


def _ensure_cv_components() -> None:
    """Load heavy CV components on first use; record status for health checks."""
    if _cv_state["model_loaded"] and _cv_state["ocr_loaded"]:
        return

    try:
        _get_detector()
        _cv_state["model_loaded"] = True
        _cv_state["model_error"] = None
    except Exception as exc:
        _cv_state["model_loaded"] = False
        _cv_state["model_error"] = str(exc)
        logger.exception("Failed to load YOLO model from %s", MODEL_PATH)
        raise HTTPException(
            status_code=503,
            detail=f"Computer vision model unavailable: {exc}",
        ) from exc

    try:
        _get_ocr()
        _cv_state["ocr_loaded"] = True
    except Exception as exc:
        _cv_state["ocr_loaded"] = False
        logger.exception("Failed to load OCR engine")
        raise HTTPException(
            status_code=503,
            detail=f"OCR engine unavailable: {exc}",
        ) from exc


def read_image(contents: bytes) -> np.ndarray:
    """Decode uploaded bytes into an OpenCV BGR image."""
    image = np.frombuffer(contents, dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image uploaded.")
    return image


def save_annotated_image(image: np.ndarray) -> str:
    """Save annotated image under computer_vision/results (served at /results)."""
    filename = f"{uuid.uuid4().hex}.jpg"
    path = RESULTS_DIR / filename
    if not cv2.imwrite(str(path), image):
        raise HTTPException(status_code=500, detail="Failed to save annotated image.")
    return f"/results/{filename}"


def crop_from_bbox(image: np.ndarray, bbox) -> Optional[np.ndarray]:
    x1 = max(0, bbox.x1)
    y1 = max(0, bbox.y1)
    x2 = min(image.shape[1], bbox.x2)
    y2 = min(image.shape[0], bbox.y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return image[y1:y2, x1:x2]


def _safe_parse(parser, text: str) -> Dict[str, Any]:
    try:
        return parser.parse(text)
    except Exception:
        logger.exception("Parser failed for text snippet: %s", text[:80])
        return {}


def _safe_to_text(parser, parsed: Dict[str, Any]) -> str:
    try:
        return parser.to_text(parsed) or ""
    except Exception:
        logger.exception("Parser to_text failed")
        return ""


@router.post("/detect")
async def detect_image(image: UploadFile = File(...)):
    if image.content_type is None:
        raise HTTPException(status_code=400, detail="Unknown file type.")
    if not image.content_type.startswith("image"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")

    _ensure_cv_components()

    preprocessor = _get_preprocessor()
    detector = _get_detector()
    ocr = _get_ocr()
    cleaner = _get_cleaner()
    pid_parser = _get_pid_parser()
    table_parser = _get_table_parser()
    drawing_parser = _get_drawing_parser()

    contents = await image.read()
    original = read_image(contents)

    try:
        processed = preprocessor.preprocess(original)
        detections = detector.detect(processed)
        annotated = detector.annotate(original.copy(), detections)
        annotated_path = save_annotated_image(annotated)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Detection pipeline failed")
        raise HTTPException(status_code=500, detail=f"Detection failed: {exc}") from exc

    response: List[Dict[str, Any]] = []
    pinecone_documents: List[tuple[str, Dict[str, Any]]] = []
    full_ocr = ""

    for detection in detections:
        crop = crop_from_bbox(original, detection.bounding_box)
        if crop is None:
            continue

        try:
            raw_text = ocr.extract_text(crop)
        except Exception:
            logger.exception("OCR failed for detection crop")
            raw_text = ""

        cleaned_text = cleaner.clean(raw_text)

        parsed_pid = _safe_parse(pid_parser, cleaned_text)
        parsed_table = _safe_parse(table_parser, cleaned_text)
        parsed_drawing = _safe_parse(drawing_parser, cleaned_text)

        text_chunks: List[str] = [
            f"Detected symbol: {detection.label} (confidence {detection.confidence:.4f})"
        ]
        for parser, parsed in (
            (pid_parser, parsed_pid),
            (table_parser, parsed_table),
            (drawing_parser, parsed_drawing),
        ):
            chunk = _safe_to_text(parser, parsed)
            if chunk:
                text_chunks.append(chunk)

        if cleaned_text:
            text_chunks.append(f"OCR Text: {cleaned_text}")

        document_text = "\n".join(text_chunks)
        metadata = {
            "source_type": "computer_vision",
            "image_name": image.filename or "uploaded_image",
            "symbol_class": detection.label,
            "confidence": round(detection.confidence, 4),
            "bbox_x1": detection.bounding_box.x1,
            "bbox_y1": detection.bounding_box.y1,
            "bbox_x2": detection.bounding_box.x2,
            "bbox_y2": detection.bounding_box.y2,
            "ocr_text": cleaned_text[:2000],
        }

        if document_text.strip():
            pinecone_documents.append((document_text, metadata))

        response.append(
            {
                "label": detection.label,
                "class": detection.label,
                "confidence": round(detection.confidence, 4),
                "bbox": {
                    "x1": detection.bounding_box.x1,
                    "y1": detection.bounding_box.y1,
                    "x2": detection.bounding_box.x2,
                    "y2": detection.bounding_box.y2,
                },
                "ocr": cleaned_text,
                "pid": parsed_pid,
                "table": parsed_table,
                "drawing": parsed_drawing,
            }
        )

    try:
        full_ocr = cleaner.clean(ocr.extract_text(original))
    except Exception:
        logger.exception("Full-image OCR failed")
        full_ocr = ""

    if full_ocr:
        drawing_info = _safe_parse(drawing_parser, full_ocr)
        table_info = _safe_parse(table_parser, full_ocr)
        pid_info = _safe_parse(pid_parser, full_ocr)

        full_chunks: List[str] = []
        for parser, parsed in (
            (drawing_parser, drawing_info),
            (table_parser, table_info),
            (pid_parser, pid_info),
        ):
            chunk = _safe_to_text(parser, parsed)
            if chunk:
                full_chunks.append(chunk)

        full_chunks.append(f"Complete OCR: {full_ocr}")
        full_document = "\n".join(full_chunks)

        pinecone_documents.append(
            (
                full_document,
                {
                    "source_type": "full_drawing",
                    "image_name": image.filename or "uploaded_image",
                    "ocr_text": full_ocr[:2000],
                },
            )
        )

    unique_documents: List[tuple[str, Dict[str, Any]]] = []
    seen: set[str] = set()
    for text, metadata in pinecone_documents:
        fingerprint = text.strip().lower()
        if not fingerprint or fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique_documents.append((text, metadata))
    pinecone_documents = unique_documents

    indexed_count = 0
    try:
        if pinecone_documents:
            index_documents(pinecone_documents)
            indexed_count = len(pinecone_documents)
            notify_index_updated()
            logger.info("Indexed %d document(s) into Pinecone.", indexed_count)
        else:
            logger.warning("No valid documents to index after cleaning.")
    except Exception:
        logger.exception("Failed to index documents into Pinecone")

    class_count: Dict[str, int] = {}
    for item in response:
        label = item["label"]
        class_count[label] = class_count.get(label, 0) + 1

    average_confidence = 0.0
    if response:
        average_confidence = round(
            sum(x["confidence"] for x in response) / len(response),
            4,
        )

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "filename": image.filename,
            "detections": response,
            "annotated_image": annotated_path,
            "statistics": {
                "total_detections": len(response),
                "indexed_documents": indexed_count,
                "ocr_completed": bool(full_ocr),
                "classes": class_count,
                "average_confidence": average_confidence,
            },
            "message": "Detection completed successfully.",
        },
    )


@router.get("/detect/health")
async def health():
    model_loaded = _cv_state["model_loaded"]
    ocr_loaded = _cv_state["ocr_loaded"]
    if not model_loaded and MODEL_PATH.exists():
        try:
            _ensure_cv_components()
            model_loaded = _cv_state["model_loaded"]
            ocr_loaded = _cv_state["ocr_loaded"]
        except HTTPException:
            pass

    return {
        "status": "healthy" if model_loaded and ocr_loaded else "degraded",
        "model_loaded": model_loaded,
        "model_path": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists(),
        "model_error": _cv_state["model_error"],
        "ocr_loaded": ocr_loaded,
        "parser_loaded": True,
        "pinecone_enabled": True,
    }


@router.get("/detect/info")
async def info():
    return {
        "service": "ForgeMind AI Computer Vision",
        "version": "1.0.0",
        "pipeline": [
            "Upload",
            "Preprocessing",
            "YOLO Detection",
            "OCR",
            "Text Cleaning",
            "P&ID Parsing",
            "Table Parsing",
            "Drawing Parsing",
            "Pinecone Indexing",
            "RAG",
        ],
        "supported_classes": [
            "Pump",
            "Valve",
            "HeatExchanger",
            "PressureGauge",
        ],
    }
