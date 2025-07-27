import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChatDetailItem } from '@/api/chat';
import { createChatStream } from '@/api/chat';

export const useChat = () => {
  const [messages, setMessages] = useState<ChatDetailItem[]>([]);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [input, setInput] = useState('');
  const abortRef = useRef<(() => void) | null>(null);
  const navigate = useNavigate();
  const chatIdRef = useRef<string | null>(null);

  const sendMessage = (input: string, chatId?: string) => {
    const newMessage: ChatDetailItem = {
      role: 'user',
      content: { message: input },
    };

    setMessages((prev) => [...prev, newMessage]);
    setIsStreaming(true);
    setInput('');

    abortRef.current = createChatStream(
      { message: input, chat_id: chatId },
      (data) => {
        if (!chatIdRef.current && data.chat_id) {
          chatIdRef.current = data.chat_id;
          navigate(`/chat/${data.chat_id}`);
        }

        if (data.status === 'pending' && data.content?.message) {
          setPendingMessage(data.content.message);
        }

        if (data.status === 'response') {
          setPendingMessage(null);

          setMessages((prev) => {
            const last = prev.at(-1);
            const isLastAssistant = last?.role === 'assistant';

            const incomingMessage = data.content?.message ?? '';
            const incomingProducts = data.content?.products;

            if (isLastAssistant && last?.content.message !== undefined) {
              return [
                ...prev.slice(0, -1),
                {
                  role: 'assistant',
                  content: {
                    ...last.content,
                    message: (last.content.message || '') + incomingMessage,
                    products: incomingProducts ?? last.content.products,
                  },
                },
              ];
            }

            return [
              ...prev,
              {
                role: 'assistant',
                content: {
                  message: incomingMessage,
                  products: incomingProducts,
                },
              },
            ];
          });
        }

        if (data.status === 'stop') {
          setPendingMessage(null);
          setIsStreaming(false);
          chatIdRef.current = null;
        }
      }
    );
  };

  const cancelStreamingResponse = () => {
    if (abortRef.current) {
      abortRef.current();
      setIsStreaming(false);
    }
  };

  return {
    messages,
    pendingMessage,
    isStreaming,
    input,
    setMessages,
    setInput,
    sendMessage,
    cancelStreamingResponse,
  };
};
