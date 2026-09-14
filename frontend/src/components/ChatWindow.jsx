import React, { useState, useRef, useEffect } from 'react'

export function ChatWindow({
  messages,
  onSendMessage,
  onGenerateEssay,
  onOpenArtifact,
  activeProvider,
  onProviderChange,
  isLoading
}) {
  const [inputText, setInputText] = useState('')
  const [expandedCitations, setExpandedCitations] = useState({})
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

  return (
    <div className="chat-window">
      <header className="chat-header">
        <div className="chat-title-group">
          <h2>Lenny Growth Assistant</h2>
        </div>

        <div className="provider-selector-toggle">
          <label htmlFor="provider-select">Provider:</label>
          <select
            id="provider-select"
            value={activeProvider}
            onChange={(e) => onProviderChange(e.target.value)}
          >
            <option value="anthropic">Anthropic (Claude 3.5)</option>
            <option value="openai">OpenAI (GPT-4o)</option>
            <option value="ollama">Ollama (Local Llama)</option>
          </select>
        </div>
      </header>

      <div className="messages-feed" ref={feedRef}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', margin: 'auto', color: '#94a3b8' }}>
            <h3 style={{ fontSize: '1.4rem', color: '#fff', marginBottom: '0.5rem' }}>
              Ask Lenny's Podcast Knowledge Base
            </h3>
            <p style={{ maxWidth: '480px', margin: '0 auto' }}>
              Get citable growth frameworks from Elena Verna, Brian Balfour, Shreyas Doshi, and more, or generate a Ship 30 for 30 essay.
            </p>
          </div>
        ) : (
          messages.map((m) => {
            const citations = m.metadata?.citations || []
            const artifact = m.metadata?.artifact
            const isExpanded = expandedCitations[m.id]

            return (
              <div key={m.id} className={`message-row ${m.role}`}>
                <div className="message-bubble">
                  {m.content}

                  {artifact && (
                    <div className="message-actions">
                      <button
                        className="action-chip"
                        onClick={() => onOpenArtifact(artifact)}
                      >
                        📄 Open Artifact: {artifact.title}
                      </button>
                    </div>
                  )}

                  {m.role === 'assistant' && !artifact && (
                    <div className="message-actions">
                      <button
                        className="action-chip"
                        onClick={() => onGenerateEssay(m.content)}
                      >
                        ✍️ Generate Ship 30 Essay
                      </button>
                    </div>
                  )}

                  {citations.length > 0 && (
                    <div className="citations-box">
                      <div
                        className="citations-header"
                        style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}
                        onClick={() => toggleCitations(m.id)}
                      >
                        <span>📚 {citations.length} Grounded Source Citations</span>
                        <span>{isExpanded ? '▲' : '▼'}</span>
                      </div>

                      {isExpanded &&
                        citations.map((c, idx) => (
                          <div key={idx} className="citation-card">
                            <a
                              href={c.episode_url || '#'}
                              target="_blank"
                              rel="noreferrer"
                              className="citation-link"
                            >
                              {c.episode_title} ({c.guest_name}) [{c.timestamp_start}-{c.timestamp_end}]
                            </a>
                            <p className="citation-snippet">{c.content_snippet}</p>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}

        {isLoading && (
          <div className="message-row assistant">
            <div className="message-bubble" style={{ color: '#94a3b8', display: 'flex', gap: '8px' }}>
              <span>Thinking & Retrieving Transcripts</span>
              <span className="pulse-dots">...</span>
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
          />
          <button type="submit" className="send-btn" disabled={isLoading || !inputText.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
