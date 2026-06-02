"""
Compara os trajetos presentes no Mapa_Reconstruido.kml
com o catalogo de linhas em data/linhas-nomes/linhas.json.

Gera: data/kml/relatorio_kml_vs_linhas.txt

Uso:
    python python/gerar_relatorio_kml.py
"""

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parents[1]
KML_PATH   = BASE_DIR / "data" / "kml" / "Mapa_Reconstruido.kml"
LINHAS_PATH = BASE_DIR / "data" / "linhas-nomes" / "linhas.json"
SAIDA      = BASE_DIR / "data" / "kml" / "relatorio_kml_vs_linhas.txt"

NS = {"k": "http://www.opengis.net/kml/2.2"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def extrair_codigo(texto: str) -> str:
    """Extrai o código de 4 dígitos (ou especial como M001) do nome do placemark."""
    if not texto:
        return ""
    # Código no início: "0024 - Nome" ou "0024-A Nome"
    m = re.match(r"^([A-Z]?\d{3,4})", texto.strip())
    if m:
        return m.group(1).zfill(4) if m.group(1).isdigit() else m.group(1)
    return ""


def tipo_geometria(placemark, ns):
    if placemark.find(".//k:LineString", ns) is not None:
        return "LineString"
    if placemark.find(".//k:MultiGeometry", ns) is not None:
        return "MultiGeometry"
    if placemark.find(".//k:Point", ns) is not None:
        return "Point"
    return "Outro"


# ---------------------------------------------------------------------------
# lê o KML
# ---------------------------------------------------------------------------

tree = ET.parse(KML_PATH)
root = tree.getroot()
placemarks = root.findall(".//k:Placemark", NS)

kml_itens = []
for p in placemarks:
    nome_el = p.find("k:name", NS)
    nome = nome_el.text.strip() if nome_el is not None and nome_el.text else "(sem nome)"
    geom = tipo_geometria(p, NS)
    cod  = extrair_codigo(nome)
    kml_itens.append({"nome": nome, "geom": geom, "codigo": cod})

# separa trajetos (LineString) dos pontos
trajetos = [x for x in kml_itens if x["geom"] in ("LineString", "MultiGeometry")]
pontos   = [x for x in kml_itens if x["geom"] == "Point"]

# agrupa trajetos por código
trajetos_por_cod: dict[str, list] = defaultdict(list)
for t in trajetos:
    trajetos_por_cod[t["codigo"]].append(t["nome"])

# códigos únicos de trajetos no KML (exclui sem código)
codigos_kml = {c for c in trajetos_por_cod if c}

# ---------------------------------------------------------------------------
# lê linhas.json
# ---------------------------------------------------------------------------

with LINHAS_PATH.open(encoding="utf-8") as f:
    linhas_catalogo = json.load(f)

# dict codigo → nome (pode ser vazio)
catalogo: dict[str, str] = {}
for entry in linhas_catalogo:
    cod  = str(entry.get("codigo", "")).strip().zfill(4) if str(entry.get("codigo","")).isdigit() else str(entry.get("codigo","")).strip()
    nome = str(entry.get("nome", "")).strip()
    catalogo[cod] = nome

codigos_catalogo = set(catalogo.keys())

# ---------------------------------------------------------------------------
# cruzamentos
# ---------------------------------------------------------------------------

# presentes no KML E no catálogo
no_kml_e_catalogo = sorted(codigos_kml & codigos_catalogo)

# presentes no KML mas NÃO no catálogo (adicionados ao KML sem estar no catálogo)
so_no_kml = sorted(codigos_kml - codigos_catalogo)

# no catálogo mas SEM trajeto no KML
so_no_catalogo = sorted(codigos_catalogo - codigos_kml)

# catálogo sem nome (só código)
sem_nome_catalogo = sorted(c for c in codigos_catalogo if not catalogo[c])

# catálogo com nome
com_nome_catalogo = sorted(c for c in codigos_catalogo if catalogo[c])

# ---------------------------------------------------------------------------
# escreve relatório
# ---------------------------------------------------------------------------

with SAIDA.open("w", encoding="utf-8") as f:

    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO — KML MAPA_RECONSTRUIDO vs CATÁLOGO DE LINHAS\n")
    f.write(f"KML   : {KML_PATH.name}\n")
    f.write(f"Fonte : {LINHAS_PATH.name}\n")
    f.write("=" * 80 + "\n\n")

    # --- RESUMO ---
    f.write("[ RESUMO ]\n\n")
    f.write(f"  Placemarks no KML               : {len(kml_itens)}\n")
    f.write(f"    Trajetos (LineString)           : {len(trajetos)}\n")
    f.write(f"    Pontos/Paradas                  : {len(pontos)}\n")
    f.write(f"  Códigos únicos com trajeto no KML: {len(codigos_kml)}\n")
    f.write(f"  Linhas no catálogo (linhas.json) : {len(codigos_catalogo)}\n")
    f.write(f"    Com nome                        : {len(com_nome_catalogo)}\n")
    f.write(f"    Só código (sem nome)            : {len(sem_nome_catalogo)}\n\n")
    f.write(f"  Presentes no KML e no catálogo   : {len(no_kml_e_catalogo)}\n")
    f.write(f"  NO KML mas fora do catálogo      : {len(so_no_kml)}  ← adicionados/extras\n")
    f.write(f"  No catálogo SEM trajeto no KML   : {len(so_no_catalogo)}  ← faltam no KML\n\n")

    # --- NO KML MAS FORA DO CATÁLOGO ---
    f.write("=" * 80 + "\n")
    f.write(f"[ NO KML MAS FORA DO CATÁLOGO ]  {len(so_no_kml)} linhas\n")
    f.write("-" * 80 + "\n\n")
    if so_no_kml:
        f.write("  Estes trajetos foram adicionados ao KML mas não existem\n")
        f.write("  no catálogo linhas.json. Podem ser linhas novas.\n\n")
        for cod in so_no_kml:
            nomes_kml = trajetos_por_cod.get(cod, [])
            for n in nomes_kml:
                f.write(f"  {cod}  {n}\n")
        f.write("\n")
    else:
        f.write("  Nenhum — todos os trajetos do KML estão no catálogo.\n\n")

    # --- NO CATÁLOGO SEM TRAJETO NO KML ---
    f.write("=" * 80 + "\n")
    f.write(f"[ NO CATÁLOGO SEM TRAJETO NO KML ]  {len(so_no_catalogo)} linhas\n")
    f.write("-" * 80 + "\n\n")
    f.write("  Estas linhas existem no catálogo mas ainda não têm\n")
    f.write("  trajeto desenhado no Mapa_Reconstruido.kml.\n\n")
    for cod in so_no_catalogo:
        nome_cat = catalogo[cod] if catalogo[cod] else "(sem nome no catálogo)"
        f.write(f"  {cod}  {nome_cat}\n")
    f.write("\n")

    # --- PRESENTES EM AMBOS ---
    f.write("=" * 80 + "\n")
    f.write(f"[ PRESENTES NO KML E NO CATÁLOGO ]  {len(no_kml_e_catalogo)} linhas\n")
    f.write("-" * 80 + "\n\n")
    for cod in no_kml_e_catalogo:
        nome_cat = catalogo.get(cod, "(sem nome)")
        nomes_kml = trajetos_por_cod.get(cod, [])
        qtd = len(nomes_kml)
        sufixo = f"  [{qtd} trajeto(s) no KML]" if qtd > 1 else ""
        f.write(f"  {cod}  {nome_cat}{sufixo}\n")
        if qtd > 1:
            for n in nomes_kml:
                f.write(f"         KML: {n}\n")
    f.write("\n")

    f.write("-" * 80 + "\n")
    f.write("Gerado por python/gerar_relatorio_kml.py\n")

print(f"[OK] {SAIDA}")
print()
print(f"  Trajetos no KML          : {len(trajetos)}")
print(f"  Codigos unicos no KML    : {len(codigos_kml)}")
print(f"  No catalogo              : {len(codigos_catalogo)}")
print(f"  Presentes em ambos       : {len(no_kml_e_catalogo)}")
print(f"  So no KML (extras)       : {len(so_no_kml)}")
print(f"  Faltam no KML            : {len(so_no_catalogo)}")
