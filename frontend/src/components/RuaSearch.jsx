import { useState } from "react";

const SENTIDO_LABEL = { ida: "→ IDA", volta: "← VOLTA" };

export default function RuaSearch({ onSelectLinha }) {
  const [query, setQuery] = useState("");
  const [resultados, setResultados] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

  async function handleSearch(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) { setResultados([]); return; }

    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/ruas/search?q=${encodeURIComponent(q)}&limit=200`);
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const data = await res.json();
      setResultados(data.resultados || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Agrupa resultados por linha
  const porLinha = resultados.reduce((acc, item) => {
    if (!acc[item.linha_id]) {
      acc[item.linha_id] = { nome: item.linha_nome, id: item.linha_id, sentidos: [] };
    }
    acc[item.linha_id].sentidos.push({ sentido: item.sentido, codigo: item.codigo });
    return acc;
  }, {});

  return (
    <div className="rua-search-panel">
      <h2 className="sidebar-title">Buscar por rua</h2>
      <form onSubmit={handleSearch} className="search-form">
        <input
          className="search-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ex.: Fernandes Lima"
        />
        <button className="search-btn" type="submit" disabled={loading}>
          {loading ? "..." : "Buscar"}
        </button>
      </form>

      {error && <p className="error-msg">{error}</p>}

      {resultados.length > 0 && (
        <p className="result-count">{Object.keys(porLinha).length} linha(s) encontrada(s)</p>
      )}

      <ul className="result-list">
        {Object.values(porLinha).map((linha) => (
          <li key={linha.id} className="result-item">
            <button
              className="result-linha-btn"
              onClick={() => onSelectLinha(linha.id)}
              title="Clique para ver no mapa"
            >
              {linha.nome}
            </button>
            <div className="result-sentidos">
              {linha.sentidos.map((s, i) => (
                <span key={i} className={`sentido-badge sentido-${s.sentido}`}>
                  {SENTIDO_LABEL[s.sentido] || s.sentido}
                  {s.codigo && <span className="codigo-badge">{s.codigo}</span>}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
