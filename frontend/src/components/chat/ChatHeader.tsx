import { Link } from "react-router"
import { BarChart3, Menu, MoreHorizontal, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { ChatSidebar } from "./ChatSidebar"

interface ChatHeaderProps {
  title?: string
  activeChatId?: string
  onSelect: (id: string) => void
  onNewChat: () => void
}

export function ChatHeader({ title, activeChatId, onSelect, onNewChat }: ChatHeaderProps) {
  const sidebar = <ChatSidebar activeChatId={activeChatId} onSelect={onSelect} onNewChat={onNewChat} />

  return (
    <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center gap-2 border-b bg-background/95 px-3 backdrop-blur">
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open chat history">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" aria-label="Chat history">
          <SheetHeader>
            <SheetTitle>Chats</SheetTitle>
          </SheetHeader>
          <div className="min-h-0 flex-1">{sidebar}</div>
        </SheetContent>
      </Sheet>

      <Link to="/chat" className="flex items-center gap-2 md:hidden" aria-label="AlphaLens home">
        <BarChart3 className="h-5 w-5 text-primary" />
      </Link>

      <h1 className="min-w-0 flex-1 truncate text-sm font-medium">
        {title ?? "New chat"}
      </h1>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Chat options">
            <MoreHorizontal className="h-5 w-5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem icon={<Settings className="h-3.5 w-3.5" />}>
            <Link to="/settings">Settings</Link>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}
