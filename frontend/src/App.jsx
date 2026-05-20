import { useEffect, useState } from "react";
import HorariosPanel from "./components/HorariosPanel";
import ItinerarioPanel from "./components/ItinerarioPanel";
import LinhaSelector from "./components/LinhaSelector";
import MapStyleSelector from "./components/MapStyleSelector";
import MapView from "./components/MapView";
import RuaSearch from "./components/RuaSearch";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const EMPTY_FC = { type: "FeatureCollection", features: [] };

async function fetchJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Erro ${res.status} em ${path}`);
  return res.json();
}

const NOMINATIM = "https://nominatim.openstreetmap.org";

export default function App() {
  const [linhas, setLinhas] = useState([]);
  const [selectedLinhaId, setSelectedLinhaId] = useState("");
  const [selectedSentido, setSelectedSentido] = useState("ambos");
  const [geojson, setGeojson] = useState(EMPTY_FC);
  const [detalheLinha, setDetalheLinha] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mapStyle, setMapStyle] = useState("dark");
  const [geojsonVersion, setGeojsonVersion] = useState(0);
  const [horarios, setHorarios] = useState(null);
  const [ruaGeojson, setRuaGeojson] = useState(null);
  const [externalQuery, setExternalQuery] = useState("");
  const [linhaContexto, setLinhaContexto] = useState(null);

  // Carrega lista de linhas ao montar
  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchJson("/linhas")
      .then((data) => { if (active) setLinhas(data.itens || []); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  // Carrega mapa e detalhe quando linha ou sentido muda
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    const sentidoQuery = selectedSentido ? `?sentido=${selectedSentido}` : "";

    const requests = selectedLinhaId
      ? Promise.all([
          fetchJson(`/geojson/linhas/${selectedLinhaId}${sentidoQuery}`),
          fetchJson(`/linhas/${selectedLinhaId}`),
        ]).then(([mapData, detalhe]) => ({ mapData, detalhe }))
      : fetchJson(`/geojson/linhas${sentidoQuery}`).then((mapData) => ({ mapData, detalhe: null }));

    requests
      .then(({ mapData, detalhe }) => {
        if (!active) return;
        setGeojson(mapData);
        setDetalheLinha(detalhe);
        setGeojsonVersion((v) => v + 1);
      })
      .catch((err) => {
        if (!active) return;
        setError(err.message);
        setGeojson(EMPTY_FC);
        setDetalheLinha(null);
        setGeojsonVersion((v) => v + 1);
      })
      .finally(() => { if (active) setLoading(false); });

    // Horários: busca paralela e independente, falha silenciosa
    if (selectedLinhaId) {
      fetchJson(`/horarios/${selectedLinhaId}`)
        .then((data) => { if (active) setHorarios(data); })
        .catch(() => { if (active) setHorarios(null); });
    } else {
      setHorarios(null);
    }

    return () => { active = false; };
  }, [selectedLinhaId, selectedSentido]);

  async function handleRuaHighlight(nomeDaRua) {
    if (!nomeDaRua) { setRuaGeojson(null); return; }
    try {
      const url = `${NOMINATIM}/search?q=${encodeURIComponent(nomeDaRua + ", Maceió, AL, Brasil")}&format=geojson&polygon_geojson=1&limit=1&countrycodes=br`;
      const res = await fetch(url, { headers: { "Accept-Language": "pt-BR" } });
      const data = await res.json();
      setRuaGeojson(data.features?.length > 0 ? data : null);
    } catch { setRuaGeojson(null); }
  }

  async function handleMapClick(lat, lng) {
    try {
      const url = `${NOMINATIM}/reverse?lat=${lat}&lon=${lng}&format=json&accept-language=pt-BR`;
      const res = await fetch(url);
      const data = await res.json();
      const rua = data.address?.road || data.address?.pedestrian || "";
      if (rua) setExternalQuery(rua);
    } catch {}
  }

  function handleSelectLinha(id, sentido) {
    setSelectedLinhaId(id);
    setRuaGeojson(null);
    setLinhaContexto(null);
    if (sentido !== undefined) setSelectedSentido(sentido);
  }

  function handleContextoAmbos() {
    if (linhaContexto) handleSelectLinha(linhaContexto.id, "ambos");
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Linhas DMTT — Maceió</h1>
        {loading && <span className="loading-badge">Carregando…</span>}
        {error && <span className="error-badge">{error}</span>}
      </header>

      <LinhaSelector
        linhas={linhas}
        selectedLinhaId={selectedLinhaId}
        selectedSentido={selectedSentido}
        onSelectLinha={handleSelectLinha}
        onSelectSentido={setSelectedSentido}
      />

      <div className="app-body">
        <MapView geojson={geojson} isLinhaSelected={!!selectedLinhaId} linhaId={selectedLinhaId} tileStyle={mapStyle} geojsonVersion={geojsonVersion} ruaGeojson={ruaGeojson} onMapClick={handleMapClick} linhaContexto={linhaContexto} onContextoAmbos={handleContextoAmbos} />

        <aside className="sidebar">
          <MapStyleSelector value={mapStyle} onChange={setMapStyle} />
          <HorariosPanel horarios={horarios} selectedLinhaId={selectedLinhaId} />
          <ItinerarioPanel
            detalheLinha={detalheLinha}
            selectedSentido={selectedSentido}
          />
          <RuaSearch onSelectLinha={handleSelectLinha} onRuaHighlight={handleRuaHighlight} externalQuery={externalQuery} onLinhaContexto={setLinhaContexto} />
        </aside>
      </div>
    </div>
  );
}
