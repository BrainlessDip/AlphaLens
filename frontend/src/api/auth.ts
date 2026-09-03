import { apiFetch } from "./client"
import type { TokenResponse } from "@/types/api"

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
