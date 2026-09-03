import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BinanceConnectionCard } from "@/components/binance/BinanceConnectionCard"
import { useHealth } from "@/hooks/useHealth"
import { Activity } from "lucide-react"

export function SettingsPage() {
  const { data: health, isLoading: healthLoading } = useHealth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your connections and application settings.</p>
      </div>

      <BinanceConnectionCard />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Application</CardTitle>
          <CardDescription>Basic application information.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">AlphaLens</span>
            <span className="text-xs text-muted-foreground">Binance Market Intelligence Agent</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Backend Status</span>
            {healthLoading ? (
              <div className="h-5 w-16 animate-pulse rounded bg-muted" />
            ) : (
              <Badge variant={health?.status === "ok" ? "success" : "destructive"}>
                <Activity className="mr-1 h-3 w-3" />
                {health?.status === "ok" ? "Healthy" : "Error"}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
