import { ChatListItem } from '@/api/chat';
import { create } from 'zustand';

interface ChatListState {
  chatList: ChatListItem[];
  setChatList: (list: ChatListItem[]) => void;
  updateTitle: (chat_id: string, title: string, updated_at?: string) => void;
}

export const useChatListStore = create<ChatListState>((set) => ({
  chatList: [],
  setChatList: (newList) => {
    set({ chatList: newList });
  },
  updateTitle: (chat_id, title, updated_at?) =>
    set((state) => {
      const updated = [...state.chatList];
      const index = updated.findIndex((item) => item.chat_id === chat_id);

      if (index !== -1) {
        updated[index] = { ...updated[index], title };
      } else {
        updated.unshift({
          chat_id,
          title,
          updated_at: updated_at ?? new Date().toISOString(),
        });
      }

      return { chatList: updated };
    }),
}));
