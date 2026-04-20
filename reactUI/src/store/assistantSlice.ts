import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { ChatMessage } from '../types'

interface AssistantState {
  messages: ChatMessage[]
  input: string
  loading: boolean
  conversationId: string | null
}

const initialState: AssistantState = {
  messages: [],
  input: '',
  loading: false,
  conversationId: null,
}

const assistantSlice = createSlice({
  name: 'assistant',
  initialState,
  reducers: {
    setInput(state, action: PayloadAction<string>) {
      state.input = action.payload
    },
    addMessage(state, action: PayloadAction<ChatMessage>) {
      state.messages.push(action.payload)
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload
    },
    setConversationId(state, action: PayloadAction<string | null>) {
      state.conversationId = action.payload
    },
    clearConversation(state) {
      state.messages = []
      state.conversationId = null
      state.input = ''
      state.loading = false
    },
  },
})

export const {
  setInput,
  addMessage,
  setLoading,
  setConversationId,
  clearConversation,
} = assistantSlice.actions

export const assistantReducer = assistantSlice.reducer