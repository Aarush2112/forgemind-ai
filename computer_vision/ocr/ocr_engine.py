"""
ForgeMind AI
OCR Engine

Production-ready EasyOCR wrapper for industrial drawings.

Features
--------
- Singleton OCR reader
- Image preprocessing
- Region OCR
- Full image OCR
- Confidence filtering
- Structured output
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
import logging

import cv2
import easyocr
import numpy as np

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Data Models
# --------------------------------------------------

@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: List[List[int]]


# --------------------------------------------------
# OCR Engine
# --------------------------------------------------

class OCREngine:

    def __init__(
        self,
        languages=None,
        gpu=False,
        min_confidence=0.35,
    ):

        if languages is None:
            languages = ["en"]

        self.min_confidence = min_confidence

        logger.info("Loading EasyOCR...")

        self.reader = easyocr.Reader(
            languages,
            gpu=gpu,
        )

        logger.info("EasyOCR Loaded")

    # --------------------------------------------------

    def preprocess(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        gray = cv2.fastNlMeansDenoising(gray)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )

        return thresh

    # --------------------------------------------------

    def read(
        self,
        image: np.ndarray,
    ) -> List[OCRResult]:

        processed = self.preprocess(image)

        raw = self.reader.readtext(processed)

        results: List[OCRResult] = []

        for bbox, text, conf in raw:

            if conf < self.min_confidence:
                continue

            text = text.strip()

            if not text:
                continue

            results.append(

                OCRResult(
                    text=text,
                    confidence=float(conf),
                    bbox=bbox,
                )

            )

        return results

    # --------------------------------------------------

    def read_region(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> List[OCRResult]:

        crop = image[y1:y2, x1:x2]

        if crop.size == 0:
            return []

        return self.read(crop)

    # --------------------------------------------------

    def extract_text(
        self,
        image: np.ndarray,
    ) -> str:

        data = self.read(image)

        return " ".join(

            item.text

            for item in data

        )

    # --------------------------------------------------

    def extract_region_text(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> str:

        data = self.read_region(
            image,
            x1,
            y1,
            x2,
            y2,
        )

        return " ".join(

            item.text

            for item in data

        )