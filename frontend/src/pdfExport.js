import jsPDF from "jspdf";
import html2canvas from "html2canvas";

async function capturarMapa() {
  const mapEl = document.querySelector(".leaflet-container");
  if (!mapEl) return null;
  try {
    const canvas = await html2canvas(mapEl, { useCORS: true, logging: false });
    return canvas.toDataURL("image/png");
  } catch {
    return null;
  }
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

export async function exportarLinhaPDF(detalheLinha, selectedSentido) {
  const mostrarIda = selectedSentido !== "volta";
  const mostrarVolta = selectedSentido !== "ida";

  const mapaDataUrl = await capturarMapa();

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
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

  let y = 30;

  if (mapaDataUrl) {
    const img = new Image();
    img.src = mapaDataUrl;
    await new Promise((resolve) => { img.onload = resolve; img.onerror = resolve; });
    const imgWidth = pageWidth - margin * 2;
    const imgHeight = img.height && img.width ? (img.height / img.width) * imgWidth : imgWidth * 0.6;
    doc.addImage(mapaDataUrl, "PNG", margin, y, imgWidth, imgHeight);
    y += imgHeight + 8;
  } else {
    doc.setFontSize(9);
    doc.setTextColor(150);
    doc.text("(Não foi possível capturar a imagem do mapa.)", margin, y);
    doc.setTextColor(0);
    y += 8;
  }

  const distParts = [];
  if (mostrarIda && detalheLinha.ida?.distancia_km) distParts.push(`IDA: ${detalheLinha.ida.distancia_km} km`);
  if (mostrarVolta && detalheLinha.volta?.distancia_km) distParts.push(`VOLTA: ${detalheLinha.volta.distancia_km} km`);
  if (mostrarIda && mostrarVolta && detalheLinha.distancia_km_total) {
    distParts.push(`Total: ${detalheLinha.distancia_km_total} km`);
  }
  if (distParts.length > 0) {
    doc.setFontSize(10);
    doc.text(distParts.join("   ·   "), margin, y);
    y += 8;
  }

  // jsPDF (fonte Helvetica padrão) não tem os glifos → / ← — usar texto puro
  if (mostrarIda) y = renderSentido(doc, "IDA", detalheLinha.ida?.ruas, margin, y);
  if (mostrarVolta) y = renderSentido(doc, "VOLTA", detalheLinha.volta?.ruas, margin, y);

  const nomeArquivo = detalheLinha.nome.replace(/[^\w\-]+/g, "_").slice(0, 60);
  doc.save(`${nomeArquivo}.pdf`);
}
