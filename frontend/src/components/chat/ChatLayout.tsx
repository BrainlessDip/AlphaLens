import * as React from "react"
import { Link } from "react-router"
import { BarChart3 } from "lucide-react"
import { ChatSidebar } from "./ChatSidebar"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

export function ChatLayout({
  activeChatId,
  onSelect,
  onNewChat,
  collapsed,
  children,
}: {
  activeChatId?: string
  onSelect: (id: string) => void
  onNewChat: () => void
  collapsed?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="flex h-dvh bg-background">
      <aside
        className={cn(
          "hidden shrink-0 flex-col gap-3 border-r p-3 transition-[width] duration-200 md:flex",
          collapsed ? "w-0 overflow-hidden" : "w-64"
        )}
        aria-label="Chat history"
      >
        <Link to="/chat" className="flex items-center gap-2 px-2 py-1" aria-label="AlphaLens home">
          <BarChart3 className="h-5 w-5 text-primary" />
          <span className="font-semibold">AlphaLens</span>
        </Link>
        <Separator />
        <div className="min-h-0 flex-1">
          <ChatSidebar activeChatId={activeChatId} onSelect={onSelect} onNewChat={onNewChat} />
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">{children}</div>
    </div>
  )
}
