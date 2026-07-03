"""
Compara as vias de intinerario-vias-novos.json com itinerario_completo.json.
Tenta expandir abreviações e classifica cada via em:
  1. MATCH EXATO — já está igual ao nome de referência
  2. EXPANDIDA   — abreviação expandida encontrou match na referência
  3. NOVA        — não encontrou correspondência (via nova ou sem referência)

Saída: data/json/novos_trajetos/relatorio_expansao_vias.txt

Uso:
    python python/gerar_relatorio_expansao_vias.py
"""

import json
import re
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
NOVOS_F  = BASE_DIR / "data" / "json" / "novos_trajetos" / "intinerario-vias-novos.json"
REF_F    = BASE_DIR / "data" / "json" / "intinerario manual" / "itinerario_completo.json"
SAIDA    = BASE_DIR / "data" / "json" / "novos_trajetos" / "relatorio_expansao_vias.txt"

# Tabela de expansão de abreviações (ordem importa: mais longas primeiro)
ABREVIACOES = [
    (r"\bAV\.\s+",    "AVENIDA "),
    (r"\bR\.\s+",     "RUA "),
    (r"\bLAD\.\s+",   "LADEIRA "),
    (r"\bP[CÇ]A?\.\s+", "PRACA "),
    (r"\bTV\.\s+",    "TRAVESSA "),
    (r"\bTRAV\.\s+",  "TRAVESSA "),
    (r"\bDR\.\s+",    "DOUTOR "),
    (r"\bPROF\.\s+",  "PROFESSOR "),
    (r"\bDEP\.\s+",   "DEPUTADO "),
    (r"\bENG\.\s+",   "ENGENHEIRO "),
    (r"\bJORN\.\s+",  "JORNALISTA "),
    (r"\bGOV\.\s+",   "GOVERNADOR "),
    (r"\bGAL\.\s+",   "GENERAL "),
    (r"\bGEN\.\s+",   "GENERAL "),
    (r"\bCEL\.\s+",   "CORONEL "),
    (r"\bCAP\.\s+",   "CAPITAO "),
    (r"\bSGT\.\s+",   "SARGENTO "),
    (r"\bTERM\.\s+",  "TERMINAL "),
    (r"\bDESEMB\.\s+","DESEMBARGADOR "),
    (r"\bDES\.\s+",   "DESEMBARGADOR "),
    (r"\bVER\.\s+",   "VEREADOR "),
    (r"\bSEN\.\s+",   "SENADOR "),
    (r"\bPRA\.\s+",   "PRACA "),
    (r"\bSTA\.\s+",   "SANTA "),
    (r"\bSTO\.\s+",   "SANTO "),
    (r"\bCJ\.\s+",    "CONJUNTO "),
    (r"\bCONJ\.\s+",  "CONJUNTO "),
]


def normalizar(txt: str) -> str:
    """Uppercase, remove acentos, colapsa espaços."""
    txt = txt.upper().strip()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"\s+", " ", txt)
    return txt


def expandir(txt: str) -> str:
    """Aplica expansões de abreviações ao texto normalizado."""
    for padrao, substituicao in ABREVIACOES:
        txt = re.sub(padrao, substituicao, txt, flags=re.IGNORECASE)
    return normalizar(txt)


# --- carrega arquivos ---
novos    = json.loads(NOVOS_F.read_text(encoding="utf-8"))
completo = json.loads(REF_F.read_text(encoding="utf-8"))

# --- monta conjunto de referência (normalizado → original) ---
ref_norm: dict[str, str] = {}
for linha, dados in completo.items():
    for sentido in ["ida", "volta"]:
        for via in dados.get(sentido, []):
            if isinstance(via, str):
                ref_norm[normalizar(via)] = via

# --- coleta vias do arquivo novo com contexto (linha + sentido) ---
via_contextos: dict[str, list[str]] = {}  # via original → ["linha/IDA", ...]
for linha, dados in novos.items():
    cod = linha.split(" - ")[0].strip() if " - " in linha else linha
    for sentido in ["ida", "volta"]:
        for via in dados.get(sentido, []):
            if isinstance(via, str):
                v = via.strip()
                via_contextos.setdefault(v, []).append(f"{cod}/{sentido.upper()}")

# --- classifica cada via ---
exatas: list[tuple] = []          # (original)
expandidas: list[tuple] = []      # (original, expandido, ref_match)
novas: list[tuple] = []           # (original)

for via_orig, contextos in sorted(via_contextos.items()):
    norm = normalizar(via_orig)

    # 1. match exato
    if norm in ref_norm:
        exatas.append((via_orig, ref_norm[norm], contextos))
        continue

    # 2. tenta expandir
    expandido = expandir(via_orig)
    norm_exp  = normalizar(expandido)
    if norm_exp in ref_norm:
        expandidas.append((via_orig, ref_norm[norm_exp], contextos))
        continue

    # 3. via nova
    novas.append((via_orig, contextos))

# --- escreve relatório ---
with SAIDA.open("w", encoding="utf-8") as f:

    def w(linha=""):
        f.write(linha + "\n")

    w("=" * 80)
    w("RELATÓRIO — EXPANSÃO DE ABREVIAÇÕES")
    w("Fonte nova : intinerario-vias-novos.json")
    w("Referência : itinerario_completo.json")
    w("=" * 80)
    w()
    w(f"  Total de vias únicas no novo  : {len(via_contextos)}")
    w(f"  Match exato                   : {len(exatas)}")
    w(f"  Expandidas com match          : {len(expandidas)}")
    w(f"  Vias novas (sem match)        : {len(novas)}")
    w()

    # --- MATCH EXATO ---
    w("=" * 80)
    w(f"[ 1. MATCH EXATO ]  {len(exatas)} vias  (já estão corretas)")
    w("-" * 80)
    for orig, ref, ctx in sorted(exatas):
        w(f"  {orig}")
    w()

    # --- EXPANDIDAS ---
    w("=" * 80)
    w(f"[ 2. EXPANDIDAS COM MATCH NA REFERÊNCIA ]  {len(expandidas)} vias")
    w("  Estas abreviações podem ser substituídas automaticamente.")
    w("-" * 80)
    w(f"  {'ABREVIADO':<50}  NOME COMPLETO (referência)")
    w(f"  {'-'*49}  {'-'*40}")
    for orig, ref, ctx in sorted(expandidas):
        linhas_str = ", ".join(ctx[:4]) + ("..." if len(ctx) > 4 else "")
        w(f"  {orig:<50}  {ref}")
        w(f"  {'':50}  [{linhas_str}]")
    w()

    # --- VIAS NOVAS ---
    w("=" * 80)
    w(f"[ 3. VIAS NOVAS (sem match mesmo após expansão) ]  {len(novas)} vias")
    w("  Estas vias não existem no itinerario_completo.json.")
    w("  Podem ser: ruas de fato novas, erros de digitação, ou variantes de nome.")
    w("-" * 80)
    for orig, ctx in sorted(novas):
        linhas_str = ", ".join(ctx[:4]) + ("..." if len(ctx) > 4 else "")
        w(f"  {orig}")
        w(f"    [{linhas_str}]")
    w()

    w("-" * 80)
    w("Gerado por python/gerar_relatorio_expansao_vias.py")

print(f"[OK] {SAIDA}")
print(f"  Match exato   : {len(exatas)}")
print(f"  Expandidas    : {len(expandidas)}")
print(f"  Vias novas    : {len(novas)}")
