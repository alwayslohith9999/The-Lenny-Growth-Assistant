import os
import sys
import json
import logging
from pathlib import Path

# Add parent backend directory to sys.path to access app models & database
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.database import SessionLocal, engine, Base
from app.models import TranscriptChunk
from chunker import process_transcript_file
from embedder import text_to_vector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion")


def run_ingestion(transcripts_dir: str):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    transcripts_path = Path(transcripts_dir)
    if not transcripts_path.exists():
        print(json.dumps({"error": f"Directory '{transcripts_dir}' does not exist"}))
        return

    episodes_processed = 0
    chunks_created = 0
    chunks_skipped = 0
    failures = 0

    json_files = list(transcripts_path.glob("*.json"))
    for file_path in json_files:
        try:
            chunks = process_transcript_file(str(file_path))
            episodes_processed += 1

            for chunk_data in chunks:
                content_hash = chunk_data["content_hash"]
                
                # Idempotency check: check if chunk metadata already contains this content_hash
                existing = db.query(TranscriptChunk).filter(
                    TranscriptChunk.episode_id == chunk_data["episode_id"],
                    TranscriptChunk.timestamp_start == chunk_data["timestamp_start"]
                ).first()

                if existing:
                    chunks_skipped += 1
                    continue

                vector = text_to_vector(chunk_data["content"])

                new_chunk = TranscriptChunk(
                    episode_id=chunk_data["episode_id"],
                    episode_title=chunk_data["episode_title"],
                    episode_url=chunk_data["episode_url"],
                    guest_name=chunk_data["guest_name"],
                    timestamp_start=chunk_data["timestamp_start"],
                    timestamp_end=chunk_data["timestamp_end"],
                    content=chunk_data["content"],
                    embedding=vector,
                    metadata_json={"content_hash": content_hash}
                )
                db.add(new_chunk)
                chunks_created += 1

            db.commit()
        except Exception as e:
            failures += 1
            logger.error(f"Failed to ingest file {file_path}: {e}")
            db.rollback()

    db.close()

    stats = {
        "status": "completed",
        "episodes_processed": episodes_processed,
        "chunks_created": chunks_created,
        "chunks_skipped": chunks_skipped,
        "failures": failures
    }
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    transcripts_dir = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent / "transcripts")
    run_ingestion(transcripts_dir)
