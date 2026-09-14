import math
import re
from typing import List

# Fixed dimension for lightweight vector embedding
VECTOR_DIM = 384


def text_to_vector(text: str, dim: int = VECTOR_DIM) -> List[float]:
    """
    Generates a normalized dense vector embedding representation for text.
    Provides fast, reproducible semantic feature representations.
    """
    words = re.findall(r'\w+', text.lower())
    if not words:
        return [0.0] * dim

    vec = [0.0] * dim
    for word in words:
        h = hash(word)
        idx = abs(h) % dim
        sign = 1.0 if h > 0 else -1.0
        vec[idx] += sign * 1.0

    # L2 normalize vector
    magnitude = math.sqrt(sum(v * v for v in vec))
    if magnitude > 0:
        vec = [v / magnitude for v in vec]

    return vec


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    return float(dot_product)
