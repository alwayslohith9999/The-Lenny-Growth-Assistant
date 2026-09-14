import React from 'react'

export function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  activeProvider
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="logo-icon">⚡</span>
        <h1 className="sidebar-title">Lenny Growth</h1>
      </div>

      <button className="new-chat-btn" onClick={onNewSession}>
        <span>+</span> New Growth Chat
      </button>

      <div className="session-list">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`session-item ${s.id === activeSessionId ? 'active' : ''}`}
            onClick={() => onSelectSession(s.id)}
          >
            <span className="session-title-text">{s.title || 'Growth Chat'}</span>
            <button
              className="delete-session-btn"
              onClick={(e) => {
                e.stopPropagation()
                onDeleteSession(s.id)
              }}
              title="Delete session"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="provider-badge-box">
        <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>ACTIVE RUNTIME</div>
        <div className="provider-status">
          <span className="status-dot"></span>
          <span>{activeProvider ? activeProvider.toUpperCase() : 'ANTHROPIC'}</span>
        </div>
      </div>
    </aside>
  )
}
