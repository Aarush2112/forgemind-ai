"""
ForgeMind AI
Industrial Symbol Detector

Loads YOLO model and performs inference.

Author: ForgeMind AI
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from ultralytics import YOLO


# =====================================================
# Data Models
# =====================================================

@dataclass
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class Detection:

    label: str

    confidence: float

    bounding_box: BoundingBox


# =====================================================
# Symbol Detector
# =====================================================

class SymbolDetector:

    def __init__(

        self,

        model_path: str,

        confidence: float = 0.35,

        iou: float = 0.45,

        imgsz: int = 1024,

        device: Optional[str] = None,

    ):

        self.model_path = Path(model_path)

        self.confidence = confidence

        self.iou = iou

        self.imgsz = imgsz

        self.device = device or self._detect_device()

        if not self.model_path.exists():

            raise FileNotFoundError(

                f"Model not found:\n{self.model_path}"

            )

        self.model = YOLO(str(self.model_path))
        logger = logging.getLogger(__name__)
        logger.info("YOLO model loaded from %s on device=%s", self.model_path, self.device)

    # -------------------------------------------------

    def _detect_device(self):

        try:

            import torch

            if torch.backends.mps.is_available():

                return "mps"

            if torch.cuda.is_available():

                return "0"

            return "cpu"

        except Exception:

            return "cpu"

    # -------------------------------------------------

    def detect(

        self,

        image: np.ndarray,

    ) -> List[Detection]:

        if image is None:

            return []

        results = self.model.predict(

            source=image,

            conf=self.confidence,

            iou=self.iou,

            imgsz=self.imgsz,

            device=self.device,

            verbose=False,

        )

        detections: List[Detection] = []

        if not results:

            return detections

        result = results[0]

        if result.boxes is None:

            return detections

        names = self.model.names

        for box in result.boxes:

            cls = int(box.cls[0])

            conf = float(box.conf[0])

            x1, y1, x2, y2 = map(

                int,

                box.xyxy[0].tolist()

            )

            detections.append(

                Detection(

                    label=names[cls],

                    confidence=conf,

                    bounding_box=BoundingBox(

                        x1=x1,

                        y1=y1,

                        x2=x2,

                        y2=y2,

                    ),

                )

            )

        return detections

    # -------------------------------------------------

    def annotate(

        self,

        image: np.ndarray,

        detections: List[Detection],

    ) -> np.ndarray:

        output = image.copy()

        for det in detections:

            x1 = det.bounding_box.x1

            y1 = det.bounding_box.y1

            x2 = det.bounding_box.x2

            y2 = det.bounding_box.y2

            cv2.rectangle(

                output,

                (x1, y1),

                (x2, y2),

                (0, 255, 0),

                2,

            )

            label = (

                f"{det.label} "

                f"{det.confidence:.2f}"

            )

            cv2.putText(

                output,

                label,

                (x1, y1 - 8),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (0, 255, 0),

                2,

            )

        return output

    # -------------------------------------------------

    def crop_objects(

        self,

        image: np.ndarray,

        detections: List[Detection],

    ):

        crops = []

        for det in detections:

            x1 = det.bounding_box.x1

            y1 = det.bounding_box.y1

            x2 = det.bounding_box.x2

            y2 = det.bounding_box.y2

            crop = image[y1:y2, x1:x2]

            crops.append(

                {

                    "label": det.label,

                    "confidence": det.confidence,

                    "image": crop,

                    "bbox": det.bounding_box,

                }

            )

        return crops

    # -------------------------------------------------

    def detect_and_crop(

        self,

        image: np.ndarray,

    ):

        detections = self.detect(image)

        crops = self.crop_objects(

            image,

            detections,

        )

        annotated = self.annotate(

            image,

            detections,

        )

        return {

            "detections": detections,

            "crops": crops,

            "annotated": annotated,

        }