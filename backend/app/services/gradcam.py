"""
Phase 5 — Explainable AI (Grad-CAM).

Génère une heatmap Grad-CAM réelle (pas une simulation) en s'appuyant sur les
gradients de la classe prédite par rapport à la dernière couche convolutive
du modèle EfficientNetV2B0 chargé par ai_model_service.

Référence de la méthode : Selvaraju et al., "Grad-CAM: Visual Explanations
from Deep Networks via Gradient-based Localization" (2017).
"""
import logging
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf

from app.config import settings
from app.services.ai_model import ai_model_service

logger = logging.getLogger("gradcam")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
ORIGINALS_DIR = STATIC_DIR / "frames"
GRADCAM_DIR = STATIC_DIR / "gradcam"
ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
GRADCAM_DIR.mkdir(parents=True, exist_ok=True)


def _find_last_conv_layer(model) -> str:
    """
    Trouve dynamiquement le nom de la dernière couche à sortie 4D (conv/activation
    spatiale) du modèle — évite de coder en dur un nom de couche spécifique à
    une version d'EfficientNetV2B0, ce qui rendrait le service fragile si le
    modèle est réentraîné ou légèrement modifié.
    """
    for layer in reversed(model.layers):
        try:
            shape = layer.output_shape
        except AttributeError:
            continue
        if isinstance(shape, tuple) and len(shape) == 4:
            return layer.name
    raise RuntimeError("Aucune couche convolutive 4D trouvée dans le modèle pour Grad-CAM.")


class GradCAMService:
    def __init__(self):
        self._last_conv_layer_name = None
        self._grad_model = None

    def _ensure_grad_model(self):
        if self._grad_model is not None:
            return
        model = ai_model_service.model
        if model is None:
            raise RuntimeError("Modèle IA non chargé — impossible de construire le Grad-CAM.")

        self._last_conv_layer_name = _find_last_conv_layer(model)
        self._grad_model = tf.keras.models.Model(
            inputs=model.inputs,
            outputs=[model.get_layer(self._last_conv_layer_name).output, model.output],
        )
        logger.info("Grad-CAM branché sur la couche : %s", self._last_conv_layer_name)

    def compute_heatmap(self, image_tensor: tf.Tensor, class_index: int) -> np.ndarray:
        """Retourne une heatmap normalisée [0,1] de la taille de la dernière feature map."""
        self._ensure_grad_model()

        with tf.GradientTape() as tape:
            conv_output, predictions = self._grad_model(image_tensor)
            class_score = predictions[:, class_index]

        grads = tape.gradient(class_score, conv_output)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        conv_output = conv_output[0]
        heatmap = conv_output @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        heatmap = tf.maximum(heatmap, 0)  # ReLU
        max_val = tf.reduce_max(heatmap)
        if max_val > 0:
            heatmap = heatmap / max_val
        return heatmap.numpy()

    def generate_and_save(
        self,
        image_tensor: tf.Tensor,
        original_bgr: np.ndarray,
        class_index: int,
        prediction_id: int,
    ) -> tuple[str, str]:
        """
        Calcule la heatmap, la superpose à l'image originale, sauvegarde les
        deux fichiers sur disque et retourne leurs chemins relatifs (servis
        via /static).
        """
        heatmap = self.compute_heatmap(image_tensor, class_index)

        heatmap_resized = cv2.resize(heatmap, (original_bgr.shape[1], original_bgr.shape[0]))
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        overlay = cv2.addWeighted(original_bgr, 0.55, heatmap_color, 0.45, 0)

        original_filename = f"pred_{prediction_id}_original.jpg"
        gradcam_filename = f"pred_{prediction_id}_gradcam.jpg"

        cv2.imwrite(str(ORIGINALS_DIR / original_filename), original_bgr)
        cv2.imwrite(str(GRADCAM_DIR / gradcam_filename), overlay)

        return f"/static/frames/{original_filename}", f"/static/gradcam/{gradcam_filename}"


gradcam_service = GradCAMService()
