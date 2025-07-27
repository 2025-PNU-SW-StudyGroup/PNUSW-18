import spinner from '@/assets/chat/spinner.svg';
import { institutionImages } from '@/constants/institutionImages';
import { useChatProductStore } from '@/stores/chatProductStore';

interface PendingProps {
  pendingMessage?: string;
}

export const PendingTaskLoader = ({ pendingMessage }: PendingProps) => {
  const products = useChatProductStore((state) => state.products);

  const visibleProducts = products?.slice(0, 3) ?? [];
  const extraCount = Math.max((products?.length ?? 0) - 3, 0);

  return (
    <div className="flex flex-col gap-[12px]">
      <div className="flex items-center gap-[8px]">
        <img
          src={spinner}
          alt="pending"
          className="h-[24px] w-[24px] animate-spin"
        />
        <span className="text-[16px] font-[500] text-gray6">
          {pendingMessage}
        </span>
      </div>

      {products && (
        <div className="flex w-fit items-center rounded-[32px] bg-gray2 py-[4px] pl-[4px] pr-[6px]">
          <div className="flex items-center">
            {visibleProducts.map((product, index) => {
              const imageSrc = product.institution
                ? institutionImages[product.institution]
                : institutionImages['default'];
              return (
                <img
                  key={index}
                  src={imageSrc}
                  alt={product.institution ?? 'institution'}
                  className={`z-[${30 - index * 10}] h-[18px] w-[18px] rounded-full object-cover ${
                    index !== 0 ? '-ml-[6px]' : ''
                  }`}
                />
              );
            })}
          </div>

          {extraCount > 0 && (
            <span className="ml-[4px] text-[12px] font-[500] text-gray5">
              + {extraCount}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
