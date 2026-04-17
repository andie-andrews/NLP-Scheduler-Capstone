import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import type { ChatMessage } from '../types'

const assistantUrl = import.meta.env.VITE_AI_ASSISTANT_URL as string | undefined

interface AssistantResponse {
  conversationId: string
  response: unknown
}

export function AIAssistantPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)

  const resetConversation = async () => {
    if (!assistantUrl || !conversationId || !user) {
      setMessages([])
      setConversationId(null)
      return
    }

    try {
      await fetch(`${assistantUrl}/${conversationId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${user.token}`,
        },
      })
    } finally {
      setMessages([])
      setConversationId(null)
    }
  }

  const send = async () => {
    if (!input.trim()) return

    const userPrompt = input
    setMessages((prev) => [...prev, { role: 'user', content: userPrompt }])
    setInput('')
    setLoading(true)

    try {
      if (!assistantUrl || !user) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'AI endpoint not configured. Set VITE_AI_ASSISTANT_URL to your backend assistant endpoint (for example: http://localhost:8000/api/assistant/chat).',
          },
        ])
        return
      }

      const res = await fetch(assistantUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${user.token}`,
        },
        body: JSON.stringify({ message: userPrompt, conversationId }),
      })

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(errorText || `Assistant request failed with ${res.status}`)
      }

      const data = await res.json() as AssistantResponse
      if (data.conversationId) {
        setConversationId(data.conversationId)
      }

      const responseText =
        typeof data.response === 'string'
          ? data.response
          : JSON.stringify(data.response, null, 2)

      setMessages((prev) => [...prev, { role: 'assistant', content: responseText }])
    } catch (error) {
      const fallback = error instanceof Error ? error.message : 'Unable to reach AI assistant service.'
      setMessages((prev) => [...prev, { role: 'assistant', content: fallback }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2>🤖 AI Scheduler Assistant</h2>
      <button onClick={resetConversation}>🆕 New chat</button>
      <div style={{ minHeight: 360, border: '1px solid #ddd', marginTop: 12, padding: 12, whiteSpace: 'pre-wrap' }}>
        {messages.map((m, i) => <p key={i}><strong>{m.role}:</strong> {m.content}</p>)}
        {!messages.length && <p>Ask something about schedules, shifts, or hours...</p>}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input style={{ flex: 1 }} value={input} onChange={(e) => setInput(e.target.value)} placeholder='Ask something about schedules, shifts, or hours...' />
        <button disabled={loading} onClick={send}>{loading ? '...' : 'Send'}</button>
      </div>
    </section>
  )
}
