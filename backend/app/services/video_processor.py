"""
Phase  — Extraction de frames depuis un flux vidéo (fichier .mp4 pour l'instant,
la même logique s'appliquera à un flux RTSP/caméra live plus tard : il suffira
de remplacer le chemin fichier par l'URL du flux dans cv2.VideoCapture).

Dépose tes fichiers vidéo dans le dossier : videos/  (voir videos/README.md)
"""
import logging
from pathlib import Path
from typing import Generator, NamedTuple

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger("video_processor")


class ExtractedFrame(NamedTuple):
    frame_bgr: np.ndarray
    frame_index: int
    timestamp_seconds: float


class VideoProcessor:
    def __init__(self, video_folder: str | Path | None = None):
        self.video_folder = Path(video_folder or settings.VIDEO_FOLDER)

    def resolve_path(self, video_filename: str) -> Path:
        path = self.video_folder / video_filename
        if not path.exists():
            raise FileNotFoundError(
                f"Vidéo '{video_filename}' introuvable dans {self.video_folder}. "
                f"Dépose le fichier .mp4 dans ce dossier."
            )
        return path

    def list_videos(self) -> list[str]:
        if not self.video_folder.exists():
            return []
        return sorted(
            f.name for f in self.video_folder.iterdir()
            if f.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}
        )

    def extract_frames(
        self,
        video_filename: str,
        frame_interval_seconds: float | None = None,
        max_frames: int | None = None,
    ) -> Generator[ExtractedFrame, None, None]:
        """
        Ouvre la vidéo et retourne un frame toutes les `frame_interval_seconds`
        (au lieu de traiter chaque frame -> évite de saturer le modèle IA pour rien).
        """
        interval = frame_interval_seconds or settings.DEFAULT_FRAME_INTERVAL_SECONDS
        video_path = self.resolve_path(video_filename)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la vidéo : {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        step = max(1, round(fps * interval))
        logger.info(
            "Ouverture de %s (fps=%.2f) — extraction toutes les %.1fs (1 frame / %d)",
            video_path.name, fps, interval, step,
        )

        frame_index = 0
        yielded = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break  # fin de la vidéo

                if frame_index % step == 0:
                    timestamp = frame_index / fps
                    yield ExtractedFrame(frame_bgr=frame, frame_index=frame_index, timestamp_seconds=timestamp)
                    yielded += 1
                    if max_frames and yielded >= max_frames:
                        break

                frame_index += 1
        finally:
            cap.release()

        logger.info("Extraction terminée : %d frames analysées sur %s", yielded, video_path.name)


video_processor = VideoProcessor()
