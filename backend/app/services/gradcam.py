"""
Grad-CAM Interpretability Hook Service for PyTorch ResNet18.
Generates attention heatmap overlays for disease detection explainability.
"""

import io
import base64
import numpy as np
import cv2
import torch
import torch.nn.functional as F
from PIL import Image

from ..core.logging import logger


class GradCAM:
    """Grad-CAM generator targeting specified layer (layer4[-1]) of ResNet18."""

    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        self.target_layer.register_forward_hook(self._save_activation)
        self.target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate_heatmap_base64(
        self,
        input_tensor: torch.Tensor,
        pil_image: Image.Image,
        target_class_idx: int
    ) -> str:
        """
        Generate Grad-CAM heatmap overlay as a base64 encoded PNG string.
        Returns None if generation fails.
        """
        try:
            self.model.eval()
            self.model.zero_grad()

            # Forward pass
            output = self.model(input_tensor)

            # Target score for specified class
            score = output[0, target_class_idx]
            score.backward()

            if self.gradients is None or self.activations is None:
                logger.warning("Grad-CAM hooks failed to capture gradients or activations.")
                return None

            # Compute channel weights
            weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)
            cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
            cam = F.relu(cam)

            cam_np = cam.squeeze().cpu().detach().numpy()
            if cam_np.max() > 0:
                cam_np = cam_np / cam_np.max()

            # Resize heatmap to match input image
            orig_w, orig_h = pil_image.size
            cam_resized = cv2.resize(cam_np, (orig_w, orig_h))
            heatmap = np.uint8(255 * cam_resized)
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

            # Convert PIL image to BGR numpy array
            img_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # Blend original image and heatmap
            overlay = cv2.addWeighted(img_bgr, 0.6, heatmap_color, 0.4, 0)

            # Encode to PNG base64
            _, buffer = cv2.imencode('.png', overlay)
            b64_str = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/png;base64,{b64_str}"

        except Exception as e:
            logger.warning(f"Grad-CAM generation failed: {e}")
            return None
