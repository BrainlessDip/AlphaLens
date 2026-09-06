import { useCallback, useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"
import { ChatLayout } from "@/components/chat/ChatLayout"
import { ChatHeader } from "@/components/chat/ChatHeader"
import { ChatMessages } from "@/components/chat/ChatMessages"
import { ChatComposer } from "@/components/chat/ChatComposer"
import { ChatEmptyState } from "@/components/chat/ChatEmptyState"
import { ChatSuggestions } from "@/components/chat/ChatSuggestions"
import { CommandMenu } from "@/components/chat/CommandMenu"
import { useChatMessages } from "@/hooks/useChatMessages"
import { EMPTY_STREAM, toDisplayMessages, useChatStream } from "@/hooks/useChatStream"
import { useChatHistory } from "@/hooks/useChatHistory"
import type { ChatMessage as ChatMessageType } from "@/types/api"

const FOLLOW_UPS = [
  "Compare with ETH",
  "Show the 4h trend",
  "Explain the indicators",
  "What could invalidate this view?",
]

export function ChatPage() {
  const { chatId } = useParams<{ chatId?: string }>()
  const navigate = useNavigate()
  const { data: detail, isLoading, refetch } = useChatMessages(chatId)
  const { data: history } = useChatHistory()
  const { isStreaming, active, send, stop, reset } = useChatStream()
  const scrollRef = useRef<HTMLDivElement>(null)
  const composerRef = useRef<HTMLTextAreaElement>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const composerKey = `composer-${chatId ?? "new"}`

  const persisted: ChatMessageType[] = (detail?.messages ?? []).map((m) => ({
    id: m.id,
    role: m.role,
    content: m.content,
    createdAt: m.created_at,
    status: m.status === "streaming" ? "streaming" : "completed",
  }))

  const showActive =
    isStreaming ||
    (active.content !== "" ||
      active.streamEvents.length > 0 ||
      active.error !== null)
  const messages = showActive
    ? toDisplayMessages(
        persisted,
        active.chatId === (chatId ?? null) || !chatId
          ? active
          : { ...EMPTY_STREAM },
        isStreaming
      )
    : persisted

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length, messages[messages.length - 1]?.content])

  // Abort an in-flight stream if the user switches conversation.
  const prevChatId = useRef(chatId)
  useEffect(() => {
    if (prevChatId.current !== chatId) {
      prevChatId.current = chatId
      if (!isStreaming) {
        stop()
        reset()
      }
    }
  }, [chatId, stop, reset, isStreaming])

  // Cleanup: abort any ongoing stream when component unmounts
  useEffect(() => {
    return () => {
      stop()
    }
  }, [stop])

  const handleSend = useCallback(
    async (message: string) => {
      const result = await send(message, chatId ?? null, (id) => {
        navigate(`/chat/${id}`, { replace: true })
      })
      if (result.chatId) {
        await refetch()
      }
      reset()
    },
    [send, chatId, navigate, reset, refetch]
  )

  const handleNewChat = useCallback(() => {
    stop()
    reset()
    navigate("/chat")
  }, [stop, reset, navigate])

  const handleFocusComposer = useCallback(() => {
    composerRef.current?.focus()
  }, [])

  const handleSelect = useCallback(
    (id: string) => {
      navigate(`/chat/${id}`)
    },
    [navigate]
  )

  const lastUserMessage = [...persisted].reverse().find((m) => m.role === "user")?.content
  const lastMessage = persisted[persisted.length - 1]
  const showFollowUps =
    !isStreaming &&
    !active.error &&
    lastMessage?.role === "assistant" &&
    lastMessage.content !== ""

  const title =
    detail?.title ??
    history?.items.find((c) => c.id === chatId)?.title ??
    (chatId ? "Chat" : undefined)

  return (
    <ChatLayout activeChatId={chatId} onSelect={handleSelect} onNewChat={handleNewChat} collapsed={!sidebarOpen}>
      <ChatHeader
        title={title}
        activeChatId={chatId}
        onSelect={handleSelect}
        onNewChat={handleNewChat}
      />
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
        {persisted.length === 0 && !showActive && !isLoading ? (
          <ChatEmptyState onPrompt={handleSend} />
        ) : (
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            error={active.error}
            chatId={chatId}
            onRetry={lastUserMessage ? () => handleSend(lastUserMessage) : undefined}
            onRegenerate={handleSend}
          />
        )}
      </div>
      {showFollowUps && (
        <ChatSuggestions suggestions={FOLLOW_UPS} onSelect={handleSend} />
      )}
      <ChatComposer
        key={composerKey}
        draftKey={composerKey}
        onSend={handleSend}
        isStreaming={isStreaming}
        onStop={stop}
        autoFocus={persisted.length === 0}
      />
      <CommandMenu
        onNewChat={handleNewChat}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        onFocusComposer={handleFocusComposer}
      />
    </ChatLayout>
  )
}
