import React, { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function ArtifactViewer({ artifact, onClose }) {
  const [viewMode, setViewMode] = useState('rendered') // 'rendered' | 'raw'
  const [isCopied, setIsCopied] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!artifact) return null

  const isHtml = artifact.type === 'html'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content || '')
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy artifact:', err)
    }
  }

  const handleDownload = () => {
    const extension = isHtml ? 'html' : 'md'
    const mimeType = isHtml ? 'text/html' : 'text/markdown'
    const blob = new Blob([artifact.content || ''], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${artifact.title ? artifact.title.toLowerCase().replace(/\s+/g, '_') : 'artifact'}.${extension}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Defense-in-depth: prevent artifact content from closing the wrapper
  // document via injected </body> or </html> tags inside the srcdoc.
  const safeContent = (artifact.content || '').replace(/<\/(body|html)/gi, '<\\/$1')

  const iframeSrcDoc = isHtml
    ? `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data: https:;">
        <style>
          body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 2rem; color: #1e293b; background: #ffffff; line-height: 1.6; }
          h1, h2, h3 { color: #0f172a; }
          pre { background: #f1f5f9; padding: 1rem; border-radius: 6px; overflow-x: auto; }
          code { font-family: ui-monospace, SFMono-Regular, monospace; font-size: 0.9em; }
        </style>
      </head>
      <body>
        ${safeContent}
      </body>
    </html>
  `
    : ''

  return (
    <aside
      className="artifact-viewer-pane"
      role="region"
      aria-label={`Artifact: ${artifact.title}`}
    >
      <div className="artifact-header">
        <div className="artifact-title-group">
          <span className={`artifact-badge ${artifact.type}`}>
            {artifact.type.toUpperCase()}
          </span>
          <h3 className="artifact-title">{artifact.title}</h3>
        </div>

        <div className="artifact-controls">
          <div className="security-indicator" title="Sandbox protection active">
            <span className="shield-icon" aria-hidden="true">🛡️</span>
            <span className="security-text">
              {isHtml ? 'Sandboxed (null origin)' : 'Sanitized Markdown'}
            </span>
          </div>

          <div className="toggle-group" role="tablist" aria-label="View format">
            <button
              className={`toggle-btn ${viewMode === 'rendered' ? 'active' : ''}`}
              onClick={() => setViewMode('rendered')}
              role="tab"
              aria-selected={viewMode === 'rendered'}
            >
              Rendered
            </button>
            <button
              className={`toggle-btn ${viewMode === 'raw' ? 'active' : ''}`}
              onClick={() => setViewMode('raw')}
              role="tab"
              aria-selected={viewMode === 'raw'}
            >
              Raw Source
            </button>
          </div>

          <button
            className="artifact-action-btn"
            onClick={handleCopy}
            title="Copy artifact content to clipboard"
            aria-label="Copy artifact content"
          >
            {isCopied ? '✓ Copied' : '📋 Copy'}
          </button>

          <button
            className="artifact-action-btn"
            onClick={handleDownload}
            title="Download artifact file"
            aria-label="Download artifact file"
          >
            ⬇️ Export
          </button>

          <button
            className="close-btn"
            onClick={onClose}
            title="Close Pane (Esc)"
            aria-label="Close artifact pane"
          >
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
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {artifact.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </aside>
  )
}