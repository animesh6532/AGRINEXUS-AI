"""
Computer Vision Service using OpenCV.
Handles image quality gates (blur, exposure, size, format) and preprocessing pipelines.
"""

import io
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any, Optional
import torch
from torchvision import transforms

from ..core.config import settings
from ..core.logging import logger

# Standard ImageNet normalization expected by ResNet18 and MobileNetV3 Small
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

eval_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
])


class CVService:
    """OpenCV Image Processing and Quality Gate Service."""

    @staticmethod
    def inspect_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
        """
        Validate raw image bytes and assess quality parameters using OpenCV.
        Checks for blur (Laplacian variance) and exposure (brightness).
        """
        if not image_bytes or len(image_bytes) == 0:
            raise ValueError("Empty image byte payload received.")

        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise ValueError(f"Image size ({size_mb:.2f} MB) exceeds limit of {settings.MAX_UPLOAD_SIZE_MB} MB.")

        # Decode image using OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_cv is None:
            raise ValueError("Corrupted or unsupported image file format.")

        height, width, channels = img_cv.shape

        # Convert to Grayscale for quality metrics
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # 1. Blur Detection using Laplacian Variance
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < settings.CV_BLUR_THRESHOLD

        # 2. Exposure Check using Mean Brightness
        brightness = float(np.mean(gray))
        is_exposure_ok = (settings.CV_BRIGHTNESS_LOW <= brightness <= settings.CV_BRIGHTNESS_HIGH)

        warnings = []
        if is_blurry:
            warnings.append(f"Image may be blurry (Laplacian score: {laplacian_var:.1f} < threshold: {settings.CV_BLUR_THRESHOLD}). Capture a clearer photo.")
        if brightness < settings.CV_BRIGHTNESS_LOW:
            warnings.append("Image is underexposed / too dark.")
        elif brightness > settings.CV_BRIGHTNESS_HIGH:
            warnings.append("Image is overexposed / too bright.")

        is_valid = (not is_blurry) and is_exposure_ok

        report = {
            "is_valid": is_valid,
            "blur_score": laplacian_var,
            "is_blurry": is_blurry,
            "brightness_score": brightness,
            "is_exposure_ok": is_exposure_ok,
            "resolution": [width, height],
            "warnings": warnings
        }

        return report

    @staticmethod
    def preprocess_for_pytorch(image_bytes: bytes) -> Tuple[torch.Tensor, Image.Image]:
        """
        Convert raw image bytes to PIL Image and PyTorch Normalized Tensor (1, 3, 224, 224).
        Reproduces exact evaluation transform used in notebook training.
        """
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to load image with PIL: {e}")

        tensor = eval_transform(pil_img).unsqueeze(0)  # Add batch dimension: (1, 3, 224, 224)
        return tensor, pil_img
