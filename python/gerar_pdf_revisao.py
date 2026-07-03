"""
Gera PDF de revisão de vias por bairro — impressão em P&B
data/vias-por-bairro/relatorio_revisao_vias.pdf

Estrutura:
  CAPA      — resumo geral + tabela por bairro (totais / pendências)
  SEÇÃO 1   — PENDÊNCIAS: duplicatas e sem código
  SEÇÃO 2   — LISTAGEM COMPLETA por bairro com marcadores [D] e [?]
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ── Caminhos ──────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parents[1]
JSON_BAIRRO= BASE / "data/vias-por-bairro/vias_por_bairro.json"
JSON_DU    = BASE / "data/json/dados_unificados.json"
PDF_OUT    = BASE / "data/vias-por-bairro/relatorio_revisao_vias.pdf"
GERADO_EM  = datetime.now().strftime("%d/%m/%Y  %H:%M")

# ── Medidas ───────────────────────────────────────────────────────────────────
PW, PH     = A4
ML = MR    = 1.5 * cm
MT         = 3.0 * cm
MB         = 1.8 * cm
CONTENT_W  = PW - ML - MR   # ~18 cm

# ── Cores (tons de cinza — bom em P&B) ───────────────────────────────────────
PRETO      = colors.black
CINZA_ESC  = colors.HexColor("#222222")
CINZA_MED  = colors.HexColor("#555555")
CINZA_BG1  = colors.HexColor("#dddddd")   # cabeçalho de seção
CINZA_BG2  = colors.HexColor("#eeeeee")   # bairro header
CINZA_BG3  = colors.HexColor("#f7f7f7")   # linha alternada
CINZA_BG4  = colors.HexColor("#f0f0f0")   # subtotal
BRANCO     = colors.white

# ── Estilos de parágrafo ──────────────────────────────────────────────────────
def ps(name, font="Helvetica", size=8, leading=10, color=CINZA_ESC, align=TA_LEFT, bold=False):
    fn = "Helvetica-Bold" if bold else font
    return ParagraphStyle(name, fontName=fn, fontSize=size, leading=leading,
                          textColor=color, alignment=align)

S_NORMAL   = ps("norm")
S_BOLD     = ps("bold", bold=True)
S_SMALL    = ps("small", size=7, leading=9, color=CINZA_MED)
S_HDR_COL  = ps("hcol", bold=True, size=8, color=PRETO)
S_BAIRRO   = ps("bai",  bold=True, size=9, color=PRETO)
S_SECAO    = ps("sec",  bold=True, size=10, color=PRETO)
S_MARK_D   = ps("mD",   bold=True, size=8, color=PRETO)    # [D]
S_MARK_Q   = ps("mQ",   bold=True, size=8, color=CINZA_MED) # [?]
S_CAPA_TIT = ps("ctit", bold=True, size=18, color=PRETO, align=TA_CENTER)
S_CAPA_SUB = ps("csub", size=11, color=CINZA_MED, align=TA_CENTER)
S_LEGENDA  = ps("leg",  size=7.5, color=CINZA_MED)

# ── Cabeçalho / rodapé de página ──────────────────────────────────────────────
def header_page(canvas, doc):
    canvas.saveState()

    # barra superior preta
    canvas.setFillColor(PRETO)
    canvas.rect(ML, PH - 2.2*cm, CONTENT_W, 1.7*cm, fill=1, stroke=0)

    # título
    canvas.setFillColor(BRANCO)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawCentredString(PW/2, PH - 1.35*cm, "REVISÃO DE VIAS POR BAIRRO — DMTT MACEIÓ")

    # data e página
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(ML + 0.3*cm, PH - 1.85*cm, f"Gerado em: {GERADO_EM}")
    canvas.drawRightString(PW - MR - 0.3*cm, PH - 1.85*cm, f"Página {doc.page}")

    # separador abaixo do cabeçalho
    canvas.setStrokeColor(CINZA_BG1)
    canvas.line(ML, PH - 2.35*cm, PW - MR, PH - 2.35*cm)

    # rodapé
    canvas.setFillColor(CINZA_MED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(PW/2, 1.1*cm,
        "MicroSaaS Linhas DMTT  |  Revisão pendente de aprovação")
    canvas.setStrokeColor(CINZA_BG1)
    canvas.line(ML, 1.5*cm, PW - MR, 1.5*cm)

    canvas.restoreState()

# ── Carregar dados ────────────────────────────────────────────────────────────
bairros_json = json.loads(JSON_BAIRRO.read_text("utf-8"))
du_json      = json.loads(JSON_DU.read_text("utf-8"))

# via → lista de linhas que a usam
via_linhas: dict[str, list[str]] = defaultdict(set)
for nome_linha, dados in du_json.items():
    cod_linha = nome_linha.split(" - ")[0].strip()
    for s in ["ida", "volta"]:
        for r in dados.get(s, {}).get("ruas", []):
            v = r.get("via", "").strip()
            if v:
                via_linhas[v].add(cod_linha)

via_linhas = {v: sorted(ls) for v, ls in via_linhas.items()}

def fmt_linhas(via: str) -> str:
    ls = via_linhas.get(via, [])
    if not ls:
        return "—"
    texto = " · ".join(ls[:5])
    if len(ls) > 5:
        texto += f" +{len(ls)-5}"
    return texto

# codigos com múltiplos nomes → duplicatas
codigo_para_vias: dict[str, set] = defaultdict(set)
for bairro, vias in bairros_json.items():
    for item in vias:
        c = item.get("codigo")
        if c:
            codigo_para_vias[c].add(item["via"])

codigos_dup = {c for c, vs in codigo_para_vias.items() if len(vs) > 1}

def is_dup(item):
    return bool(item.get("codigo")) and item["codigo"] in codigos_dup

def is_sem_cod(item):
    return not item.get("codigo")

# ── Utilidades de tabela ──────────────────────────────────────────────────────
CB = "□"   # checkbox

BASE_TSTYLE = [
    ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#bbbbbb")),
    ("TOPPADDING",  (0,0), (-1,-1), 3),
    ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
    ("RIGHTPADDING",(0,0), (-1,-1), 5),
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
]

# ── CAPA ──────────────────────────────────────────────────────────────────────
story = []

story.append(Spacer(1, 1.5*cm))
story.append(Paragraph("RELATÓRIO DE REVISÃO", S_CAPA_TIT))
story.append(Paragraph("Vias por Bairro — DMTT Maceió/AL", S_CAPA_SUB))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph(f"Gerado em: {GERADO_EM}", ps("dt", size=9, color=CINZA_MED, align=TA_CENTER)))
story.append(Spacer(1, 0.8*cm))

# Legenda
legenda_rows = [
    [Paragraph("□", S_BOLD),     Paragraph("Checkbox para marcar OK ou X durante a revisão", S_LEGENDA)],
    [Paragraph("[D]", S_MARK_D), Paragraph("Via DUPLICADA — mesmo código cadastrado com nomes diferentes", S_LEGENDA)],
    [Paragraph("[?]", S_MARK_Q), Paragraph("Via SEM CÓDIGO DMTT — precisa ser verificada/cadastrada", S_LEGENDA)],
]
leg_t = Table(legenda_rows, colWidths=[1.2*cm, CONTENT_W-1.2*cm])
leg_t.setStyle(TableStyle([
    ("BOX",         (0,0), (-1,-1), 0.5, PRETO),
    ("INNERGRID",   (0,0), (-1,-1), 0.3, CINZA_BG1),
    ("TOPPADDING",  (0,0), (-1,-1), 4),
    ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING",(0,0), (-1,-1), 6),
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ("BACKGROUND",  (0,0), (-1,-1), CINZA_BG3),
]))
story.append(leg_t)
story.append(Spacer(1, 0.8*cm))

# Totais gerais
total_bairros = len(bairros_json) - 1  # exclui SEM CODIGO
total_vias    = sum(len(v) for v in bairros_json.values())
total_dups    = sum(1 for b, vs in bairros_json.items() for i in vs if is_dup(i))
total_sem_cod = sum(1 for b, vs in bairros_json.items() for i in vs if is_sem_cod(i))

stats_rows = [
    [Paragraph("TOTAIS GERAIS", ps("th", bold=True, size=9, color=BRANCO))]*4,
    [Paragraph("Bairros",  S_HDR_COL), Paragraph("Vias únicas", S_HDR_COL),
     Paragraph("Duplicatas [D]", S_HDR_COL), Paragraph("Sem código [?]", S_HDR_COL)],
    [Paragraph(str(total_bairros), ps("num", bold=True, size=14, align=TA_CENTER)),
     Paragraph(str(total_vias),    ps("num", bold=True, size=14, align=TA_CENTER)),
     Paragraph(str(total_dups),    ps("num", bold=True, size=14, align=TA_CENTER)),
     Paragraph(str(total_sem_cod), ps("num", bold=True, size=14, align=TA_CENTER))],
]
cw = CONTENT_W / 4
stats_t = Table(stats_rows, colWidths=[cw]*4)
stats_t.setStyle(TableStyle([
    ("SPAN",        (0,0), (3,0)),
    ("BACKGROUND",  (0,0), (3,0), PRETO),
    ("BACKGROUND",  (0,1), (3,1), CINZA_BG1),
    ("BACKGROUND",  (0,2), (3,2), BRANCO),
    ("GRID",        (0,0), (-1,-1), 0.5, CINZA_BG1),
    ("ALIGN",       (0,0), (-1,-1), "CENTER"),
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING",  (0,0), (-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
]))
story.append(stats_t)
story.append(Spacer(1, 0.8*cm))

# Tabela resumo por bairro
story.append(Paragraph("RESUMO POR BAIRRO", ps("rbh", bold=True, size=9, color=PRETO)))
story.append(Spacer(1, 0.2*cm))

res_hdr = [
    Paragraph("BAIRRO",       S_HDR_COL),
    Paragraph("Total",        ps("hc", bold=True, size=8, align=TA_CENTER)),
    Paragraph("Dup. [D]",     ps("hc", bold=True, size=8, align=TA_CENTER)),
    Paragraph("S/Cód [?]",    ps("hc", bold=True, size=8, align=TA_CENTER)),
    Paragraph("OK",           ps("hc", bold=True, size=8, align=TA_CENTER)),
]
res_rows = [res_hdr]
for bairro, vias in bairros_json.items():
    d = sum(1 for i in vias if is_dup(i))
    s = sum(1 for i in vias if is_sem_cod(i))
    res_rows.append([
        Paragraph(bairro, S_NORMAL),
        Paragraph(str(len(vias)), ps("nc", size=8, align=TA_CENTER)),
        Paragraph(str(d) if d else "—", ps("nc", size=8, align=TA_CENTER, bold=bool(d))),
        Paragraph(str(s) if s else "—", ps("nc", size=8, align=TA_CENTER, bold=bool(s))),
        Paragraph("□", ps("cb", size=10, align=TA_CENTER)),
    ])

res_col_w = [9.5*cm, 1.7*cm, 2.0*cm, 2.0*cm, 1.8*cm]
res_t = Table(res_rows, colWidths=res_col_w, repeatRows=1)
res_extra = [("BACKGROUND", (0,0), (-1,0), CINZA_BG1)]
for i in range(1, len(res_rows)):
    if res_rows[i][0].text == "SEM CODIGO":
        res_extra.append(("BACKGROUND", (0,i), (-1,i), CINZA_BG2))
    elif i % 2 == 0:
        res_extra.append(("BACKGROUND", (0,i), (-1,i), CINZA_BG3))
res_t.setStyle(TableStyle(BASE_TSTYLE + res_extra))
story.append(res_t)

story.append(PageBreak())

# ── SEÇÃO 1 — PENDÊNCIAS ──────────────────────────────────────────────────────
story.append(Paragraph("SEÇÃO 1 — PENDÊNCIAS", S_CAPA_TIT))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    f"Esta seção lista todas as vias que precisam de atenção: "
    f"{total_dups} duplicatas [D] e {total_sem_cod} sem código [?]. "
    "Use o checkbox □ para marcar as que forem validadas.",
    ps("desc", size=9, color=CINZA_MED)
))
story.append(Spacer(1, 0.6*cm))

# 1.1 — Duplicatas agrupadas por código
story.append(Paragraph("1.1  DUPLICATAS — mesmo código, nomes diferentes", ps("sh", bold=True, size=10)))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "Cada bloco abaixo mostra um código com todos os nomes usados no sistema. "
    "Marque qual nome é o correto e risque os incorretos.",
    S_SMALL
))
story.append(Spacer(1, 0.3*cm))

# Monta grupos de duplicatas com bairro
dup_grupos: dict[str, list] = {}   # codigo → [{via, bairro, linhas}]
for bairro, vias in bairros_json.items():
    for item in vias:
        c = item.get("codigo")
        if c and c in codigos_dup:
            dup_grupos.setdefault(c, []).append({
                "via": item["via"], "bairro": bairro,
                "linhas": fmt_linhas(item["via"])
            })

dup_hdr = [
    Paragraph("□", S_HDR_COL),
    Paragraph("CÓDIGO", S_HDR_COL),
    Paragraph("VIA", S_HDR_COL),
    Paragraph("BAIRRO", S_HDR_COL),
    Paragraph("LINHAS", S_HDR_COL),
]
CW_DUP = [0.6*cm, 1.8*cm, 7.5*cm, 4.0*cm, 4.1*cm]

dup_rows = [dup_hdr]
dup_styles = [("BACKGROUND", (0,0), (-1,0), CINZA_BG1)]
ri = 1
for codigo in sorted(dup_grupos.keys()):
    grupo = dup_grupos[codigo]
    for j, entry in enumerate(grupo):
        cod_txt  = Paragraph(f"[D] {codigo}" if j == 0 else "", S_MARK_D)
        via_txt  = Paragraph(entry["via"], S_NORMAL)
        bai_txt  = Paragraph(entry["bairro"], S_SMALL)
        lin_txt  = Paragraph(entry["linhas"], S_SMALL)
        dup_rows.append([Paragraph("□", ps("cb2", size=9, align=TA_CENTER)),
                         cod_txt, via_txt, bai_txt, lin_txt])
        bg = CINZA_BG3 if ri % 2 == 0 else BRANCO
        dup_styles.append(("BACKGROUND", (0, ri), (-1, ri), bg))
        ri += 1
    # linha separadora entre grupos
    dup_styles.append(("LINEABOVE", (0, ri-len(grupo)), (-1, ri-len(grupo)), 0.8, CINZA_BG1))

dup_t = Table(dup_rows, colWidths=CW_DUP, repeatRows=1)
dup_t.setStyle(TableStyle(BASE_TSTYLE + dup_styles))
story.append(dup_t)
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph(f"Total de duplicatas: {total_dups}  |  Códigos afetados: {len(dup_grupos)}",
                       ps("tot", bold=True, size=8)))

story.append(PageBreak())

# 1.2 — Sem código
story.append(Paragraph("1.2  SEM CÓDIGO — vias sem código DMTT cadastrado", ps("sh", bold=True, size=10)))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "Estas vias aparecem nos itinerários mas não possuem código DMTT. "
    "Verifique se são vias novas a cadastrar ou erros de digitação.",
    S_SMALL
))
story.append(Spacer(1, 0.3*cm))

sem_hdr = [
    Paragraph("□", S_HDR_COL),
    Paragraph("VIA", S_HDR_COL),
    Paragraph("BAIRRO", S_HDR_COL),
    Paragraph("LINHAS", S_HDR_COL),
]
CW_SEM = [0.6*cm, 8.0*cm, 4.5*cm, 4.9*cm]

sem_rows = [sem_hdr]
sem_styles = [("BACKGROUND", (0,0), (-1,0), CINZA_BG1)]
ri = 1
for bairro, vias in bairros_json.items():
    for item in vias:
        if not is_sem_cod(item):
            continue
        sem_rows.append([
            Paragraph("□", ps("cb3", size=9, align=TA_CENTER)),
            Paragraph(f"[?] {item['via']}", S_MARK_Q),
            Paragraph(bairro, S_SMALL),
            Paragraph(fmt_linhas(item["via"]), S_SMALL),
        ])
        bg = CINZA_BG3 if ri % 2 == 0 else BRANCO
        sem_styles.append(("BACKGROUND", (0, ri), (-1, ri), bg))
        ri += 1

sem_t = Table(sem_rows, colWidths=CW_SEM, repeatRows=1)
sem_t.setStyle(TableStyle(BASE_TSTYLE + sem_styles))
story.append(sem_t)
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph(f"Total sem código: {total_sem_cod}", ps("tot2", bold=True, size=8)))

story.append(PageBreak())

# ── SEÇÃO 2 — LISTAGEM COMPLETA ───────────────────────────────────────────────
story.append(Paragraph("SEÇÃO 2 — LISTAGEM COMPLETA POR BAIRRO", S_CAPA_TIT))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "Lista todas as vias organizadas por bairro. "
    "[D] = duplicata  ·  [?] = sem código  ·  □ = marcar durante revisão.",
    ps("desc2", size=9, color=CINZA_MED)
))
story.append(Spacer(1, 0.6*cm))

CW_LIST = [0.6*cm, 2.0*cm, 9.5*cm, 5.9*cm]

for bairro, vias in bairros_json.items():
    if not vias:
        continue

    n_d = sum(1 for i in vias if is_dup(i))
    n_s = sum(1 for i in vias if is_sem_cod(i))
    badges = []
    if n_d: badges.append(f"{n_d} [D]")
    if n_s: badges.append(f"{n_s} [?]")
    badge_txt = "  ·  " + "  ·  ".join(badges) if badges else ""

    # Header do bairro (linha de seção)
    bai_hdr = Table([[
        Paragraph(f"{bairro}   ({len(vias)} vias{badge_txt})", S_BAIRRO)
    ]], colWidths=[CONTENT_W])
    bai_hdr.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), CINZA_BG2),
        ("BOX",          (0,0), (-1,-1), 0.5, PRETO),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
    ]))

    # Cabeçalho de colunas
    col_hdr = [
        Paragraph("□",      S_HDR_COL),
        Paragraph("CÓDIGO", S_HDR_COL),
        Paragraph("VIA",    S_HDR_COL),
        Paragraph("LINHAS", S_HDR_COL),
    ]
    rows   = [col_hdr]
    extras = [("BACKGROUND", (0,0), (-1,0), CINZA_BG1)]

    for i, item in enumerate(vias):
        via = item["via"]
        cod = item.get("codigo")

        if is_dup(item):
            cod_p = Paragraph(f"[D] {cod}", S_MARK_D)
        elif is_sem_cod(item):
            cod_p = Paragraph("[?]", S_MARK_Q)
        else:
            cod_p = Paragraph(cod or "—", S_NORMAL)

        via_p = Paragraph(via, S_NORMAL)
        lin_p = Paragraph(fmt_linhas(via), S_SMALL)
        rows.append([Paragraph("□", ps(f"cb{i}", size=9, align=TA_CENTER)),
                     cod_p, via_p, lin_p])

        bg = CINZA_BG3 if i % 2 == 0 else BRANCO
        extras.append(("BACKGROUND", (0, i+1), (-1, i+1), bg))

    # Sub-total
    rows.append([
        Paragraph("", S_SMALL),
        Paragraph("", S_SMALL),
        Paragraph(f"Sub-Total: {len(vias)}", ps("st2", size=7.5, bold=True, color=CINZA_MED)),
        Paragraph("", S_SMALL),
    ])
    extras.append(("BACKGROUND", (0, len(rows)-1), (-1, len(rows)-1), CINZA_BG4))

    t = Table(rows, colWidths=CW_LIST, repeatRows=1)
    t.setStyle(TableStyle(BASE_TSTYLE + extras))

    story.append(KeepTogether([bai_hdr, Spacer(1, 0.05*cm), t]))
    story.append(Spacer(1, 0.4*cm))

# ── Montar documento ──────────────────────────────────────────────────────────
frame   = Frame(ML, MB, CONTENT_W, PH - MT - MB, id="main")
tmpl    = PageTemplate(id="padrao", frames=[frame], onPage=header_page)
doc     = BaseDocTemplate(
    str(PDF_OUT), pagesize=A4, pageTemplates=[tmpl],
    title="Revisão de Vias por Bairro — DMTT Maceió",
    author="MicroSaaS Linhas DMTT",
)
doc.build(story)

print(f"[OK] {PDF_OUT.name}")
print(f"     {total_bairros} bairros  |  {total_vias} vias")
print(f"     {total_dups} duplicatas  |  {total_sem_cod} sem código")
print(f"     {doc.page} páginas")
