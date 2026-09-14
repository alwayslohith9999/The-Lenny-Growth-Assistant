from typing import List, Dict, Any
from sqlalchemy.orm import Session as DBSession
from app.models import TranscriptChunk
from embedder import text_to_vector, cosine_similarity


def retrieve_relevant_chunks(db: DBSession, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Given a query string, embeds the query and performs cosine similarity search
    against indexed transcript chunks in the database.
    """
    query_vec = text_to_vector(query)
    chunks = db.query(TranscriptChunk).all()

    scored_chunks = []
    for chunk in chunks:
        chunk_vec = chunk.embedding or []
        score = cosine_similarity(query_vec, chunk_vec)
        
        # Word overlap boost for keyword accuracy
        query_words = set(query.lower().split())
        chunk_words = set(chunk.content.lower().split())
        overlap = len(query_words.intersection(chunk_words))
        score += (overlap * 0.05)

        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, chunk in scored_chunks[:top_k]:
        if score > 0.05:  # Relevance threshold
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
