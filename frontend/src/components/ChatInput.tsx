import { useEffect, useRef, useState } from 'react';

import sendIconDisabled from '@/assets/chat/send-icon-disabled.svg';
import sendIconHover from '@/assets/chat/send-icon-hover.svg';
import sendIcon from '@/assets/chat/send-icon.svg';
import stopIconHover from '@/assets/chat/stop-icon-hover.svg';
import stopIcon from '@/assets/chat/stop-icon.svg';

interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  isStreaming: boolean;
  onSend: (input: string) => void;
  onCancel: () => void;
}

export const ChatInput = ({
  input,
  setInput,
  isStreaming,
  onSend,
  onCancel,
}: ChatInputProps) => {
  const [isSendOrStopHovered, setIsSendOrStopHovered] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`; // 자동 높이 + 최대 높이 220px로 제한
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) return; // 줄바꿈 허용
      e.preventDefault();

      if (isStreaming) return;

      if (!isStreaming && input.trim()) {
        onSend(input);
      }
    }
  };

  return (
    <div className="flex absolute translate-x-[-50%] left-[calc(50%+76px/2-4px)] bottom-[40px] w-[720px] h-fit">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="궁금한 내용을 입력해주세요"
        className="max-h-[220px] min-h-[160px] w-full resize-none overflow-y-auto rounded-[24px] border border-[gray2] bg-white p-6 text-[20px] font-[500] text-black placeholder-gray3 shadow-[0px_0px_12px_0px_rgba(98,98,98,0.04)] outline-none"
        disabled={isStreaming}
      />

      <button
        onClick={isStreaming ? onCancel : () => onSend(input)}
        onMouseEnter={() => setIsSendOrStopHovered(true)}
        onMouseLeave={() => setIsSendOrStopHovered(false)}
        className="absolute bottom-8 right-6 items-center justify-center"
      >
        <img
          src={
            isStreaming
              ? isSendOrStopHovered
                ? stopIconHover
                : stopIcon
              : !input.trim()
                ? sendIconDisabled
                : isSendOrStopHovered
                  ? sendIconHover
                  : sendIcon
          }
          alt={isStreaming ? '중단' : '전송'}
          className="w-[36px]"
        />
      </button>
    </div>
  );
};
