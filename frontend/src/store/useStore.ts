import { create } from "zustand";
import type { FilterState, Photo, Stats } from "../types";
import { fetchPhotos, fetchStats } from "../api/photos";

interface AppStore {
  photos: Photo[];
  selectedIds: Set<number>;
  activePhoto: Photo | null;
  filters: FilterState;
  stats: Stats | null;
  loading: boolean;
  error: string | null;

  setPhotos: (photos: Photo[]) => void;
  toggleSelect: (id: number) => void;
  selectAll: () => void;
  clearSelection: () => void;
  setActivePhoto: (photo: Photo | null) => void;
  setFilters: (f: Partial<FilterState>) => void;
  loadPhotos: () => Promise<void>;
  loadStats: () => Promise<void>;
}

export const useStore = create<AppStore>((set, get) => ({
  photos: [],
  selectedIds: new Set(),
  activePhoto: null,
  filters: { theme: "", search: "", dateFrom: "", dateTo: "" },
  stats: null,
  loading: false,
  error: null,

  setPhotos: (photos) => set({ photos }),

  toggleSelect: (id) =>
    set((s) => {
      const next = new Set(s.selectedIds);
      next.has(id) ? next.delete(id) : next.add(id);
      return { selectedIds: next };
    }),

  selectAll: () =>
    set((s) => ({ selectedIds: new Set(s.photos.map((p) => p.id)) })),

  clearSelection: () => set({ selectedIds: new Set() }),

  setActivePhoto: (photo) => set({ activePhoto: photo }),

  setFilters: (f) =>
    set((s) => ({ filters: { ...s.filters, ...f } })),

  loadPhotos: async () => {
    set({ loading: true, error: null });
    try {
      const photos = await fetchPhotos(get().filters);
      set({ photos, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  loadStats: async () => {
    try {
      const stats = await fetchStats();
      set({ stats });
    } catch {}
  },
}));
