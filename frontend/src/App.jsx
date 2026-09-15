import React, { useState, useEffect, useCallback } from 'react'
import { Sidebar } from './components/Sidebar'
import { ChatWindow } from './components/ChatWindow'
import { ArtifactViewer } from './components/ArtifactViewer'
import { api } from './api'
import { useToast } from './components/ToastProvider'

function App() {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [activeArtifact, setActiveArtifact] = useState(null)
  const [activeProvider, setActiveProvider] = useState('anthropic')
  const [isLoading, setIsLoading] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const { addToast } = useToast()

  // Fetch sessions once on mount; preserve valid active selection
  const fetchSessions = useCallback(async () => {
    try {
      const data = await api.getSessions()
      setSessions(data)
      setActiveSessionId((prev) =>
        prev && data.some((s) => s.id === prev) ? prev : data[0]?.id ?? null
      )
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
      addToast(err.message || 'Failed to load sessions', 'error')
    }
  }, [addToast])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  // Fetch messages when active session changes
  const fetchMessages = useCallback(async (sessionId) => {
    try {
      const data = await api.getMessages(sessionId)
      setMessages(data)

      const latestWithArtifact = [...data].reverse().find((m) => m.metadata?.artifact)
      setActiveArtifact(latestWithArtifact ? latestWithArtifact.metadata.artifact : null)
    } catch (err) {
      console.error('Failed to fetch messages:', err)
      addToast(err.message || 'Failed to load messages', 'error')
    }
  }, [addToast])

  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId)
    } else {
      setMessages([])
      setActiveArtifact(null)
    }
  }, [activeSessionId, fetchMessages])

  const handleCreateSession = async () => {
    try {
      const newSession = await api.createSession({
        title: 'New Growth Chat',
        provider_preference: activeProvider
      })
      setSessions((prev) => [newSession, ...prev])
      setActiveSessionId(newSession.id)
      setMessages([])
      setActiveArtifact(null)
      addToast('Created new chat session', 'success', 2000)
    } catch (err) {
      console.error('Failed to create session:', err)
      addToast(err.message || 'Failed to create new session', 'error')
    }
  }

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId)
      const remaining = sessions.filter((s) => s.id !== sessionId)
      setSessions(remaining)
      if (activeSessionId === sessionId) {
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null)
        setActiveArtifact(null)
      }
      addToast('Chat deleted', 'info', 2000)
    } catch (err) {
      console.error('Failed to delete session:', err)
      addToast(err.message || 'Failed to delete session', 'error')
    }
  }

  const handleSendMessage = async (text) => {
    let currentSessionId = activeSessionId

    if (!currentSessionId) {
      try {
        const newSession = await api.createSession({
          title: text.slice(0, 30),
          provider_preference: activeProvider
        })
        setSessions((prev) => [newSession, ...prev])
        currentSessionId = newSession.id
        setActiveSessionId(currentSessionId)
      } catch (err) {
        addToast(err.message || 'Failed to initialize session', 'error')
        return
      }
    }

    setIsLoading(true)

    const tempId = `temp-${Date.now()}`
    const optimisticMsg = {
      id: tempId,
      session_id: currentSessionId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
      metadata: null
    }
    setMessages((prev) => [...prev, optimisticMsg])

    try {
      const assistantMsg = await api.sendMessage(currentSessionId, {
        content: text,
        provider: activeProvider
      })

      setMessages((prev) => [...prev.filter((m) => m.id !== tempId), optimisticMsg, assistantMsg])

      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId && s.title === 'New Growth Chat'
            ? { ...s, title: text.slice(0, 35) + (text.length > 35 ? '...' : '') }
            : s
        )
      )
    } catch (err) {
      console.error('Failed to send message:', err)
      addToast(err.message || 'Failed to generate response. Check your API key or backend status.', 'error')
      setMessages((prev) => prev.filter((m) => m.id !== tempId))
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateEssay = async (promptText) => {
    if (!activeSessionId) return
    setIsLoading(true)

    try {
      const assistantMsg = await api.generateEssay(activeSessionId, {
        content: promptText,
        provider: activeProvider
      })

      setMessages((prev) => [...prev, assistantMsg])

      if (assistantMsg.metadata?.artifact) {
        setActiveArtifact(assistantMsg.metadata.artifact)
        addToast('Ship 30 for 30 Essay generated successfully!', 'success', 3000)
      }
    } catch (err) {
      console.error('Failed to generate essay:', err)
      addToast(err.message || 'Failed to generate Ship 30 essay', 'error')
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
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <ChatWindow
        messages={messages}
        onSendMessage={handleSendMessage}
        onGenerateEssay={handleGenerateEssay}
        onOpenArtifact={setActiveArtifact}
        activeProvider={activeProvider}
        onProviderChange={setActiveProvider}
        isLoading={isLoading}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
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