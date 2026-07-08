"""
ForgeMind AI - Denoising Module

This module provides various denoising techniques for preprocessing images.
"""

import cv2
import numpy as np
from typing import Literal, Tuple, Optional

from ..config import GAUSSIAN_KERNEL
from ..utils import logger


def denoise(
    image: np.ndarray,
    method: Literal["gaussian", "median", "bilateral", "non_local_means"] = "gaussian",
    kernel_size: Tuple[int, int] = GAUSSIAN_KERNEL,
    sigma_color: float = 75,
    sigma_space: float = 75,
    h: float = 10,
    template_window_size: int = 7,
    search_window_size: int = 21,
) -> np.ndarray:
    """
    Denoise an image using the specified method.

    Args:
        image: Input image (grayscale or color).
        method: Denoising method to use.
        kernel_size: Size of the kernel for Gaussian and median blur.
        sigma_color: Filter sigma in the color space for bilateral filter.
        sigma_space: Filter sigma in the coordinate space for bilateral filter.
        h: Parameter regulating filter strength for non-local means.
        template_window_size: Size in pixels of the template patch for non-local means.
        search_window_size: Size in pixels of the window used to compute weighted average for non-local means.

    Returns:
        Denoised image.
    """
    if image is None or image.size == 0:
        logger.warning("Empty image provided to denoise.")
        return image

    if method == "gaussian":
        return cv2.GaussianBlur(image, kernel_size, 0)
    elif method == "median":
        return cv2.medianBlur(image, kernel_size[0])  # kernel_size must be a single integer for median
    elif method == "bilateral":
        return cv2.bilateralFilter(image, kernel_size[0], sigma_color, sigma_space)
    elif method == "non_local_means":
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(
                image, None, h, h, template_window_size, search_window_size
            )
        else:
            return cv2.fastNlMeansDenoising(
                image, None, h, template_window_size, search_window_size
            )
    else:
        raise ValueError(f"Unsupported denoising method: {method}")


def denoise_gaussian(image: np.ndarray, kernel_size: Tuple[int, int] = (5, 5)) -> np.ndarray:
    """
    Apply Gaussian blur for denoising.
    """
    return denoise(image, method="gaussian", kernel_size=kernel_size)


def denoise_median(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    Apply median blur for denoising.
    """
    return denoise(image, method="median", kernel_size=(kernel_size, kernel_size))


def denoise_bilateral(
    image: np.ndarray,
    d: int = 9,
    sigma_color: float = 75,
    sigma_space: float = 75,
) -> np.ndarray:
    """
    Apply bilateral filter for denoising.
    """
    return denoise(
        image,
        method="bilateral",
        kernel_size=(d, d),
        sigma_color=sigma_color,
        sigma_space=sigma_space,
    )


def denoise_non_local_means(
    image: np.ndarray,
    h: float = 10,
    template_window_size: int = 7,
    search_window_size: int = 21,
) -> np.ndarray:
    """
    Apply non-local means denoising.
    """
    return denoise(
        image,
        method="non_local_means",
        h=h,
        template_window_size=template_window_size,
        search_window_size=search_window_size,
    )