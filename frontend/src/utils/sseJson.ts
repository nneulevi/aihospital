import { getToken } from './auth'

export type SseJsonEvent = {
  event: string
  data: any
}

export type SseJsonHandlers = {
  onEvent?: (event: SseJsonEvent) => void
  onFinal?: (data: any) => void
  onError?: (data: any) => void
}

const parseBlock = (block: string): SseJsonEvent | null => {
  const lines = block.split(/\r?\n/)
  let event = 'message'
  const dataLines: string[] = []
  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }
  if (!dataLines.length) {
    return null
  }
  const rawData = dataLines.join('\n')
  try {
    return { event, data: JSON.parse(rawData) }
  } catch {
    return { event, data: rawData }
  }
}

const dispatchEvent = (parsed: SseJsonEvent | null, handlers: SseJsonHandlers) => {
  if (!parsed) return
  handlers.onEvent?.(parsed)
  if (parsed.event === 'final') {
    handlers.onFinal?.(parsed.data)
  } else if (parsed.event === 'error') {
    handlers.onError?.(parsed.data)
  }
}

export const postJsonSse = async (url: string, body: any, handlers: SseJsonHandlers = {}) => {
  const token = getToken()
  const response = await fetch(`/api${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body || {}),
  })
  if (!response.ok) {
    throw new Error(`SSE request failed with status ${response.status}`)
  }
  if (!response.body) {
    throw new Error('SSE response body is not readable')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split(/\r?\n\r?\n/)
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      dispatchEvent(parseBlock(block), handlers)
    }
  }

  buffer += decoder.decode()
  if (buffer.trim()) {
    dispatchEvent(parseBlock(buffer), handlers)
  }
}
