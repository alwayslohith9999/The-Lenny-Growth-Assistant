import hashlib
import json
from typing import List, Dict, Any


def generate_chunk_hash(episode_id: str, content: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(f"{episode_id}:{content}".encode("utf-8"))
    return hasher.hexdigest()


def process_transcript_file(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    episode_id = data.get("episode_id", "ep-unknown")
    episode_title = data.get("episode_title", "Untitled Episode")
    guest_name = data.get("guest_name", "Unknown Guest")
    episode_url = data.get("episode_url", "")
    transcript_blocks = data.get("transcript", [])

    chunks = []
    for block in transcript_blocks:
        content = block.get("text", "").strip()
        if not content:
            continue

        chunk_hash = generate_chunk_hash(episode_id, content)

        chunks.append({
            "episode_id": episode_id,
            "episode_title": episode_title,
            "guest_name": guest_name,
            "episode_url": episode_url,
            "timestamp_start": block.get("timestamp_start", "00:00:00"),
            "timestamp_end": block.get("timestamp_end", "00:00:00"),
            "content": content,
            "content_hash": chunk_hash
        })

    return chunks
