import { apiFetch } from "./client"
import type { BinanceAuthStatus, TokenResponse } from "@/types/api"

export function registerUser(username: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  })
}

export function loginUser(username: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  })
}

export function getBinanceStatus(): Promise<BinanceAuthStatus> {
  return apiFetch<BinanceAuthStatus>("/binance/auth/status")
}

export function logoutBinance(): Promise<{ authenticated: boolean }> {
  return apiFetch<{ authenticated: boolean }>("/binance/auth/logout", { method: "POST" })
}

export function getBinanceAuthUrl(): string {
  return "/api/v1/binance/auth"
}
