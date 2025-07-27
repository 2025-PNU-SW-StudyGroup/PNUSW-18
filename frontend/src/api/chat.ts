import { useChatListStore } from '@/stores/chatListStore';
import { fetchInstance } from './fetchInstance';
import { useChatProductStore } from '@/stores/chatProductStore';

// 대화 요청
export interface ChatRequestBody {
  chat_id?: string | null;
  message: string;
}

type ChatStatus = 'pending' | 'title' | 'response' | 'stop' | 'failed';

export interface ProductOption {
  category: string;
  value: string;
}

export interface Product {
  name: string | null;
  product_type: string | null;
  description: string | null;
  institution: string | null;
  details: string | null;
  tags: string[] | null;
  options: ProductOption[] | null;
}

export interface ChatContent {
  message?: string;
  products?: Product[];
}

export interface SSEChatResponse {
  chat_id: string;
  status: ChatStatus;
  content: ChatContent | null;
}

export const createChatStream = (
  body: ChatRequestBody,
  onMessage: (data: SSEChatResponse) => void
) => {
  const controller = new AbortController();

  fetch(`/api/v1/chats`, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('accessToken') || ''}`,
    },
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body?.getReader();
    const decoder = new TextDecoder('utf-8');

    if (!reader) return;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });

      chunk.split('\n').forEach((line) => {
        if (line.startsWith('data: ')) {
          const jsonString = line.replace('data: ', '').trim();
          if (jsonString === '[DONE]') {
            controller.abort();
            return;
          }

          try {
            const parsed: SSEChatResponse = JSON.parse(jsonString);
            onMessage(parsed);

            if (parsed.status === 'pending') {
              if (parsed.content?.products) {
                useChatProductStore
                  .getState()
                  .setProducts(parsed.content.products);
              } else {
                useChatProductStore.getState().setProducts(null);
              }
            }

            if (parsed.status === 'title' && parsed.content?.message) {
              useChatListStore
                .getState()
                .updateTitle(parsed.chat_id, parsed.content.message);
            }
          } catch (err) {
            console.error('파싱 오류', err);
          }
        }
      });
    }
  });

  return () => {
    controller.abort();
  };
};

// 전체 대화 목록
export interface ChatListItem {
  title: string;
  chat_id: string;
  updated_at: string;
}

export interface ChatListResponse {
  size: number;
  offset: number;
  items: ChatListItem[];
}

export const getChatList = async (
  offset = 0,
  size = 20
): Promise<ChatListResponse> => {
  return await fetchInstance.get('/api/v1/chats', {
    params: { offset, size },
  });
};

// 상세 대화 내역
export interface ChatDetailItem {
  role: 'user' | 'assistant';
  content: ChatContent;
}

export interface ChatDetailResponse {
  size: number;
  offset: number;
  chat_id: string;
  items: ChatDetailItem[];
}

export const getChatDetail = async (
  chatId: string,
  offset = 0,
  size = 10
): Promise<ChatDetailResponse> => {
  return await fetchInstance.get(`/api/v1/chats/${chatId}`, {
    params: { offset, size },
  });
};
