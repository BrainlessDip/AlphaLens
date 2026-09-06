import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getChats, createChat, renameChat, deleteChat } from "@/api/chats"

export const CHATS_QUERY_KEY = ["chats"] as const

export function useChatHistory(search?: string, limit = 100, offset = 0) {
  return useQuery({
    queryKey: [...CHATS_QUERY_KEY, { search: search ?? "", limit, offset }],
    queryFn: () => getChats({
      search: search || undefined,
      limit,
      offset,
    }),
    staleTime: 10_000,
  })
}

export function useCreateChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createChat,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHATS_QUERY_KEY })
    },
  })
}

export function useRenameChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => renameChat(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHATS_QUERY_KEY })
    },
  })
}

export function useDeleteChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteChat(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHATS_QUERY_KEY })
    },
  })
}
