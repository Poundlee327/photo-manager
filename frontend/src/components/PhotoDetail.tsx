import { X, MapPin, Camera, Aperture, Clock, Zap, Ruler } from "lucide-react";
import { imageUrl } from "../api/photos";
import { useStore } from "../store/useStore";

export function PhotoDetail() {
  const { activePhoto, setActivePhoto } = useStore();
  if (!activePhoto) return null;

  const p = activePhoto;
  const tags: string[] = p.ai_tags ? JSON.parse(p.ai_tags) : [];
  const subjects: string[] = p.ai_subjects ? JSON.parse(p.ai_subjects) : [];

  const fmt = (v: string | null | undefined, suffix = "") =>
    v ? `${v}${suffix}` : "—";

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
      onClick={() => setActivePhoto(null)}
    >
      <div
        className="bg-panel rounded-2xl overflow-hidden flex max-w-5xl w-full max-h-[90vh] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Image */}
        <div className="flex-1 bg-black flex items-center justify-center min-w-0">
          <img
            src={imageUrl(p.id)}
            alt={p.file_name}
            className="max-w-full max-h-[90vh] object-contain"
          />
        </div>

        {/* Metadata panel */}
        <div className="w-72 flex-shrink-0 overflow-y-auto p-5 space-y-5">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-white font-semibold text-sm truncate">{p.file_name}</h2>
              {p.ai_theme && (
                <span className="mt-1 inline-block text-xs bg-accent/20 text-accent px-2 py-0.5 rounded-full">
                  {p.ai_theme}
                </span>
              )}
            </div>
            <button
              onClick={() => setActivePhoto(null)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* AI description */}
          {p.ai_description && (
            <div className="bg-white/5 rounded-xl p-3">
              <p className="text-gray-300 text-xs leading-relaxed">{p.ai_description}</p>
              {p.ai_provider && (
                <p className="text-gray-600 text-xs mt-1">由 {p.ai_provider} 分析</p>
              )}
            </div>
          )}

          {/* Subjects */}
          {subjects.length > 0 && (
            <div>
              <p className="text-gray-500 text-xs mb-2">主体元素</p>
              <div className="flex flex-wrap gap-1">
                {subjects.map((s) => (
                  <span key={s} className="text-xs bg-white/10 text-gray-300 px-2 py-0.5 rounded-full">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {tags.length > 0 && (
            <div>
              <p className="text-gray-500 text-xs mb-2">标签</p>
              <div className="flex flex-wrap gap-1">
                {tags.map((t) => (
                  <span key={t} className="text-xs bg-card text-gray-400 px-2 py-0.5 rounded-full">
                    #{t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* EXIF */}
          <div>
            <p className="text-gray-500 text-xs mb-2">拍摄参数</p>
            <div className="space-y-2">
              {p.camera_model && (
                <Row icon={<Camera size={12} />} label="机身" value={`${p.camera_make ?? ""} ${p.camera_model}`} />
              )}
              {p.lens_model && <Row icon={<Ruler size={12} />} label="镜头" value={p.lens_model} />}
              {p.shot_at && (
                <Row
                  icon={<Clock size={12} />}
                  label="拍摄时间"
                  value={new Date(p.shot_at).toLocaleString("zh-CN")}
                />
              )}
              {p.focal_length && <Row icon={<Ruler size={12} />} label="焦距" value={fmt(p.focal_length, "mm")} />}
              {p.aperture && <Row icon={<Aperture size={12} />} label="光圈" value={p.aperture} />}
              {p.shutter_speed && <Row icon={<Zap size={12} />} label="快门" value={p.shutter_speed} />}
              {p.iso && <Row icon={<Zap size={12} />} label="ISO" value={String(p.iso)} />}
              {p.width && p.height && (
                <Row icon={<Camera size={12} />} label="分辨率" value={`${p.width} × ${p.height}`} />
              )}
            </div>
          </div>

          {/* GPS */}
          {p.gps_lat !== null && p.gps_lon !== null && (
            <div>
              <p className="text-gray-500 text-xs mb-2">拍摄地点</p>
              <a
                href={`https://maps.google.com/?q=${p.gps_lat},${p.gps_lon}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
              >
                <MapPin size={12} />
                {p.gps_lat.toFixed(5)}, {p.gps_lon.toFixed(5)}
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-gray-500 mt-0.5">{icon}</span>
      <div className="min-w-0">
        <p className="text-gray-500 text-xs">{label}</p>
        <p className="text-gray-200 text-xs truncate">{value}</p>
      </div>
    </div>
  );
}
