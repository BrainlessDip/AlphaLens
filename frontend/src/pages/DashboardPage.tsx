import { Link } from "react-router"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useHealth } from "@/hooks/useHealth"
import {
  BarChart3,
  MessageSquare,
  Activity,
  TrendingUp,
  ArrowRight,
  Zap,
} from "lucide-react"

const quickPrompts = [
  "Why is BTC moving?",
  "Analyze ETH momentum",
  "What changed in the market today?",
  "Compare BTC and ETH",
]

export function DashboardPage() {
  const { data: health, isLoading: healthLoading } = useHealth()

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">
          Understand the market.
          <br />
          Ask better questions.
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          AI-powered Binance market intelligence for faster, evidence-based crypto analysis.
        </p>
        <div className="flex gap-3">
          <Button>
            <Link to="/analyze">
              <BarChart3 className="h-4 w-4" />
              Analyze the Market
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline">
            <Link to="/chat">
              <MessageSquare className="h-4 w-4" />
              Ask the Agent
            </Link>
          </Button>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Backend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              {healthLoading ? (
                <div className="h-4 w-16 animate-pulse rounded bg-muted" />
              ) : (
                <Badge variant={health?.status === "ok" ? "success" : "destructive"}>
                  {health?.status === "ok" ? "Healthy" : "Error"}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Market Data</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              <Badge variant="success">Binance Spot API</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="sm:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Quick Analysis</CardTitle>
            <CardDescription>Get instant market insights</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" size="sm">
              <Link to="/analyze">
                <TrendingUp className="h-4 w-4" />
                Start Analysis
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Quick Prompts</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          {quickPrompts.map((prompt) => (
            <Link
              key={prompt}
              to={`/chat?q=${encodeURIComponent(prompt)}`}
              className="flex items-center gap-2 rounded-lg border bg-secondary/30 px-4 py-3 text-sm transition-colors hover:bg-secondary"
            >
              <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
              {prompt}
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
