import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AnalysisResult } from "@/components/analysis/AnalysisResult"
import { analyzeMarket } from "@/api/agent"
import type { AnalyzeResponse } from "@/types/api"
import { AlertCircle, BarChart3, Loader2 } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Message, MessageAvatar, MessageContent } from "@/components/ui/message"

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]

export function AnalyzePage() {
  const [symbol, setSymbol] = useState("BTCUSDT")
  const [question, setQuestion] = useState("")
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim() || !question.trim()) return
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await analyzeMarket({ symbol: symbol.trim().toUpperCase(), question: question.trim() })
      setResult(data)
    } catch (err: unknown) {
      const apiErr = err as { error?: { message?: string } }
      setError(apiErr?.error?.message || "Analysis failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {result && <AnalysisResult data={result} />}

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isLoading && (
          <Message>
            <MessageAvatar>
              <Avatar>
                <AvatarFallback className="bg-primary/10 text-primary">
                  <BarChart3 className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            </MessageAvatar>
            <MessageContent>
              <Bubble>
                <BubbleContent variant="muted">
                  <span className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Analyzing {symbol}...
                  </span>
                </BubbleContent>
              </Bubble>
            </MessageContent>
          </Message>
        )}

        {!result && !isLoading && !error && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
              <BarChart3 className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-xl font-semibold">Market Analysis</h1>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Get an evidence-based AI analysis of any trading pair.
            </p>
          </div>
        )}
      </div>

      <div className="shrink-0 border-t bg-background px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3">
        <form onSubmit={handleSubmit} className="mx-auto max-w-3xl space-y-3">
          <div className="flex flex-wrap gap-2">
            {SYMBOLS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSymbol(s)}
                className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                  symbol === s
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:bg-secondary"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="Symbol"
              className="w-28"
            />
            <Textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about market conditions..."
              rows={1}
              className="flex-1 resize-none"
            />
            <Button type="submit" disabled={!symbol.trim() || !question.trim() || isLoading}>
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
