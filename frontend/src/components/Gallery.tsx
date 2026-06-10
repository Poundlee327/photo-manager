import { useEffect } from "react";
import { useStore } from "../store/useStore";
import { PhotoCard } from "./PhotoCard";
import { PhotoDetail } from "./PhotoDetail";
import { Toolbar } from "./Toolbar";

export function Gallery() {
  const { photos, loading, error, loadPhotos, loadStats } = useStore();

  useEffect(() => {
    loadPhotos();
    loadStats();
  }, []);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="flex-shrink-0 p-5 border-b border-white/10">
        <Toolbar />
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto p-5">
        {loading && (
          <div className="flex items-center justify-center h-40 text-gray-400">
            加载中…
          </div>
        )}

        {!loading && error && (
          <div className="flex items-center justify-center h-40 text-red-400">
            {error}
          </div>
        )}

        {!loading && !error && photos.length === 0 && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <p className="text-lg mb-2">暂无照片</p>
            <p className="text-sm">点击「导入文件夹」扫描本地照片</p>
          </div>
        )}

        {!loading && photos.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
            {photos.map((photo) => (
              <PhotoCard key={photo.id} photo={photo} />
            ))}
          </div>
        )}
      </div>

      {/* Detail modal */}
      <PhotoDetail />
    </div>
  );
}
