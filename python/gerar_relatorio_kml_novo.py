"""
Compara Mapa Reconstruido.kml (versao atual, com espaco) contra:
  1. Mapa_Reconstruido.kml (versao anterior, com underscore)
  2. data/linhas-nomes/linhas.json (catalogo oficial)

Saida: data/kml/relatorio_mapa_reconstruido_novo.txt

Uso:
    python python/gerar_relatorio_kml_novo.py
"""

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

BASE        = Path(__file__).resolve().parents[1]
KML_ANTIGO  = BASE / "data" / "kml" / "Mapa_Reconstruido.kml"
KML_NOVO    = BASE / "data" / "kml" / "Mapa Reconstruido.kml"
LINHAS_PATH = BASE / "data" / "linhas-nomes" / "linhas.json"
SAIDA       = BASE / "data" / "kml" / "relatorio_mapa_reconstruido_novo.txt"

NS = {"k": "http://www.opengis.net/kml/2.2"}


def extrair_codigo(texto: str) -> str:
    if not texto:
        return ""
    m = re.match(r"^([A-Z]?\d{3,4})", texto.strip())
    if not m:
        return ""
    v = m.group(1)
    return v.zfill(4) if v.isdigit() else v


def ler_kml(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    pms  = root.findall(".//k:Placemark", NS)
    trajetos, pontos = [], []
    for p in pms:
        n_el = p.find("k:name", NS)
        nome = n_el.text.strip() if n_el is not None and n_el.text else "(sem nome)"
        cod  = extrair_codigo(nome)
        if p.find(".//k:LineString", NS) is not None:
            trajetos.append({"nome": nome, "codigo": cod})
        elif p.find(".//k:Point", NS) is not None:
            pontos.append({"nome": nome, "codigo": cod})
    return trajetos, pontos


# --- lê os dois KMLs ---
traj_ant, pts_ant = ler_kml(KML_ANTIGO)
traj_nov, pts_nov = ler_kml(KML_NOVO)

cods_ant = {t["codigo"] for t in traj_ant if t["codigo"]}
cods_nov = {t["codigo"] for t in traj_nov if t["codigo"]}

adicionados = sorted(cods_nov - cods_ant)
removidos   = sorted(cods_ant - cods_nov)

nomes_nov: dict[str, list[str]] = defaultdict(list)
for t in traj_nov:
    if t["codigo"]:
        nomes_nov[t["codigo"]].append(t["nome"])

# --- catálogo ---
cat_raw  = json.load(open(LINHAS_PATH, encoding="utf-8"))
catalogo: dict[str, str] = {}
for e in cat_raw:
    c = str(e.get("codigo", "")).strip()
    c = c.zfill(4) if c.isdigit() else c
    catalogo[c] = str(e.get("nome", "")).strip()

cods_cat   = set(catalogo.keys())
so_no_kml  = sorted(cods_nov - cods_cat)
faltam_kml = sorted(cods_cat - cods_nov)
em_ambos   = sorted(cods_nov & cods_cat)

# ---------------------------------------------------------------------------
# escreve relatório
# ---------------------------------------------------------------------------

with SAIDA.open("w", encoding="utf-8") as f:

    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO — MAPA RECONSTRUIDO (VERSÃO ATUALIZADA) vs CATÁLOGO\n")
    f.write("Arquivo atual  : Mapa Reconstruido.kml\n")
    f.write("Arquivo anterior: Mapa_Reconstruido.kml\n")
    f.write("=" * 80 + "\n\n")

    # RESUMO
    f.write("[ RESUMO GERAL ]\n\n")
    f.write(f"  Trajetos no KML atual            : {len(traj_nov)}\n")
    f.write(f"  Pontos/Paradas no KML atual      : {len(pts_nov)}\n")
    f.write(f"  Códigos únicos com trajeto       : {len(cods_nov)}\n")
    f.write(f"  Linhas no catálogo               : {len(cods_cat)}\n\n")
    f.write(f"  Presentes no KML e no catálogo   : {len(em_ambos)}\n")
    f.write(f"  No KML mas fora do catálogo      : {len(so_no_kml)}\n")
    f.write(f"  No catálogo sem trajeto no KML   : {len(faltam_kml)}  ← ainda faltam\n\n")

    # O QUE FOI ADICIONADO
    f.write("=" * 80 + "\n")
    f.write(f"[ O QUE FOI ADICIONADO vs VERSÃO ANTERIOR ]  {len(adicionados)} linhas novas\n")
    f.write("-" * 80 + "\n\n")
    f.write(f"  Versão anterior : {len(traj_ant)} trajetos  ({len(cods_ant)} códigos únicos)\n")
    f.write(f"  Versão atual    : {len(traj_nov)} trajetos  ({len(cods_nov)} códigos únicos)\n")
    f.write(f"  Diferença       : +{len(traj_nov)-len(traj_ant)} trajetos  +{len(adicionados)} códigos novos\n\n")

    for cod in adicionados:
        cat_nome = catalogo.get(cod, "(nao esta no catalogo)")
        nomes = nomes_nov.get(cod, [])
        f.write(f"  {cod}  Catálogo : {cat_nome}\n")
        for n in nomes:
            f.write(f"       KML     : {n}\n")
        f.write("\n")

    if removidos:
        f.write("  ATENÇÃO — Códigos que sumiraram vs versão anterior:\n")
        for cod in removidos:
            f.write(f"    {cod}  {catalogo.get(cod, '')}\n")
        f.write("\n")

    # AINDA FALTAM
    f.write("=" * 80 + "\n")
    f.write(f"[ LINHAS QUE AINDA FALTAM NO KML ]  {len(faltam_kml)}\n")
    f.write("-" * 80 + "\n\n")
    for cod in faltam_kml:
        nome_cat = catalogo.get(cod) or "(sem nome no catalogo)"
        f.write(f"  {cod}  {nome_cat}\n")
    f.write("\n")

    # FORA DO CATÁLOGO
    if so_no_kml:
        f.write("=" * 80 + "\n")
        f.write(f"[ NO KML MAS FORA DO CATÁLOGO ]  {len(so_no_kml)}\n")
        f.write("-" * 80 + "\n\n")
        for cod in so_no_kml:
            for n in nomes_nov.get(cod, []):
                f.write(f"  {cod}  {n}\n")
        f.write("\n")

    # TODOS PRESENTES
    f.write("=" * 80 + "\n")
    f.write(f"[ TODAS AS LINHAS PRESENTES NO KML E NO CATÁLOGO ]  {len(em_ambos)}\n")
    f.write("-" * 80 + "\n\n")
    for cod in em_ambos:
        cat_nome = catalogo.get(cod, "")
        qtd = len(nomes_nov.get(cod, []))
        extra = f"  [{qtd} trajeto(s)]" if qtd > 2 else ""
        f.write(f"  {cod}  {cat_nome}{extra}\n")

    f.write("\n")
    f.write("-" * 80 + "\n")
    f.write("Gerado por python/gerar_relatorio_kml_novo.py\n")


print(f"[OK] {SAIDA.name}")
print()
print(f"  Versao anterior : {len(traj_ant)} trajetos  ({len(cods_ant)} codigos)")
print(f"  Versao atual    : {len(traj_nov)} trajetos  ({len(cods_nov)} codigos)")
print(f"  Adicionados     : {adicionados}")
print(f"  Ainda faltam    : {faltam_kml}")
