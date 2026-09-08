import { apiFetch } from "./client"
import type {
  SubAccountInfo,
  SubAccountStatus,
  SubAccountAssetsResponse,
  SubAccountSpotSummary,
  FuturesAccountResponse,
  FuturesPositionRiskResponse,
  FuturesAccountSummaryResponse,
  MarginAccountResponse,
  MarginAccountSummaryResponse,
  SpotTransfer,
  FuturesTransfer,
  UniversalTransfer,
  DepositHistoryResponse,
  SubAccountConfigResponse,
} from "@/types/api"

export async function getSubAccountConfig(): Promise<SubAccountConfigResponse> {
  return apiFetch<SubAccountConfigResponse>("/sub-account/config")
}

export async function getSubAccounts(
  params?: { email?: string; page?: number; limit?: number }
): Promise<SubAccountInfo[]> {
  const query = new URLSearchParams()
  if (params?.email) query.set("email", params.email)
  if (params?.page) query.set("page", String(params.page))
  if (params?.limit) query.set("limit", String(params.limit))
  const qs = query.toString()
  return apiFetch<SubAccountInfo[]>(`/sub-account${qs ? `?${qs}` : ""}`)
}

export async function getSubAccountStatus(
  email?: string
): Promise<SubAccountStatus[]> {
  const query = email ? `?email=${encodeURIComponent(email)}` : ""
  return apiFetch<SubAccountStatus[]>(`/sub-account/status${query}`)
}

export async function getSubAccountAssets(
  email: string
): Promise<SubAccountAssetsResponse> {
  return apiFetch<SubAccountAssetsResponse>(
    `/sub-account/assets?email=${encodeURIComponent(email)}`
  )
}

export async function getSubAccountSpotSummary(
  email?: string
): Promise<SubAccountSpotSummary> {
  const query = email ? `?email=${encodeURIComponent(email)}` : ""
  return apiFetch<SubAccountSpotSummary>(
    `/sub-account/spot-summary${query}`
  )
}

export async function getFuturesAccount(
  email: string
): Promise<FuturesAccountResponse> {
  return apiFetch<FuturesAccountResponse>(
    `/sub-account/futures?email=${encodeURIComponent(email)}`
  )
}

export async function getFuturesPositions(
  email: string
): Promise<FuturesPositionRiskResponse> {
  return apiFetch<FuturesPositionRiskResponse>(
    `/sub-account/futures/positions?email=${encodeURIComponent(email)}`
  )
}

export async function getFuturesSummary(
  page = 1,
  limit = 10
): Promise<FuturesAccountSummaryResponse> {
  return apiFetch<FuturesAccountSummaryResponse>(
    `/sub-account/futures/summary?page=${page}&limit=${limit}`
  )
}

export async function getMarginAccount(
  email: string
): Promise<MarginAccountResponse> {
  return apiFetch<MarginAccountResponse>(
    `/sub-account/margin?email=${encodeURIComponent(email)}`
  )
}

export async function getMarginSummary(): Promise<MarginAccountSummaryResponse> {
  return apiFetch<MarginAccountSummaryResponse>(
    `/sub-account/margin/summary`
  )
}

export async function getSpotTransfers(params?: {
  from_email?: string
  to_email?: string
  start_time?: number
  end_time?: number
  page?: number
  limit?: number
}): Promise<SpotTransfer[]> {
  const query = new URLSearchParams()
  if (params?.from_email) query.set("from_email", params.from_email)
  if (params?.to_email) query.set("to_email", params.to_email)
  if (params?.start_time) query.set("start_time", String(params.start_time))
  if (params?.end_time) query.set("end_time", String(params.end_time))
  if (params?.page) query.set("page", String(params.page))
  if (params?.limit) query.set("limit", String(params.limit))
  const qs = query.toString()
  return apiFetch<SpotTransfer[]>(
    `/sub-account/transfers/spot${qs ? `?${qs}` : ""}`
  )
}

export async function getFuturesTransfers(params?: {
  email?: string
  futures_type?: number
  start_time?: number
  end_time?: number
  page?: number
  limit?: number
}): Promise<FuturesTransfer[]> {
  const query = new URLSearchParams()
  if (params?.email) query.set("email", params.email)
  if (params?.futures_type) query.set("futures_type", String(params.futures_type))
  if (params?.start_time) query.set("start_time", String(params.start_time))
  if (params?.end_time) query.set("end_time", String(params.end_time))
  if (params?.page) query.set("page", String(params.page))
  if (params?.limit) query.set("limit", String(params.limit))
  const qs = query.toString()
  return apiFetch<FuturesTransfer[]>(
    `/sub-account/transfers/futures${qs ? `?${qs}` : ""}`
  )
}

export async function getUniversalTransfers(params?: {
  from_email?: string
  to_email?: string
  start_time?: number
  end_time?: number
  page?: number
  limit?: number
}): Promise<UniversalTransfer[]> {
  const query = new URLSearchParams()
  if (params?.from_email) query.set("from_email", params.from_email)
  if (params?.to_email) query.set("to_email", params.to_email)
  if (params?.start_time) query.set("start_time", String(params.start_time))
  if (params?.end_time) query.set("end_time", String(params.end_time))
  if (params?.page) query.set("page", String(params.page))
  if (params?.limit) query.set("limit", String(params.limit))
  const qs = query.toString()
  return apiFetch<UniversalTransfer[]>(
    `/sub-account/transfers/universal${qs ? `?${qs}` : ""}`
  )
}

export async function getDepositHistory(params: {
  email: string
  coin?: string
  start_time?: number
  end_time?: number
  limit?: number
}): Promise<DepositHistoryResponse> {
  const query = new URLSearchParams({ email: params.email })
  if (params.coin) query.set("coin", params.coin)
  if (params.start_time) query.set("start_time", String(params.start_time))
  if (params.end_time) query.set("end_time", String(params.end_time))
  if (params.limit) query.set("limit", String(params.limit))
  return apiFetch<DepositHistoryResponse>(
    `/sub-account/deposits?${query.toString()}`
  )
}
