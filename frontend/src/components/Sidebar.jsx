import React from 'react'

export function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  activeProvider,
  isOpen,
  onClose
}) {
  return (
    <>
      {isOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={`sidebar ${isOpen ? 'open' : ''}`}
        aria-label="Chat Sessions"
      >
        <div className="sidebar-header">
          <div className="logo-group">
            <span className="logo-icon" aria-hidden="true">⚡</span>
            <h1 className="sidebar-title">Lenny Growth</h1>
          </div>
          <button
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            ✕
          </button>
        </div>

        <button
          className="new-chat-btn"
          onClick={() => {
            onNewSession()
            if (onClose) onClose()
          }}
          aria-label="Start a new growth chat session"
        >
          <span aria-hidden="true">+</span> New Growth Chat
        </button>

        <nav className="session-list" aria-label="Previous sessions">
          {sessions.length === 0 ? (
            <div className="sidebar-empty">No chats yet</div>
          ) : (
            <ul className="session-ul">
              {sessions.map((s) => {
                const isActive = s.id === activeSessionId
                return (
                  <li key={s.id} className="session-li">
                    <div
                      className={`session-item ${isActive ? 'active' : ''}`}
                      onClick={() => {
                        onSelectSession(s.id)
                        if (onClose) onClose()
                      }}
                      role="button"
                      tabIndex={0}
                      aria-current={isActive ? 'true' : undefined}
                      aria-label={`Select session: ${s.title || 'Growth Chat'}`}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          onSelectSession(s.id)
                          if (onClose) onClose()
                        }
                      }}
                    >
                      <span className="session-title-text">{s.title || 'Growth Chat'}</span>
                      <button
                        className="delete-session-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          if (window.confirm(`Delete chat "${s.title || 'Growth Chat'}"?`)) {
                            onDeleteSession(s.id)
                          }
                        }}
                        aria-label={`Delete chat: ${s.title || 'Growth Chat'}`}
                        title="Delete session"
                      >
                        ✕
                      </button>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </nav>

        <div className="provider-badge-box">
          <div className="provider-badge-label">ACTIVE RUNTIME</div>
          <div className="provider-status">
            <span className="status-dot" aria-hidden="true"></span>
            <span>{activeProvider ? activeProvider.toUpperCase() : 'ANTHROPIC'}</span>
          </div>
        </div>
      </aside>
    </>
  )
}
