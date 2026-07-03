import { useEffect, useRef, useState } from "react";

export default function LinhaSelector({
  linhas,
  selectedLinhaIds,
  selectedSentido,
  onToggleLinha,
  onClearLinhas,
  onSelectSentido,
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const filtered = search.trim()
    ? linhas.filter((l) => l.nome.toLowerCase().includes(search.toLowerCase()))
    : linhas;

  const label =
    selectedLinhaIds.length === 0
      ? "Todas as linhas"
      : selectedLinhaIds.length === 1
      ? (linhas.find((l) => l.id === selectedLinhaIds[0])?.nome ?? "1 linha")
      : `${selectedLinhaIds.length} linhas selecionadas`;

  return (
    <div className="controls">
      <div className="control-group multiselect-root" ref={ref}>
        <span className="control-label">Linhas</span>

        <div className="multiselect-trigger-wrap">
          <button
            className={`multiselect-btn${open ? " multiselect-btn--open" : ""}`}
            onClick={() => setOpen((v) => !v)}
          >
            <span className="multiselect-label">{label}</span>
            <span className="multiselect-arrow">{open ? "▲" : "▼"}</span>
          </button>
          {selectedLinhaIds.length > 0 && (
            <button
              className="multiselect-clear"
              onClick={() => { onClearLinhas(); setSearch(""); }}
              title="Limpar seleção"
            >
              ✕
            </button>
          )}
        </div>

        {open && (
          <div className="multiselect-panel">
            <div className="multiselect-search-wrap">
              <input
                className="multiselect-search"
                type="text"
                placeholder="Filtrar linha…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                autoFocus
              />
              {selectedLinhaIds.length > 0 && (
                <span className="multiselect-count">{selectedLinhaIds.length} ✓</span>
              )}
            </div>
            <div className="multiselect-list">
              {filtered.length === 0 && (
                <p className="multiselect-empty">Nenhuma linha encontrada</p>
              )}
              {filtered.map((linha) => {
                const checked = selectedLinhaIds.includes(linha.id);
                return (
                  <label
                    key={linha.id}
                    className={`multiselect-item${checked ? " multiselect-item--checked" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => onToggleLinha(linha.id)}
                    />
                    <span>{linha.nome}</span>
                  </label>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <label className="control-group">
        <span className="control-label">Sentido</span>
        <select
          value={selectedSentido}
          onChange={(e) => onSelectSentido(e.target.value)}
          className="control-select"
        >
          <option value="ambos">Ida e Volta</option>
          <option value="ida">Somente Ida</option>
          <option value="volta">Somente Volta</option>
        </select>
      </label>
    </div>
  );
}
