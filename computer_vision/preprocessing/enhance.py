"""
ForgeMind AI - Contrast Enhancement Module

This module provides various contrast enhancement techniques for preprocessing images.
"""

import cv2
import numpy as np
from typing import Literal, Tuple, Optional

from ..utils import logger


def enhance_contrast(
    image: np.ndarray,
    method: Literal["clahe", "histogram_equalization", "gamma", "linear"] = "clahe",
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    gamma: float = 1.0,
    alpha: float = 1.0,
    beta: int = 0,
) -> np.ndarray:
    """
    Enhance the contrast of an image.

    Args:
        image: Input image (grayscale or color).
        method: Enhancement method to use.
        clip_limit: Threshold for contrast limiting in CLAHE.
        tile_grid_size: Size of grid for histogram equalization in CLAHE.
        gamma: Gamma correction value.
        alpha: Contrast control (1.0 means no change) for linear contrast.
        beta: Brightness control (0 means no change) for linear contrast.

    Returns:
        Contrast-enhanced image.
    """
    if image is None or image.size == 0:
        logger.warning("Empty image provided to enhance_contrast.")
        return image

    # Convert to grayscale if color and method expects grayscale? Actually, some methods work on color.
    # We'll handle each method appropriately.

    if method == "clahe":
        # CLAHE works on grayscale images.
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        enhanced = clahe.apply(gray)
        if len(image.shape) == 3:
            # Convert back to BGR
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        return enhanced
    elif method == "histogram_equalization":
        if len(image.shape) == 3:
            # Convert to YCrCb and equalize the Y channel
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            enhanced = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        else:
            enhanced = cv2.equalizeHist(image)
        return enhanced
    elif method == "gamma":
        # Gamma correction
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)
    elif method == "linear":
        # Linear contrast adjustment
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    else:
        raise ValueError(f"Unsupported enhancement method: {method}")


def enhance_contrast_default(image: np.ndarray) -> np.ndarray:
    """
    Default contrast enhancement using CLAHE.
    """
    return enhance_contrast(image, method="clahe")