/**
 * Centralized API client for Lenny Growth Assistant
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(message, status, code, detail) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.detail = detail
  }
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  }

  const config = {
    ...options,
    headers
  }

  let response
  try {
    response = await fetch(url, config)
  } catch (netErr) {
    throw new ApiError(
      `Unable to reach backend at ${API_BASE_URL}. Ensure the FastAPI server is running.`,
      0,
      'NETWORK_ERROR',
      netErr.message
    )
  }

  let data
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    data = await response.json()
  } else {
    data = await response.text()
  }

  if (!response.ok) {
    const errorInfo = data?.error || {}
    const message = errorInfo.message || data?.detail || `Request failed with status ${response.status}`
    const code = errorInfo.code || 'HTTP_ERROR'
    const detail = errorInfo.detail || data
    throw new ApiError(message, response.status, code, detail)
  }

  return data
}

export const api = {
  getHealth: () => request('/health'),
  getConfig: () => request('/config'),
  getSessions: () => request('/sessions'),
  createSession: (body = {}) => request('/sessions', { method: 'POST', body: JSON.stringify(body) }),
  getSession: (id) => request(`/sessions/${id}`),
  deleteSession: (id) => request(`/sessions/${id}`, { method: 'DELETE' }),
  getMessages: (sessionId) => request(`/sessions/${sessionId}/messages`),
  sendMessage: (sessionId, body) => request(`/sessions/${sessionId}/messages`, { method: 'POST', body: JSON.stringify(body) }),
  generateEssay: (sessionId, body) => request(`/sessions/${sessionId}/essay`, { method: 'POST', body: JSON.stringify(body) })
}

export { ApiError }
