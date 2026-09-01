import { useEffect, useRef, useState } from "react";
import HorariosPanel from "../components/HorariosPanel";
import ItinerarioPanel from "../components/ItinerarioPanel";
import LinhaSelector from "../components/LinhaSelector";
import MapStyleSelector from "../components/MapStyleSelector";
import MapView from "../components/MapView";
import RuaSearch from "../components/RuaSearch";
import { listarLinhas, getTerminais, getZonas, detalharLinha, geojsonTodasLinhas, geojsonLinha, getHorarios } from "../staticApi";

const EMPTY_FC = { type: "FeatureCollection", features: [] };

const NOMINATIM = "https://nominatim.openstreetmap.org";

export default function LinhasPage() {
  const [linhas, setLinhas] = useState([]);
  const [selectedLinhaIds, setSelectedLinhaIds] = useState([]);
  const [selectedSentido, setSelectedSentido] = useState("ambos");
  const [geojson, setGeojson] = useState(EMPTY_FC);
  const [detalheLinha, setDetalheLinha] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mapStyle, setMapStyle] = useState("light");
  const [geojsonVersion, setGeojsonVersion] = useState(0);
  const [horarios, setHorarios] = useState(null);
  const [ruaGeojson, setRuaGeojson] = useState(null);
  const [externalQuery, setExternalQuery] = useState("");
  const [linhaContexto, setLinhaContexto] = useState(null);
  const [terminais, setTerminais] = useState([]);
  const [showTerminais, setShowTerminais] = useState(false);
  const [zonas, setZonas] = useState(null);
  const [showZonas, setShowZonas] = useState(false);
  const mapRef = useRef(null);

  // Carrega lista de linhas e terminais ao montar
  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([listarLinhas(), getTerminais(), getZonas()])
      .then(([linhasData, terminaisData, zonasData]) => {
        if (!active) return;
        setLinhas(linhasData.itens || []);
        setTerminais(terminaisData || []);
        setZonas(zonasData || null);
      })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  // Carrega mapa e detalhe quando seleção ou sentido muda
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    let requests;
    if (selectedLinhaIds.length === 0) {
      requests = geojsonTodasLinhas(selectedSentido)
        .then((mapData) => ({ mapData, detalhe: null }));
    } else if (selectedLinhaIds.length === 1) {
      requests = Promise.all([
        geojsonLinha(selectedLinhaIds[0], selectedSentido),
        detalharLinha(selectedLinhaIds[0]),
      ]).then(([mapData, detalhe]) => ({ mapData, detalhe }));
    } else {
      requests = Promise.all(
        selectedLinhaIds.map((id) => geojsonLinha(id, selectedSentido))
      ).then((results) => ({
        mapData: {
          type: "FeatureCollection",
          features: results.flatMap((r) => r.features || []),
        },
        detalhe: null,
      }));
    }

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

    // Horários: apenas quando exatamente 1 linha
    if (selectedLinhaIds.length === 1) {
      getHorarios(selectedLinhaIds[0])
        .then((data) => { if (active) setHorarios(data); })
        .catch(() => { if (active) setHorarios(null); });
    } else {
      setHorarios(null);
    }

    return () => { active = false; };
  }, [selectedLinhaIds, selectedSentido]);

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
    setSelectedLinhaIds(id ? [id] : []);
    setRuaGeojson(null);
    setLinhaContexto(null);
    if (sentido !== undefined) setSelectedSentido(sentido);
  }

  function handleToggleLinha(id) {
    setSelectedLinhaIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setLinhaContexto(null);
  }

  function handleClearLinhas() {
    setSelectedLinhaIds([]);
    setLinhaContexto(null);
  }

  function handleContextoAmbos() {
    if (linhaContexto) {
      setSelectedLinhaIds([linhaContexto.id]);
      setSelectedSentido("ambos");
      setLinhaContexto(null);
    }
  }

  return (
    <>
      {(loading || error) && (
        <div className="page-status-bar">
          {loading && <span className="loading-badge">Carregando…</span>}
          {error && <span className="error-badge">{error}</span>}
        </div>
      )}

      <LinhaSelector
        linhas={linhas}
        selectedLinhaIds={selectedLinhaIds}
        selectedSentido={selectedSentido}
        onToggleLinha={handleToggleLinha}
        onClearLinhas={handleClearLinhas}
        onSelectSentido={setSelectedSentido}
      />

      <div className="app-body">
        <MapView geojson={geojson} isLinhaSelected={selectedLinhaIds.length > 0} linhaId={selectedLinhaIds[0] ?? ""} tileStyle={mapStyle} geojsonVersion={geojsonVersion} ruaGeojson={ruaGeojson} onMapClick={handleMapClick} linhaContexto={selectedLinhaIds.length <= 1 ? linhaContexto : null} onContextoAmbos={handleContextoAmbos} terminais={terminais} showTerminais={showTerminais} zonas={zonas} showZonas={showZonas} mapRef={mapRef} />

        <aside className="sidebar">
          <MapStyleSelector value={mapStyle} onChange={setMapStyle} showTerminais={showTerminais} onToggleTerminais={() => setShowTerminais((v) => !v)} showZonas={showZonas} onToggleZonas={() => setShowZonas((v) => !v)} />
          <HorariosPanel horarios={horarios} selectedLinhaId={selectedLinhaIds[0] ?? ""} />
          <ItinerarioPanel
            detalheLinha={detalheLinha}
            selectedSentido={selectedSentido}
            mapRef={mapRef}
            horarios={horarios}
          />
          <RuaSearch onSelectLinha={handleSelectLinha} onRuaHighlight={handleRuaHighlight} externalQuery={externalQuery} onLinhaContexto={setLinhaContexto} />
        </aside>
      </div>
    </>
  );
}
