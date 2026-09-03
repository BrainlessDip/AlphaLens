import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useBinanceStatus, useBinanceLogout } from "@/hooks/useBinanceStatus"
import { getBinanceAuthUrl } from "@/api/binance"
import { ExternalLink, Unlink } from "lucide-react"

export function BinanceConnectionCard() {
  const { data: status, isLoading } = useBinanceStatus()
  const logoutMutation = useBinanceLogout()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="h-5 w-32 animate-pulse rounded bg-muted" />
          <div className="h-4 w-48 animate-pulse rounded bg-muted" />
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Binance Account</CardTitle>
          <Badge variant={status?.authenticated ? "success" : "secondary"}>
            {status?.authenticated ? "Connected" : "Not connected"}
          </Badge>
        </div>
        <CardDescription>
          {status?.authenticated
            ? "Your Binance account is linked for market data access."
            : "Connect your Binance account to access market intelligence."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {status?.authenticated ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => logoutMutation.mutate()}
            disabled={logoutMutation.isPending}
          >
            <Unlink className="h-4 w-4" />
            Disconnect
          </Button>
        ) : (
          <Button size="sm">
            <a href={getBinanceAuthUrl()}>
              <ExternalLink className="h-4 w-4" />
              Connect Binance
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
