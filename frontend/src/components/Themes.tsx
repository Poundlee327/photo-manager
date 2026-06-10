import { useEffect } from "react";
import { useStore } from "../store/useStore";
import { PhotoCard } from "./PhotoCard";
import { PhotoDetail } from "./PhotoDetail";

const THEME_COLORS: Record<string, string> = {
  风光: "bg-blue-600",
  人像: "bg-pink-600",
  街头: "bg-yellow-600",
  建筑: "bg-gray-600",
  生态: "bg-green-600",
  美食: "bg-orange-600",
  运动: "bg-red-600",
  天文: "bg-indigo-600",
};

export function Themes() {
  const { stats, photos, filters, setFilters, loadPhotos, loadStats } = useStore();

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    loadPhotos();
  }, [filters.theme]);

  const themes = stats?.themes ?? {};

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Theme tabs */}
      <div className="flex-shrink-0 p-5 border-b border-white/10">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setFilters({ theme: "" })}
            className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
              !filters.theme ? "bg-accent text-white" : "bg-white/10 text-gray-300 hover:bg-white/20"
            }`}
          >
            全部
          </button>
          {Object.entries(themes).map(([theme, count]) => (
            <button
              key={theme}
              onClick={() => setFilters({ theme })}
              className={`px-3 py-1.5 rounded-full text-sm transition-colors flex items-center gap-1.5 ${
                filters.theme === theme
                  ? "bg-accent text-white"
                  : "bg-white/10 text-gray-300 hover:bg-white/20"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${THEME_COLORS[theme] ?? "bg-gray-400"}`} />
              {theme}
              <span className="text-xs opacity-70">({count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Photos for selected theme */}
      <div className="flex-1 overflow-y-auto p-5">
        {photos.length === 0 ? (
          <p className="text-gray-500 text-center mt-20">
            {filters.theme ? `"${filters.theme}" 主题暂无照片` : "暂无照片，请先进行 AI 分析"}
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
            {photos.map((p) => (
              <PhotoCard key={p.id} photo={p} />
            ))}
          </div>
        )}
      </div>

      <PhotoDetail />
    </div>
  );
}
