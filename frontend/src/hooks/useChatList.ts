import { useQuery } from '@tanstack/react-query';
import { getChatList } from '@/api/chat';
import { ChatListResponse } from '@/api/chat';

export const useChatList = () => {
  return useQuery<ChatListResponse>({
    queryKey: ['chatList'],
    queryFn: () => getChatList(),
  });
};
