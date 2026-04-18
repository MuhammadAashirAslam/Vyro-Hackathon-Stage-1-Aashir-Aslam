"""
Grabpic Face Service
Handles face embedding extraction and similarity matching using DeepFace + pgvector.
"""

import logging
import numpy as np
from deepface import DeepFace

logger = logging.getLogger(__name__)


def get_embedding(image_path: str) -> list[dict] | None:
    """
    Extract ALL face embeddings from an image.
    Returns a list of dicts with 'embedding' and 'facial_area' keys,
    or None if no faces are detected.
    """
    try:
        results = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",
            enforce_detection=False,
            detector_backend="opencv",
        )
        if not results:
            return None

        faces = []
        for r in results:
            emb = r.get("embedding")
            facial_area = r.get("facial_area", {})
            if emb:
                faces.append({
                    "embedding": emb,
                    "facial_area": facial_area,
                })
        return faces if faces else None
    except Exception as e:
        logger.warning(f"Face detection failed for {image_path}: {e}")
        return None


def get_single_embedding(image_path: str) -> list[float] | None:
    """
    Extract the dominant (first) face embedding from an image.
    Used for selfie authentication where we expect one face.
    """
    try:
        results = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",
            enforce_detection=True,
            detector_backend="opencv",
        )
        if results:
            return results[0].get("embedding")
        return None
    except Exception as e:
        logger.warning(f"Single face detection failed for {image_path}: {e}")
        return None


def embedding_to_pgvector(embedding: list[float]) -> str:
    """Convert a Python list of floats to pgvector string format: '[0.1,0.2,...]'"""
    return "[" + ",".join(str(float(x)) for x in embedding) + "]"


def cosine_distance(a: list[float], b: list[float]) -> float:
    """Compute cosine distance between two embeddings (0 = identical, 2 = opposite)."""
    a_arr, b_arr = np.array(a), np.array(b)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 1.0
    return float(1 - np.dot(a_arr, b_arr) / norm)
