import sys
import json
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))
sys.path.append(str(Path(__file__).parent.parent / "ingestion"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Create a session
session_res = client.post("/sessions", json={"title": "RAG Verification Test"})
session_data = session_res.json()
session_id = session_data["id"]
print(f"Created Session ID: {session_id}")

questions = [
    {
        "type": "Clearly Answerable",
        "query": "What is Elena Verna's advice on PLG vs Sales-led motion?"
    },
    {
        "type": "Partially Answerable",
        "query": "How do growth loops work according to Brian Balfour and what pricing model should I use for them?"
    },
    {
        "type": "Out of Scope",
        "query": "What is Quantum Supremacy according to Lenny's Podcast?"
    }
]

output_markdown = "# Grounded Conversational RAG Test Results\n\n"
output_markdown += f"**Session ID:** `{session_id}`\n\n"

for q in questions:
    print(f"Testing [{q['type']}]: {q['query']}")
    res = client.post(f"/sessions/{session_id}/messages", json={"content": q["query"]})
    if res.status_code != 200:
        print(f"Error {res.status_code}: {res.text}")
        continue
    data = res.json()
    
    output_markdown += f"## {q['type']} Question\n"
    output_markdown += f"**User Query:** \"{q['query']}\"\n\n"
    output_markdown += f"**Assistant Response:**\n{data['content']}\n\n"
    output_markdown += f"**Citations Returned ({len(data.get('metadata', {}).get('citations', []))}):**\n"
    for cit in data.get('metadata', {}).get('citations', []):
        output_markdown += f"- **Episode:** {cit['episode_title']} ({cit['guest_name']}) [{cit['timestamp_start']}-{cit['timestamp_end']}]\n"
        output_markdown += f"  - **Snippet:** *\"{cit['content_snippet']}\"*\n"
    output_markdown += "\n---\n\n"


output_file = Path(__file__).parent / "grounded_rag_test_results.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(output_markdown)

print(f"Results written to {output_file}")
