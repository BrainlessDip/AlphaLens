import { BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"

const SUGGESTIONS = [
  "Analyze BTC right now",
  "What is the current ETH trend?",
  "Compare BTC 1h vs 4h momentum",
  "What are the biggest market movers?",
]

export function ChatEmptyState({ onPrompt }: { onPrompt: (prompt: string) => void }) {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-6 px-4 py-12 text-center">
      <div>
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
          <BarChart3 className="h-6 w-6 text-primary" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">AlphaLens</h1>
        <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
          Your AI market intelligence assistant. Ask about markets, trends, volatility,
          momentum, and Binance market data.
        </p>
      </div>
      <div className="grid w-full gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <Button
            key={suggestion}
            variant="outline"
            className="h-auto justify-start whitespace-normal px-4 py-3 text-left text-sm font-normal"
            onClick={() => onPrompt(suggestion)}
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  )
}
