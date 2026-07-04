import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import LinhasPage from "./pages/LinhasPage";
import DashboardsPage from "./pages/DashboardsPage";
import SobrePage from "./pages/SobrePage";

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <Routes>
        <Route path="/" element={<LinhasPage />} />
        <Route path="/dashboards" element={<DashboardsPage />} />
        <Route path="/sobre" element={<SobrePage />} />
      </Routes>
    </div>
  );
}
