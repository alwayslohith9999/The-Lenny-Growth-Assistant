"""Retrieval-Augmented Generation (RAG) service.

Handles deterministic query embedding, transcript chunk ranking via cosine similarity
and keyword overlap, and structured context assembly for downstream prompts.
"""
import hashlib
import math
import re
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session as DBSession
from app.models import TranscriptChunk

logger = logging.getLogger(__name__)

VECTOR_DIM = 384


def _deterministic_hash(word: str) -> int:
    """Returns a deterministic 64-bit signed integer hash for a string."""
    digest = hashlib.md5(word.encode("utf-8")).hexdigest()
    val = int(digest[:16], 16)
    if val >= (1 << 63):
        val -= (1 << 64)
    return val


def _extract_keywords(text: str) -> set:
    """Extracts normalized lowercase keywords (4+ chars) from text, stripping punctuation."""
    return set(w.lower() for w in re.findall(r"\w+", text) if len(w) > 3)


def text_to_vector(text: str, dim: int = VECTOR_DIM) -> List[float]:
    """Generates a normalized dense vector embedding representation for text."""
    words = re.findall(r"\w+", text.lower())
    if not words:
        return [0.0] * dim

    vec = [0.0] * dim
    for word in words:
        h = _deterministic_hash(word)
        idx = abs(h) % dim
        sign = 1.0 if h >= 0 else -1.0
        vec[idx] += sign * 1.0

    magnitude = math.sqrt(sum(v * v for v in vec))
    if magnitude > 0:
        vec = [v / magnitude for v in vec]
    return vec


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two unit vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    return float(sum(a * b for a, b in zip(vec1, vec2)))


class RAGService:
    """Service for retrieving and assembling grounded transcript chunks."""

    @staticmethod
    def retrieve_relevant_chunks(db: DBSession, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Searches indexed transcript chunks using combined dense vector similarity and keyword overlap."""
        query_vec = text_to_vector(query)
        chunks = db.query(TranscriptChunk).all()
        if not chunks:
            logger.info("No transcript chunks indexed in database.")
            return []

        scored_chunks: List[Tuple[float, TranscriptChunk]] = []
        query_words = _extract_keywords(query)

        for chunk in chunks:
            chunk_vec = chunk.embedding or []
            base_score = cosine_similarity(query_vec, chunk_vec) if chunk_vec else 0.0

            chunk_words = _extract_keywords(chunk.content)
            overlap = len(query_words.intersection(chunk_words))

            if overlap == 0 and base_score < 0.1:
                score = 0.0
            else:
                score = min(1.0, max(0.0, base_score * 0.7 + min(overlap * 0.08, 0.3)))

            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored_chunks[:top_k]:
            if score >= 0.12:  # Grounded relevance threshold
                results.append({
                    "chunk_id": chunk.id,
                    "episode_id": chunk.episode_id,
                    "episode_title": chunk.episode_title,
                    "guest_name": chunk.guest_name,
                    "timestamp_start": chunk.timestamp_start,
                    "timestamp_end": chunk.timestamp_end,
                    "episode_url": chunk.episode_url,
                    "content": chunk.content,
                    "score": round(score, 4)
                })

        return results

    @staticmethod
    def build_prompt_context(chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """Formats retrieved chunks into a structured prompt context block and citations list."""
        context_blocks = []
        citations = []

        for i, chunk in enumerate(chunks, 1):
            context_blocks.append(
                f"[Source {i}]: Episode '{chunk['episode_title']}' by {chunk['guest_name']} "
                f"({chunk['timestamp_start']}-{chunk['timestamp_end']})\n"
                f"URL: {chunk['episode_url']}\n"
                f"Content: {chunk['content']}\n"
            )
            citations.append({
                "chunk_id": chunk["chunk_id"],
                "episode_title": chunk["episode_title"],
                "guest_name": chunk["guest_name"],
                "timestamp_start": chunk["timestamp_start"],
                "timestamp_end": chunk["timestamp_end"],
                "episode_url": chunk["episode_url"],
                "content_snippet": chunk["content"][:160] + "...",
                "score": chunk.get("score", 1.0)
            })

        formatted_context = "\n---\n".join(context_blocks)
        return formatted_context, citations