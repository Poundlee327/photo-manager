import { Camera, Cloud, Home, Settings, Tag } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useStore } from "../store/useStore";

export function Sidebar() {
  const { stats } = useStore();

  const navItem = (to: string, icon: React.ReactNode, label: string) => (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
          isActive
            ? "bg-accent text-white"
            : "text-gray-400 hover:text-white hover:bg-white/10"
        }`
      }
    >
      {icon}
      {label}
    </NavLink>
  );

  return (
    <aside className="w-56 bg-panel flex flex-col py-6 px-3 gap-1 border-r border-white/10 flex-shrink-0">
      <div className="flex items-center gap-2 px-4 mb-6">
        <Camera className="text-accent" size={22} />
        <span className="font-bold text-white text-lg">PhotoLib</span>
      </div>

      {navItem("/", <Home size={16} />, "照片库")}
      {navItem("/themes", <Tag size={16} />, "主题分类")}
      {navItem("/cloud", <Cloud size={16} />, "云同步")}
      {navItem("/settings", <Settings size={16} />, "设置")}

      {stats && (
        <div className="mt-auto px-4 pt-6 border-t border-white/10">
          <div className="text-xs text-gray-500 space-y-1">
            <div className="flex justify-between">
              <span>照片总数</span>
              <span className="text-white">{stats.total}</span>
            </div>
            <div className="flex justify-between">
              <span>已分析</span>
              <span className="text-green-400">{stats.analyzed}</span>
            </div>
            <div className="flex justify-between">
              <span>已同步</span>
              <span className="text-blue-400">{stats.synced}</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
