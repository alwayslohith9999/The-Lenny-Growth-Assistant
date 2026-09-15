"""Unit tests for RAGService, deterministic embeddings, and similarity metrics."""
import pytest
from app.services.rag_service import text_to_vector, cosine_similarity, RAGService
from app.models import TranscriptChunk


def test_text_to_vector_determinism():
    """Verifies that vector generation is 100% deterministic across multiple runs."""
    text = "Product-led growth and viral acquisition loops"
    vec1 = text_to_vector(text)
    vec2 = text_to_vector(text)

    assert len(vec1) == 384
    assert len(vec2) == 384
    assert vec1 == vec2


def test_text_to_vector_normalization():
    """Verifies that generated vectors are L2-normalized unit vectors."""
    import math
    text = "Elena Verna PLG monetization"
    vec = text_to_vector(text)
    magnitude = math.sqrt(sum(v * v for v in vec))
    assert abs(magnitude - 1.0) < 1e-4


def test_cosine_similarity_identical():
    """Verifies cosine similarity of identical vectors equals 1.0."""
    vec = text_to_vector("Retention and habit loops")
    assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-4


def test_cosine_similarity_empty():
    """Verifies cosine similarity handles empty inputs safely."""
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0


def test_rag_service_retrieval(db_session, seed_transcripts):
    """Verifies RAGService returns top relevant chunks matching the query."""
    results = RAGService.retrieve_relevant_chunks(db_session, "growth loops vs traditional funnels", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "Brian Balfour" in top_result["guest_name"]
    assert top_result["score"] > 0.12
