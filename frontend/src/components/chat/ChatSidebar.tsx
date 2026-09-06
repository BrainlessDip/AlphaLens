import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router"
import { LogOut, MoreHorizontal, Pencil, Plus, Search, Settings, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  useChatHistory,
  useCreateChat,
  useDeleteChat,
  useRenameChat,
} from "@/hooks/useChatHistory"
import { useAuth } from "@/contexts/AuthContext"
import type { ChatSummary } from "@/types/api"
import { cn } from "@/lib/utils"

function groupLabel(dateISO: string, now: Date): string {
  const date = new Date(dateISO)
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startOfYesterday = new Date(startOfToday.getTime() - 24 * 60 * 60 * 1000)
  const startOfWeek = new Date(startOfToday.getTime() - 7 * 24 * 60 * 60 * 1000)
  if (date >= startOfToday) return "Today"
  if (date >= startOfYesterday) return "Yesterday"
  if (date >= startOfWeek) return "Previous 7 Days"
  return "Older"
}

function ChatRow({
  chat,
  active,
  onSelect,
}: {
  chat: ChatSummary
  active: boolean
  onSelect: (id: string) => void
}) {
  const navigate = useNavigate()
  const rename = useRenameChat()
  const remove = useDeleteChat()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(chat.title)

  const handleRename = () => {
    const title = draft.trim()
    if (title && title !== chat.title) {
      rename.mutate({ id: chat.id, title })
    }
    setEditing(false)
  }

  const handleDelete = () => {
    remove.mutate(chat.id, {
      onSuccess: () => {
        if (active) navigate("/chat", { replace: true })
      },
    })
  }

  return (
    <div
      className={cn(
        "group flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm transition-colors",
        active ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
      )}
    >
      {editing ? (
        <Input
          value={draft}
          autoFocus
          maxLength={120}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={handleRename}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleRename()
            if (e.key === "Escape") {
              setDraft(chat.title)
              setEditing(false)
            }
          }}
          className="h-7 text-sm"
          aria-label="Rename chat"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <button
          className="min-w-0 flex-1 truncate text-left"
          onClick={() => onSelect(chat.id)}
          title={chat.title}
        >
          {chat.title}
        </button>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100 max-sm:opacity-100"
            aria-label={`Options for ${chat.title}`}
          >
            <MoreHorizontal className="h-3.5 w-3.5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            icon={<Pencil className="h-3.5 w-3.5" />}
            onSelect={() => {
              setDraft(chat.title)
              setEditing(true)
            }}
          >
            Rename
          </DropdownMenuItem>
          <DropdownMenuItem icon={<Trash2 className="h-3.5 w-3.5" />} onSelect={handleDelete}>
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

export function ChatSidebar({
  activeChatId,
  onSelect,
  onNewChat,
}: {
  activeChatId?: string
  onSelect: (id: string) => void
  onNewChat: () => void
}) {
  const [search, setSearch] = useState("")
  const [debounced, setDebounced] = useState("")
  const [offset, setOffset] = useState(0)
  const create = useCreateChat()
  const { user, logout } = useAuth()
  const PAGE_SIZE = 50
  const { data, isLoading } = useChatHistory(debounced || undefined, PAGE_SIZE, offset)

  const handleSearch = (value: string) => {
    setSearch(value)
  }

  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(search.trim()), 300)
    return () => window.clearTimeout(t)
  }, [search])

  const groups = new Map<string, ChatSummary[]>()
  const now = new Date()
  for (const chat of data?.items ?? []) {
    const label = groupLabel(chat.updated_at, now)
    if (!groups.has(label)) groups.set(label, [])
    groups.get(label)!.push(chat)
  }

  const handleNew = () => {
    if (onNewChat) {
      onNewChat()
    } else {
      create.mutate(undefined, {
        onSuccess: (chat) => onSelect(chat.id),
      })
    }
  }

  const hasMore = data && data.total > offset + PAGE_SIZE

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-col gap-2">
        <Button variant="outline" className="justify-start" onClick={handleNew} disabled={create.isPending}>
          <Plus className="h-4 w-4" />
          New chat
        </Button>

        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search chats"
            className="h-8 pl-8 text-sm"
            aria-label="Search chats"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex flex-col gap-2 pt-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : groups.size === 0 ? (
          <p className="px-2 pt-4 text-xs text-muted-foreground">
            {debounced ? "No chats match your search." : "No conversations yet."}
          </p>
        ) : (
          <>
            {[...groups.entries()].map(([label, chats]) => (
              <div key={label} className="pt-3 first:pt-1">
                <p className="px-2 pb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  {label}
                </p>
                {chats.map((chat) => (
                  <ChatRow key={chat.id} chat={chat} active={chat.id === activeChatId} onSelect={onSelect} />
                ))}
              </div>
            ))}
            {hasMore && (
              <div className="pt-2">
                <Button
                  variant="ghost"
                  className="w-full text-xs text-muted-foreground"
                  onClick={() => setOffset((v) => v + PAGE_SIZE)}
                >
                  Load more
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      <div className="mt-auto shrink-0 border-t pt-2">
        <div className="flex items-center justify-between px-2 py-1.5">
          <span className="truncate text-xs text-muted-foreground">{user?.username ?? "User"}</span>
          <div className="flex gap-1">
            <Link to="/settings">
              <Button variant="ghost" size="icon" className="h-6 w-6" aria-label="Settings">
                <Settings className="h-3.5 w-3.5" />
              </Button>
            </Link>
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={logout} aria-label="Logout">
              <LogOut className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
