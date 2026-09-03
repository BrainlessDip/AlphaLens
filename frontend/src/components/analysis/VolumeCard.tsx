import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatVolume } from "@/lib/utils"

interface VolumeCardProps {
  volume24h: number
  quoteVolume24h: number
}

export function VolumeCard({ volume24h, quoteVolume24h }: VolumeCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-muted-foreground">24h Volume</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div>
          <p className="text-2xl font-bold">{formatVolume(volume24h)}</p>
          <p className="text-xs text-muted-foreground">Base volume</p>
        </div>
        <div>
          <p className="text-lg font-semibold">${formatVolume(quoteVolume24h)}</p>
          <p className="text-xs text-muted-foreground">Quote volume</p>
        </div>
      </CardContent>
    </Card>
  )
}
