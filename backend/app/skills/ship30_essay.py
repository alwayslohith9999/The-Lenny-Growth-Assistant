import logging
from typing import Dict, Any, List
from app.skills.base import BaseSkill
from app.llm import generate_with_fallback

logger = logging.getLogger(__name__)

SHIP30_SYSTEM_PROMPT = """You are an expert growth strategist and master copywriter trained in the official Ship 30 for 30 digital writing framework.

YOUR MANDATE:
Transform the provided grounded transcript insights into a high-impact, ~1,250-word Ship 30 for 30 style essay formatted cleanly in Markdown.

SHIP 30 FOR 30 WRITING PRINCIPLES:
1. THE HOOK (Lines 1-3):
   - Start with a compelling headline (H1) and a punchy 1-2 sentence hook.
   - Address a high-stakes problem or counter-intuitive growth mistake.

2. NARRATIVE PROGRESSION:
   - Structure into 4 clear sections using Markdown H2 headers:
     * Section 1: The Core Misconception / High-Stakes Problem
     * Section 2: The Breakthrough Framework (Grounded in Lenny's Podcast Guest insights)
     * Section 3: Tactical Execution Pillars (Step-by-step skimmable rules)
     * Section 4: The 24-Hour Actionable Takeaway
   - Short sentences. Paragraphs must NEVER exceed 3 sentences.

3. HIGH-CONTRAST SKIMMABLE FORMATTING:
   - Use **Bolded Lead-ins** for every bullet point.
   - Use clear bullet points and numbered lists.
   - Use horizontal rules (`---`) between major sections.

4. STRICT GROUNDING & ATTRIBUTION:
   - All strategic recommendations, metrics, and frameworks MUST trace directly back to the provided transcript sources.
   - Explicitly credit the guest (e.g. "As Elena Verna explains...", "According to Brian Balfour...").
   - Include source citations in brackets `[Episode Title, Timestamp]` where key claims are made.

5. TARGET LENGTH & WORD BUDGET:
   - Target ~1,250 words of rich, comprehensive, actionable content.
"""


class Ship30EssaySkill(BaseSkill):
    @property
    def name(self) -> str:
        return "ship30_essay_generator"

    @property
    def description(self) -> str:
        return "Generates a ~1,250 word Ship 30 for 30 style Markdown essay grounded in Lenny's Podcast transcripts."

    def run(self, input_text: str, context_chunks: List[Dict[str, Any]], provider_name: str = None) -> Dict[str, Any]:
        context_blocks = []
        citations = []

        for i, chunk in enumerate(context_chunks, 1):
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
                "content_snippet": chunk["content"][:150] + "...",
                "score": chunk.get("score", 1.0)
            })

        formatted_context = "\n---\n".join(context_blocks)
        full_system_prompt = f"{SHIP30_SYSTEM_PROMPT}\n\nPROVIDED TRANSCRIPT SOURCES:\n{formatted_context}"

        messages = [
            {"role": "user", "content": f"Write a comprehensive Ship 30 for 30 style essay addressing: '{input_text}'"}
        ]

        llm_res = generate_with_fallback(
            messages=messages,
            system=full_system_prompt,
            requested_provider=provider_name
        )

        essay_markdown = llm_res["content"]

        # Ensure title extracted cleanly
        first_line = essay_markdown.strip().split("\n")[0]
        essay_title = first_line.replace("#", "").strip() if first_line.startswith("#") else f"Ship 30 Essay: {input_text[:40]}"

        artifact = {
            "type": "markdown",
            "title": essay_title,
            "content": essay_markdown
        }

        return {
            "content": essay_markdown,
            "artifact": artifact,
            "citations": citations,
            "provider_used": llm_res.get("provider"),
            "model_used": llm_res.get("model")
        }
