import { Cloud, Sparkles } from "lucide-react";
import { thumbnailUrl } from "../api/photos";
import { useStore } from "../store/useStore";
import type { Photo } from "../types";

interface Props {
  photo: Photo;
}

export function PhotoCard({ photo }: Props) {
  const { selectedIds, toggleSelect, setActivePhoto } = useStore();
  const selected = selectedIds.has(photo.id);

  const dateStr = photo.shot_at
    ? new Date(photo.shot_at).toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      })
    : null;

  return (
    <div
      className={`relative group cursor-pointer rounded-xl overflow-hidden bg-card transition-all duration-200 ${
        selected ? "ring-2 ring-accent" : "hover:scale-[1.02]"
      }`}
      onClick={() => setActivePhoto(photo)}
    >
      {/* Thumbnail */}
      <div className="aspect-square bg-white/5 overflow-hidden">
        <img
          src={thumbnailUrl(photo.id)}
          alt={photo.file_name}
          loading="lazy"
          className="w-full h-full object-cover"
        />
      </div>

      {/* Select checkbox */}
      <div
        className={`absolute top-2 left-2 w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
          selected
            ? "bg-accent border-accent"
            : "bg-black/40 border-white/60 opacity-0 group-hover:opacity-100"
        }`}
        onClick={(e) => {
          e.stopPropagation();
          toggleSelect(photo.id);
        }}
      >
        {selected && (
          <svg viewBox="0 0 10 8" className="w-3 h-3 text-white fill-current">
            <path d="M1 4l2.5 2.5L9 1" stroke="currentColor" strokeWidth="1.5" fill="none" />
          </svg>
        )}
      </div>

      {/* Badges */}
      <div className="absolute top-2 right-2 flex flex-col gap-1">
        {photo.ai_analyzed_at && (
          <span className="bg-purple-600/80 p-1 rounded">
            <Sparkles size={10} className="text-white" />
          </span>
        )}
        {photo.cloud_synced && (
          <span className="bg-blue-600/80 p-1 rounded">
            <Cloud size={10} className="text-white" />
          </span>
        )}
      </div>

      {/* Info overlay */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 translate-y-full group-hover:translate-y-0 transition-transform duration-200">
        {photo.ai_theme && (
          <span className="text-xs bg-accent/80 text-white px-2 py-0.5 rounded-full">{photo.ai_theme}</span>
        )}
        <p className="text-white text-xs mt-1 truncate">{photo.file_name}</p>
        {dateStr && <p className="text-gray-300 text-xs">{dateStr}</p>}
        {photo.camera_model && <p className="text-gray-400 text-xs truncate">{photo.camera_model}</p>}
      </div>
    </div>
  );
}
