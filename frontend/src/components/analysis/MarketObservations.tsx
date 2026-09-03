import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye } from "lucide-react"

interface MarketObservationsProps {
  observations: string[]
}

export function MarketObservations({ observations }: MarketObservationsProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Eye className="h-4 w-4" />
          Market Observations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {observations.map((obs, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              {obs}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
