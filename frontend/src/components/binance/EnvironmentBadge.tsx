import { useBinanceStatus } from "@/hooks/useBinanceStatus"
import { cn } from "@/lib/utils"

export function EnvironmentBadge({ className }: { className?: string }) {
  const { data: status, isLoading } = useBinanceStatus()

  if (isLoading) {
    return (
      <span className={cn("inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-muted", className)}>
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-pulse" />
        Loading...
      </span>
    )
  }

  if (!status) return null

  const isTestnet = status.environment === "testnet"

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full font-medium",
        isTestnet
          ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
          : "bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20",
        className
      )}
      title={
        isTestnet
          ? status.testnet_auto_enabled
            ? "No API credentials configured — running in Testnet (sandbox) mode automatically"
            : "Running in Binance Testnet (sandbox) mode"
          : "Running in Binance Production mode — trades are real"
      }
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", isTestnet ? "bg-amber-500" : "bg-red-500")} />
      {isTestnet ? "Binance Testnet" : "Binance Production"}
    </span>
  )
}
