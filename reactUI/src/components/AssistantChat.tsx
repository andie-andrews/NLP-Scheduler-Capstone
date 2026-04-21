import { useEffect, useRef } from 'react'
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
  response: {
    data?: {
      nextShift?: {
        id?: number
        start: string
        durationHours: number
      }
      updatedShift?: {
        id?: number
        start?: string
        durationHours?: number
      }
      createdShift?: {
        id?: number
        start: string
        durationHours: number
      }
      createdShifts?: Array<{
        id?: number
        start: string
        durationHours: number
      }>
    }
  } | string | unknown
}

interface AssistantChatProps {
  title?: string
}

export function AssistantChat({ title = '🤖 AI Scheduler Assistant' }: AssistantChatProps) {
  const { user } = useAuth()
  const dispatch = useAppDispatch()
  const { messages, input, loading, conversationId } = useAppSelector((state) => state.assistant)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

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

      const extractedShift =
        typeof data.response === 'object' &&
        data.response !== null &&
        'data' in data.response &&
        data.response.data !== null &&
        typeof data.response.data === 'object' &&
        'nextShift' in data.response.data &&
        typeof (data.response.data as { nextShift: unknown }).nextShift === 'object' &&
        (data.response.data as { nextShift: unknown }).nextShift !== null
          ? (data.response.data as { nextShift: { id?: number; start: string; durationHours: number } }).nextShift
          : null

      const extractedUpdatedShift =
        typeof data.response === 'object' &&
        data.response !== null &&
        'data' in data.response &&
        data.response.data !== null &&
        typeof data.response.data === 'object' &&
        'updatedShift' in data.response.data &&
        typeof (data.response.data as { updatedShift: unknown }).updatedShift === 'object' &&
        (data.response.data as { updatedShift: unknown }).updatedShift !== null
          ? (data.response.data as { updatedShift: { id?: number; start?: string; durationHours?: number } }).updatedShift
          : null

      const extractedCreatedShift =
        typeof data.response === 'object' &&
        data.response !== null &&
        'data' in data.response &&
        data.response.data !== null &&
        typeof data.response.data === 'object' &&
        'createdShift' in data.response.data &&
        typeof (data.response.data as { createdShift: unknown }).createdShift === 'object' &&
        (data.response.data as { createdShift: unknown }).createdShift !== null
          ? (data.response.data as { createdShift: { id?: number; start: string; durationHours: number } }).createdShift
          : null

      const extractedCreatedShifts =
        typeof data.response === 'object' &&
        data.response !== null &&
        'data' in data.response &&
        data.response.data !== null &&
        typeof data.response.data === 'object' &&
        'createdShifts' in data.response.data &&
        Array.isArray((data.response.data as { createdShifts: unknown }).createdShifts)
          ? (data.response.data as { createdShifts: Array<{ id?: number; start: string; durationHours: number }> }).createdShifts
          : null

      const createdShiftForCard =
        extractedCreatedShifts && extractedCreatedShifts.length === 1 ? extractedCreatedShifts[0] : null

      dispatch(addMessage({
        role: 'assistant',
        content: responseText,
        shiftData: extractedShift || undefined,
        updatedShiftData: extractedUpdatedShift || undefined,
        createdShiftData: createdShiftForCard || undefined,
      }))

      if (extractedUpdatedShift) {
        window.dispatchEvent(new CustomEvent('shifts:updated'))
      }
      if (extractedCreatedShift || (extractedCreatedShifts && extractedCreatedShifts.length > 0)) {
        window.dispatchEvent(new CustomEvent('shifts:created'))
      }
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

      <Card withBorder radius='md' p='md' ref={scrollRef} style={{ height: 'calc(100vh - 260px)', minHeight: 360, overflowY: 'auto' }}>
        <Stack gap='sm'>
          {messages.map((m, i) => (
            <Stack key={i} gap='sm'>
              <Card withBorder radius='sm' bg={m.role === 'assistant' ? 'gray.0' : 'blue.0'}>
                <Text fw={600} tt='capitalize'>
                  {m.role}
                </Text>
                <Text style={{ whiteSpace: 'pre-wrap' }}>{m.content}</Text>
              </Card>
              {m.shiftData && (
                <Card withBorder radius='md' p='md' bg='green.0'>
                  <Stack gap='xs'>
                    <Text fw={700}>📅 Next Shift</Text>
                    <Text size='sm'>
                      {new Date(m.shiftData.start).toLocaleString()}
                    </Text>
                    <Text size='sm' c='dimmed'>
                      Duration: {m.shiftData.durationHours} hour{m.shiftData.durationHours === 1 ? '' : 's'}
                    </Text>
                  </Stack>
                </Card>
              )}
              {m.updatedShiftData && (
                <Card withBorder radius='md' p='md' bg='yellow.0'>
                  <Stack gap='xs'>
                    <Text fw={700}>🛠️ Updated Shift</Text>
                    {m.updatedShiftData.start && <Text size='sm'>
                      {new Date(m.updatedShiftData.start).toLocaleString()}
                    </Text>}
                    {m.updatedShiftData.durationHours && <Text size='sm'>
                      Duration: {m.updatedShiftData.durationHours} hour{m.updatedShiftData.durationHours === 1 ? '' : 's'}
                    </Text>}
                  </Stack>
                </Card>
              )}
              {m.createdShiftData && (
                <Card withBorder radius='md' p='md' bg='blue.1'>
                  <Stack gap='xs'>
                    <Text fw={700}>✨ Created Shift</Text>
                    <Text size='sm'>
                      {new Date(m.createdShiftData.start).toLocaleString()}
                    </Text>
                    <Text size='sm' c='dimmed'>
                      Duration: {m.createdShiftData.durationHours} hour{m.createdShiftData.durationHours === 1 ? '' : 's'}
                    </Text>
                  </Stack>
                </Card>
              )}
            </Stack>
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