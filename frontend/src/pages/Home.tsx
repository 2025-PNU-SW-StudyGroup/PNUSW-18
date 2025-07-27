import { useEffect, useRef, useState } from 'react';
import { useChatListStore } from '@/stores/chatListStore';
import { useChat } from '@/hooks/useChat';
import { ChatInput } from '@/components/ChatInput';
import { MessageItem } from '@/components/MessageItem';
import { Sidebar } from '@/components/Sidebar';
import { useChatList } from '@/hooks/useChatList';
import { useParams } from 'react-router-dom';
import { getChatDetail } from '@/api/chat';

export const HomePage = () => {
  const { data: chatListData } = useChatList();
  const setChatList = useChatListStore((state) => state.setChatList);

  useEffect(() => {
    if (chatListData?.items) {
      setChatList(chatListData.items);
    }
  }, [chatListData, setChatList]);

  const { chatId } = useParams();
  const {
    messages,
    pendingMessage,
    isStreaming,
    input,
    setMessages,
    setInput,
    sendMessage,
    cancelStreamingResponse,
  } = useChat();

  useEffect(() => {
    if (chatId) {
      (async () => {
        const { items } = await getChatDetail(chatId);
        setMessages(items);
      })();
    } else {
      setMessages([]);
    }
  }, [chatId, setMessages]);

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="relative flex h-screen bg-white overflow-hidden">
      <div className="fixed right-[60px] top-[36px] z-50 flex items-center gap-[8px]">
        <div className="h-8 w-8 rounded-full bg-[#D9D9D9]" />
        <span className="text-[16px] font-[700] text-[#333534]">
          이용자 이름
        </span>
      </div>

      <Sidebar isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />

      <div
        className={`flex flex-1 [&::-webkit-scrollbar]:[width:8px] [&::-webkit-scrollbar-thumb]:[background-color:lightgray] [&::-webkit-scrollbar-thumb]:[border-radius:8px] [&::-webkit-scrollbar-thumb]:[bg-none] overflow-y-auto h-[calc(100vh-40px)] box-border flex-col items-center transition-all duration-300 ${messages.length === 0 ? 'justify-center' : 'relative mb-[40px] pt-[100px]'}`}
      >
        {messages.length === 0 && (
          <div className="mb-[24px] text-center">
            <h2 className="text-[32px] font-[600] text-[#5D5F62]">
              무엇을 도와드릴까요?
            </h2>
          </div>
        )}

        <div
          className={`absolute translate-x-[-50%] left-[calc(50%+76px/2)] w-full max-w-[800px] pb-[200px] min-h-fit ${
            messages.length === 0 ? '' : 'flex-1'
          }`}
        >
          {messages.map((m, i) => (
            <MessageItem key={i} chatMessage={m} />
          ))}

          {pendingMessage && (
            <MessageItem
              chatMessage={{
                role: 'assistant',
                content: { message: pendingMessage },
              }}
            />
          )}

          <div ref={bottomRef} />

          <div
            className={`${
              messages.length === 0
                ? 'flex items-center justify-center'
                : 'absolute bottom-0 left-0 w-full py-5'
            }`}
          >
          </div>
        </div>
      </div>
        <ChatInput
          input={input}
          setInput={setInput}
          isStreaming={isStreaming}
          onSend={() => sendMessage(input, chatId)}
          onCancel={cancelStreamingResponse}
        />
    </div>
  );
};
