import { BrowserRouter, Route, Routes } from "react-router-dom";
import { CloudPage } from "./components/CloudPage";
import { Gallery } from "./components/Gallery";
import { Settings } from "./components/Settings";
import { Sidebar } from "./components/Sidebar";
import { Themes } from "./components/Themes";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-surface text-white overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Gallery />} />
            <Route path="/themes" element={<Themes />} />
            <Route path="/cloud" element={<CloudPage />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
