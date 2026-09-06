import { useCallback, useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { streamChat } from "@/api/agent"
import type { ChatMessage, StreamEvent, StreamUnknownEvent, ToolUseItem } from "@/types/api"
import { CHATS_QUERY_KEY } from "./useChatHistory"
import { chatMessagesKey } from "./useChatMessages"

let toolEventCounter = 0
let streamEventCounter = 0

function nextToolId() {
  toolEventCounter += 1
  return `tool-${Date.now()}-${toolEventCounter}`
}

function nextStreamEventId() {
  streamEventCounter += 1
  return `se-${Date.now()}-${streamEventCounter}`
}

export interface ActiveStream {
  chatId: string | null
  content: string
  error: string | null
  dataTimestamp: string | null
  suggestions: string[] | null
  toolsUsed: ToolUseItem[]
  streamEvents: StreamEvent[]
}

export const EMPTY_STREAM: ActiveStream = {
  chatId: null,
  content: "",
  error: null,
  dataTimestamp: null,
  suggestions: null,
  toolsUsed: [],
  streamEvents: [],
}

function toDisplayErrorStatus(streamEvents: StreamEvent[]): StreamEvent[] {
  return streamEvents.map((event): StreamEvent => {
    if (event.type === "tool" && "status" in event && event.status === "running") {
      return { ...event, status: "error" }
    }
    return event
  })
}

export function useChatStream() {
  const queryClient = useQueryClient()
  const [isStreaming, setIsStreaming] = useState(false)
  const [active, setActive] = useState<ActiveStream>(EMPTY_STREAM)
  const abortRef = useRef<AbortController | null>(null)

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const send = useCallback(
    async (message: string, chatId: string | null, onChatCreated?: (id: string) => void) => {
      const controller = new AbortController()
      abortRef.current = controller
      setIsStreaming(true)
      setActive({ ...EMPTY_STREAM, chatId })

      let resolvedChatId = chatId
      let content = ""
      let error: string | null = null

      try {
        for await (const frame of streamChat(
          chatId ? { message, chat_id: chatId } : { message },
          controller.signal
        )) {
          const now = new Date().toISOString()

          if (!frame.known) {
            const unknownEvent = frame.event as Record<string, unknown>
            setActive((prev) => ({
              ...prev,
              streamEvents: [
                ...prev.streamEvents,
                {
                  id: nextStreamEventId(),
                  type: typeof unknownEvent.type === "string" ? unknownEvent.type : "unknown",
                  raw: unknownEvent as Record<string, unknown>,
                  receivedAt: now,
                } as StreamUnknownEvent,
              ],
            }))
            continue
          }

          const event = frame.event

          switch (event.type) {
            case "message_start": {
              resolvedChatId = event.chat_id
              if (!chatId) {
                onChatCreated?.(event.chat_id)
                queryClient.invalidateQueries({ queryKey: CHATS_QUERY_KEY })
              }
              setActive((prev) => ({
                ...prev,
                chatId: event.chat_id,
              }))
              break
            }
            case "tool_start": {
              const entry: ToolUseItem = { tool: event.tool, label: event.label }
              setActive((prev) => ({
                ...prev,
                toolsUsed: prev.toolsUsed.some(
                  (t) => t.tool === entry.tool && t.label === entry.label
                )
                  ? prev.toolsUsed
                  : [...prev.toolsUsed, entry],
                streamEvents: [
                  ...prev.streamEvents,
                  {
                    id: nextToolId(),
                    type: "tool",
                    tool: event.tool,
                    label: event.label,
                    status: "running",
                    receivedAt: now,
                  },
                ],
              }))
              break
            }
            case "tool_complete": {
              const completedTool = event.tool
              setActive((prev) => ({
                ...prev,
                streamEvents: prev.streamEvents.map((e): StreamEvent => {
                  if (e.type === "tool" && "status" in e && e.tool === completedTool && e.status === "running") {
                    return { ...e, status: "completed" }
                  }
                  return e
                }),
              }))
              break
            }
            case "assistant_delta": {
              content += event.content
              setActive((prev) => ({
                ...prev,
                content,
                streamEvents: [
                  ...prev.streamEvents,
                  { id: nextStreamEventId(), type: "assistant_delta", content: event.content, receivedAt: now },
                ],
              }))
              break
            }
            case "message_complete": {
              resolvedChatId = event.chat_id
              setActive((prev) => ({
                ...prev,
                dataTimestamp: event.data_timestamp ?? prev.dataTimestamp,
                suggestions: event.suggestions ?? prev.suggestions,
                toolsUsed: event.tools_used ?? prev.toolsUsed,
              }))
              break
            }
            case "market_data": {
              setActive((prev) => ({
                ...prev,
                streamEvents: [
                  ...prev.streamEvents,
                  {
                    id: nextStreamEventId(),
                    type: "market_data",
                    symbol: event.symbol,
                    price: event.price,
                    change_pct: event.change_pct,
                    volume_24h: event.volume_24h,
                    quote_volume_24h: event.quote_volume_24h,
                    timestamp: event.timestamp,
                    receivedAt: now,
                  },
                ],
              }))
              break
            }
            case "error": {
              error = event.message
              setActive((prev) => ({ ...prev, error: event.message }))
              break
            }
          }
        }
      } catch (err: unknown) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          error = err instanceof Error ? err.message : "Stream failed"
          setActive((prev) => ({ ...prev, error }))
        }
      } finally {
        setIsStreaming(false)
        abortRef.current = null
        setActive((prev) => ({
          ...prev,
          streamEvents: toDisplayErrorStatus(prev.streamEvents),
        }))
        if (resolvedChatId) {
          queryClient.invalidateQueries({ queryKey: chatMessagesKey(resolvedChatId) })
          queryClient.invalidateQueries({ queryKey: CHATS_QUERY_KEY })
        }
      }

      return { chatId: resolvedChatId, content, error }
    },
    [queryClient]
  )

  const reset = useCallback(() => {
    setActive(EMPTY_STREAM)
  }, [])

  return { isStreaming, active, send, stop, reset }
}

export function toDisplayMessages(
  persisted: ChatMessage[],
  active: ActiveStream,
  isStreaming = false,
  streamingAssistantId = "streaming"
): ChatMessage[] {
  if (
    !active.chatId &&
    active.content === "" &&
    active.streamEvents.length === 0 &&
    !active.error
  ) {
    return persisted
  }

  // After the stream finishes, the refetched history already contains the
  // completed assistant message. Skip appending the live copy to avoid
  // rendering the same message twice in the window before reset().
  if (!isStreaming && active.content !== "" && !active.error && persisted.length > 0) {
    const last = persisted[persisted.length - 1]
    if (last.role === "assistant" && last.content === active.content) {
      return persisted
    }
  }

  return [
    ...persisted,
    {
      id: streamingAssistantId,
      role: "assistant",
      content: active.content,
      createdAt: new Date().toISOString(),
      status: active.error ? "error" : "streaming",
      dataTimestamp: active.dataTimestamp ?? undefined,
      streamEvents: active.streamEvents.length > 0 ? active.streamEvents : undefined,
      toolsUsed: active.toolsUsed.length > 0 ? active.toolsUsed : undefined,
    },
  ]
}
