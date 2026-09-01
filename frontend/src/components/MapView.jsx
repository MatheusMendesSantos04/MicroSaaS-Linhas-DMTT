import { Component, useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, Tooltip, useMap, useMapEvents } from "react-leaflet";

const ESRI_ATTR = "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, FAO, NOAA, USGS, &copy; OpenStreetMap contributors, GIS User Community";

export const TILE_STYLES = {
  dark:      { label: "Escuro",   swatch: "#1a202c", url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",                attribution: ESRI_ATTR, maxNativeZoom: 16, labelsUrl: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}" },
  light:     { label: "Claro",    swatch: "#e8f0f7", url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",               attribution: ESRI_ATTR, maxNativeZoom: 16, labelsUrl: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}" },
  standard:  { label: "Padrão",   swatch: "#aacf9f", url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",                                                                         attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' },
  voyager:   { label: "Ruas",     swatch: "#e0d8c8", url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",                           attribution: ESRI_ATTR, maxNativeZoom: 19 },
  satellite: { label: "Satélite", swatch: "#3d5a3e", url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",                              attribution: "Tiles &copy; Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community" },
};

const STYLE_IDA = { color: "#16A34A", weight: 4, opacity: 0.9 };
const STYLE_VOLTA = { color: "#2E64D4", weight: 4, opacity: 0.9 };
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

const STYLE_ZONA = { color: "#D98407", weight: 2, fillColor: "#D98407", fillOpacity: 0.12 };

function onEachZona(feature, layer) {
  const nome = feature?.properties?.nome;
  if (nome) layer.bindTooltip(nome, { sticky: true, className: "zona-tooltip" });
}

class MapErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(e) { return { error: e }; }
  render() {
    if (this.state.error) return <div style={{ padding: 16, color: "red" }}>Erro no mapa: {this.state.error.message}</div>;
    return this.props.children;
  }
}

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) { onMapClick(e.latlng.lat, e.latlng.lng); },
  });
  return null;
}

function StreetZoom({ ruaGeojson }) {
  const map = useMap();
  useEffect(() => {
    if (!ruaGeojson?.features?.length) return;
    try {
      const coords = [];
      for (const f of ruaGeojson.features) {
        const geom = f.geometry;
        if (!geom) continue;
        const pts =
          geom.type === "LineString" ? geom.coordinates :
          geom.type === "MultiLineString" ? geom.coordinates.flat() :
          geom.type === "Point" ? [geom.coordinates] : [];
        coords.push(...pts);
      }
      if (!coords.length) return;
      let minLat = Infinity, maxLat = -Infinity, minLon = Infinity, maxLon = -Infinity;
      for (const [lon, lat] of coords) {
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
        if (lon < minLon) minLon = lon;
        if (lon > maxLon) maxLon = lon;
      }
      if (!isFinite(minLat)) return;
      map.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [60, 60] });
    } catch (_) {}
  }, [ruaGeojson, map]);
  return null;
}

export const PANE_LINHA_PRINCIPAL = "linha-principal";

function MainPaneSetup() {
  const map = useMap();
  useEffect(() => {
    if (!map.getPane(PANE_LINHA_PRINCIPAL)) {
      map.createPane(PANE_LINHA_PRINCIPAL);
    }
  }, [map]);
  return null;
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

export default function MapView({ geojson, isLinhaSelected, linhaId, tileStyle = "dark", geojsonVersion = 0, ruaGeojson = null, onMapClick = null, linhaContexto = null, onContextoAmbos = null, terminais = [], showTerminais = false, zonas = null, showZonas = false, mapRef = null }) {
  // key muda somente quando os dados novos chegam (junto com geojsonVersion), nunca antes
  const geoJsonKey = geojsonVersion;
  const tile = TILE_STYLES[tileStyle] ?? TILE_STYLES.dark;

  return (
    <div className="map-wrapper">
    <MapErrorBoundary>
      <MapContainer
        ref={mapRef}
        center={[-9.6658, -35.7353]}
        zoom={12}
        scrollWheelZoom
        preferCanvas
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer attribution={tile.attribution} url={tile.url} maxNativeZoom={tile.maxNativeZoom} maxZoom={19} crossOrigin="anonymous" />
        {tile.labelsUrl && (
          <TileLayer url={tile.labelsUrl} maxNativeZoom={tile.maxNativeZoom} maxZoom={19} crossOrigin="anonymous" />
        )}
        <MainPaneSetup />
        <GeoJSON
          key={geoJsonKey}
          data={geojson}
          style={featureStyle}
          onEachFeature={onEachFeature}
          pane={PANE_LINHA_PRINCIPAL}
        />
        <AutoZoom geojson={geojson} isLinhaSelected={isLinhaSelected} />
        {onMapClick && <MapClickHandler onMapClick={onMapClick} />}
        {showZonas && zonas && (
          <GeoJSON data={zonas} style={STYLE_ZONA} onEachFeature={onEachZona} />
        )}
        {showTerminais && terminais.map((t) => (
          <CircleMarker
            key={t.nome}
            center={[t.lat, t.lon]}
            radius={9}
            pathOptions={{ color: "#D98407", fillColor: "#D98407", fillOpacity: 0.9, weight: 2 }}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
              <span style={{ fontSize: 12, fontWeight: 600 }}>{t.nome}</span>
            </Tooltip>
            <Popup>
              <strong>{t.nome}</strong>
            </Popup>
          </CircleMarker>
        ))}
        {ruaGeojson && (
          <>
            {/* halo espesso semi-transparente para aparecer por cima das linhas */}
            <GeoJSON
              key={`halo-${ruaGeojson.features?.[0]?.properties?.place_id}`}
              data={ruaGeojson}
              style={{ color: "#E0A400", weight: 18, opacity: 0.22 }}
            />
            {/* traçado sólido principal */}
            <GeoJSON
              key={`line-${ruaGeojson.features?.[0]?.properties?.place_id}`}
              data={ruaGeojson}
              style={{ color: "#E0A400", weight: 5, opacity: 1 }}
            />
            <StreetZoom ruaGeojson={ruaGeojson} />
          </>
        )}
      </MapContainer>
    </MapErrorBoundary>

      <div className="map-legend">
        <span className="legend-item legend-ida">→ IDA</span>
        <span className="legend-item legend-volta">← VOLTA</span>
        {ruaGeojson && <span className="legend-item legend-rua">◆ Rua</span>}
      </div>

      {linhaContexto && (
        <div
          className="mapa-contexto"
          style={{ borderLeftColor: linhaContexto.sentido === "ida" ? "#16A34A" : "#2E64D4" }}
        >
          <p
            className="contexto-titulo"
            style={{ color: linhaContexto.sentido === "ida" ? "#16A34A" : "#2E64D4" }}
          >
            {linhaContexto.sentido === "ida" ? "→ IDA" : "← VOLTA"} — apenas um sentido exibido
          </p>
          <p className="contexto-desc">
            <strong>{linhaContexto.nome}</strong> atende{" "}
            <em>{linhaContexto.ruaDisplay}</em> somente nesse sentido.
          </p>
          {onContextoAmbos && (
            <button className="contexto-btn-ambos" onClick={onContextoAmbos}>
              Ver os dois sentidos
            </button>
          )}
        </div>
      )}
    </div>
  );
}
