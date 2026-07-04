import { NavLink } from "react-router-dom";

function linkClass({ isActive }) {
  return `navbar-link${isActive ? " navbar-link--active" : ""}`;
}

export default function Navbar() {
  return (
    <header className="navbar">
      <span className="navbar-brand">Linhas DMTT — Maceió</span>
      <nav className="navbar-links">
        <NavLink to="/" end className={linkClass}>Linhas</NavLink>
        <NavLink to="/dashboards" className={linkClass}>Dashboards</NavLink>
        <NavLink to="/sobre" className={linkClass}>Sobre</NavLink>
      </nav>
    </header>
  );
}
