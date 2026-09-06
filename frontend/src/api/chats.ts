import { apiFetch } from "./client"
import type {
  ChatDetailResponse,
  ChatListResponse,
  ChatSummary,
  ShareResponse,
} from "@/types/api"

export function getChats(params?: {
  search?: string
  limit?: number
  offset?: number
}): Promise<ChatListResponse> {
  const query = new URLSearchParams()
  if (params?.search) query.set("search", params.search)
  if (params?.limit !== undefined) query.set("limit", String(params.limit))
  if (params?.offset !== undefined) query.set("offset", String(params.offset))
  const suffix = query.toString() ? `?${query.toString()}` : ""
  return apiFetch<ChatListResponse>(`/chats${suffix}`)
}

export function createChat(): Promise<{ id: string; title: string }> {
  return apiFetch<{ id: string; title: string }>("/chats", { method: "POST" })
}

export function getChat(
  id: string,
  params?: { limit?: number; offset?: number }
): Promise<ChatDetailResponse> {
  const query = new URLSearchParams()
  if (params?.limit !== undefined) query.set("limit", String(params.limit))
  if (params?.offset !== undefined) query.set("offset", String(params.offset))
  const suffix = query.toString() ? `?${query.toString()}` : ""
  return apiFetch<ChatDetailResponse>(`/chats/${id}${suffix}`)
}

export function renameChat(id: string, title: string): Promise<ChatSummary> {
  return apiFetch<ChatSummary>(`/chats/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  })
}

export async function deleteChat(id: string): Promise<void> {
  await apiFetch<unknown>(`/chats/${id}`, { method: "DELETE" })
}

export function createShare(id: string): Promise<ShareResponse> {
  return apiFetch<ShareResponse>(`/chats/${id}/share`, { method: "POST" })
}

export function getSharedChat(id: string, token: string): Promise<ChatDetailResponse> {
  return apiFetch<ChatDetailResponse>(`/chats/${id}/shared?token=${encodeURIComponent(token)}`)
}
