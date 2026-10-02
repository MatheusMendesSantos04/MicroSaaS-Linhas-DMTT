"""
Gera data/json/bairros/bairro-codigo.pdf a partir de data/json/bairros/bairro-codigo.json
(bairros em ordem alfabetica, vias em ordem alfabetica, com o codigo novo de cada via).

Uso:
    python python/gerar_pdf_bairro_codigo.py
"""
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

BASE = Path(__file__).resolve().parents[1]
JSON_IN = BASE / "data/json/bairros/bairro-codigo.json"
PDF_OUT = BASE / "data/json/bairros/bairro-codigo.pdf"

# Helvetica padrao nao cobre todos os acentos de forma confiavel; usa Arial/DejaVu se houver
FONTE, FONTE_B, MONO = "Helvetica", "Helvetica-Bold", "Courier-Bold"
for reg, bold in (("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),):
    if Path(reg).exists() and Path(bold).exists():
        pdfmetrics.registerFont(TTFont("Arial", reg))
        pdfmetrics.registerFont(TTFont("Arial-Bold", bold))
        FONTE, FONTE_B = "Arial", "Arial-Bold"

AZUL = colors.HexColor("#1a2e4a")
AZUL_CLARO = colors.HexColor("#d0d8e4")
ZEBRA = colors.HexColor("#f7f9fb")
BORDA = colors.HexColor("#c0c8d4")

s_titulo = ParagraphStyle("t", fontName=FONTE_B, fontSize=16, textColor=AZUL, alignment=TA_CENTER, spaceAfter=4)
s_sub = ParagraphStyle("s", fontName=FONTE, fontSize=9, textColor=colors.HexColor("#565c66"), alignment=TA_CENTER, spaceAfter=12)
s_via = ParagraphStyle("v", fontName=FONTE, fontSize=8.5, leading=10.5)


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONTE, 8)
    canvas.setFillColor(colors.HexColor("#565c66"))
    canvas.drawString(1.5 * cm, 1 * cm, "DMTT Maceió — Vias por bairro com código")
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def bloco_bairro(nome, b):
    cab = Table(
        [[Paragraph(f'<font name="{FONTE_B}" color="#1a2e4a">{nome}</font>', s_via),
          Paragraph(f'<font name="{FONTE}" color="#1a2e4a">{b["codigo_inicial"]} – {b["codigo_final"]}  ·  {len(b["vias"])} vias</font>',
                    ParagraphStyle("r", parent=s_via, alignment=2))]],
        colWidths=[11 * cm, 6 * cm],
    )
    cab.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
                             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                             ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    linhas = [[v["codigo"], Paragraph(v["via"], s_via)] for v in b["vias"]]
    estilo = TableStyle([
        ("FONTNAME", (0, 0), (0, -1), MONO), ("FONTSIZE", (0, 0), (0, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, ZEBRA]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])

    def tabela(rows):
        t = Table(rows, colWidths=[2 * cm, 15 * cm])
        t.setStyle(estilo)
        return t

    # cabecalho sempre junto das 4 primeiras vias; o resto do bairro flui normalmente
    itens = [KeepTogether([cab, tabela(linhas[:4])])]
    if len(linhas) > 4:
        itens.append(tabela(linhas[4:]))
    itens.append(Spacer(1, 10))
    return itens


def main():
    data = json.loads(JSON_IN.read_text(encoding="utf-8"))
    doc = BaseDocTemplate(str(PDF_OUT), pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                          topMargin=1.5 * cm, bottomMargin=1.8 * cm,
                          title="Vias por bairro com código", author="DMTT Maceió")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")],
                                       onPage=rodape)])
    story = [Paragraph("Vias por bairro com código", s_titulo),
             Paragraph(f'{data["total_bairros"]} bairros · {data["total_vias"]} vias · '
                       f'códigos {next(iter(data["bairros"].values()))["codigo_inicial"]} a '
                       f'{list(data["bairros"].values())[-1]["codigo_final"]} · gerado em {datetime.now():%d/%m/%Y}', s_sub)]
    for nome, b in data["bairros"].items():
        story.extend(bloco_bairro(nome, b))
    doc.build(story)
    print(f"OK -> {PDF_OUT} ({data['total_bairros']} bairros, {data['total_vias']} vias)")


if __name__ == "__main__":
    main()
