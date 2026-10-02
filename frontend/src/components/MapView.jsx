import { Component, useEffect, useMemo, useRef, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, useMap, useMapEvents } from "react-leaflet";

const ESRI_ATTR = "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, FAO, NOAA, USGS, &copy; OpenStreetMap contributors, GIS User Community";

const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services";
const ESRI_IMG_ATTR = "Tiles &copy; Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community";

export const TILE_STYLES = {
  voyager:   { label: "Mapa",     swatch: "#f2efe9", url: `${ESRI}/World_Street_Map/MapServer/tile/{z}/{y}/{x}`,        attribution: ESRI_ATTR, maxNativeZoom: 19 },
  satellite: { label: "Satélite", swatch: "#3d5a3e", url: `${ESRI}/World_Imagery/MapServer/tile/{z}/{y}/{x}`,           attribution: ESRI_IMG_ATTR, maxNativeZoom: 19 },
  hybrid:    { label: "Híbrido",  swatch: "linear-gradient(135deg,#3d5a3e 55%,#e8e8e8 55%)", url: `${ESRI}/World_Imagery/MapServer/tile/{z}/{y}/{x}`, attribution: ESRI_IMG_ATTR, maxNativeZoom: 19, labelsUrls: [`${ESRI}/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}`, `${ESRI}/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}`], satelliteLike: true },
  light:     { label: "Claro",    swatch: "#e8f0f7", url: `${ESRI}/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}`, attribution: ESRI_ATTR, maxNativeZoom: 16, labelsUrls: [`${ESRI}/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}`] },
  dark:      { label: "Escuro",   swatch: "#1a202c", url: `${ESRI}/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`,  attribution: ESRI_ATTR, maxNativeZoom: 16, labelsUrls: [`${ESRI}/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`] },
  standard:  { label: "OpenStreetMap", swatch: "#aacf9f", url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' },
};

const STYLE_IDA = { color: "#16A34A", weight: 5, opacity: 0.95, lineCap: "round", lineJoin: "round" };
const STYLE_VOLTA = { color: "#2E64D4", weight: 5, opacity: 0.95, lineCap: "round", lineJoin: "round" };
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

const STYLE_ZONA = { color: "#B38F00", weight: 2, fillColor: "#F2C200", fillOpacity: 0.14 };

const STYLE_ZONA_HOVER = { color: "#0A0A0A", weight: 2.5, fillColor: "#F2C200", fillOpacity: 0.34 };

function anelContem(lng, lat, anel) {
  let dentro = false;
  for (let i = 0, j = anel.length - 1; i < anel.length; j = i++) {
    const [xi, yi] = anel[i], [xj, yj] = anel[j];
    if ((yi > lat) !== (yj > lat) && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) dentro = !dentro;
  }
  return dentro;
}

function poligonoContem(lng, lat, coords) {
  return anelContem(lng, lat, coords[0]) && !coords.slice(1).some((buraco) => anelContem(lng, lat, buraco));
}

function zonaContem(lng, lat, geom) {
  if (!geom) return false;
  if (geom.type === "Polygon") return poligonoContem(lng, lat, geom.coordinates);
  if (geom.type === "MultiPolygon") return geom.coordinates.some((poly) => poligonoContem(lng, lat, poly));
  return false;
}

// As rotas são desenhadas em canvas por cima de tudo e engolem os eventos do mouse, então zonas e
// terminais não recebem hover próprio. Aqui o hover é resolvido pelo mapa: terminal mais próximo
// (raio em pixels) tem prioridade; senão, a zona sob o cursor.
function HoverInfo({ zonas, showZonas, terminais, showTerminais }) {
  const map = useMap();
  const [info, setInfo] = useState(null);
  const pendente = useRef(null);
  const agendado = useRef(false);

  const features = useMemo(() => (zonas?.features || []).filter((f) => f.properties?.nome), [zonas]);

  useMapEvents({
    mousemove(e) {
      pendente.current = e;
      if (agendado.current) return;
      agendado.current = true;
      requestAnimationFrame(() => {
        agendado.current = false;
        const ev = pendente.current;
        if (!ev) return;
        const { lat, lng } = ev.latlng;
        const { x, y } = ev.containerPoint;
        let achado = null;
        if (showTerminais) {
          let melhor = 14;
          for (const t of terminais) {
            const p = map.latLngToContainerPoint([t.lat, t.lon]);
            const d = Math.hypot(p.x - x, p.y - y);
            if (d < melhor) { melhor = d; achado = { tipo: "Terminal", nome: t.nome }; }
          }
        }
        if (!achado && showZonas) {
          const f = features.find((ft) => zonaContem(lng, lat, ft.geometry));
          if (f) achado = { tipo: "Bairro / zona", nome: f.properties.nome, feature: f };
        }
        setInfo(achado ? { ...achado, x, y } : null);
      });
    },
    mouseout() { pendente.current = null; setInfo(null); },
  });

  return (
    <>
      {info?.feature && <GeoJSON key={info.nome} data={info.feature} style={STYLE_ZONA_HOVER} interactive={false} />}
      {info && (
        <div className="map-hover-tip" style={{ left: info.x, top: info.y }}>
          <span className="map-hover-tip-tipo">{info.tipo}</span>
          <span className="map-hover-tip-nome">{info.nome}</span>
        </div>
      )}
    </>
  );
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

export default function MapView({ geojson, isLinhaSelected, linhaId, tileStyle = "voyager", geojsonVersion = 0, ruaGeojson = null, onMapClick = null, linhaContexto = null, onContextoAmbos = null, terminais = [], showTerminais = false, zonas = null, showZonas = false, mapRef = null }) {
  // key muda somente quando os dados novos chegam (junto com geojsonVersion), nunca antes
  const geoJsonKey = geojsonVersion;
  const tile = TILE_STYLES[tileStyle] ?? TILE_STYLES.voyager;

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
        <TileLayer key={tileStyle} attribution={tile.attribution} url={tile.url} maxNativeZoom={tile.maxNativeZoom} maxZoom={19} crossOrigin="anonymous" />
        {tile.labelsUrls?.map((u) => (
          <TileLayer key={u} url={u} maxNativeZoom={tile.maxNativeZoom} maxZoom={19} crossOrigin="anonymous" />
        ))}
        <MainPaneSetup />
        <HoverInfo zonas={zonas} showZonas={showZonas} terminais={terminais} showTerminais={showTerminais} />
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
          <GeoJSON data={zonas} style={STYLE_ZONA} interactive={false} />
        )}
        {showTerminais && terminais.map((t) => (
          <CircleMarker
            key={t.nome}
            center={[t.lat, t.lon]}
            radius={9}
            pathOptions={{ color: "#0A0A0A", fillColor: "#F2C200", fillOpacity: 1, weight: 2.5 }}
          >
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
