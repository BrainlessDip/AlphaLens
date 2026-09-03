import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { BarChart3, Loader2 } from "lucide-react"

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]

interface AnalysisFormProps {
  onSubmit: (symbol: string, question: string) => void
  isLoading: boolean
}

export function AnalysisForm({ onSubmit, isLoading }: AnalysisFormProps) {
  const [symbol, setSymbol] = useState("BTCUSDT")
  const [question, setQuestion] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim() || !question.trim()) return
    onSubmit(symbol.trim().toUpperCase(), question.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1.5 block text-sm font-medium">Trading Pair</label>
        <div className="flex flex-wrap gap-2">
          {SYMBOLS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSymbol(s)}
              className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                symbol === s
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:bg-secondary"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <Input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="e.g. BTCUSDT"
          className="mt-2"
        />
      </div>
      <div>
        <label className="mb-1.5 block text-sm font-medium">Question</label>
        <Textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Why has BTC moved significantly in the last few hours?"
          rows={3}
        />
      </div>
      <Button type="submit" disabled={!symbol.trim() || !question.trim() || isLoading}>
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <BarChart3 className="h-4 w-4" />
        )}
        Analyze Market
      </Button>
    </form>
  )
}
