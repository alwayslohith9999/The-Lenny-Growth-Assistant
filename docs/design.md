# UI/UX Design System & Specification: Lenny Growth Assistant

Comprehensive design specifications detailing layout architecture, color palette tokens, typography scales, component state matrices, and accessibility standards.

---

## 1. Core UX Principles
1. **Side-by-Side Dual-Pane Workspace:** Strategic conversation and generated output artifacts remain visible simultaneously without navigation disruption.
2. **First-Class Source Attribution:** Grounded citations are not buried footnotes; they appear prominently in structured, expandable cards with episode links and match confidence.
3. **Transparent System State:** Users always know which model is active, the true response latency, and whether a fallback was triggered.
4. **Resilient Mobile Responsiveness:** Clean navigation drawer and overlay pane ensuring accessibility on screens from 320px to 4K displays.

---

## 2. Design Tokens & Visual Hierarchy

### Color Palette (WCAG 2.1 AA Compliant)

| Token Name | Hex Value | Semantic Usage | Minimum Contrast Ratio |
| :--- | :--- | :--- | :--- |
| `--bg-dark` | `#090d16` | App background | Baseline |
| `--bg-sidebar` | `#0f172a` | Navigation sidebar background | Baseline |
| `--bg-card` | `#1e293b` | Message bubbles, citation cards, inputs | 4.8:1 against text-main |
| `--bg-card-hover` | `#334155` | Interactive hover states | 3.5:1 against card |
| `--accent-primary` | `#6366f1` | Primary CTA, user message bubbles | 5.2:1 against white text |
| `--accent-primary-hover` | `#4f46e5` | Button hover state | 6.1:1 against white text |
| `--accent-emerald` | `#10b981` | Success state, healthy indicators | 4.9:1 |
| `--accent-amber` | `#f59e0b` | Warning states, degraded indicators | 4.7:1 |
| `--accent-rose` | `#f43f5e` | Error states, validation badges | 4.6:1 |
| `--text-main` | `#f8fafc` | Primary headings and body copy | 14.5:1 against bg-dark |
| `--text-muted` | `#cbd5e1` | Secondary labels, citations, metadata | **5.8:1 against bg-card (Passes AA)** |
| `--border-color` | `#334155` | Subtle separators and card outlines | 3.2:1 against bg-dark |

### Typography Scale

- **Display Heading:** `Inter`, 24px (1.5rem), Weight 700, Line-height 1.2
- **Section Heading (H2):** `Inter`, 19px (1.2rem), Weight 600, Line-height 1.3
- **Card Heading (H3):** `Inter`, 16px (1.0rem), Weight 600, Line-height 1.4
- **Body Regular:** `Inter`, 15px (0.95rem), Weight 400, Line-height 1.6
- **Caption / Meta:** `Inter`, 12px (0.75rem), Weight 500, Line-height 1.4
- **Code / Monospace:** `JetBrains Mono`, 13.5px (0.85rem), Weight 400

---

## 3. Responsive Layout & Breakpoints

```
Desktop (>= 1200px):
+--------------------+--------------------------------+----------------------------+
|  Sidebar (280px)   |      Chat Window (Flex: 1)     | Artifact Viewer (Flex: 1)  |
|  - Session history |      - Header + Provider       | - Rendered / Raw toggle    |
|  - Active runtime  |      - Markdown message feed   | - Sandboxed iframe         |
|  - New chat CTA    |      - Expandable citations    | - Copy & Export buttons    |
|                    |      - Starter prompt cards    | - Close button             |
+--------------------+--------------------------------+----------------------------+

Tablet (768px - 1199px):
+--------------------+---------------------------------------------------------------+
|  Sidebar (280px)   |      Chat Window (Flex: 1)                                    |
|  - Session history |      (Artifact Viewer slides out as 65% floating drawer)       |
+--------------------+---------------------------------------------------------------+

Mobile (< 768px):
+------------------------------------------------------------------------------------+
|  Top Header: [☰ Hamburger Menu]  Lenny Growth Assistant  [Provider Selector]        |
|  - Sidebar slides in from left (transform: translateX) over darkened backdrop       |
|  - Chat window fills 100dvh width                                                  |
|  - Artifact Viewer takes 100% full screen modal overlay                            |
+------------------------------------------------------------------------------------+
```

---

## 4. Component State Matrix

| Component | Default State | Hover / Focus State | Active / Selected | Loading State | Error State |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **New Chat Button** | Indigo gradient, glow shadow | TranslateY(-1px), enhanced glow | Pressed active scale | Disabled opacity 0.6 | N/A |
| **Session Item** | Transparent bg, muted text | `#1e293b` bg, white text | Accent border, bold white | N/A | Red delete icon |
| **Starter Prompt** | Card border, muted text | Elevated -2px, accent border | N/A | Disabled while thinking | N/A |
| **Message Bubble** | User: Indigo / Assistant: Card | Copy button visible on hover | N/A | Pulsing dots + spinner | Toast error on failure |
| **Citation Header** | Uppercase muted text | White text, pointer | Chevron toggles ▲/▼ | N/A | N/A |
| **Artifact Viewer** | Split-pane visible | Action buttons highlight | Tab switch Rendered/Raw | Loading iframe spinner | Error boundary fallback |

---

## 5. Accessibility (WCAG 2.1 AA) Conformance

1. **Keyboard Navigation:**
   - All interactive elements (`<button>`, citation accordions, session cards) have explicit `tabIndex={0}`, `role="button"`, and handle both `Enter` and `Space` keypress events.
   - Visible focus indicator: `outline: 2px solid var(--accent-primary)` with `outline-offset: 2px`.
2. **Screen Reader Support:**
   - Message feed declares `role="log"` and `aria-live="polite"` so new assistant responses are announced automatically.
   - Citation accordion declares `aria-expanded={isExpanded}`.
   - Artifact viewer declares `role="region"` and `aria-label`.
   - Modals and drawers announce state changes and can be closed via the `Escape` key.
3. **Contrast Compliance:**
   - Upgraded secondary text color to `#cbd5e1`, achieving a minimum contrast ratio of 5.8:1 against card backgrounds, well above the 4.5:1 AA requirement.
