import React, { useState, useEffect } from 'react'
import { Sidebar } from './components/Sidebar'
import { ChatWindow } from './components/ChatWindow'
import { ArtifactViewer } from './components/ArtifactViewer'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [activeArtifact, setActiveArtifact] = useState(null)
  const [activeProvider, setActiveProvider] = useState('anthropic')
  const [isLoading, setIsLoading] = useState(false)

  // Fetch initial session list
  useEffect(() => {
    fetchSessions()
  }, [])

  // Fetch messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId)
    } else {
      setMessages([])
    }
  }, [activeSessionId])

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/sessions`)
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
        if (data.length > 0 && !activeSessionId) {
          setActiveSessionId(data[0].id)
        }
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    }
  }

  const fetchMessages = async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`)
      if (res.ok) {
        const data = await res.json()
        setMessages(data)

        // Auto open latest artifact if available
        const latestWithArtifact = [...data].reverse().find((m) => m.metadata?.artifact)
        if (latestWithArtifact) {
          setActiveArtifact(latestWithArtifact.metadata.artifact)
        }
      }
    } catch (err) {
      console.error('Failed to fetch messages:', err)
    }
  }

  const handleCreateSession = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Growth Chat', provider_preference: activeProvider })
      })
      if (res.ok) {
        const newSession = await res.json()
        setSessions((prev) => [newSession, ...prev])
        setActiveSessionId(newSession.id)
        setActiveArtifact(null)
      }
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  }

  const handleDeleteSession = async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, { method: 'DELETE' })
      if (res.ok) {
        const remaining = sessions.filter((s) => s.id !== sessionId)
        setSessions(remaining)
        if (activeSessionId === sessionId) {
          setActiveSessionId(remaining.length > 0 ? remaining[0].id : null)
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  const handleSendMessage = async (text) => {
    let currentSessionId = activeSessionId
    if (!currentSessionId) {
      // Auto-create session if none exists
      const res = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: text.slice(0, 30), provider_preference: activeProvider })
      })
      if (res.ok) {
        const newSession = await res.json()
        setSessions((prev) => [newSession, ...prev])
        currentSessionId = newSession.id
        setActiveSessionId(currentSessionId)
      } else {
        return
      }
    }

    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${currentSessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, provider: activeProvider })
      })
      if (res.ok) {
        await fetchMessages(currentSessionId)
      }
    } catch (err) {
      console.error('Failed to send message:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateEssay = async (promptText) => {
    if (!activeSessionId) return
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${activeSessionId}/essay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: promptText, provider: activeProvider })
      })
      if (res.ok) {
        const messageData = await res.json()
        await fetchMessages(activeSessionId)
        if (messageData.metadata?.artifact) {
          setActiveArtifact(messageData.metadata.artifact)
        }
      }
    } catch (err) {
      console.error('Failed to generate essay:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        activeProvider={activeProvider}
      />

      <ChatWindow
        messages={messages}
        onSendMessage={handleSendMessage}
        onGenerateEssay={handleGenerateEssay}
        onOpenArtifact={setActiveArtifact}
        activeProvider={activeProvider}
        onProviderChange={setActiveProvider}
        isLoading={isLoading}
      />

      {activeArtifact && (
        <ArtifactViewer
          artifact={activeArtifact}
          onClose={() => setActiveArtifact(null)}
        />
      )}
    </div>
  )
}

export default App
