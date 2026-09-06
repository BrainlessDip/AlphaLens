import { Link, useParams, useSearchParams } from "react-router"
import { useQuery } from "@tanstack/react-query"
import { BarChart3 } from "lucide-react"
import { getSharedChat } from "@/api/chats"
import { ChatMessage } from "@/components/chat/ChatMessage"
import type { ChatMessage as ChatMessageType } from "@/types/api"

function toChatMessage(item: { id: string; role: "user" | "assistant"; content: string; status: string; created_at: string }): ChatMessageType {
  return {
    id: item.id,
    role: item.role,
    content: item.content,
    status: (item.status === "streaming" ? "streaming" : item.status === "error" ? "error" : "completed") as ChatMessageType["status"],
    createdAt: item.created_at,
  }
}

export function SharedChatPage() {
  const { chatId = "" } = useParams()
  const [params] = useSearchParams()
  const token = params.get("token") ?? ""
  const { data, isError, isLoading } = useQuery({
    queryKey: ["shared-chat", chatId, token],
    queryFn: () => getSharedChat(chatId, token),
    enabled: !!chatId && !!token,
    retry: false,
  })

  return (
    <div className="flex h-dvh flex-col bg-background">
      <header className="flex h-14 shrink-0 items-center gap-3 border-b px-4">
        <Link to="/" className="flex items-center gap-2 text-sm font-semibold" aria-label="AlphaLens home">
          <BarChart3 className="h-4 w-4 text-primary" />
          AlphaLens
        </Link>
        <span className="min-w-0 truncate text-sm text-muted-foreground">{data?.title}</span>
        <span className="ml-auto shrink-0 rounded-full border border-border/60 px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
          Shared
        </span>
      </header>
      <main className="mx-auto w-full max-w-3xl flex-1 overflow-y-auto px-4 py-6">
        {isLoading && <p className="text-sm text-muted-foreground">Loading shared analysis…</p>}
        {isError && (
          <div className="flex flex-col items-center gap-3 rounded-lg border border-border/50 p-8 text-center">
            <p className="text-sm text-muted-foreground">
              This shared analysis is unavailable or the link is invalid.
            </p>
            <Link
              to="/"
              className="rounded-md border border-border/60 px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent"
            >
              Back to AlphaLens
            </Link>
          </div>
        )}
        <div className="flex flex-col gap-4">
          {(data?.messages ?? []).map((m) => (
            <ChatMessage key={m.id} message={toChatMessage(m)} />
          ))}
        </div>
      </main>
    </div>
  )
}
