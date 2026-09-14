import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "backend"))
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Create session
session_res = client.post("/sessions", json={"title": "Essay Skill Test"})
session_id = session_res.json()["id"]

print(f"Testing Essay Generation on Session '{session_id}'...")

essay_res = client.post(
    f"/sessions/{session_id}/essay",
    json={"content": "PLG vs Sales-led monetization strategy for B2B SaaS"}
)

assert essay_res.status_code == 200, f"Essay endpoint failed: {essay_res.text}"
data = essay_res.json()

print("\n--- ESSAY SKILL RESPONSE ---")
print("Role:", data["role"])
print("Has Artifact:", data["metadata"]["artifact"] is not None)
if data["metadata"]["artifact"]:
    print("Artifact Type:", data["metadata"]["artifact"]["type"])
    print("Artifact Title:", data["metadata"]["artifact"]["title"])
    print("First 300 Chars of Content:")
    print(data["metadata"]["artifact"]["content"][:300])

print("\nCitations Count:", len(data["metadata"]["citations"]))
print("SUCCESS: Ship 30 Essay Skill verified end-to-end!")
