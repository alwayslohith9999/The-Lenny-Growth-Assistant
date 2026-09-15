"""Pytest test harness and fixtures.

Uses an isolated in-memory SQLite database with transaction rollbacks and
pre-populated transcript chunks for deterministic integration testing.
"""
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend and ingestion directories to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "ingestion"))

from app.database import Base, get_db
from app.main import app
from app.models import Session as SessionModel, TranscriptChunk
from app.services.rag_service import text_to_vector

# In-memory SQLite with StaticPool ensures all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initializes schema once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provides a transactional database session rolled back after every test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with database session dependency override."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_transcripts(db_session):
    """Populates realistic podcast transcript chunks for RAG pipeline testing."""
    chunks_data = [
        {
            "id": "chunk-elena-01",
            "episode_id": "ep-elena-verna",
            "episode_title": "Elena Verna on B2B Product-Led Growth and Funnels",
            "guest_name": "Elena Verna",
            "timestamp_start": "00:08:15",
            "timestamp_end": "00:11:30",
            "episode_url": "https://lennyspodcast.com/elena-verna",
            "content": (
                "Product-led growth is not a replacement for sales; it is an acquisition motion. "
                "The core of B2B PLG is creating an end-user habit loop before introducing commercial friction. "
                "Once you see multiple users in a single company domain, that is your trigger for sales-assist."
            )
        },
        {
            "id": "chunk-balfour-01",
            "episode_id": "ep-brian-balfour",
            "episode_title": "Brian Balfour on Growth Loops vs Funnels",
            "guest_name": "Brian Balfour",
            "timestamp_start": "00:14:20",
            "timestamp_end": "00:18:00",
            "episode_url": "https://lennyspodcast.com/brian-balfour",
            "content": (
                "Traditional marketing funnels are linear: you pour money in at the top and get customers out the bottom. "
                "Growth loops are closed systems where one cohort of users directly generates the input for the next cohort. "
                "Viral loops, content loops, and paid loops are the three foundational architectures."
            )
        }
    ]

    for item in chunks_data:
        chunk = TranscriptChunk(
            id=item["id"],
            episode_id=item["episode_id"],
            episode_title=item["episode_title"],
            guest_name=item["guest_name"],
            timestamp_start=item["timestamp_start"],
            timestamp_end=item["timestamp_end"],
            episode_url=item["episode_url"],
            content=item["content"],
            embedding=text_to_vector(item["content"])
        )
        db_session.add(chunk)
    db_session.commit()
    return chunks_data
