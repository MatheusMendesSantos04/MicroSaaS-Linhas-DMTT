// Substitui o backend: lê os JSONs pré-gerados em public/data/ (ver
// python/gerar_dados_estaticos.py) e resolve busca/filtro no navegador.

const DATA_BASE = `${import.meta.env.BASE_URL}data`;

let linhasPromise = null;
let ruaIndexPromise = null;
let horariosPromise = null;
let geojsonTodasPromise = null;
const linhaDetalheCache = new Map();

async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Erro ${res.status} em ${path}`);
  return res.json();
}

const COMBINING_MARKS = new RegExp("[̀-ͯ]", "g");

function normalizeText(value) {
  return value
    .normalize("NFKD")
    .replace(COMBINING_MARKS, "")
    .toUpperCase()
    .trim()
    .replace(/[^A-Z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function horarioParaMinutos(h) {
  const [hh, mm] = h.split(":").map(Number);
  return hh * 60 + mm;
}

function getLinhas() {
  if (!linhasPromise) linhasPromise = loadJson(`${DATA_BASE}/linhas.json`);
  return linhasPromise;
}

function getRuaIndex() {
  if (!ruaIndexPromise) ruaIndexPromise = loadJson(`${DATA_BASE}/rua_index.json`);
  return ruaIndexPromise;
}

function getHorariosPorLinha() {
  if (!horariosPromise) horariosPromise = loadJson(`${DATA_BASE}/horarios_por_linha.json`);
  return horariosPromise;
}

function getGeojsonTodas() {
  if (!geojsonTodasPromise) geojsonTodasPromise = loadJson(`${DATA_BASE}/geojson_todas.json`);
  return geojsonTodasPromise;
}

function getLinhaDetalhe(id) {
  if (!linhaDetalheCache.has(id)) {
    linhaDetalheCache.set(id, loadJson(`${DATA_BASE}/linhas/${id}.json`));
  }
  return linhaDetalheCache.get(id);
}

export async function listarLinhas() {
  return getLinhas();
}

export async function getTerminais() {
  return loadJson(`${DATA_BASE}/terminais.json`);
}

export async function getZonas() {
  return loadJson(`${DATA_BASE}/zonas.json`);
}

export async function detalharLinha(id) {
  return getLinhaDetalhe(id);
}

function filtrarFeaturesPorSentido(features, sentido) {
  const s = (sentido || "").toLowerCase();
  if (!s || s === "ambos") return features;
  return features.filter((f) => f.properties.sentido === s);
}

export async function geojsonTodasLinhas(sentido) {
  const fc = await getGeojsonTodas();
  return { type: "FeatureCollection", features: filtrarFeaturesPorSentido(fc.features, sentido) };
}

export async function geojsonLinha(id, sentido) {
  const linha = await getLinhaDetalhe(id);
  const features = [];
  const s = (sentido || "").toLowerCase();
  const incluiIda = !s || s === "ida" || s === "ambos";
  const incluiVolta = !s || s === "volta" || s === "ambos";

  if (incluiIda && linha.ida.coordenadas.length) {
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates: linha.ida.coordenadas.map(([lat, lon]) => [lon, lat]) },
      properties: { linha_id: linha.id, linha_nome: linha.nome, sentido: "ida" },
    });
  }
  if (incluiVolta && linha.volta.coordenadas.length) {
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates: linha.volta.coordenadas.map(([lat, lon]) => [lon, lat]) },
      properties: { linha_id: linha.id, linha_nome: linha.nome, sentido: "volta" },
    });
  }
  return { type: "FeatureCollection", features };
}

export async function getHorarios(linhaId) {
  const horarios = await getHorariosPorLinha();
  return horarios[linhaId] ?? null;
}

export async function sugerirRuas(query, limit = 10) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return [];
  const index = await getRuaIndex();
  const matches = Object.keys(index).filter((key) => key.includes(normalizedQuery));
  matches.sort();
  return matches.slice(0, limit);
}

export async function buscarRuas(query, { limit = 100 } = {}) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return [];
  const index = await getRuaIndex();
  const results = [];
  for (const [key, entries] of Object.entries(index)) {
    if (!key.includes(normalizedQuery)) continue;
    for (const entry of entries) {
      results.push({
        linha_id: entry.linha_id,
        linha_nome: entry.linha_nome,
        sentido: entry.sentido,
        rua: key,
        codigo: entry.codigo,
      });
      if (results.length >= limit) return results;
    }
  }
  return results;
}

export async function buscarRuasComHorario(query, { horario, dia = "dia_util", janela = 20, limit = 100 }) {
  const base = await buscarRuas(query, { limit });
  const horariosPorLinha = await getHorariosPorLinha();
  const targetMin = horarioParaMinutos(horario);
  const enriched = [];
  for (const item of base) {
    const horariosLinha = horariosPorLinha[item.linha_id];
    if (!horariosLinha) continue;
    const tempos = horariosLinha[dia]?.[item.sentido] ?? [];
    const proximos = tempos.filter((t) => Math.abs(horarioParaMinutos(t) - targetMin) <= janela);
    if (proximos.length > 0) {
      enriched.push({ ...item, horarios_proximos: proximos });
    }
  }
  return enriched;
}
