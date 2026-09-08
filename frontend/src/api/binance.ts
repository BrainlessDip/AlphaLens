import { apiFetch } from "./client"
import type { BinanceStatusResponse } from "@/types/api"

export async function getBinanceStatus(): Promise<BinanceStatusResponse> {
  return apiFetch<BinanceStatusResponse>("/binance/status")
}
