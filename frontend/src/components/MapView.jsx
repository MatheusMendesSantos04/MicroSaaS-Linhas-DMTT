import { Component, useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";

export const TILE_STYLES = {
  dark:      { label: "Escuro",   swatch: "#1a202c", url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",                                                              attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>' },
  light:     { label: "Claro",    swatch: "#e8f0f7", url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",                                                             attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>' },
  standard:  { label: "Padrão",   swatch: "#aacf9f", url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",                                                                         attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' },
  voyager:   { label: "Voyager",  swatch: "#e0d8c8", url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",                                                   attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>' },
  satellite: { label: "Satélite", swatch: "#3d5a3e", url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",                              attribution: "Tiles &copy; Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community" },
};

const STYLE_IDA = { color: "#3b82f6", weight: 3, opacity: 0.85 };
const STYLE_VOLTA = { color: "#f97316", weight: 3, opacity: 0.85 };
const STYLE_DEFAULT = { color: "#6b7280", weight: 2, opacity: 0.6 };

function featureStyle(feature) {
  const sentido = feature?.properties?.sentido;
  if (sentido === "ida") return STYLE_IDA;
  if (sentido === "volta") return STYLE_VOLTA;
  return STYLE_DEFAULT;
}

function onEachFeature(feature, layer) {
  const { linha_nome, sentido } = feature?.properties || {};
  if (linha_nome) {
    const dir = sentido === "ida" ? "→ IDA" : sentido === "volta" ? "← VOLTA" : "";
    layer.bindPopup(`<strong>${linha_nome}</strong><br/>${dir}`);
  }
}

class MapErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(e) { return { error: e }; }
  render() {
    if (this.state.error) return <div style={{ padding: 16, color: "red" }}>Erro no mapa: {this.state.error.message}</div>;
    return this.props.children;
  }
}

function AutoZoom({ geojson, isLinhaSelected }) {
  const map = useMap();
  useEffect(() => {
    if (!isLinhaSelected) return;
    const features = geojson?.features || [];
    if (features.length === 0) return;
    try {
      const allCoords = features.flatMap((f) => f.geometry?.coordinates || []);
      if (allCoords.length === 0) return;
      // usar reduce em vez de spread para não explodir a call stack com arrays grandes
      let minLat = Infinity, maxLat = -Infinity, minLon = Infinity, maxLon = -Infinity;
      for (const [lon, lat] of allCoords) {
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
        if (lon < minLon) minLon = lon;
        if (lon > maxLon) maxLon = lon;
      }
      if (!isFinite(minLat)) return;
      map.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [30, 30] });
    } catch (_) {}
  }, [geojson, isLinhaSelected, map]);
  return null;
}

export default function MapView({ geojson, isLinhaSelected, linhaId, tileStyle = "dark", geojsonVersion = 0 }) {
  // key muda somente quando os dados novos chegam (junto com geojsonVersion), nunca antes
  const geoJsonKey = geojsonVersion;
  const tile = TILE_STYLES[tileStyle] ?? TILE_STYLES.dark;

  return (
    <div className="map-wrapper">
    <MapErrorBoundary>
      <MapContainer
        center={[-9.6658, -35.7353]}
        zoom={12}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer attribution={tile.attribution} url={tile.url} />
        <GeoJSON
          key={geoJsonKey}
          data={geojson}
          style={featureStyle}
          onEachFeature={onEachFeature}
        />
        <AutoZoom geojson={geojson} isLinhaSelected={isLinhaSelected} />
      </MapContainer>
    </MapErrorBoundary>

      <div className="map-legend">
        <span className="legend-item legend-ida">→ IDA</span>
        <span className="legend-item legend-volta">← VOLTA</span>
      </div>
    </div>
  );
}
