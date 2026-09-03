import { useState, useRef, useEffect, useCallback } from "react"
import { useSearchParams } from "react-router"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { ChatInput } from "@/components/chat/ChatInput"
import { ChatEmptyState } from "@/components/chat/ChatEmptyState"
import { ScrollArea } from "@/components/ui/scroll-area"
import { streamChat } from "@/api/agent"

interface Message {
  role: "user" | "assistant"
  content: string
}

export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleSend = useCallback(
    async (message: string) => {
      setError(null)
      setMessages((prev) => [...prev, { role: "user", content: message }])
      setIsStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller

      let assistantContent = ""
      setMessages((prev) => [...prev, { role: "assistant", content: "" }])

      try {
        for await (const event of streamChat({ message }, controller.signal)) {
          if (event.type === "token") {
            assistantContent += event.content
            setMessages((prev) => {
              const updated = [...prev]
              updated[updated.length - 1] = { role: "assistant", content: assistantContent }
              return updated
            })
          } else if (event.type === "error") {
            setError(event.message)
            setMessages((prev) => {
              const updated = [...prev]
              updated[updated.length - 1] = {
                role: "assistant",
                content: `Error: ${event.message}`,
              }
              return updated
            })
          }
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          // User cancelled
        } else {
          const errMsg = err instanceof Error ? err.message : "Stream failed"
          setError(errMsg)
          setMessages((prev) => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              role: "assistant",
              content: `Error: ${errMsg}`,
            }
            return updated
          })
        }
      } finally {
        setIsStreaming(false)
        abortRef.current = null
      }
    },
    []
  )

  const handleStop = () => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }

  const handleClear = () => {
    setMessages([])
    setError(null)
  }

  // Handle URL query param
  useEffect(() => {
    const q = searchParams.get("q")
    if (q) {
      setSearchParams({}, { replace: true })
      handleSend(q)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <h1 className="text-lg font-semibold">Market Intelligence</h1>
          <p className="text-xs text-muted-foreground">
            {messages.length > 0 ? `${messages.length} messages` : "Ask anything about the market"}
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Clear conversation
          </button>
        )}
      </div>

      {messages.length === 0 ? (
        <ChatEmptyState onPrompt={handleSend} />
      ) : (
        <ScrollArea className="flex-1">
          <div ref={scrollRef} className="space-y-4 p-4">
            {messages.map((msg, i) => (
              <ChatMessage key={i} role={msg.role} content={msg.content} />
            ))}
            {isStreaming && messages[messages.length - 1]?.content === "" && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <div className="h-4 w-4 animate-pulse rounded-full bg-primary" />
                </div>
                <div className="rounded-lg bg-secondary px-4 py-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      )}

      {error && (
        <div className="border-t border-destructive/50 bg-destructive/5 px-4 py-2 text-xs text-destructive">
          {error}
        </div>
      )}

      <ChatInput onSend={handleSend} isLoading={isStreaming} onStop={handleStop} />
    </div>
  )
}
