# Design Specification (docs/design.md): Lenny Growth Assistant

## 1. UI/UX Core Principles
- **Clarity & High Signal-to-Noise:** Designed specifically for PMs and growth leads who require rapid, verifiable strategic insights. Clean typography, strong visual hierarchy, and high contrast eliminate fluff.
- **Side-by-Side Dual-Pane Workspace:** Chat and document artifact workflows occur in a single unified workspace. Generating essays or HTML prototypes immediately opens an isolated right pane without disturbing chat context.
- **Verifiable Transparency:** Every assistant answer features expandable citation accordions detailing guest names, episode titles, timestamp offsets, and direct podcast URLs.
- **Provider Awareness:** Clear, real-time indication of active runtime LLM engine (Cloud Anthropic/OpenAI vs Local Ollama) with zero-reload runtime switching.

## 2. Information Architecture & Layout Structure

```
+---------------------------------------------------------------------------------------------------+
|  SIDEBAR (280px)   |  CHAT WINDOW (Flex: 1)                              | ARTIFACT VIEWER (50%)  |
|  - App Title & Logo|  - Header: Active Session Title & Provider Selector | - Header: Title & Type |
|  - "+ New Chat"    |  - Messages Feed:                                   | - Security Badge       |
|  - Sessions List   |    * User Bubble (Primary Indigo gradient)          | - View Mode Toggle     |
|  - Active Provider |    * Assistant Bubble (Slate card + Citations)     |   (Rendered vs Raw)    |
|    Status Indicator|    * Action Chips: "✍️ Generate Ship 30 Essay"      | - Sandboxed <iframe    |
|                    |  - Input Bar: Textarea + Keyboard Submit (Enter)    |   srcdoc> or Markdown  |
+---------------------------------------------------------------------------------------------------+
```

## 3. Key Interaction States
1. **Empty State:**
   - Displays welcoming splash prompt encouraging high-value queries ("Ask Lenny's Podcast Knowledge Base").
   - Quick action suggestions (PLG vs Sales-led, Growth Loops, LNO Prioritization).
2. **Loading State:**
   - Animated pulse dots ("Thinking & Retrieving Transcripts...") provide immediate visual feedback while RAG retrieval and LLM generation occur.
3. **Citation Accordion State:**
   - Collapsed by default to maintain clean readability.
   - Click to expand reveals exact source episode metadata, guest name, timestamp bounds, and excerpt snippets.
4. **Artifact View State:**
   - Triggers automatically when an essay or artifact is generated.
   - Displays security badge (`Sandboxed (null origin)` for HTML or `Sanitized Markdown` for docs).
   - Instant toggle between rendered output and raw source code.

## 4. Responsive Layout Behavior
- **Desktop View ($> 1200\text{px}$):** Full three-column layout (Sidebar + Chat + Artifact Split Pane).
- **Tablet / Narrow View ($768\text{px} - 1199\text{px}$):** Artifact viewer overlays as a 60% right slide-over panel with explicit close controls (`✕`).
- **Mobile View ($< 768\text{px}$):** Sidebar collapses into top drawer toggle; chat occupies 100% viewport width.

## 5. Accessibility Considerations (a11y)
- **Keyboard Navigation:** Full support for `Enter` to submit, `Shift+Enter` for multi-line inputs, `Tab` focus ring indicators across all buttons and inputs.
- **Semantic HTML5:** Native `<aside>`, `<header>`, `<main>`, `<button>`, `<textarea>`, and `<iframe>` elements used throughout.
- **Contrast Ratios:** Text colors (`#f8fafc` on `#090d16` / `#1e293b`) meet WCAG AAA contrast ratio specifications ($\ge 7:1$).

## 6. Design Trade-Offs under Timebox
- **Pre-rendered Markdown vs Full WYSIWYG Editor:** Implemented a clean structured markdown previewer and raw source inspector rather than a complex heavy rich-text editor to guarantee 100% security sandboxing stability within the timeframe.
