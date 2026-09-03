import { MessageSquare, BarChart3, TrendingUp, GitCompare } from "lucide-react"

const prompts = [
  { text: "Why is BTC moving?", icon: TrendingUp },
  { text: "Analyze ETH momentum", icon: BarChart3 },
  { text: "What changed in the market today?", icon: MessageSquare },
  { text: "Compare BTC and ETH", icon: GitCompare },
]

interface ChatEmptyStateProps {
  onPrompt: (prompt: string) => void
}

export function ChatEmptyState({ onPrompt }: ChatEmptyStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
        <MessageSquare className="h-8 w-8 text-primary" />
      </div>
      <div className="text-center">
        <h2 className="text-xl font-semibold">Market Intelligence Agent</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask questions about crypto markets. The agent will fetch real-time data from Binance.
        </p>
      </div>
      <div className="grid w-full max-w-md gap-2 sm:grid-cols-2">
        {prompts.map((p) => (
          <button
            key={p.text}
            onClick={() => onPrompt(p.text)}
            className="flex items-center gap-2 rounded-lg border bg-secondary/50 px-4 py-3 text-left text-sm transition-colors hover:bg-secondary"
          >
            <p.icon className="h-4 w-4 shrink-0 text-muted-foreground" />
            {p.text}
          </button>
        ))}
      </div>
    </div>
  )
}
