"""
ForgeMind AI - Table Detection Module

This module detects tables in document images using a YOLO model.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
from pydantic import BaseModel

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from ..config import YOLO_CONFIDENCE, YOLO_IOU, YOLO_IMAGE_SIZE
from ..schemas import BoundingBox
from ..utils import logger


class TableDetector:
    """
    Detects tables in document images using a YOLO model.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the table detector.

        Args:
            model_path: Path to the YOLO model weights file. If None,
                       a default model should be provided or the user
                       must set it before calling detect().
        """
        self.model_path = model_path
        self.model = None
        self.class_names = ["table"]

        if model_path is not None:
            self.load_model(model_path)

        logger.info("Table Detector initialized")

    def load_model(self, model_path: str) -> None:
        """
        Load the YOLO model from the specified path.

        Args:
            model_path: Path to the YOLO model weights file
        """
        if YOLO is None:
            raise ImportError(
                "Ultralytics YOLO is not installed. "
                "Please install it with: pip install ultralytics"
            )

        self.model = YOLO(model_path)
        self.model_path = model_path
        logger.info(f"Loaded table detection model from {model_path}")

    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect tables in the input image.

        Args:
            image: Input image as a numpy array (BGR format)

        Returns:
            List of detected table bounding boxes
        """
        if self.model is None:
            raise ValueError(
                "Model not loaded. Please provide a model path to the constructor "
                "or call load_model() before calling detect()."
            )

        # Run inference
        results = self.model(
            image,
            conf=YOLO_CONFIDENCE,
            iou=YOLO_IOU,
            imgsz=YOLO_IMAGE_SIZE,
            verbose=False
        )

        # Process results
        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                    # Get confidence
                    confidence = float(box.conf[0].cpu().numpy())

                    # Create bounding box
                    bbox = BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
                    detections.append(bbox)

        return detections

    def is_model_loaded(self) -> bool:
        """
        Check if a model has been loaded.

        Returns:
            True if a model is loaded, False otherwise
        """
        return self.model is not None