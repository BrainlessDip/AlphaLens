import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useHealth } from "@/hooks/useHealth"
import { useAuth } from "@/contexts/AuthContext"
import { Activity } from "lucide-react"

function StatusBadge({ ok, okLabel, badLabel }: { ok: boolean; okLabel: string; badLabel: string }) {
  return (
    <Badge variant={ok ? "success" : "destructive"}>
      <Activity className="mr-1 h-3 w-3" />
      {ok ? okLabel : badLabel}
    </Badge>
  )
}

export function SettingsPage() {
  const { data: health, isLoading: healthLoading } = useHealth()
  const { user } = useAuth()

  const binanceOk = health?.binance_status === "operational"

  return (
    <div className="mx-auto w-full max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Application status and account.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">AI</CardTitle>
          <CardDescription>Model provider information.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Provider</span>
            <span className="text-xs text-muted-foreground">OpenRouter</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Model</span>
            {healthLoading ? (
              <div className="h-5 w-32 animate-pulse rounded bg-muted" />
            ) : (
              <span className="font-mono text-xs text-muted-foreground">{health?.model ?? "Unknown"}</span>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Binance</CardTitle>
          <CardDescription>Market data availability. No account connection needed.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Market data</span>
            <span className="text-xs text-muted-foreground">Binance Spot REST API (public)</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">API status</span>
            {healthLoading ? (
              <div className="h-5 w-24 animate-pulse rounded bg-muted" />
            ) : (
              <StatusBadge ok={binanceOk} okLabel="Operational" badLabel={health?.binance_status ?? "Unknown"} />
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Account</CardTitle>
          <CardDescription>Signed-in user.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Username</span>
            <span className="text-xs text-muted-foreground">{user?.username ?? "—"}</span>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <span className="text-sm">Backend</span>
            {healthLoading ? (
              <div className="h-5 w-16 animate-pulse rounded bg-muted" />
            ) : (
              <StatusBadge ok={health?.status === "ok"} okLabel="Healthy" badLabel="Error" />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
