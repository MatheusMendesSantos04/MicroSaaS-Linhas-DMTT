import { useEffect, useRef, useState } from "react";

const SENTIDO_LABEL = { ida: "→ IDA", volta: "← VOLTA" };
const DIAS_OPCOES = [
  { value: "dia_util", label: "Dia Útil" },
  { value: "sabado",   label: "Sábado"   },
  { value: "domingo",  label: "Domingo"  },
];
const DEBOUNCE_MS = 250;
const MIN_CHARS = 2;
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function toTitleCase(str) {
  return str.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function RuaSearch({ onSelectLinha, onRuaHighlight, externalQuery, onLinhaContexto }) {
  const [inputValue, setInputValue]     = useState("");
  const [sugestoes, setSugestoes]       = useState([]);
  const [showSugestoes, setShowSugestoes] = useState(false);
  const [ruaSelecionada, setRuaSelecionada] = useState(null);

  const [horario, setHorario]           = useState("");
  const [dia, setDia]                   = useState("dia_util");
  const [resultados, setResultados]     = useState([]);
  const [loadingSug, setLoadingSug]     = useState(false);
  const [loadingRes, setLoadingRes]     = useState(false);
  const [error, setError]               = useState("");
  const [modoHorario, setModoHorario]   = useState(false);

  const timerRef      = useRef(null);
  const sugController = useRef(null);
  const resController = useRef(null);
  const wrapperRef    = useRef(null);

  // Reage a clique no mapa (externalQuery vindo do App)
  useEffect(() => {
    if (!externalQuery) return;
    setInputValue(externalQuery);
    setRuaSelecionada(externalQuery);
    setShowSugestoes(false);
    setSugestoes([]);
    if (onLinhaContexto) onLinhaContexto(null);
    if (onRuaHighlight) onRuaHighlight(externalQuery);
  }, [externalQuery]);

  // Fecha sugestões ao clicar fora
  useEffect(() => {
    function handleClick(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowSugestoes(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Busca sugestões de nomes de rua conforme o usuário digita
  useEffect(() => {
    clearTimeout(timerRef.current);
    if (ruaSelecionada) return;

    const q = inputValue.trim();
    if (q.length < MIN_CHARS) { setSugestoes([]); setShowSugestoes(false); return; }

    timerRef.current = setTimeout(async () => {
      if (sugController.current) sugController.current.abort();
      sugController.current = new AbortController();
      setLoadingSug(true);
      try {
        const res = await fetch(`${API_BASE}/ruas/suggest?q=${encodeURIComponent(q)}&limit=12`, {
          signal: sugController.current.signal,
        });
        if (!res.ok) throw new Error(`Erro ${res.status}`);
        const data = await res.json();
        setSugestoes(data);
        setShowSugestoes(data.length > 0);
      } catch (err) {
        if (err.name !== "AbortError") setSugestoes([]);
      } finally {
        setLoadingSug(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timerRef.current);
  }, [inputValue, ruaSelecionada]);

  // Busca linhas quando uma rua é selecionada (ou quando horário/dia muda)
  useEffect(() => {
    if (!ruaSelecionada) { setResultados([]); return; }

    if (resController.current) resController.current.abort();
    resController.current = new AbortController();
    setLoadingRes(true);
    setError("");

    const url = new URL(`${API_BASE}/ruas/search`);
    url.searchParams.set("q", ruaSelecionada);
    url.searchParams.set("limit", "200");
    if (horario) {
      url.searchParams.set("horario", horario);
      url.searchParams.set("dia", dia);
      url.searchParams.set("janela", "20");
    }

    fetch(url.toString(), { signal: resController.current.signal })
      .then((r) => { if (!r.ok) throw new Error(`Erro ${r.status}`); return r.json(); })
      .then((data) => { setModoHorario(!!horario); setResultados(data.resultados || []); })
      .catch((err) => { if (err.name !== "AbortError") setError(err.message); })
      .finally(() => setLoadingRes(false));
  }, [ruaSelecionada, horario, dia]);

  function selecionarRua(rua) {
    setRuaSelecionada(rua);
    setInputValue(toTitleCase(rua));
    setShowSugestoes(false);
    setSugestoes([]);
    if (onRuaHighlight) onRuaHighlight(rua);
  }

  function handleInputChange(e) {
    setInputValue(e.target.value);
    setRuaSelecionada(null);
    setResultados([]);
    setError("");
    if (onLinhaContexto) onLinhaContexto(null);
    if (!e.target.value && onRuaHighlight) onRuaHighlight(null);
  }

  function handleSentidoClick(linhaId, linhaNome, sentido) {
    onSelectLinha(linhaId, sentido);
    if (onLinhaContexto) onLinhaContexto({ id: linhaId, nome: linhaNome, sentido, ruaDisplay: toTitleCase(ruaSelecionada || "") });
  }

  function handleLinhaClick(linhaId) {
    if (onLinhaContexto) onLinhaContexto(null);
    onSelectLinha(linhaId, "ambos");
  }

  function handleInputKeyDown(e) {
    if (e.key === "Escape") { setShowSugestoes(false); }
    if (e.key === "Enter" && sugestoes.length === 1) { selecionarRua(sugestoes[0]); }
  }

  // Agrupa resultados por linha
  const porLinha = resultados.reduce((acc, item) => {
    if (!acc[item.linha_id]) {
      acc[item.linha_id] = { nome: item.linha_nome, id: item.linha_id, sentidos: [] };
    }
    acc[item.linha_id].sentidos.push({
      sentido: item.sentido,
      codigo: item.codigo,
      horarios_proximos: item.horarios_proximos || [],
    });
    return acc;
  }, {});

  const totalLinhas = Object.keys(porLinha).length;

  return (
    <div className="rua-search-panel">
      <h2 className="sidebar-title">Buscar por rua</h2>

      <div className="search-autocomplete-wrapper" ref={wrapperRef}>
        <div className="search-form">
          <input
            className="search-input"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleInputKeyDown}
            onFocus={() => sugestoes.length > 0 && setShowSugestoes(true)}
            placeholder="Ex.: Fernandes Lima"
            autoComplete="off"
          />
          {loadingSug && <span className="search-spinner">…</span>}
        </div>

        {showSugestoes && (
          <ul className="suggest-list">
            {sugestoes.map((rua) => (
              <li
                key={rua}
                className="suggest-item"
                onMouseDown={() => selecionarRua(rua)}
              >
                {toTitleCase(rua)}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="horario-filter">
        <div className="horario-filter-row">
          <label className="control-label">Horário</label>
          <input
            type="time"
            className="search-input horario-input"
            value={horario}
            onChange={(e) => setHorario(e.target.value)}
          />
          {horario && (
            <select
              className="control-select dia-select"
              value={dia}
              onChange={(e) => setDia(e.target.value)}
            >
              {DIAS_OPCOES.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          )}
        </div>
        {horario && <p className="horario-filter-hint">Janela de ±20 min em torno de {horario}</p>}
      </div>

      {error && <p className="error-msg">{error}</p>}

      {ruaSelecionada && !loadingRes && (
        <p className="result-count">
          {totalLinhas > 0
            ? `${totalLinhas} linha(s) em "${toTitleCase(ruaSelecionada)}"`
            : modoHorario
              ? "Nenhuma linha passa nesse horário."
              : "Nenhuma linha encontrada."}
        </p>
      )}

      <ul className="result-list">
        {Object.values(porLinha).map((linha) => (
          <li key={linha.id} className="result-item">
            <button
              className="result-linha-btn"
              onClick={() => handleLinhaClick(linha.id)}
              title="Clique para ver ambos os sentidos no mapa"
            >
              {linha.nome}
            </button>
            <div className="result-sentidos">
              {linha.sentidos.map((s, i) => (
                <button
                  key={i}
                  className={`sentido-badge sentido-${s.sentido} sentido-btn`}
                  onClick={() => handleSentidoClick(linha.id, linha.nome, s.sentido)}
                  title="Clique para ver só este sentido no mapa"
                >
                  {SENTIDO_LABEL[s.sentido] || s.sentido}
                  {s.codigo && <span className="codigo-badge">{s.codigo}</span>}
                </button>
              ))}
            </div>
            {modoHorario && linha.sentidos.some((s) => s.horarios_proximos.length > 0) && (
              <div className="horarios-proximos">
                {linha.sentidos.flatMap((s) =>
                  s.horarios_proximos.map((h) => (
                    <span key={`${s.sentido}-${h}`} className="horario-chip horario-chip-destaque">
                      {h}
                    </span>
                  ))
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
