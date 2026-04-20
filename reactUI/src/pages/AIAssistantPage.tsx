import { useState } from 'react'
import { ActionIcon, Button, Card, Group, Stack, Text, TextInput, Title } from '@mantine/core'
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
    <Stack>
      <Group justify='space-between' align='center'>
        <Title order={2}>AI Scheduler Assistant</Title>
        <ActionIcon variant='light' size='lg' onClick={resetConversation} aria-label='Reset chat'>
          ↺
        </ActionIcon>
      </Group>

      <Card withBorder radius='md' p='md' mih={360}>
        <Stack gap='sm'>
          {messages.map((m, i) => (
            <Card key={i} withBorder radius='sm' bg={m.role === 'assistant' ? 'gray.0' : 'blue.0'}>
              <Text fw={600} tt='capitalize'>
                {m.role}
              </Text>
              <Text style={{ whiteSpace: 'pre-wrap' }}>{m.content}</Text>
            </Card>
          ))}
          {!messages.length && <Text c='dimmed'>Ask something about schedules, shifts, or hours...</Text>}
        </Stack>
      </Card>

      <Group align='end' wrap='nowrap'>
        <TextInput
          style={{ flex: 1 }}
          value={input}
          onChange={(e) => setInput(e.currentTarget.value)}
          placeholder='Ask something about schedules, shifts, or hours...'
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              void send()
            }
          }}
        />
        <Button loading={loading} onClick={() => void send()}>
          Send
        </Button>
      </Group>
    </Stack>
  )
}
