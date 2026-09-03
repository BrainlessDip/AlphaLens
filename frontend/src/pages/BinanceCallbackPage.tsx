import { useEffect, useState } from "react"
import { useNavigate } from "react-router"
import { useBinanceStatus } from "@/hooks/useBinanceStatus"
import { Loader2 } from "lucide-react"

export function BinanceCallbackPage() {
  const navigate = useNavigate()
  const { data: status, isLoading } = useBinanceStatus()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isLoading && status) {
      if (status.authenticated) {
        navigate("/settings", { replace: true })
      } else {
        setError("Binance connection failed. Please try connecting again.")
      }
    }
  }, [status, isLoading, navigate])

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Connecting to Binance...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <p className="text-sm text-destructive">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  return null
}
