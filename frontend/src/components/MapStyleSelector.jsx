import { TILE_STYLES } from "./MapView";

export default function MapStyleSelector({ value, onChange, showTerminais, onToggleTerminais }) {
  return (
    <div className="map-style-panel">
      <p className="sidebar-title">Estilo do Mapa</p>
      <div className="style-options">
        {Object.entries(TILE_STYLES).map(([key, style]) => (
          <button
            key={key}
            className={`style-option${value === key ? " style-option--active" : ""}`}
            onClick={() => onChange(key)}
          >
            <span className="style-swatch" style={{ background: style.swatch }} />
            <span className="style-label">{style.label}</span>
            {value === key && <span className="style-check">✓</span>}
          </button>
        ))}
      </div>

      <div className="terminais-toggle">
        <button
          className={`terminais-toggle-btn${showTerminais ? " terminais-toggle-btn--active" : ""}`}
          onClick={onToggleTerminais}
        >
          <span className="terminais-swatch" />
          <span>Terminais</span>
          <span className="terminais-toggle-check">{showTerminais ? "✓" : ""}</span>
        </button>
      </div>
    </div>
  );
}
