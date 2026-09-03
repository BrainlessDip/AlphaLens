import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AnalysisForm } from "@/components/analysis/AnalysisForm"
import { AnalysisResult } from "@/components/analysis/AnalysisResult"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { analyzeMarket } from "@/api/agent"
import type { AnalyzeResponse } from "@/types/api"
import { AlertCircle } from "lucide-react"

export function AnalyzePage() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (symbol: string, question: string) => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await analyzeMarket({ symbol, question })
      setResult(data)
    } catch (err: unknown) {
      const apiErr = err as { error?: { message?: string } }
      setError(apiErr?.error?.message || "Analysis failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Market Analysis</h1>
        <p className="text-muted-foreground">
          Get an evidence-based AI analysis of a trading pair.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Configure Analysis</CardTitle>
          <CardDescription>Select a trading pair and enter your question.</CardDescription>
        </CardHeader>
        <CardContent>
          <AnalysisForm onSubmit={handleSubmit} isLoading={isLoading} />
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Analysis Failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isLoading && (
        <div className="space-y-4">
          <div className="h-8 w-48 animate-pulse rounded bg-muted" />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="h-32 animate-pulse rounded-lg bg-muted" />
            <div className="h-32 animate-pulse rounded-lg bg-muted" />
          </div>
          <div className="h-48 animate-pulse rounded-lg bg-muted" />
        </div>
      )}

      {result && <AnalysisResult data={result} />}
    </div>
  )
}
