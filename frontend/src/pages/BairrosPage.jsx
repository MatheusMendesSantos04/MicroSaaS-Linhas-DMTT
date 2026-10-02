import { useEffect, useMemo, useState } from "react";
import { getBairroCodigo, getMatrixCodigos } from "../staticApi";

const COMBINING_MARKS = new RegExp("[̀-ͯ]", "g");
const norm = (s) => s.normalize("NFKD").replace(COMBINING_MARKS, "").toUpperCase().trim();

const LIMITE_MATRIX = 300;

function MatrixCodigos() {
  const [data, setData] = useState(null);
  const [erro, setErro] = useState(null);
  const [q, setQ] = useState("");
  const [copiado, setCopiado] = useState(null);

  useEffect(() => {
    getMatrixCodigos().then(setData).catch((e) => setErro(e.message));
  }, []);

  const termo = norm(q);
  const vias = useMemo(
    () => (data ? data.vias.filter((v) => !termo || v.codigo.includes(termo) || norm(v.via).includes(termo) || norm(v.via_original).includes(termo)) : []),
    [data, termo]
  );

  function copiar(codigo) {
    navigator.clipboard?.writeText(codigo).catch(() => {});
    setCopiado(codigo);
    setTimeout(() => setCopiado((c) => (c === codigo ? null : c)), 1200);
  }

  if (erro) return <p className="page-text">Erro ao carregar: {erro}</p>;
  if (!data) return <p className="page-text">Carregando…</p>;

  return (
    <>
      <p className="page-subtitle">
        {data.total} códigos de via cadastrados no Matrix, com as abreviações expandidas (passe o mouse no nome para ver como está no Matrix).
      </p>
      <div className="bairros-filtros">
        <input
          className="bairros-input"
          type="search"
          placeholder="Ex.: 00906, Cruz das Almas ou R. Joao Canuto"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <p className="bairros-resumo">
        {vias.length} código(s){vias.length > LIMITE_MATRIX ? ` — mostrando os primeiros ${LIMITE_MATRIX}, refine a busca` : ""}
      </p>
      {vias.length === 0 && <p className="page-text">Nenhum resultado.</p>}
      <section className="bairro-card">
        <ul className="bairro-vias">
          {vias.slice(0, LIMITE_MATRIX).map((v) => (
            <li key={v.codigo} className="bairro-via">
              <span title={v.via_original !== v.via ? `No Matrix: ${v.via_original}` : undefined}>{v.via}</span>
              <button className="bairro-codigo" onClick={() => copiar(v.codigo)} title="Copiar código">
                {copiado === v.codigo ? "copiado" : v.codigo}
              </button>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

export default function BairrosPage() {
  const [aba, setAba] = useState("bairros");
  const [data, setData] = useState(null);
  const [erro, setErro] = useState(null);
  const [q, setQ] = useState("");
  const [bairro, setBairro] = useState("");
  const [copiado, setCopiado] = useState(null);

  useEffect(() => {
    getBairroCodigo().then(setData).catch((e) => setErro(e.message));
  }, []);

  const grupos = useMemo(() => {
    if (!data) return [];
    const termo = norm(q);
    const out = [];
    for (const [nome, b] of Object.entries(data.bairros)) {
      if (bairro && nome !== bairro) continue;
      const bairroBate = termo && norm(nome).includes(termo);
      const vias = b.vias.filter(
        (v) => !termo || bairroBate || norm(v.via).includes(termo) || v.codigo.includes(termo)
      );
      if (vias.length) out.push({ nome, b, vias });
    }
    return out;
  }, [data, q, bairro]);

  const totalVias = grupos.reduce((n, g) => n + g.vias.length, 0);

  function copiar(codigo) {
    navigator.clipboard?.writeText(codigo).catch(() => {});
    setCopiado(codigo);
    setTimeout(() => setCopiado((c) => (c === codigo ? null : c)), 1200);
  }

  const abas = (
    <div className="bairros-abas">
      <button className={`bairros-aba${aba === "bairros" ? " bairros-aba--ativa" : ""}`} onClick={() => setAba("bairros")}>
        Bairros (novos códigos)
      </button>
      <button className={`bairros-aba${aba === "matrix" ? " bairros-aba--ativa" : ""}`} onClick={() => setAba("matrix")}>
        Códigos do Matrix
      </button>
    </div>
  );

  if (aba === "matrix") {
    return (
      <div className="page-content page-content--wide">
        <h1 className="page-title">Bairros e códigos de vias</h1>
        {abas}
        <MatrixCodigos />
      </div>
    );
  }

  if (erro) return <div className="page-content"><p className="page-text">Erro ao carregar: {erro}</p></div>;
  if (!data) return <div className="page-content"><p className="page-text">Carregando…</p></div>;

  return (
    <div className="page-content page-content--wide">
      <h1 className="page-title">Bairros e códigos de vias</h1>
      {abas}
      <p className="page-subtitle">
        {data.total_vias} vias em {data.total_bairros} bairros ({data.total_com_codigo_matrix ?? 0} com código no Matrix, marcado com "M"). Busque por nome de via, bairro ou código.
      </p>

      <div className="bairros-filtros">
        <input
          className="bairros-input"
          type="search"
          placeholder="Ex.: Fernandes Lima, Jaraguá ou 0123"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className="bairros-select" value={bairro} onChange={(e) => setBairro(e.target.value)}>
          <option value="">Todos os bairros</option>
          {Object.keys(data.bairros).map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </div>

      <p className="bairros-resumo">
        {totalVias} via(s) em {grupos.length} bairro(s)
      </p>

      {grupos.length === 0 && <p className="page-text">Nenhum resultado.</p>}

      {grupos.map(({ nome, b, vias }) => (
        <section key={nome} className="bairro-card">
          <header className="bairro-card-header">
            <h2 className="bairro-card-nome">{nome}</h2>
            <span className="bairro-card-faixa">{b.codigo_inicial} – {b.codigo_final}</span>
          </header>
          <ul className="bairro-vias">
            {vias.map((v) => (
              <li key={v.codigo} className="bairro-via">
                <span>{v.via}</span>
                <span className="bairro-codigos">
                  {v.codigo_matrix && (
                    <button
                      className="bairro-codigo bairro-codigo--matrix"
                      onClick={() => copiar(String(v.codigo_matrix))}
                      title={`Código no Matrix${v.via_matrix ? `: ${v.via_matrix}` : ""} (clique para copiar)`}
                    >
                      {copiado === String(v.codigo_matrix) ? "copiado" : `M ${[].concat(v.codigo_matrix).join(" / ")}`}
                    </button>
                  )}
                  <button className="bairro-codigo" onClick={() => copiar(v.codigo)} title="Código novo (clique para copiar)">
                    {copiado === v.codigo ? "copiado" : v.codigo}
                  </button>
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
