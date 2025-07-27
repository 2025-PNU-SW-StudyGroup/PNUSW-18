import { ChatListItem } from '@/api/chat';
import logo from '@/assets/sidebar/logo.svg';
import newChat from '@/assets/sidebar/new-chat.svg';
import newChatHover from '@/assets/sidebar/new-chat-hover.svg';
import policyIcon from '@/assets/sidebar/policy.svg';
import policyIconHover from '@/assets/sidebar/policy-hover.svg';
import prevIcon from '@/assets/sidebar/prev.svg';
import prevIconHover from '@/assets/sidebar/prev-hover.svg';
import { useChatListStore } from '@/stores/chatListStore';
import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

interface SidebarProps {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const Sidebar = ({ isSidebarOpen, toggleSidebar }: SidebarProps) => {
  const chatList = useChatListStore((state) => state.chatList);

  const formatDateLabel = (updatedAt: string) => {
    const formatToYMD = (date: Date) =>
      date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      });

    const date = new Date(updatedAt);
    const today = new Date();
    const yesterday = new Date(today);
    const oneWeekAgo = new Date(today);

    yesterday.setDate(today.getDate() - 1);
    oneWeekAgo.setDate(today.getDate() - 7);

    const dateYMD = formatToYMD(date);
    const todayYMD = formatToYMD(today);
    const yesterdayYMD = formatToYMD(yesterday);

    if (dateYMD === todayYMD) return '오늘';
    if (dateYMD === yesterdayYMD) return '어제';
    if (date > oneWeekAgo) return '지난 7일';

    return '이전';
  };

  const groupChatsByDate = (chats: ChatListItem[]) =>
    chats.reduce(
      (acc, chat) => {
        const label = formatDateLabel(chat.updated_at);
        if (!acc[label]) acc[label] = [];
        acc[label].push(chat);
        return acc;
      },
      {} as Record<string, ChatListItem[]>
    );

  const navigate = useNavigate();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const navigateToChatDetail = (chatId: string) => {
    navigate(`/chat/${chatId}`);
  };

  return (
    <div>
      {/* 접힌 상태 */}
      <div className="fixed left-0 top-0 z-30 flex h-screen w-[76px] flex-col items-center justify-between border-r border-gray2 bg-[#FBFBFB] pb-[44px] pt-[36px]">
        <div className="flex h-full flex-col items-center">
          <Link to="/">
            <img src={logo} alt="logo" className="w-[52px]" />
          </Link>
          <div
            className="mt-[44px] flex cursor-pointer flex-col items-center font-[400] text-gray3 hover:text-gray5"
            onClick={toggleSidebar}
            onMouseEnter={() => setHoveredItem('prev')}
            onMouseLeave={() => setHoveredItem(null)}
          >
            <img
              src={hoveredItem === 'prev' ? prevIconHover : prevIcon}
              alt="이전 기록"
              className="w-[40px]"
            />
            <span>이전 기록</span>
          </div>
          <div
            className="mt-[36px] flex cursor-pointer flex-col items-center font-[400] text-gray3 hover:text-gray5"
            onMouseEnter={() => setHoveredItem('policy')}
            onMouseLeave={() => setHoveredItem(null)}
          >
            <img
              src={hoveredItem === 'policy' ? policyIconHover : policyIcon}
              alt="정책"
              className="w-[40px]"
            />
            <span>정책</span>
          </div>
        </div>

        <button
          onClick={() => navigate('/')}
          onMouseEnter={() => setHoveredItem('new')}
          onMouseLeave={() => setHoveredItem(null)}
        >
          <img
            src={hoveredItem === 'new' ? newChatHover : newChat}
            alt="new"
            className="w-[40px]"
          />
        </button>
      </div>

      {/* 펼친 상태 */}
      <div
        className={`absolute left-[76px] top-0 z-20 h-full w-[240px] transform overflow-y-auto border-r border-gray2 bg-[#FBFBFB] px-[16px] pt-[64px] transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {Object.entries(groupChatsByDate([...chatList])).map(
          ([label, chats]) =>
            chats.length > 0 && (
              <div key={label} className="mb-[32px]">
                <h3 className="mb-[12px] text-[12px] font-[600] text-main">
                  {label}
                </h3>
                <ul className="px-[12px]">
                  {chats.map((chat) => (
                    <li
                      key={chat.chat_id}
                      className="mb-1 cursor-pointer truncate py-[8px] text-[14px] font-[400] text-[#242525] hover:font-[600]"
                      onClick={() => navigateToChatDetail(chat.chat_id)}
                    >
                      {chat.title || '제목 없음'}
                    </li>
                  ))}
                </ul>
              </div>
            )
        )}
      </div>
    </div>
  );
};
