import { useQuery } from "@tanstack/react-query"
import {
  getSubAccountConfig,
  getSubAccounts,
  getSubAccountAssets,
  getSubAccountSpotSummary,
  getFuturesAccount,
  getFuturesPositions,
  getFuturesSummary,
  getMarginAccount,
  getMarginSummary,
  getSpotTransfers,
  getDepositHistory,
} from "@/api/subAccount"

export function useSubAccountConfig() {
  return useQuery({
    queryKey: ["sub-account-config"],
    queryFn: getSubAccountConfig,
    staleTime: 60_000,
  })
}

export function useSubAccounts() {
  return useQuery({
    queryKey: ["sub-accounts"],
    queryFn: () => getSubAccounts(),
    staleTime: 15_000,
  })
}

export function useSubAccountAssets(email: string | null) {
  return useQuery({
    queryKey: ["sub-account-assets", email],
    queryFn: () => getSubAccountAssets(email!),
    enabled: !!email,
    staleTime: 10_000,
  })
}

export function useSubAccountSpotSummary(email?: string) {
  return useQuery({
    queryKey: ["sub-account-spot-summary", email],
    queryFn: () => getSubAccountSpotSummary(email),
    staleTime: 10_000,
  })
}

export function useFuturesAccount(email: string | null) {
  return useQuery({
    queryKey: ["futures-account", email],
    queryFn: () => getFuturesAccount(email!),
    enabled: !!email,
    staleTime: 10_000,
  })
}

export function useFuturesPositions(email: string | null) {
  return useQuery({
    queryKey: ["futures-positions", email],
    queryFn: () => getFuturesPositions(email!),
    enabled: !!email,
    staleTime: 10_000,
  })
}

export function useFuturesSummary() {
  return useQuery({
    queryKey: ["futures-summary"],
    queryFn: () => getFuturesSummary(),
    staleTime: 15_000,
  })
}

export function useMarginAccount(email: string | null) {
  return useQuery({
    queryKey: ["margin-account", email],
    queryFn: () => getMarginAccount(email!),
    enabled: !!email,
    staleTime: 10_000,
  })
}

export function useMarginSummary() {
  return useQuery({
    queryKey: ["margin-summary"],
    queryFn: getMarginSummary,
    staleTime: 15_000,
  })
}

export function useSpotTransfers(params?: {
  from_email?: string
  to_email?: string
  start_time?: number
  end_time?: number
  page?: number
  limit?: number
}) {
  return useQuery({
    queryKey: ["spot-transfers", params],
    queryFn: () => getSpotTransfers(params),
    staleTime: 10_000,
  })
}

export function useDepositHistory(email: string | null, coin?: string) {
  return useQuery({
    queryKey: ["deposit-history", email, coin],
    queryFn: () => getDepositHistory({ email: email!, coin }),
    enabled: !!email,
    staleTime: 15_000,
  })
}
