"""
recognition/services.py

AI services for face recognition pipeline.
Handles embedding generation, face detection, and similarity matching.

Architecture:
- Separates AI logic from Django ORM
- Allows easy testing and swapping of models
- No circular imports
"""

import numpy as np
from PIL import Image
import logging
from typing import Optional, Tuple, List
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)


# Initialize face recognition model globally to avoid reloading
_face_model = None


def get_face_model() -> FaceAnalysis:
    """
    Lazy-load InsightFace model.
    
    This is initialized once and reused for performance.
    In production, consider using a model server (TensorRT, ONNX Runtime).
    """
    global _face_model
    if _face_model is None:
        try:
            _face_model = FaceAnalysis(
                name="buffalo_l",  # High accuracy model
                providers=["CPUProvider"],  # Use GPU with ["CUDAProvider"] if available
            )
            _face_model.prepare(ctx_id=0)
            logger.info("InsightFace model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load InsightFace model: {e}")
            raise
    return _face_model


def generate_embedding(image_path: str) -> Optional[np.ndarray]:
    """
    Generate a 512-dimensional face embedding from an image.
    
    Args:
        image_path: Path to image file (local or uploaded file path)
    
    Returns:
        numpy array of shape (512,) if face detected, None if no face found
    
    Raises:
        FileNotFoundError: If image file doesn't exist
        Exception: If InsightFace fails
    
    Why this architecture:
    - Returns numpy array (not saved to DB directly)
    - Allows Django signals to handle DB saving
    - Enables testing without Django ORM
    - Separates concerns: AI logic vs. DB persistence
    """
    try:
        # Load image
        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img)
        
        # Get face model
        model = get_face_model()
        
        # Detect faces and get embeddings
        faces = model.get(img_array)
        
        if len(faces) == 0:
            logger.warning(f"No face detected in image: {image_path}")
            return None
        
        # Return embedding of the first (largest) face
        # In production, you might validate face quality, size, etc.
        embedding = faces[0].embedding
        logger.info(f"Generated embedding for {image_path}")
        return embedding
        
    except FileNotFoundError:
        logger.error(f"Image file not found: {image_path}")
        raise
    except Exception as e:
        logger.error(f"Error generating embedding for {image_path}: {e}")
        raise
    finally:
        # Don't hold image in memory
        if 'img' in locals():
            del img


def detect_faces(image_path: str) -> List[Tuple[np.ndarray, object]]:
    """
    Detect all faces in an image and return their embeddings.
    
    Args:
        image_path: Path to image file
    
    Returns:
        List of (embedding, face_object) tuples.
        face_object contains: bbox, kps (keypoints), gender, age, etc.
    
    Used by: recognition/face_processor.py
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img)
        
        model = get_face_model()
        faces = model.get(img_array)
        
        if len(faces) == 0:
            logger.info(f"No faces detected in image: {image_path}")
            return []
        
        # Return list of (embedding, face_info) tuples
        results = [(face.embedding, face) for face in faces]
        logger.info(f"Detected {len(results)} faces in {image_path}")
        return results
        
    except Exception as e:
        logger.error(f"Error detecting faces in {image_path}: {e}")
        raise


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two face embeddings.
    
    Args:
        embedding1, embedding2: numpy arrays of shape (512,)
    
    Returns:
        Similarity score between 0 and 1
        
    Formula: cos(θ) = (A·B) / (||A|| * ||B||)
    """
    # Normalize embeddings
    emb1_norm = embedding1 / np.linalg.norm(embedding1)
    emb2_norm = embedding2 / np.linalg.norm(embedding2)
    
    # Compute cosine similarity
    similarity = float(np.dot(emb1_norm, emb2_norm))
    return similarity
