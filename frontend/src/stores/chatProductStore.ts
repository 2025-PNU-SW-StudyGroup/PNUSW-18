import { create } from 'zustand';
import { Product } from '@/api/chat';

interface PendingProductState {
  products: Product[] | null;
  setProducts: (products: Product[] | null) => void;
  resetProducts: () => void;
}

export const useChatProductStore = create<PendingProductState>((set) => ({
  products: null,
  setProducts: (products) => set({ products }),
  resetProducts: () => set({ products: null }),
}));
