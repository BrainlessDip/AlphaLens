import { useQuery } from "@tanstack/react-query"
import { getBinanceStatus } from "@/api/binance"

export function useBinanceStatus() {
  return useQuery({
    queryKey: ["binance-status"],
    queryFn: getBinanceStatus,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}
