import time
import logging
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers

from app.config import settings

logger = logging.getLogger("ai_model")


class AIModelService:
    _instance: "AIModelService | None" = None

    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.class_names = settings.CLASS_NAMES
        self.img_size = (settings.IMG_SIZE, settings.IMG_SIZE)

        # Même pipeline d'augmentation légère que dans predict.ipynb
        self._tta_augmentation = tf.keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),
            layers.RandomZoom(0.05),
        ])

    @classmethod
    def get_instance(cls) -> "AIModelService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self) -> None:
        #Charge le modèle .keras. Ne lève pas d'exception fatale si absent :l'API doit pouvoir démarrer (DB, CRUD...) même sans modèle disponible ; seules les routes d'inférence échoueront avec un message clair.
        model_path = Path(settings.MODEL_PATH)
        if not model_path.exists():
            logger.warning(
                "Modèle introuvable à %s — les endpoints d'inférence renverront une erreur "
                "tant que le fichier .keras n'est pas déposé à cet emplacement.",
                model_path,
            )
            self.model_loaded = False
            return

        logger.info("Chargement du modèle depuis %s ...", model_path)
        self.model = tf.keras.models.load_model(str(model_path))
        self.model_loaded = True
        logger.info("Modèle chargé avec succès.")

    def _ensure_loaded(self):
        if not self.model_loaded:
            raise RuntimeError(
                f"Modèle IA non chargé. Placez final_model.keras dans "
                f"'{settings.MODEL_PATH}' puis redémarrez l'API."
            )

    def _preprocess_array(self, image_rgb: np.ndarray) -> tf.Tensor:
        """Prend une image RGB (numpy, HxWx3, uint8) et la prépare comme à l'entraînement."""
        image = tf.image.resize(image_rgb, self.img_size)
        image = tf.expand_dims(image, axis=0)
        return image

    def preprocess_from_file(self, image_path: str | Path) -> tf.Tensor:
        image = tf.io.read_file(str(image_path))
        image = tf.image.decode_jpeg(image, channels=3)
        image = tf.image.resize(image, self.img_size)
        image = tf.expand_dims(image, axis=0)
        return image

    def preprocess_from_bgr_frame(self, frame_bgr: np.ndarray) -> tf.Tensor:
        """Frame OpenCV (BGR) -> tensor prêt pour le modèle (RGB)."""
        frame_rgb = frame_bgr[:, :, ::-1]  # BGR -> RGB, évite une dépendance cv2 ici
        return self._preprocess_array(frame_rgb)

    def predict(self, image_tensor: tf.Tensor, use_tta: bool | None = None) -> dict:
        self._ensure_loaded()
        use_tta = settings.USE_TTA if use_tta is None else use_tta
        start = time.perf_counter()

        if use_tta:
            preds_sum = self.model.predict(image_tensor, verbose=0)
            for _ in range(settings.TTA_ROUNDS):
                aug_image = self._tta_augmentation(image_tensor, training=True)
                preds_sum += self.model.predict(aug_image, verbose=0)
            probabilities = preds_sum / (settings.TTA_ROUNDS + 1)
        else:
            probabilities = self.model.predict(image_tensor, verbose=0)

        elapsed_ms = (time.perf_counter() - start) * 1000
        probabilities = probabilities[0]
        predicted_idx = int(np.argmax(probabilities))

        return {
            "predicted_class": self.class_names[predicted_idx],
            "confidence": round(float(probabilities[predicted_idx]), 4),
            "probabilities": {
                cls: round(float(probabilities[i]), 4)
                for i, cls in enumerate(self.class_names)
            },
            "processing_time_ms": round(elapsed_ms, 2),
        }

    def predict_from_file(self, image_path: str | Path, use_tta: bool | None = None) -> dict:
        tensor = self.preprocess_from_file(image_path)
        return self.predict(tensor, use_tta=use_tta)

    def predict_from_bgr_frame(self, frame_bgr: np.ndarray, use_tta: bool | None = None) -> dict:
        tensor = self.preprocess_from_bgr_frame(frame_bgr)
        return self.predict(tensor, use_tta=use_tta)


ai_model_service = AIModelService.get_instance()
