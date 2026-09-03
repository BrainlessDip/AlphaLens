import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getBinanceStatus, logoutBinance } from "@/api/binance"

export function useBinanceStatus() {
  return useQuery({
    queryKey: ["binance-status"],
    queryFn: getBinanceStatus,
    refetchInterval: 60_000,
    retry: false,
  })
}

export function useBinanceLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: logoutBinance,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["binance-status"] })
    },
  })
}
