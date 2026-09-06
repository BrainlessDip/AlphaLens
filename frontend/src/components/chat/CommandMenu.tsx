import { useEffect, useState } from "react"
import { useNavigate } from "react-router"
import { MessageSquarePlus, Search, BarChart3, Settings, PanelLeft, PenLine } from "lucide-react"
import { CommandDialog, CommandInput, CommandItem, CommandList } from "@/components/ui/command"

export function CommandMenu({
  onNewChat,
  onToggleSidebar,
  onFocusComposer,
}: {
  onNewChat: () => void
  onToggleSidebar?: () => void
  onFocusComposer?: () => void
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const navigate = useNavigate()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setOpen((v) => !v)
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  useEffect(() => {
    if (!open) setQuery("")
  }, [open ])

  const run = (fn: () => void) => () => {
    setOpen(false)
    fn()
  }

  const q = query.trim().toLowerCase()
  const actions = [
    { id: "new", label: "New chat", icon: <MessageSquarePlus className="h-4 w-4" />, run: run(onNewChat), keywords: "new chat create" },
    { id: "search", label: "Search chats", icon: <Search className="h-4 w-4" />, run: run(() => navigate("/chat")), keywords: "search find chats" },
    { id: "analyze", label: "Go to Analyze", icon: <BarChart3 className="h-4 w-4" />, run: run(() => navigate("/analyze")), keywords: "analyze market" },
    { id: "settings", label: "Go to Settings", icon: <Settings className="h-4 w-4" />, run: run(() => navigate("/settings")), keywords: "settings preferences" },
    ...(onToggleSidebar
      ? [{ id: "sidebar", label: "Toggle sidebar", icon: <PanelLeft className="h-4 w-4" />, run: run(onToggleSidebar), keywords: "toggle sidebar hide show" }]
      : []),
    ...(onFocusComposer
      ? [{ id: "composer", label: "Focus composer", icon: <PenLine className="h-4 w-4" />, run: run(onFocusComposer), keywords: "focus composer write ask" }]
      : []),
  ].filter((a) => !q || a.label.toLowerCase().includes(q) || a.keywords.includes(q))

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Type a command or search..."
        aria-label="Command menu"
      />
      <CommandList>
        {actions.length === 0 && (
          <p className="px-3 py-4 text-center text-sm text-muted-foreground">No matching actions.</p>
        )}
        {actions.map((action) => (
          <CommandItem key={action.id} icon={action.icon} onClick={action.run}>
            {action.label}
          </CommandItem>
        ))}
      </CommandList>
    </CommandDialog>
  )
}
