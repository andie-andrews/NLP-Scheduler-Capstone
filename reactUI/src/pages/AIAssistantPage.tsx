import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import type { ChatMessage } from '../types'

const assistantUrl = import.meta.env.VITE_AI_ASSISTANT_URL as string | undefined

export function AIAssistantPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async () => {
    if (!input.trim()) return
    const next = [...messages, { role: 'user' as const, content: input }]
    setMessages(next)
    setInput('')
    setLoading(true)

    try {
      if (!assistantUrl) {
        setMessages((prev) => [...prev, { role: 'assistant', content: 'AI endpoint not configured. Set VITE_AI_ASSISTANT_URL to mirror Python orchestrator responses.' }])
        return
      }

      const res = await fetch(assistantUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: user ? `Bearer ${user.token}` : '',
        },
        body: JSON.stringify({ message: input }),
      })
      const data = await res.json() as { summary?: string }
      setMessages((prev) => [...prev, { role: 'assistant', content: data.summary ?? JSON.stringify(data) }])
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Unable to reach AI assistant service.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2>🤖 AI Scheduler Assistant</h2>
      <button onClick={() => setMessages([])}>🆕 New chat</button>
      <div style={{ minHeight: 360, border: '1px solid #ddd', marginTop: 12, padding: 12 }}>
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
