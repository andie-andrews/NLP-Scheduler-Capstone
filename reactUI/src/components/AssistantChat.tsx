import { Button, Card, Group, Stack, Text, TextInput, Title } from '@mantine/core'
import { useAuth } from '../context/AuthContext'
import {
  addMessage,
  clearConversation,
  setConversationId,
  setInput,
  setLoading,
} from '../store/assistantSlice'
import { useAppDispatch, useAppSelector } from '../store'

const assistantUrl = import.meta.env.VITE_AI_ASSISTANT_URL as string | undefined

interface AssistantResponse {
  conversationId: string
  response: unknown
}

interface AssistantChatProps {
  title?: string
}

export function AssistantChat({ title = 'AI Scheduler Assistant' }: AssistantChatProps) {
  const { user } = useAuth()
  const dispatch = useAppDispatch()
  const { messages, input, loading, conversationId } = useAppSelector((state) => state.assistant)

  const resetConversation = async () => {
    if (!assistantUrl || !conversationId || !user) {
      dispatch(clearConversation())
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
      dispatch(clearConversation())
    }
  }

  const send = async () => {
    if (!input.trim()) return

    const userPrompt = input
    dispatch(addMessage({ role: 'user', content: userPrompt }))
    dispatch(setInput(''))
    dispatch(setLoading(true))

    try {
      if (!assistantUrl || !user) {
        dispatch(addMessage({
          role: 'assistant',
          content: 'AI endpoint not configured. Set VITE_AI_ASSISTANT_URL to your backend assistant endpoint (for example: http://localhost:8000/api/assistant/chat).',
        }))
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
        dispatch(setConversationId(data.conversationId))
      }

      const summaryText =
        typeof data.response === 'object' &&
        data.response !== null &&
        'summary' in data.response &&
        typeof (data.response as { summary: unknown }).summary === 'string'
          ? (data.response as { summary: string }).summary
          : null

      const responseText =
        typeof data.response === 'string'
          ? data.response
          : summaryText
            ? summaryText
          : "Unable to reach AI assistant service."

      dispatch(addMessage({ role: 'assistant', content: responseText }))
    } catch (error) {
      const fallback = error instanceof Error ? error.message : 'Unable to reach AI assistant service.'
      dispatch(addMessage({ role: 'assistant', content: fallback }))
    } finally {
      dispatch(setLoading(false))
    }
  }

  return (
    <Stack style={{ height: '100%', minHeight: 0, flex: 1, overflow: 'hidden' }}>
      <Group justify='space-between' align='center'>
        <Title order={4}>{title}</Title>
        <Button variant='light' onClick={resetConversation} aria-label='Reset chat' radius={5}>
          Reset
        </Button>
      </Group>

      <Card withBorder radius='md' p='md' style={{ height: 'calc(100vh - 260px)', minHeight: 360, overflowY: 'auto' }}>
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
          onChange={(e) => dispatch(setInput(e.currentTarget.value))}
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