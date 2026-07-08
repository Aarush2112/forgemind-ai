"""
ForgeMind AI - Deskew Utility

Provides document deskewing using OpenCV.

This module can be reused by:
- OCR
- Layout Detection
- Table Detection
- Symbol Detection
"""

from __future__ import annotations

import cv2
import numpy as np

from ..utils import logger


class DeskewProcessor:
    """
    Utility class for correcting document rotation.
    """

    @staticmethod
    def compute_skew_angle(image: np.ndarray) -> float:
        """
        Estimate skew angle of a document.

        Parameters
        ----------
        image : np.ndarray
            Grayscale image.

        Returns
        -------
        float
            Rotation angle in degrees.
        """

        coords = np.column_stack(np.where(image > 0))

        if len(coords) == 0:
            logger.warning("No foreground pixels found for deskew.")
            return 0.0

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        logger.debug(f"Detected skew angle: {angle:.2f}")

        return angle

    @staticmethod
    def rotate(image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotate image by given angle.
        """

        h, w = image.shape[:2]

        center = (w // 2, h // 2)

        matrix = cv2.getRotationMatrix2D(
            center,
            angle,
            1.0,
        )

        rotated = cv2.warpAffine(
            image,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return rotated

    @classmethod
    def process(cls, image: np.ndarray) -> np.ndarray:
        """
        Automatically deskew image.
        """

        angle = cls.compute_skew_angle(image)

        if abs(angle) < 0.5:
            logger.info("Document already aligned.")
            return image

        logger.info(f"Deskewing image ({angle:.2f}°).")

        return cls.rotate(image, angle)