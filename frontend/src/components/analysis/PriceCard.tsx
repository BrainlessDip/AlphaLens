import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatPrice, formatPct } from "@/lib/utils"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface PriceCardProps {
  symbol: string
  price: number
  changePct: number | null
}

export function PriceCard({ symbol, price, changePct }: PriceCardProps) {
  const isUp = changePct !== null && changePct > 0
  const isDown = changePct !== null && changePct < 0

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-muted-foreground">Current Price</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-3">
          <span className="text-3xl font-bold tracking-tight">{formatPrice(price)}</span>
          {changePct !== null && (
            <span
              className={`flex items-center gap-1 text-sm font-medium ${
                isUp ? "text-success" : isDown ? "text-destructive" : "text-muted-foreground"
              }`}
            >
              {isUp ? <TrendingUp className="h-4 w-4" /> : isDown ? <TrendingDown className="h-4 w-4" /> : <Minus className="h-4 w-4" />}
              {formatPct(changePct)}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{symbol}</p>
      </CardContent>
    </Card>
  )
}
