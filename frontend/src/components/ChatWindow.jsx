import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const STARTER_PROMPTS = [
  "What does Elena Verna recommend for building sustainable B2B PLG funnels?",
  "How does Brian Balfour explain the difference between growth loops and traditional funnels?",
  "What are Shreyas Doshi's key principles on product thinking and high-agency PM execution?",
  "Explain usage-based pricing versus seat-based pricing triggers."
]

export function ChatWindow({
  messages,
  onSendMessage,
  onGenerateEssay,
  onOpenArtifact,
  activeProvider,
  onProviderChange,
  isLoading,
  onToggleSidebar
}) {
  const [inputText, setInputText] = useState('')
  const [expandedCitations, setExpandedCitations] = useState({})
  const [copiedMsgId, setCopiedMsgId] = useState(null)
  const feedRef = useRef(null)

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!inputText.trim() || isLoading) return
    onSendMessage(inputText.trim())
    setInputText('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const toggleCitations = (msgId) => {
    setExpandedCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }))
  }

  const handleCopyMessage = async (msgId, text) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedMsgId(msgId)
      setTimeout(() => setCopiedMsgId(null), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  // Use the original user question as the essay retrieval query,
  // not the assistant's long markdown answer.
  const getEssayPrompt = (assistantIdx) => {
    for (let i = assistantIdx - 1; i >= 0; i--) {
      if (messages[i].role === 'user') return messages[i].content
    }
    return messages[assistantIdx].content
  }

  return (
    <div className="chat-window">
      <header className="chat-header">
        <div className="chat-title-group">
          <button
            className="mobile-hamburger-btn"
            onClick={onToggleSidebar}
            aria-label="Toggle navigation sidebar"
          >
            ☰
          </button>
          <h2>Lenny Growth Assistant</h2>
        </div>

        <div className="provider-selector-toggle">
          <label htmlFor="provider-select">Provider:</label>
          <select
            id="provider-select"
            value={activeProvider}
            onChange={(e) => onProviderChange(e.target.value)}
            aria-label="Select active LLM provider"
          >
            <option value="anthropic">Anthropic (Claude 3.5)</option>
            <option value="openai">OpenAI (GPT-4o)</option>
            <option value="ollama">Ollama (Local Llama)</option>
          </select>
        </div>
      </header>

      <div
        className="messages-feed"
        ref={feedRef}
        role="log"
        aria-live="polite"
        aria-label="Conversation messages"
      >
        {messages.length === 0 ? (
          <div className="empty-state-container">
            <div className="empty-state-hero">
              <span className="hero-badge">Curated Transcript Knowledge Base</span>
              <h3>Ask Lenny's Podcast Insights</h3>
              <p>
                Query battle-tested growth frameworks from Elena Verna, Brian Balfour,
                Shreyas Doshi, and more, or generate a Ship 30 for 30 executive essay.
              </p>
            </div>

            <div className="starter-prompts-grid">
              {STARTER_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  className="starter-prompt-card"
                  onClick={() => onSendMessage(prompt)}
                  disabled={isLoading}
                >
                  <span className="prompt-icon">💡</span>
                  <span className="prompt-text">{prompt}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, idx) => {
            const citations = m.metadata?.citations || []
            const artifact = m.metadata?.artifact
            const isExpanded = !!expandedCitations[m.id]
            const isAssistant = m.role === 'assistant'
            const isCopied = copiedMsgId === m.id
            const latency = m.metadata?.latency_ms
            const providerUsed = m.metadata?.provider_used

            return (
              <div key={m.id} className={`message-row ${m.role}`}>
                <div className="message-bubble">
                  <div className="message-top-bar">
                    <span className="message-role-label">
                      {isAssistant ? '⚡ Assistant' : '👤 You'}
                    </span>
                    {isAssistant && (
                      <div className="message-meta-tags">
                        {providerUsed && (
                          <span className="meta-tag provider-tag" title="Provider used">
                            {providerUsed}
                          </span>
                        )}
                        {latency !== undefined && latency > 0 && (
                          <span className="meta-tag latency-tag" title="Generation latency">
                            {latency}ms
                          </span>
                        )}
                        <button
                          className="copy-msg-btn"
                          onClick={() => handleCopyMessage(m.id, m.content)}
                          aria-label="Copy message text"
                          title="Copy message"
                        >
                          {isCopied ? '✓ Copied' : '📋 Copy'}
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="markdown-body">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ node, ...props }) => (
                          <a {...props} target="_blank" rel="noreferrer" />
                        )
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  </div>

                  {artifact && (
                    <div className="message-actions">
                      <button
                        className="action-chip artifact-chip"
                        onClick={() => onOpenArtifact(artifact)}
                        aria-label={`Open generated artifact: ${artifact.title}`}
                      >
                        📄 Open Artifact: {artifact.title}
                      </button>
                    </div>
                  )}

                  {isAssistant && !artifact && (
                    <div className="message-actions">
                      <button
                        className="action-chip essay-chip"
                        onClick={() => onGenerateEssay(getEssayPrompt(idx))}
                        disabled={isLoading}
                        aria-label="Generate Ship 30 for 30 essay from this answer"
                      >
                        ✍️ Generate Ship 30 Essay
                      </button>
                    </div>
                  )}

                  {citations.length > 0 && (
                    <div className="citations-box" aria-label="Grounded source citations">
                      <div
                        className="citations-header"
                        onClick={() => toggleCitations(m.id)}
                        role="button"
                        tabIndex={0}
                        aria-expanded={isExpanded}
                        aria-label={`${citations.length} Grounded Source Citations`}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            toggleCitations(m.id)
                          }
                        }}
                      >
                        <span>📚 {citations.length} Grounded Source Citations</span>
                        <span aria-hidden="true">{isExpanded ? '▲' : '▼'}</span>
                      </div>

                      {isExpanded && (
                        <div className="citations-content">
                          {citations.map((c, cIdx) => (
                            <div key={cIdx} className="citation-card">
                              <a
                                href={c.episode_url || '#'}
                                target="_blank"
                                rel="noreferrer"
                                className="citation-link"
                              >
                                {c.episode_title} ({c.guest_name}) [{c.timestamp_start}-{c.timestamp_end}]
                              </a>
                              {c.score !== undefined && (
                                <span className="citation-score">
                                  Match: {Math.round(c.score * 100)}%
                                </span>
                              )}
                              <p className="citation-snippet">{c.content_snippet}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}

        {isLoading && (
          <div className="message-row assistant">
            <div className="message-bubble thinking-bubble" role="status" aria-label="Loading response">
              <span className="thinking-spinner" aria-hidden="true">⚡</span>
              <span>Retrieving podcast transcripts & synthesizing...</span>
              <span className="pulse-dots" aria-hidden="true">...</span>
            </div>
          </div>
        )}
      </div>

      <div className="input-container">
        <form onSubmit={handleSubmit} className="input-box">
          <textarea
            className="chat-textarea"
            placeholder="Ask a question about PLG, growth loops, metrics... (Shift+Enter for newline)"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            aria-label="Message input"
          />
          <button
            type="submit"
            className="send-btn"
            disabled={isLoading || !inputText.trim()}
            aria-label="Send message"
          >
            {isLoading ? '...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}