import React, { useState } from 'react'

export function ArtifactViewer({ artifact, onClose }) {
  const [viewMode, setViewMode] = useState('rendered') // 'rendered' | 'raw'

  if (!artifact) return null

  const isHtml = artifact.type === 'html'
  const isMarkdown = artifact.type === 'markdown'

  // Construct CSP & sanitized srcdoc for sandboxed iframe rendering
  const iframeSrcDoc = isHtml ? `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data: https:;">
        <style>
          body { font-family: system-ui, -apple-system, sans-serif; padding: 1.5rem; color: #1e293b; background: #ffffff; }
        </style>
      </head>
      <body>
        ${artifact.content}
      </body>
    </html>
  ` : ''

  return (
    <div className="artifact-viewer-pane">
      <div className="artifact-header">
        <div className="artifact-title-group">
          <span className={`artifact-badge ${artifact.type}`}>
            {artifact.type.toUpperCase()}
          </span>
          <h3 className="artifact-title">{artifact.title}</h3>
        </div>

        <div className="artifact-controls">
          <div className="security-indicator">
            <span className="shield-icon">🛡️</span>
            <span className="security-text">
              {isHtml ? 'Sandboxed (null origin)' : 'Sanitized Markdown'}
            </span>
          </div>

          <div className="toggle-group">
            <button
              className={`toggle-btn ${viewMode === 'rendered' ? 'active' : ''}`}
              onClick={() => setViewMode('rendered')}
            >
              Rendered
            </button>
            <button
              className={`toggle-btn ${viewMode === 'raw' ? 'active' : ''}`}
              onClick={() => setViewMode('raw')}
            >
              Raw Source
            </button>
          </div>

          <button className="close-btn" onClick={onClose} title="Close Pane">
            ✕
          </button>
        </div>
      </div>

      <div className="artifact-body">
        {viewMode === 'raw' ? (
          <pre className="raw-source-code">
            <code>{artifact.content}</code>
          </pre>
        ) : isHtml ? (
          <iframe
            title={artifact.title}
            srcDoc={iframeSrcDoc}
            sandbox="allow-scripts"
            className="sandboxed-iframe"
          />
        ) : (
          <div className="markdown-rendered-container">
            {/* Simple structured markdown previewer */}
            <div dangerouslySetInnerHTML={{ __html: simpleMarkdownToHtml(artifact.content) }} />
          </div>
        )}
      </div>
    </div>
  )
}

// Lightweight Markdown parser helper for rendering structured headers, lists, bold text & code blocks
function simpleMarkdownToHtml(md) {
  if (!md) return ''
  let html = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^# (.*$)/gim, '<h1 class="md-h1">$1</h1>')
    .replace(/^## (.*$)/gim, '<h2 class="md-h2">$1</h2>')
    .replace(/^### (.*$)/gim, '<h3 class="md-h3">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^---$/gim, '<hr class="md-divider" />')
    .replace(/^- (.*$)/gim, '<li class="md-li">$1</li>')
    .replace(/\n\n/g, '<p class="md-p"></p>')

  return html
}
