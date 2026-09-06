import { useQuery } from "@tanstack/react-query"
import { getChat } from "@/api/chats"

export function chatMessagesKey(chatId: string | undefined) {
  return ["chat-messages", chatId] as const
}

export function useChatMessages(chatId: string | undefined) {
  return useQuery({
    queryKey: chatMessagesKey(chatId),
    queryFn: () => getChat(chatId!, { limit: 200 }),
    enabled: !!chatId,
    staleTime: 10_000,
  })
}
