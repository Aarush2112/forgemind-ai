"""
ForgeMind AI - Image Preprocessing Pipeline

This module performs all preprocessing required before:

- OCR
- Layout Detection
- Table Detection
- Symbol Detection
- P&ID Parsing

Author: ForgeMind AI Team
"""

from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path

from ..config import (
    GAUSSIAN_KERNEL,
    ADAPTIVE_THRESHOLD_BLOCKSIZE,
    ADAPTIVE_THRESHOLD_C,
    MAX_IMAGE_SIZE,
    THRESHOLD_METHOD,
    THRESHOLD_BLOCK_SIZE,
    THRESHOLD_C,
    MORPHOLOGICAL_OPERATIONS,
    MORPHOLOGICAL_KERNEL_SIZE,
)

from ..utils import logger
from .denoise import denoise
from .deskew import DeskewProcessor


class ImagePreprocessor:
    """
    Complete preprocessing pipeline for industrial documents.
    """

    def __init__(self):
        logger.info("Image Preprocessor initialized.")

    # ---------------------------------------------------------
    # Public Pipeline
    # ---------------------------------------------------------

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Complete preprocessing pipeline.
        """
        image = self.resize(image)
        image = self.to_grayscale(image)
        image = self.denoise(image)
        image = self.enhance_contrast(image)
        image = self.sharpen(image)
        image = DeskewProcessor.process(image)
        image = self.threshold(image)
        image = self.morphological_operations(image)
        # Convert back to BGR for consistency with OpenCV color images
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image

    # ---------------------------------------------------------
    # Resize
    # ---------------------------------------------------------

    def resize(self, image: np.ndarray) -> np.ndarray:

        h, w = image.shape[:2]

        largest = max(h, w)

        if largest <= MAX_IMAGE_SIZE:
            return image

        scale = MAX_IMAGE_SIZE / largest

        width = int(w * scale)

        height = int(h * scale)

        return cv2.resize(
            image,
            (width, height),
            interpolation=cv2.INTER_AREA,
        )

    # ---------------------------------------------------------
    # Gray
    # ---------------------------------------------------------

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:

        if len(image.shape) == 2:
            return image

        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ---------------------------------------------------------
    # Denoise
    # ---------------------------------------------------------

    def denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply denoising to the image.
        """
        return denoise(
            image,
            method="gaussian",
            kernel_size=GAUSSIAN_KERNEL,
        )

    # ---------------------------------------------------------
    # CLAHE
    # ---------------------------------------------------------

    def enhance_contrast(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8),
        )

        return clahe.apply(image)

    # ---------------------------------------------------------
    # Sharpen
    # ---------------------------------------------------------

    def sharpen(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        kernel = np.array(
            [
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0],
            ]
        )

        return cv2.filter2D(
            image,
            -1,
            kernel,
        )

    # ---------------------------------------------------------
    # Deskew
    # ---------------------------------------------------------

    def deskew(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        coords = np.column_stack(
            np.where(image > 0)
        )

        if len(coords) == 0:
            return image

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        h, w = image.shape[:2]

        center = (w // 2, h // 2)

        matrix = cv2.getRotationMatrix2D(
            center,
            angle,
            1.0,
        )

        return cv2.warpAffine(
            image,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    # ---------------------------------------------------------
    # Thresholding
    # ---------------------------------------------------------

    def threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Apply thresholding to the image.
        """
        # Ensure image is grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        if THRESHOLD_METHOD == "otsu":
            _, thresh = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        elif THRESHOLD_METHOD == "adaptive":
            thresh = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                THRESHOLD_BLOCK_SIZE,
                THRESHOLD_C,
            )
        else:
            # Default to simple binary threshold
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        return thresh

    # ---------------------------------------------------------
    # Morphological Operations
    # ---------------------------------------------------------

    def morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """
        Apply morphological operations to the image.
        """
        # Ensure we're working with a binary image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Ensure image is binary (0 and 255)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, MORPHOLOGICAL_KERNEL_SIZE
        )

        result = binary.copy()
        for operation in MORPHOLOGICAL_OPERATIONS:
            if operation == "opening":
                result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel)
            elif operation == "closing":
                result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, kernel)
            elif operation == "erosion":
                result = cv2.erode(result, kernel, iterations=1)
            elif operation == "dilation":
                result = cv2.dilate(result, kernel, iterations=1)
            elif operation == "gradient":
                result = cv2.morphologyEx(result, cv2.MORPH_GRADIENT, kernel)
            elif operation == "tophat":
                result = cv2.morphologyEx(result, cv2.MORPH_TOPHAT, kernel)
            elif operation == "blackhat":
                result = cv2.morphologyEx(result, cv2.MORPH_BLACKHAT, kernel)

        return result