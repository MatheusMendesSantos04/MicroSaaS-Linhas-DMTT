import { DASHBOARDS } from "../dashboardsConfig";

const TIPO_LABEL = { publico: "Público", interno: "Interno" };

export default function DashboardsPage() {
  return (
    <div className="page-content">
      <h1 className="page-title">Dashboards — GEPOT</h1>
      <p className="page-subtitle">
        Relatórios e indicadores do setor, publicados no Power BI.
      </p>

      {DASHBOARDS.length === 0 ? (
        <p className="sidebar-hint">Nenhum dashboard publicado ainda. Volte em breve.</p>
      ) : (
        <div className="dashboard-grid">
          {DASHBOARDS.map((d) => (
            <a
              key={d.link}
              href={d.link}
              target="_blank"
              rel="noopener noreferrer"
              className="dashboard-card"
            >
              <div className="dashboard-card-header">
                <span className="dashboard-card-titulo">{d.titulo}</span>
                <span className={`dashboard-card-tipo dashboard-card-tipo--${d.tipo}`}>
                  {TIPO_LABEL[d.tipo] || d.tipo}
                </span>
              </div>
              <p className="dashboard-card-desc">{d.descricao}</p>
              <span className="dashboard-card-link">Abrir dashboard →</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
