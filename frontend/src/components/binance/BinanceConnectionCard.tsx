import axios from "axios"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useBinanceStatus, useBinanceLogout } from "@/hooks/useBinanceStatus"
import { useAuth } from "@/contexts/AuthContext"
import { ExternalLink, Unlink } from "lucide-react"

export function BinanceConnectionCard() {
  const { data: status, isLoading } = useBinanceStatus()
  const logoutMutation = useBinanceLogout()
  const { token } = useAuth()

  const handleConnect = async () => {
    try {
      const res = await axios.get("/api/v1/binance/auth", {
        headers: { Authorization: `Bearer ${token}` },
        maxRedirects: 0,
        validateStatus: (s) => s < 400,
      })
      const redirectUrl = res.request?.responseURL || res.data
      if (typeof redirectUrl === "string" && redirectUrl.startsWith("http")) {
        window.location.href = redirectUrl
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response) {
        const location = err.response.headers?.location
        if (location) {
          window.location.href = location
          return
        }
      }
      console.error("Failed to start OAuth:", err)
    }
  }

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
          <Badge variant={status?.connected ? "success" : "secondary"}>
            {status?.connected ? "Connected" : "Not connected"}
          </Badge>
        </div>
        <CardDescription>
          {status?.connected
            ? "Your Binance account is linked for market data access."
            : status?.needs_reauth
              ? "Connection expired. Please reconnect your Binance account."
              : "Connect your Binance account to access market intelligence."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {status?.connected || status?.needs_reauth ? (
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
          <Button size="sm" onClick={handleConnect}>
            <ExternalLink className="h-4 w-4" />
            Connect Binance
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
