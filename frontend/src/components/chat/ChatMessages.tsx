import { useEffect, useRef } from "react"
import { AlertCircle, RotateCcw } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ChatMessage } from "./ChatMessage"
import type { ChatMessage as ChatMessageType } from "@/types/api"

interface ChatMessagesProps {
  messages: ChatMessageType[]
  isLoading: boolean
  error: string | null
  chatId?: string
  onRetry?: () => void
  onRegenerate?: (message: string) => void
}

export function ChatMessages({ messages, isLoading, error, chatId, onRetry, onRegenerate }: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages.length, messages[messages.length - 1]?.content.length])

  if (isLoading && messages.length === 0) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6" aria-label="Loading conversation">
        <Skeleton className="h-10 w-2/3 self-end" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-10 w-1/2 self-end" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  return (
    <div ref={containerRef} className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-6">
      {messages.map((message) => (
        <ChatMessage
          key={message.id}
          message={message}
          chatId={chatId}
          onRegenerate={
            message.role === "assistant" && message.status === "completed" && onRegenerate
              ? () => {
                  const idx = messages.findIndex((m) => m.id === message.id)
                  const prevUser = [...messages.slice(0, idx)].reverse().find((m) => m.role === "user")
                  if (prevUser) onRegenerate(prevUser.content)
                }
              : undefined
          }
        />
      ))}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex flex-col gap-2">
            <span>{error}</span>
            {onRetry && (
              <Button variant="outline" size="sm" className="w-fit" onClick={onRetry}>
                <RotateCcw className="h-3.5 w-3.5" />
                Retry
              </Button>
            )}
          </AlertDescription>
        </Alert>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
