import os
import json
import tempfile
from pathlib import Path
from embedder import text_to_vector, cosine_similarity
from chunker import process_transcript_file, generate_chunk_hash


def test_text_to_vector_basic():
    vec = text_to_vector("Hello World")
    assert len(vec) == 384
    # Should be L2-normalized (magnitude ~= 1.0)
    magnitude = sum(v * v for v in vec) ** 0.5
    assert abs(magnitude - 1.0) < 0.01


def test_text_to_vector_empty():
    vec = text_to_vector("")
    assert len(vec) == 384
    assert all(v == 0.0 for v in vec)


def test_text_to_vector_deterministic():
    v1 = text_to_vector("Growth loops PLG strategy")
    v2 = text_to_vector("Growth loops PLG strategy")
    assert v1 == v2


def test_cosine_similarity_identical():
    v1 = text_to_vector("Product-led growth")
    score = cosine_similarity(v1, v1)
    assert abs(score - 1.0) < 0.01


def test_cosine_similarity_different():
    v1 = text_to_vector("product growth marketing strategy")
    v2 = text_to_vector("quantum physics electron particle")
    score = cosine_similarity(v1, v2)
    assert score < 0.5  # Very different topics should have low similarity


def test_cosine_similarity_mismatched_lengths():
    score = cosine_similarity([1.0, 0.0], [1.0])
    assert score == 0.0


def test_cosine_similarity_empty():
    score = cosine_similarity([], [])
    assert score == 0.0


def test_generate_chunk_hash():
    h1 = generate_chunk_hash("ep-1", "Hello world")
    h2 = generate_chunk_hash("ep-1", "Hello world")
    h3 = generate_chunk_hash("ep-2", "Hello world")
    assert h1 == h2  # Same input = same hash
    assert h1 != h3  # Different episode = different hash
    assert len(h1) == 64  # SHA256 hex digest length


def test_process_transcript_file():
    transcript_data = {
        "episode_id": "ep-test",
        "episode_title": "Test Episode",
        "guest_name": "Test Guest",
        "episode_url": "https://example.com/test",
        "transcript": [
            {
                "timestamp_start": "00:01:00",
                "timestamp_end": "00:05:00",
                "text": "This is a test transcript block about product growth."
            },
            {
                "timestamp_start": "00:05:01",
                "timestamp_end": "00:10:00",
                "text": "This is a second block about retention metrics."
            },
            {
                "timestamp_start": "00:10:01",
                "timestamp_end": "00:15:00",
                "text": ""
            }
        ]
    }

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(transcript_data, f)
        temp_path = f.name

    try:
        chunks = process_transcript_file(temp_path)
        assert len(chunks) == 2  # Empty text block should be skipped
        assert chunks[0]["episode_id"] == "ep-test"
        assert chunks[0]["episode_title"] == "Test Episode"
        assert chunks[0]["guest_name"] == "Test Guest"
        assert chunks[0]["timestamp_start"] == "00:01:00"
        assert chunks[0]["timestamp_end"] == "00:05:00"
        assert "product growth" in chunks[0]["content"]
        assert "content_hash" in chunks[0]
    finally:
        os.unlink(temp_path)
