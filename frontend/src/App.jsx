import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const EMPTY_FEATURE_COLLECTION = {
  type: "FeatureCollection",
  features: [],
};

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Erro ${response.status} em ${path}`);
  }
  return response.json();
}

export default function App() {
  const [linhas, setLinhas] = useState([]);
  const [selectedLinhaId, setSelectedLinhaId] = useState("");
  const [selectedSentido, setSelectedSentido] = useState("ambos");
  const [geojson, setGeojson] = useState(EMPTY_FEATURE_COLLECTION);
  const [detalheLinha, setDetalheLinha] = useState(null);
  const [ruaBusca, setRuaBusca] = useState("");
  const [ruaResultados, setRuaResultados] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const mapCenter = useMemo(() => [-9.6658, -35.7353], []);

  useEffect(() => {
    let mounted = true;
    async function loadLinhas() {
      setLoading(true);
      setError("");
      try {
        const payload = await fetchJson("/linhas");
        if (mounted) {
          setLinhas(payload.itens || []);
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || "Falha ao carregar linhas");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    loadLinhas();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    async function loadMapa() {
      setLoading(true);
      setError("");
      try {
        const sentidoQuery = selectedSentido ? `?sentido=${selectedSentido}` : "";
        if (!selectedLinhaId) {
          const data = await fetchJson(`/geojson/linhas${sentidoQuery}`);
          if (mounted) {
            setGeojson(data);
            setDetalheLinha(null);
          }
        } else {
          const [mapData, detalhe] = await Promise.all([
            fetchJson(`/geojson/linhas/${selectedLinhaId}${sentidoQuery}`),
            fetchJson(`/linhas/${selectedLinhaId}`),
          ]);
          if (mounted) {
            setGeojson(mapData);
            setDetalheLinha(detalhe);
          }
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || "Falha ao carregar mapa");
          setGeojson(EMPTY_FEATURE_COLLECTION);
          setDetalheLinha(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    loadMapa();
    return () => {
      mounted = false;
    };
  }, [selectedLinhaId, selectedSentido]);

  async function onSearchRua(event) {
    event.preventDefault();
    const query = ruaBusca.trim();
    if (!query) {
      setRuaResultados([]);
      return;
    }

    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson(`/ruas/search?q=${encodeURIComponent(query)}`);
      setRuaResultados(payload.resultados || []);
    } catch (err) {
      setError(err.message || "Falha na busca de rua");
    } finally {
      setLoading(false);
    }
  }

  function onSelectLinha(value) {
    setSelectedLinhaId(value);
    setRuaResultados([]);
  }

  function renderItinerario(sentido) {
    if (!detalheLinha) {
      return [];
    }
    if (sentido === "ida") {
      return detalheLinha.ida?.ruas || [];
    }
    if (sentido === "volta") {
      return detalheLinha.volta?.ruas || [];
    }
    return [...(detalheLinha.ida?.ruas || []), ...(detalheLinha.volta?.ruas || [])];
  }

  const ruasExibidas = renderItinerario(selectedSentido);

  return (
    <div className="page">
      <header className="header">
        <h1>MicroSaaS Linhas DMTT</h1>
        <p>Visualização de linhas, sentidos IDA/VOLTA e busca por rua</p>
      </header>

      <section className="controls">
        <label>
          Linha
          <select value={selectedLinhaId} onChange={(event) => onSelectLinha(event.target.value)}>
            <option value="">Todas as linhas</option>
            {linhas.map((linha) => (
              <option key={linha.id} value={linha.id}>
                {linha.nome}
              </option>
            ))}
          </select>
        </label>

        <label>
          Sentido
          <select value={selectedSentido} onChange={(event) => setSelectedSentido(event.target.value)}>
            <option value="ambos">Ida e volta</option>
            <option value="ida">Somente ida</option>
            <option value="volta">Somente volta</option>
          </select>
        </label>

        <form onSubmit={onSearchRua} className="rua-search">
          <label>
            Buscar rua
            <input
              value={ruaBusca}
              onChange={(event) => setRuaBusca(event.target.value)}
              placeholder="Ex.: Fernandes Lima"
            />
          </label>
          <button type="submit">Pesquisar</button>
        </form>
      </section>

      {error ? <div className="error">{error}</div> : null}
      {loading ? <div className="status">Carregando...</div> : null}

      <section className="content">
        <div className="map-box">
          <MapContainer center={mapCenter} zoom={12} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <GeoJSON data={geojson} />
          </MapContainer>
        </div>

        <div className="sidebar">
          <h2>Itinerário</h2>
          {!selectedLinhaId ? (
            <p>Selecione uma linha para visualizar o itinerário por ruas.</p>
          ) : (
            <>
              <p className="line-name">{detalheLinha?.nome || ""}</p>
              <ul>
                {ruasExibidas.map((rua, index) => (
                  <li key={`${rua}-${index}`}>{rua}</li>
                ))}
              </ul>
            </>
          )}

          <h2>Resultado da busca por rua</h2>
          {ruaResultados.length === 0 ? (
            <p>Nenhum resultado para exibir.</p>
          ) : (
            <ul>
              {ruaResultados.map((item, index) => (
                <li key={`${item.linha_id}-${item.sentido}-${index}`}>
                  {item.linha_nome} ({item.sentido})
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
