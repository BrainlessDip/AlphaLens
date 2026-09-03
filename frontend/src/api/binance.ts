import { apiFetch } from "./client"
import type { BinanceAuthStatus } from "@/types/api"

export function getBinanceStatus(): Promise<BinanceAuthStatus> {
  return apiFetch<BinanceAuthStatus>("/binance/auth/status")
}

export function logoutBinance(): Promise<BinanceAuthStatus> {
  return apiFetch<BinanceAuthStatus>("/binance/auth/logout", { method: "POST" })
}

export function getBinanceAuthUrl(): string {
  return "/api/v1/binance/auth"
}
