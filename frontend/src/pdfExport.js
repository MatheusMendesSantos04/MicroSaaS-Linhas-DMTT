import jsPDF from "jspdf";
import L from "leaflet";
import leafletImage from "leaflet-image";
import { PANE_LINHA_PRINCIPAL } from "./components/MapView";

const STYLE_IDA = { color: "#16A34A", weight: 4, opacity: 0.9 };
const STYLE_VOLTA = { color: "#2E64D4", weight: 4, opacity: 0.9 };

// html2canvas tira print do DOM e ignora a transformação CSS que o Leaflet usa
// pra posicionar o mapa (pan/zoom via translate3d) — o resultado saía sempre no
// zoom/posição inicial do MapContainer, não no que estava na tela. leaflet-image
// desenha direto a partir das coordenadas reais do mapa (tiles + overlays),
// então reflete exatamente o pan/zoom atual.
function capturarMapa(map) {
  return new Promise((resolve) => {
    if (!map) { resolve(null); return; }
    leafletImage(map, (err, canvas) => {
      if (err || !canvas) { resolve(null); return; }
      resolve(canvas.toDataURL("image/png"));
    });
  });
}

function esperar(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function medirImagem(dataUrl) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight });
    img.onerror = () => resolve({ w: 4, h: 3 });
    img.src = dataUrl;
  });
}

// desenha temporariamente os trajetos pedidos, ajusta o zoom pra eles e tira a
// foto — layers somem em seguida, não deixam rastro no mapa "ao vivo"
async function capturarSegmentos(map, segmentos) {
  const layers = segmentos
    .filter((s) => s.coords?.length > 0)
    .map((s) => L.polyline(s.coords, s.style).addTo(map));

  if (layers.length === 0) return null;

  const bounds = layers[0].getBounds();
  for (const l of layers.slice(1)) bounds.extend(l.getBounds());
  map.fitBounds(bounds, { padding: [30, 30], animate: false });

  await esperar(300); // tempo pros tiles do novo zoom/posição carregarem
  const dataUrl = await capturarMapa(map);
  layers.forEach((l) => map.removeLayer(l));
  return dataUrl;
}

function addImagemAjustada(doc, dataUrl, x, y, maxWidth, maxHeight, naturalW, naturalH) {
  const scale = Math.min(maxWidth / naturalW, maxHeight / naturalH);
  const w = naturalW * scale;
  const h = naturalH * scale;
  doc.addImage(dataUrl, "PNG", x + (maxWidth - w) / 2, y, w, h);
  return h;
}

const DIAS_HORARIO = [
  { key: "dia_util", label: "Dia Útil" },
  { key: "sabado", label: "Sábado" },
  { key: "domingo", label: "Domingo" },
];

function renderListaHorarios(doc, titulo, horariosArr, margin, yStart, usableWidth) {
  let y = yStart;
  if (y > 280) { doc.addPage(); y = 20; }
  doc.setFontSize(9);
  doc.setFont(undefined, "bold");
  doc.text(titulo, margin + 2, y);
  y += 5;

  doc.setFont(undefined, "normal");
  const linhas = doc.splitTextToSize(horariosArr.join("   "), usableWidth - 4);
  for (const linha of linhas) {
    if (y > 285) { doc.addPage(); y = 20; }
    doc.text(linha, margin + 4, y);
    y += 5;
  }
  return y + 2;
}

function renderHorarios(doc, horarios, margin, yStart, pageWidth) {
  if (!horarios) return yStart;
  let y = yStart;
  const usableWidth = pageWidth - margin * 2;

  if (y > 265) { doc.addPage(); y = 20; }
  doc.setFontSize(13);
  doc.setFont(undefined, "bold");
  doc.text("HORÁRIOS", margin, y);
  y += 8;

  for (const { key, label } of DIAS_HORARIO) {
    const diaData = horarios[key];
    const ida = diaData?.ida || [];
    const volta = diaData?.volta || [];
    if (ida.length === 0 && volta.length === 0) continue;

    if (y > 270) { doc.addPage(); y = 20; }
    doc.setFontSize(11);
    doc.setFont(undefined, "bold");
    doc.text(label, margin, y);
    y += 6;

    if (ida.length > 0) y = renderListaHorarios(doc, "IDA", ida, margin, y, usableWidth);
    if (volta.length > 0) y = renderListaHorarios(doc, "VOLTA", volta, margin, y, usableWidth);
    y += 4;
  }
  return y;
}

function renderKmCard(doc, detalheLinha, margin, yStart, pageWidth) {
  const stats = [];
  if (detalheLinha.ida?.distancia_km) {
    stats.push({ label: "IDA", valor: `${detalheLinha.ida.distancia_km} km`, cor: [22, 163, 74] });
  }
  if (detalheLinha.volta?.distancia_km) {
    stats.push({ label: "VOLTA", valor: `${detalheLinha.volta.distancia_km} km`, cor: [46, 100, 212] });
  }
  if (detalheLinha.distancia_km_total) {
    stats.push({ label: "TOTAL", valor: `${detalheLinha.distancia_km_total} km`, cor: [126, 92, 9] });
  }
  if (stats.length === 0) return yStart;

  const usableWidth = pageWidth - margin * 2;
  const gap = 3;
  const boxWidth = (usableWidth - gap * (stats.length - 1)) / stats.length;
  const boxHeight = 16;

  stats.forEach((s, i) => {
    const x = margin + i * (boxWidth + gap);
    doc.setDrawColor(225, 228, 233);
    doc.setFillColor(255, 255, 255);
    doc.roundedRect(x, yStart, boxWidth, boxHeight, 2, 2, "FD");

    doc.setFontSize(8);
    doc.setFont(undefined, "bold");
    doc.setTextColor(s.cor[0], s.cor[1], s.cor[2]);
    doc.text(s.label, x + boxWidth / 2, yStart + 6, { align: "center" });

    doc.setFontSize(11);
    doc.setTextColor(20, 20, 20);
    doc.text(s.valor, x + boxWidth / 2, yStart + 12.5, { align: "center" });
  });

  doc.setFont(undefined, "normal");
  doc.setTextColor(0);
  return yStart + boxHeight + 6;
}

function renderSentido(doc, titulo, ruas, margin, yStart) {
  let y = yStart;
  if (!ruas || ruas.length === 0) return y;

  if (y > 270) { doc.addPage(); y = 20; }
  doc.setFontSize(12);
  doc.setFont(undefined, "bold");
  doc.text(titulo, margin, y);
  y += 6;

  doc.setFont(undefined, "normal");
  doc.setFontSize(9);
  for (const rua of ruas) {
    if (y > 285) { doc.addPage(); y = 20; }
    const linha = rua.codigo ? `${rua.via}   (${rua.codigo})` : rua.via;
    doc.text(linha, margin + 2, y);
    y += 5;
  }
  return y + 4;
}

export async function exportarLinhaPDF(detalheLinha, map, horarios) {
  const idaCoords = detalheLinha.ida?.coordenadas || [];
  const voltaCoords = detalheLinha.volta?.coordenadas || [];

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 14;

  doc.setFontSize(16);
  doc.setFont(undefined, "bold");
  doc.text(detalheLinha.nome, margin, 18);

  doc.setFont(undefined, "normal");
  doc.setFontSize(9);
  doc.setTextColor(120);
  const dataStr = new Date().toLocaleDateString("pt-BR");
  doc.text(`Linhas DMTT — Maceió · gerado em ${dataStr}`, margin, 24);
  doc.setTextColor(0);

  let y = renderKmCard(doc, detalheLinha, margin, 27, pageWidth);

  if (map) {
    // esconde a camada "ao vivo" da linha selecionada pra não vazar por trás
    // das capturas temporárias, que controlam exatamente o que aparece em cada foto
    const pane = map.getPane(PANE_LINHA_PRINCIPAL);
    const paneDisplayOriginal = pane?.style.display ?? "";
    if (pane) pane.style.display = "none";

    const centroOriginal = map.getCenter();
    const zoomOriginal = map.getZoom();

    // jsPDF (fonte Helvetica padrão) não tem os glifos → / ← — usar texto puro
    const capturas = [
      { titulo: "IDA", segmentos: [{ coords: idaCoords, style: STYLE_IDA }] },
      { titulo: "VOLTA", segmentos: [{ coords: voltaCoords, style: STYLE_VOLTA }] },
      { titulo: "IDA + VOLTA", segmentos: [
        { coords: idaCoords, style: STYLE_IDA },
        { coords: voltaCoords, style: STYLE_VOLTA },
      ] },
    ];

    const boxWidth = pageWidth - margin * 2;
    const overheadPorBloco = 8 + 6; // label + espaco depois da imagem
    const boxHeight = (pageHeight - y - margin - 3 * overheadPorBloco) / 3;

    for (const { titulo, segmentos } of capturas) {
      doc.setFontSize(10);
      doc.setFont(undefined, "bold");
      doc.text(titulo, margin, y + 5);
      y += 8;

      const dataUrl = await capturarSegmentos(map, segmentos);
      if (dataUrl) {
        const { w, h } = await medirImagem(dataUrl);
        y += addImagemAjustada(doc, dataUrl, margin, y, boxWidth, boxHeight, w, h);
      } else {
        doc.setFontSize(9);
        doc.setTextColor(150);
        doc.text("(Não foi possível capturar o mapa.)", margin, y);
        doc.setTextColor(0);
        y += boxHeight;
      }
      y += 6;
    }

    // devolve o mapa "ao vivo" exatamente como estava antes da exportação
    if (pane) pane.style.display = paneDisplayOriginal;
    map.setView(centroOriginal, zoomOriginal, { animate: false });
  } else {
    doc.setFontSize(9);
    doc.setTextColor(150);
    doc.text("(Mapa não disponível para exportação.)", margin, y);
    doc.setTextColor(0);
  }

  // páginas seguintes: itinerário completo, sempre IDA e VOLTA (independe do
  // filtro de sentido usado na tela — o PDF é o documento completo da linha)
  doc.addPage();
  let y2 = 20;
  y2 = renderSentido(doc, "IDA", detalheLinha.ida?.ruas, margin, y2);
  y2 = renderSentido(doc, "VOLTA", detalheLinha.volta?.ruas, margin, y2);

  y2 += 4;
  renderHorarios(doc, horarios, margin, y2, pageWidth);

  const nomeArquivo = detalheLinha.nome.replace(/[^\w\-]+/g, "_").slice(0, 60);
  doc.save(`${nomeArquivo}.pdf`);
}
