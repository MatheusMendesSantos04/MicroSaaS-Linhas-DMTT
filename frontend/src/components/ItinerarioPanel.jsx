import { useState } from "react";
import { exportarLinhaPDF } from "../pdfExport";

const MATCH_LABEL = {
  exato: { label: "✓", title: "Match exato", cls: "match-exato" },
  exato_global: { label: "✓", title: "Match exato (global)", cls: "match-exato" },
  exato_sem_complemento: { label: "~", title: "Match sem complemento", cls: "match-fuzzy" },
  contem: { label: "~", title: "Match por contenção", cls: "match-fuzzy" },
  fuzzy: { label: "~", title: "Match aproximado", cls: "match-fuzzy" },
  fuzzy_global: { label: "~", title: "Match aproximado (global)", cls: "match-fuzzy" },
  nao_encontrado: { label: "?", title: "Código não encontrado", cls: "match-none" },
};

function RuaLinha({ rua }) {
  const m = MATCH_LABEL[rua.match] || MATCH_LABEL.nao_encontrado;
  return (
    <li className="itinerario-rua">
      <span className={`match-icon ${m.cls}`} title={m.title}>{m.label}</span>
      <span className="via-nome">{rua.via}</span>
      {rua.codigo && <span className="via-codigo">{rua.codigo}</span>}
    </li>
  );
}

function SentidoSection({ titulo, ruas, cor }) {
  if (!ruas || ruas.length === 0) return null;
  return (
    <div className="sentido-section">
      <h3 className="sentido-titulo" style={{ borderLeftColor: cor }}>{titulo}</h3>
      <ul className="itinerario-list">
        {ruas.map((rua, i) => (
          <RuaLinha key={`${rua.via}-${i}`} rua={rua} />
        ))}
      </ul>
    </div>
  );
}

function DistanciaResumo({ detalheLinha, mostrarIda, mostrarVolta }) {
  const idaKm = detalheLinha.ida?.distancia_km;
  const voltaKm = detalheLinha.volta?.distancia_km;

  const partes = [];
  if (mostrarIda && idaKm) partes.push(`→ IDA ${idaKm} km`);
  if (mostrarVolta && voltaKm) partes.push(`← VOLTA ${voltaKm} km`);
  if (mostrarIda && mostrarVolta && detalheLinha.distancia_km_total) {
    partes.push(`Total ${detalheLinha.distancia_km_total} km`);
  }

  if (partes.length === 0) return null;
  return <p className="linha-distancia">{partes.join(" · ")}</p>;
}

export default function ItinerarioPanel({ detalheLinha, selectedSentido }) {
  const [exportando, setExportando] = useState(false);

  if (!detalheLinha) {
    return (
      <div className="itinerario-panel">
        <h2 className="sidebar-title">Itinerário</h2>
        <p className="sidebar-hint">Selecione uma linha para ver o itinerário.</p>
      </div>
    );
  }

  const mostrarIda = selectedSentido !== "volta";
  const mostrarVolta = selectedSentido !== "ida";

  async function handleExportar() {
    setExportando(true);
    try {
      await exportarLinhaPDF(detalheLinha, selectedSentido);
    } finally {
      setExportando(false);
    }
  }

  return (
    <div className="itinerario-panel">
      <div className="itinerario-header">
        <h2 className="sidebar-title">Itinerário</h2>
        <button className="pdf-btn" onClick={handleExportar} disabled={exportando}>
          {exportando ? "Gerando…" : "Baixar PDF"}
        </button>
      </div>
      <p className="linha-nome-detalhe">{detalheLinha.nome}</p>
      <DistanciaResumo detalheLinha={detalheLinha} mostrarIda={mostrarIda} mostrarVolta={mostrarVolta} />

      {mostrarIda && (
        <SentidoSection titulo="→ IDA" ruas={detalheLinha.ida?.ruas} cor="#16A34A" />
      )}
      {mostrarVolta && (
        <SentidoSection titulo="← VOLTA" ruas={detalheLinha.volta?.ruas} cor="#2E64D4" />
      )}
    </div>
  );
}
