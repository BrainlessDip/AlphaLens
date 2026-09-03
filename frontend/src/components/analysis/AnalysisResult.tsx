import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PriceCard } from "./PriceCard"
import { VolumeCard } from "./VolumeCard"
import { MarketObservations } from "./MarketObservations"
import type { AnalyzeResponse } from "@/types/api"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { AlertTriangle, Brain, Clock } from "lucide-react"

interface AnalysisResultProps {
  data: AnalyzeResponse
}

export function AnalysisResult({ data }: AnalysisResultProps) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <PriceCard
          symbol={data.symbol}
          price={data.current_price}
          changePct={data.price_change.change_pct}
        />
        <VolumeCard
          volume24h={data.volume_info.volume_24h}
          quoteVolume24h={data.volume_info.quote_volume_24h}
        />
      </div>

      {data.market_observations.length > 0 && (
        <MarketObservations observations={data.market_observations} />
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Brain className="h-4 w-4" />
            AI Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.agent_analysis}</ReactMarkdown>
          </div>
        </CardContent>
      </Card>

      <Card className="border-warning/30 bg-warning/5">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm text-warning">
            <AlertTriangle className="h-4 w-4" />
            Confidence & Limitations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">{data.confidence_and_limitations}</p>
          <p className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            Data as of {new Date(data.data_timestamp).toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
