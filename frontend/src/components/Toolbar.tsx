import { FolderOpen, Sparkles, Cloud, CheckSquare, Square, X, Search } from "lucide-react";
import { useState } from "react";
import { analyzePhotos, scanDirectory, syncPhotos } from "../api/photos";
import { useStore } from "../store/useStore";

export function Toolbar() {
  const { selectedIds, photos, filters, selectAll, clearSelection, setFilters, loadPhotos, loadStats } = useStore();
  const [scanning, setScanning] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [scanDir, setScanDir] = useState("");
  const [showScan, setShowScan] = useState(false);

  const allSelected = selectedIds.size === photos.length && photos.length > 0;

  async function handleScan() {
    if (!scanDir) return;
    setScanning(true);
    try {
      const res = await scanDirectory(scanDir, true);
      alert(`导入完成：新增 ${res.added} 张，跳过 ${res.skipped} 张`);
      await loadPhotos();
      await loadStats();
      setShowScan(false);
    } catch (e: any) {
      alert("扫描失败：" + e.response?.data?.detail || e.message);
    } finally {
      setScanning(false);
    }
  }

  async function handleAnalyze() {
    if (selectedIds.size === 0) return alert("请先选择照片");
    setAnalyzing(true);
    try {
      await analyzePhotos([...selectedIds]);
      await loadPhotos();
      await loadStats();
      clearSelection();
    } catch (e: any) {
      alert("AI 分析失败：" + (e.response?.data?.detail || e.message));
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleSync() {
    if (selectedIds.size === 0) return alert("请先选择照片");
    setSyncing(true);
    try {
      await syncPhotos([...selectedIds]);
      await loadPhotos();
      await loadStats();
      clearSelection();
    } catch (e: any) {
      alert("同步失败：" + (e.response?.data?.detail || e.message));
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Top bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={() => setShowScan((v) => !v)}
          className="btn-primary flex items-center gap-2"
        >
          <FolderOpen size={15} />
          导入文件夹
        </button>

        <button
          onClick={handleAnalyze}
          disabled={analyzing || selectedIds.size === 0}
          className="btn-secondary flex items-center gap-2 disabled:opacity-40"
        >
          <Sparkles size={15} />
          {analyzing ? "分析中…" : `AI 识别主题 ${selectedIds.size > 0 ? `(${selectedIds.size})` : ""}`}
        </button>

        <button
          onClick={handleSync}
          disabled={syncing || selectedIds.size === 0}
          className="btn-secondary flex items-center gap-2 disabled:opacity-40"
        >
          <Cloud size={15} />
          {syncing ? "同步中…" : `上传云端 ${selectedIds.size > 0 ? `(${selectedIds.size})` : ""}`}
        </button>

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={allSelected ? clearSelection : selectAll}
            className="text-gray-400 hover:text-white transition-colors flex items-center gap-1 text-sm"
          >
            {allSelected ? <CheckSquare size={15} /> : <Square size={15} />}
            {allSelected ? "取消全选" : "全选"}
          </button>
        </div>
      </div>

      {/* Scan dialog inline */}
      {showScan && (
        <div className="flex items-center gap-3 bg-white/5 rounded-xl p-3">
          <input
            value={scanDir}
            onChange={(e) => setScanDir(e.target.value)}
            placeholder="粘贴照片文件夹路径，例如 D:\Photos\2024"
            className="flex-1 bg-transparent border border-white/20 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent"
          />
          <button
            onClick={handleScan}
            disabled={scanning || !scanDir}
            className="btn-primary disabled:opacity-40"
          >
            {scanning ? "扫描中…" : "开始扫描"}
          </button>
          <button onClick={() => setShowScan(false)} className="text-gray-400 hover:text-white">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Search & filter */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={filters.search}
            onChange={(e) => setFilters({ search: e.target.value })}
            onKeyDown={(e) => e.key === "Enter" && loadPhotos()}
            placeholder="搜索描述、标签、主题…"
            className="w-full pl-9 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent"
          />
        </div>

        <input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => setFilters({ dateFrom: e.target.value })}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent"
        />
        <span className="text-gray-500 text-sm">至</span>
        <input
          type="date"
          value={filters.dateTo}
          onChange={(e) => setFilters({ dateTo: e.target.value })}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent"
        />

        <button
          onClick={() => loadPhotos()}
          className="btn-primary"
        >
          筛选
        </button>

        <button
          onClick={() => { setFilters({ search: "", dateFrom: "", dateTo: "", theme: "" }); setTimeout(() => loadPhotos(), 50); }}
          className="text-gray-400 hover:text-white text-sm"
        >
          重置
        </button>
      </div>
    </div>
  );
}
