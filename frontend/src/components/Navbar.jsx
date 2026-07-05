import { NavLink } from "react-router-dom";
import logo from "../assets/logo-policiamento-viario.png";

function linkClass({ isActive }) {
  return `navbar-link${isActive ? " navbar-link--active" : ""}`;
}

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-brand-group">
        <img src={logo} alt="" className="navbar-logo" />
        <div className="navbar-brand-text">
          <span className="navbar-brand">Linhas DMTT</span>
          <span className="navbar-subtitle">Maceió</span>
        </div>
      </div>
      <nav className="navbar-links">
        <NavLink to="/" end className={linkClass}>Linhas</NavLink>
        <NavLink to="/dashboards" className={linkClass}>Dashboards</NavLink>
        <NavLink to="/sobre" className={linkClass}>Sobre</NavLink>
      </nav>
    </header>
  );
}
