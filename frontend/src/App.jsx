import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import LinhasPage from "./pages/LinhasPage";
import DashboardsPage from "./pages/DashboardsPage";
import BairrosPage from "./pages/BairrosPage";

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <Routes>
        <Route path="/" element={<LinhasPage />} />
        <Route path="/bairros" element={<BairrosPage />} />
        <Route path="/dashboards" element={<DashboardsPage />} />
      </Routes>
    </div>
  );
}
