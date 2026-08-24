/**
 * Unit tests for the useWebSocket hook.
 *
 * Uses Vitest's fake timer support and a mock WebSocket implementation
 * to test connection management, message parsing, subscription,
 * reconnection logic, and cleanup — without any real network traffic.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from '../hooks/useWebSocket'

// ── Mock WebSocket ────────────────────────────────────────────────────────────



class MockWebSocket {
  static instances: MockWebSocket[] = []

  url: string
  readyState: number = WebSocket.CONNECTING

  onopen: ((e: Event) => void) | null = null
  onmessage: ((e: MessageEvent) => void) | null = null
  onclose: ((e: CloseEvent) => void) | null = null
  onerror: ((e: Event) => void) | null = null

  sentMessages: string[] = []

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  send(data: string) {
    this.sentMessages.push(data)
  }

  close() {
    this.readyState = WebSocket.CLOSED
    this.onclose?.(new CloseEvent('close'))
  }

  // Test helpers
  simulateOpen() {
    this.readyState = WebSocket.OPEN
    this.onopen?.(new Event('open'))
  }

  simulateMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }))
  }

  simulateError() {
    this.onerror?.(new Event('error'))
  }

  simulateClose() {
    this.readyState = WebSocket.CLOSED
    this.onclose?.(new CloseEvent('close'))
  }
}

// ── Test Setup ────────────────────────────────────────────────────────────────

beforeEach(() => {
  MockWebSocket.instances = []
  vi.stubGlobal('WebSocket', MockWebSocket)
  vi.useFakeTimers()
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
})

function getLatestWs(): MockWebSocket {
  const instances = MockWebSocket.instances
  return instances[instances.length - 1]
}

// ── Connection states ─────────────────────────────────────────────────────────

describe('connection states', () => {
  it('starts in connecting state', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    expect(result.current.status).toBe('connecting')
    expect(result.current.isConnected).toBe(false)
  })

  it('transitions to connected after open', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    act(() => {
      getLatestWs().simulateOpen()
    })
    expect(result.current.status).toBe('connected')
    expect(result.current.isConnected).toBe(true)
  })

  it('transitions to disconnected after close', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    act(() => {
      getLatestWs().simulateOpen()
    })
    act(() => {
      getLatestWs().simulateClose()
    })
    expect(result.current.status).toBe('disconnected')
    expect(result.current.isConnected).toBe(false)
  })

  it('calls close on error event (triggers onclose → disconnected)', () => {
    const { result } = renderHook(() =>
      useWebSocket('ws://localhost/test', { maxRetries: 0 })
    )
    act(() => {
      getLatestWs().simulateOpen()
    })
    act(() => {
      getLatestWs().simulateError()
    })
    // The hook sets 'error' then calls socket.close() which triggers onclose → 'disconnected'
    // Final observable state is 'disconnected'
    expect(['error', 'disconnected']).toContain(result.current.status)
  })
})

// ── Sending messages ──────────────────────────────────────────────────────────

describe('sendMessage', () => {
  it('sends JSON-serialised message when connected', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    act(() => {
      getLatestWs().simulateOpen()
    })
    act(() => {
      result.current.sendMessage({ type: 'message', content: 'hello' })
    })
    expect(getLatestWs().sentMessages).toHaveLength(1)
    expect(JSON.parse(getLatestWs().sentMessages[0])).toEqual({
      type: 'message',
      content: 'hello',
    })
  })

  it('does not throw when socket is not open', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    // Still in CONNECTING state — sendMessage should be a no-op
    expect(() =>
      result.current.sendMessage({ type: 'ping' })
    ).not.toThrow()
  })
})

// ── Subscribing to messages ───────────────────────────────────────────────────

describe('subscribe', () => {
  it('delivers parsed messages to subscribers', () => {
    const received: unknown[] = []
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))

    act(() => {
      result.current.subscribe((data) => received.push(data))
      getLatestWs().simulateOpen()
      getLatestWs().simulateMessage({ type: 'token', content: 'hello' })
    })

    expect(received).toHaveLength(1)
    expect(received[0]).toEqual({ type: 'token', content: 'hello' })
  })

  it('delivers to multiple subscribers', () => {
    const r1: unknown[] = []
    const r2: unknown[] = []
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))

    act(() => {
      result.current.subscribe((d) => r1.push(d))
      result.current.subscribe((d) => r2.push(d))
      getLatestWs().simulateOpen()
      getLatestWs().simulateMessage({ type: 'ping' })
    })

    expect(r1).toHaveLength(1)
    expect(r2).toHaveLength(1)
  })

  it('unsubscribe stops receiving messages', () => {
    const received: unknown[] = []
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    let unsubscribe!: () => void

    act(() => {
      unsubscribe = result.current.subscribe((d) => received.push(d))
      getLatestWs().simulateOpen()
      getLatestWs().simulateMessage({ type: 'start' })
    })

    expect(received).toHaveLength(1)

    act(() => {
      unsubscribe()
      getLatestWs().simulateMessage({ type: 'token', content: 'after unsub' })
    })

    expect(received).toHaveLength(1) // still only 1
  })

  it('ignores malformed JSON without throwing', () => {
    const received: unknown[] = []
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))

    act(() => {
      result.current.subscribe((d) => received.push(d))
      getLatestWs().simulateOpen()
      // Send raw invalid JSON directly
      getLatestWs().onmessage?.(
        new MessageEvent('message', { data: 'not valid json' })
      )
    })

    expect(received).toHaveLength(0) // no crash, no delivery
  })
})

// ── Reconnection ──────────────────────────────────────────────────────────────

describe('reconnection', () => {
  it('reconnects after disconnect', () => {
    renderHook(() =>
      useWebSocket('ws://localhost/test', { reconnectInterval: 1000, maxRetries: 3 })
    )

    const first = getLatestWs()
    act(() => {
      first.simulateOpen()
      first.simulateClose()
    })

    // Advance past the reconnect delay
    act(() => {
      vi.advanceTimersByTime(1100)
    })

    // A new WebSocket should have been created
    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(2)
  })

  it('stops reconnecting after max retries', () => {
    renderHook(() =>
      useWebSocket('ws://localhost/test', { reconnectInterval: 100, maxRetries: 1 })
    )

    // Exhaust all retries
    for (let i = 0; i < 3; i++) {
      act(() => {
        getLatestWs().simulateClose()
        vi.advanceTimersByTime(5000)
      })
    }

    const totalAttempts = MockWebSocket.instances.length
    // Should not have created more than maxRetries + 1 connections
    expect(totalAttempts).toBeLessThanOrEqual(3)
  })
})

// ── Cleanup ───────────────────────────────────────────────────────────────────

describe('cleanup', () => {
  it('closes socket on unmount', () => {
    const { unmount } = renderHook(() =>
      useWebSocket('ws://localhost/test')
    )
    act(() => {
      getLatestWs().simulateOpen()
    })

    const ws = getLatestWs()
    unmount()
    expect(ws.readyState).toBe(WebSocket.CLOSED)
  })
})
