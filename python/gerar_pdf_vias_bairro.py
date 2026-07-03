"""
Gera data/vias-por-bairro/vias_por_bairro.pdf
no estilo do relatório original DMTT.

Fonte de dados: data/json/vias_por_bairro.json
"""

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

BASE     = Path(__file__).resolve().parents[1]
JSON_IN  = BASE / "data/vias-por-bairro/vias_por_bairro.json"
PDF_OUT  = BASE / "data/vias-por-bairro/vias_por_bairro.pdf"
PDF_OUT.parent.mkdir(parents=True, exist_ok=True)

# ── Cores ─────────────────────────────────────────────────────────────────────
COR_HEADER_BG   = colors.HexColor("#1a2e4a")   # azul escuro
COR_HEADER_TXT  = colors.white
COR_BAIRRO_BG   = colors.HexColor("#d0d8e4")   # azul acinzentado claro
COR_BAIRRO_TXT  = colors.HexColor("#1a2e4a")
COR_SUBTOTAL_BG = colors.HexColor("#eef1f5")
COR_LINHA_PAR   = colors.HexColor("#f7f9fb")
COR_LINHA_IMP   = colors.white
COR_BORDA       = colors.HexColor("#c0c8d4")
COR_TITULO_PAG  = colors.HexColor("#1a2e4a")

PAGE_W, PAGE_H = A4
MARGIN_L = MARGIN_R = 1.5 * cm
MARGIN_T = 3.2 * cm   # espaço para o cabeçalho
MARGIN_B = 1.8 * cm

# ── Header de página (chamado a cada página) ──────────────────────────────────
GERADO_EM = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")

def cabecalho_pagina(canvas, doc):
    canvas.saveState()
    w, h = PAGE_W, PAGE_H

    # Fundo do cabeçalho
    canvas.setFillColor(COR_HEADER_BG)
    canvas.rect(MARGIN_L, h - 2.4*cm, w - MARGIN_L - MARGIN_R, 2.0*cm, fill=1, stroke=0)

    # Título central
    canvas.setFillColor(COR_HEADER_TXT)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawCentredString(w / 2, h - 1.45*cm, "VIAS POR BAIRRO")

    # Data à esquerda
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN_L + 0.3*cm, h - 1.9*cm, GERADO_EM)

    # Página à direita
    canvas.drawRightString(
        w - MARGIN_R - 0.3*cm, h - 1.9*cm,
        f"Página: {doc.page}"
    )

    # Subtítulo
    canvas.setFillColor(COR_TITULO_PAG)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN_L + 0.3*cm, h - 2.65*cm,
                      "Linhas DMTT — Maceió/AL  |  Sistema MicroSaaS DMTT")

    # Rodapé
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(w / 2, 1.0*cm, f"MicroSaaS Linhas DMTT — gerado em {GERADO_EM}")
    canvas.line(MARGIN_L, 1.4*cm, w - MARGIN_R, 1.4*cm)

    canvas.restoreState()


# ── Carregar dados ─────────────────────────────────────────────────────────────
dados: dict = json.loads(JSON_IN.read_text("utf-8"))

# ── Montar conteúdo (Flowables) ───────────────────────────────────────────────
story = []

# Estilos de parágrafo para células
st_normal = ParagraphStyle("norm", fontName="Helvetica",     fontSize=8,  leading=10)
st_bold   = ParagraphStyle("bold", fontName="Helvetica-Bold",fontSize=8,  leading=10)
st_bairro = ParagraphStyle("bai",  fontName="Helvetica-Bold",fontSize=8.5,leading=11,
                           textColor=COR_BAIRRO_TXT)

COL_W = [4.0*cm, 1.8*cm, 11.2*cm]   # Bairro | Código | Via

# Cabeçalho da tabela
HEADER_ROW = [
    Paragraph("BAIRRO",  ParagraphStyle("hdr", fontName="Helvetica-Bold", fontSize=8,
                                        textColor=COR_HEADER_TXT)),
    Paragraph("CÓDIGO",  ParagraphStyle("hdr", fontName="Helvetica-Bold", fontSize=8,
                                        textColor=COR_HEADER_TXT)),
    Paragraph("VIA",     ParagraphStyle("hdr", fontName="Helvetica-Bold", fontSize=8,
                                        textColor=COR_HEADER_TXT)),
]

def build_table_for_bairro(bairro: str, vias: list) -> list:
    """Retorna uma lista de flowables (Table + Spacer) para um bairro."""
    rows = [HEADER_ROW]
    styles_extra = []   # (cmd, row_range, ...)

    row_idx = 1   # 0 = header
    for i, item in enumerate(vias):
        bairro_cell = Paragraph(bairro if i == 0 else "", st_bairro if i == 0 else st_normal)
        cod_cell    = Paragraph(item["codigo"] or "—", st_normal)
        via_cell    = Paragraph(item["via"], st_normal)
        rows.append([bairro_cell, cod_cell, via_cell])

        # Fundo alternado
        bg = COR_LINHA_PAR if (i % 2 == 0) else COR_LINHA_IMP
        styles_extra.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))
        if i == 0:
            styles_extra.append(("BACKGROUND", (0, row_idx), (0, row_idx), COR_BAIRRO_BG))

        row_idx += 1

    # Linha de Sub-Total
    rows.append([
        Paragraph("", st_normal),
        Paragraph("", st_normal),
        Paragraph(f"Sub-Total: {len(vias)}", ParagraphStyle(
            "sub", fontName="Helvetica-Bold", fontSize=7.5,
            textColor=colors.HexColor("#444444")
        )),
    ])
    styles_extra.append(("BACKGROUND", (0, row_idx), (-1, row_idx), COR_SUBTOTAL_BG))

    base_style = [
        # Cabeçalho
        ("BACKGROUND",  (0, 0), (-1, 0), COR_HEADER_BG),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        # Bordas
        ("GRID",        (0, 0), (-1, -1), 0.3, COR_BORDA),
        ("LINEBELOW",   (0, 0), (-1, 0),  0.6, COR_HEADER_BG),
        # Padding
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",(0, 0), (-1, -1), 5),
        # Valign
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]

    t = Table(rows, colWidths=COL_W, repeatRows=1)
    t.setStyle(TableStyle(base_style + styles_extra))
    return [t, Spacer(1, 0.4 * cm)]


total_bairros = 0
total_vias    = 0

for bairro, vias in dados.items():
    if not vias:
        continue
    story += build_table_for_bairro(bairro, vias)
    story.append(Spacer(1, 0.15 * cm))
    total_bairros += 1
    total_vias    += len(vias)

# ── Montar documento ──────────────────────────────────────────────────────────
frame = Frame(
    MARGIN_L, MARGIN_B,
    PAGE_W - MARGIN_L - MARGIN_R,
    PAGE_H - MARGIN_T - MARGIN_B,
    id="main",
)
template = PageTemplate(id="padrao", frames=[frame], onPage=cabecalho_pagina)
doc = BaseDocTemplate(
    str(PDF_OUT),
    pagesize=A4,
    pageTemplates=[template],
    title="Vias por Bairro — DMTT Maceió",
    author="MicroSaaS Linhas DMTT",
)
doc.build(story)

print(f"[OK] {PDF_OUT}")
print(f"     {total_bairros} bairros  |  {total_vias} vias  |  {doc.page} páginas")
