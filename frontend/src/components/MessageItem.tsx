import { ChatDetailItem } from '@/api/chat';
import ReactMarkdown from 'react-markdown';

import { ChatbotResponseRenderer } from './ChatbotResponseRenderer';
import { PendingTaskLoader } from './PendingTaskLoader';

interface MessageItemProps {
  chatMessage: ChatDetailItem;
}

export const MessageItem = ({ chatMessage }: MessageItemProps) => {
  const { message: textContent, products } = chatMessage.content || {};
  const isUser = chatMessage.role === 'user';
  const isPending = 
    !isUser && !products && textContent?.endsWith('니다.');

  return (
    <div
      className={`mb-[52px] w-fit rounded-[32px] font-[500] text-black ${
        isUser ? 'ml-auto max-w-[70%] bg-[#FAF8F6] px-[20px] py-[12px]' : 'mr-auto'
      }`}
    >
      {/* 사용자 메시지 */}
      {isUser && textContent}

      {/* 챗봇 메시지 - status: pending */}
      {isPending && (
        <div className="relative mx-auto mt-[86px] w-[720px]">
          <PendingTaskLoader pendingMessage={textContent} />
        </div>
      )}

      {/* 챗봇 메시지 - 상품 리스트 */}
      {!isUser && products && <ChatbotResponseRenderer products={products} />}

      {/* 챗봇 메시지 - 추천 이유 */}
      {!isUser && textContent && !isPending && (
        <div className="relative mx-auto mt-6 w-[800px]">
          <div className="prose mx-auto mt-[40px] w-[720px] text-[16px] font-[400] leading-[24px] text-[#242525]">
            <ReactMarkdown>{textContent}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
};
