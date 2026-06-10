import { Cloud, CheckCircle, XCircle, Upload } from "lucide-react";
import { useEffect } from "react";
import { syncPhotos } from "../api/photos";
import { useStore } from "../store/useStore";
import { PhotoCard } from "./PhotoCard";
import { PhotoDetail } from "./PhotoDetail";
import { useState } from "react";

export function CloudPage() {
  const { photos, loadPhotos, loadStats, selectedIds, clearSelection } = useStore();
  const [syncing, setSyncing] = useState(false);

  const synced = photos.filter((p) => p.cloud_synced);
  const unsynced = photos.filter((p) => !p.cloud_synced);

  useEffect(() => {
    loadPhotos();
    loadStats();
  }, []);

  async function handleSyncAll() {
    const ids = unsynced.map((p) => p.id);
    if (ids.length === 0) return;
    setSyncing(true);
    try {
      await syncPhotos(ids);
      await loadPhotos();
      await loadStats();
    } catch (e: any) {
      alert("同步失败：" + (e.response?.data?.detail || e.message));
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-shrink-0 p-5 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-white font-semibold text-lg">云端同步</h2>
            <p className="text-gray-400 text-sm mt-0.5">
              已同步 {synced.length} 张 · 待同步 {unsynced.length} 张
            </p>
          </div>
          <button
            onClick={handleSyncAll}
            disabled={syncing || unsynced.length === 0}
            className="btn-primary flex items-center gap-2 disabled:opacity-40"
          >
            <Upload size={15} />
            {syncing ? "同步中…" : `同步全部 (${unsynced.length})`}
          </button>
        </div>

        {/* Progress bar */}
        {photos.length > 0 && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>同步进度</span>
              <span>{Math.round((synced.length / photos.length) * 100)}%</span>
            </div>
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all"
                style={{ width: `${(synced.length / photos.length) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {unsynced.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <XCircle size={14} className="text-yellow-400" />
              <h3 className="text-sm text-gray-300">待同步</h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {unsynced.map((p) => <PhotoCard key={p.id} photo={p} />)}
            </div>
          </div>
        )}

        {synced.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle size={14} className="text-green-400" />
              <h3 className="text-sm text-gray-300">已同步</h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {synced.map((p) => <PhotoCard key={p.id} photo={p} />)}
            </div>
          </div>
        )}
      </div>

      <PhotoDetail />
    </div>
  );
}
