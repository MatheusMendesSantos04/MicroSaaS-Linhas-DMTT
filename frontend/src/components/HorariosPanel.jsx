import { useEffect, useState } from "react";

const DIAS = [
  { key: "dia_util", label: "Dia Útil" },
  { key: "sabado",   label: "Sábado"   },
  { key: "domingo",  label: "Domingo"  },
];

function GradeHorarios({ horarios }) {
  if (!horarios || horarios.length === 0) {
    return <p className="horario-vazio">Sem horários</p>;
  }
  return (
    <div className="horario-grade">
      {horarios.map((h) => (
        <span key={h} className="horario-chip">{h}</span>
      ))}
    </div>
  );
}

export default function HorariosPanel({ horarios, selectedLinhaId }) {
  const [diaAtivo, setDiaAtivo] = useState("dia_util");

  useEffect(() => {
    setDiaAtivo("dia_util");
  }, [selectedLinhaId]);

  if (!selectedLinhaId) return null;
  if (!horarios) {
    return (
      <div className="horarios-panel">
        <p className="sidebar-title">Horários</p>
        <p className="sidebar-hint">Sem horários disponíveis para esta linha.</p>
      </div>
    );
  }

  const diaData = horarios[diaAtivo] || { ida: [], volta: [] };
  const temVolta = diaData.volta && diaData.volta.length > 0;

  return (
    <div className="horarios-panel">
      <p className="sidebar-title">Horários</p>

      <div className="horario-tabs">
        {DIAS.map(({ key, label }) => (
          <button
            key={key}
            className={`horario-tab${diaAtivo === key ? " horario-tab--ativo" : ""}`}
            onClick={() => setDiaAtivo(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="horario-corpo">
        <div className="horario-sentido">
          <span className="horario-sentido-label ida-label">→ IDA</span>
          <GradeHorarios horarios={diaData.ida} />
        </div>

        {temVolta && (
          <div className="horario-sentido">
            <span className="horario-sentido-label volta-label">← VOLTA</span>
            <GradeHorarios horarios={diaData.volta} />
          </div>
        )}
      </div>
    </div>
  );
}
