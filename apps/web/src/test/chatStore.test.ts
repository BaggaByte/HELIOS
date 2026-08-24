/**
 * Unit tests for the Zustand chatStore.
 *
 * Tests verify each action's effect on state in isolation.
 * Each test resets the store to prevent cross-test contamination.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../stores/chatStore'
import type { ChatMessage } from '../hooks/useChat'

// Helper to build a minimal ChatMessage
function msg(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: 'msg-1',
    role: 'user',
    content: 'hello',
    timestamp: Date.now(),
    status: 'complete',
    ...overrides,
  }
}

// Reset store state before each test
beforeEach(() => {
  useChatStore.setState({
    messages: [],
    isConnected: false,
    activeAssistantMsgId: null,
  })
})

// ── addMessage ────────────────────────────────────────────────────────────────

describe('addMessage', () => {
  it('appends a message to the list', () => {
    useChatStore.getState().addMessage(msg({ id: 'a' }))
    expect(useChatStore.getState().messages).toHaveLength(1)
    expect(useChatStore.getState().messages[0].id).toBe('a')
  })

  it('appends multiple messages in order', () => {
    useChatStore.getState().addMessage(msg({ id: 'a' }))
    useChatStore.getState().addMessage(msg({ id: 'b' }))
    const ids = useChatStore.getState().messages.map((m) => m.id)
    expect(ids).toEqual(['a', 'b'])
  })

  it('does not mutate existing messages', () => {
    const original = msg({ id: 'original' })
    useChatStore.getState().addMessage(original)
    useChatStore.getState().addMessage(msg({ id: 'new' }))
    expect(useChatStore.getState().messages[0].id).toBe('original')
  })
})

// ── updateMessageContent ──────────────────────────────────────────────────────

describe('updateMessageContent', () => {
  it('appends content chunk to the correct message', () => {
    useChatStore.getState().addMessage(msg({ id: 'stream-1', content: 'Hello' }))
    useChatStore.getState().updateMessageContent('stream-1', ' world')
    expect(useChatStore.getState().messages[0].content).toBe('Hello world')
  })

  it('does not affect other messages', () => {
    useChatStore.getState().addMessage(msg({ id: 'a', content: 'A' }))
    useChatStore.getState().addMessage(msg({ id: 'b', content: 'B' }))
    useChatStore.getState().updateMessageContent('a', ' updated')
    expect(useChatStore.getState().messages[1].content).toBe('B')
  })

  it('handles non-existent id gracefully', () => {
    useChatStore.getState().addMessage(msg({ id: 'a', content: 'original' }))
    useChatStore.getState().updateMessageContent('nonexistent', ' chunk')
    expect(useChatStore.getState().messages[0].content).toBe('original')
  })

  it('accumulates multiple chunks', () => {
    useChatStore.getState().addMessage(msg({ id: 's', content: '' }))
    useChatStore.getState().updateMessageContent('s', 'tok1')
    useChatStore.getState().updateMessageContent('s', 'tok2')
    useChatStore.getState().updateMessageContent('s', 'tok3')
    expect(useChatStore.getState().messages[0].content).toBe('tok1tok2tok3')
  })
})

// ── updateMessageStatus ───────────────────────────────────────────────────────

describe('updateMessageStatus', () => {
  it('updates status on the correct message', () => {
    useChatStore.getState().addMessage(msg({ id: 'x', status: 'streaming' }))
    useChatStore.getState().updateMessageStatus('x', 'complete')
    expect(useChatStore.getState().messages[0].status).toBe('complete')
  })

  it('does not change other messages', () => {
    useChatStore.getState().addMessage(msg({ id: 'a', status: 'pending' }))
    useChatStore.getState().addMessage(msg({ id: 'b', status: 'pending' }))
    useChatStore.getState().updateMessageStatus('a', 'complete')
    expect(useChatStore.getState().messages[1].status).toBe('pending')
  })
})

// ── updateMessageAgentStatus ──────────────────────────────────────────────────

describe('updateMessageAgentStatus', () => {
  it('sets agentStatus on the target message', () => {
    useChatStore.getState().addMessage(msg({ id: 'agent-1' }))
    useChatStore.getState().updateMessageAgentStatus('agent-1', 'Running Nmap...')
    expect(useChatStore.getState().messages[0].agentStatus).toBe('Running Nmap...')
  })
})

// ── appendErrorToMessage ──────────────────────────────────────────────────────

describe('appendErrorToMessage', () => {
  it('appends error text to content and sets status to error', () => {
    useChatStore.getState().addMessage(msg({ id: 'err-1', content: 'Partial response' }))
    useChatStore.getState().appendErrorToMessage('err-1', 'Connection lost')
    const updated = useChatStore.getState().messages[0]
    expect(updated.content).toContain('Connection lost')
    expect(updated.status).toBe('error')
  })
})

// ── setConnectionStatus ───────────────────────────────────────────────────────

describe('setConnectionStatus', () => {
  it('sets isConnected to true', () => {
    useChatStore.getState().setConnectionStatus(true)
    expect(useChatStore.getState().isConnected).toBe(true)
  })

  it('sets isConnected to false', () => {
    useChatStore.getState().setConnectionStatus(true)
    useChatStore.getState().setConnectionStatus(false)
    expect(useChatStore.getState().isConnected).toBe(false)
  })
})

// ── setActiveAssistantMsgId ───────────────────────────────────────────────────

describe('setActiveAssistantMsgId', () => {
  it('sets the active assistant message id', () => {
    useChatStore.getState().setActiveAssistantMsgId('streaming-42')
    expect(useChatStore.getState().activeAssistantMsgId).toBe('streaming-42')
  })

  it('clears the id to null', () => {
    useChatStore.getState().setActiveAssistantMsgId('streaming-42')
    useChatStore.getState().setActiveAssistantMsgId(null)
    expect(useChatStore.getState().activeAssistantMsgId).toBeNull()
  })
})

// ── Full streaming lifecycle simulation ───────────────────────────────────────

describe('streaming lifecycle', () => {
  it('simulates a complete stream: start → tokens → done', () => {
    const store = useChatStore.getState()

    // 1. User sends a message
    store.addMessage(msg({ id: 'user-1', role: 'user', content: 'Analyse this' }))

    // 2. start event — create streaming assistant message
    const assistantId = 'assistant-1'
    store.setActiveAssistantMsgId(assistantId)
    store.addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      status: 'streaming',
    })

    // 3. token events
    store.updateMessageContent(assistantId, 'The ')
    store.updateMessageContent(assistantId, 'scan ')
    store.updateMessageContent(assistantId, 'found 3 hosts.')

    // 4. done event
    store.updateMessageStatus(assistantId, 'complete')
    store.setActiveAssistantMsgId(null)

    const messages = useChatStore.getState().messages
    expect(messages).toHaveLength(2)

    const assistant = messages.find((m) => m.id === assistantId)!
    expect(assistant.content).toBe('The scan found 3 hosts.')
    expect(assistant.status).toBe('complete')
    expect(useChatStore.getState().activeAssistantMsgId).toBeNull()
  })
})
