"""
Gera data/vias-por-bairro/relatorio_duplicatas.txt
Lista todas as vias com o mesmo código mas nomes diferentes.
"""

import json
import unicodedata
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE   = Path(__file__).resolve().parents[1]
PATH   = BASE / "data/vias-por-bairro/vias_por_bairro.json"
SAIDA  = BASE / "data/vias-por-bairro/relatorio_duplicatas.txt"

dados  = json.loads(PATH.read_text("utf-8"))

# ── monta: codigo → [{via, bairro}]  ─────────────────────────────────────────
codigo_entries: dict[str, list] = defaultdict(list)
for bairro, vias in dados.items():
    if bairro == "DUPLICATAS":
        continue
    for item in vias:
        c = item.get("codigo")
        if c:
            codigo_entries[c].append({"via": item["via"], "bairro": bairro})

# Apenas os que têm nomes distintos
dups = {
    c: entries
    for c, entries in sorted(codigo_entries.items())
    if len({e["via"] for e in entries}) > 1
}


# ── classifica o tipo de diferença ───────────────────────────────────────────
def sem_acento(txt):
    txt = unicodedata.normalize("NFD", txt.upper())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9 ]", " ", txt).strip()

def tipo_diferenca(nomes):
    norms = [sem_acento(n) for n in nomes]
    if len(set(norms)) == 1:
        return "ACENTO"          # apenas diferença de acentuação
    # verifica se um é prefixo do outro (complemento)
    sorted_norms = sorted(norms, key=len)
    if all(n.startswith(sorted_norms[0]) for n in sorted_norms):
        return "COMPLEMENTO"     # um tem complemento e outro não
    return "NOME DIFERENTE"      # nomes realmente distintos


# ── contagens por tipo ────────────────────────────────────────────────────────
contagem = {"ACENTO": 0, "COMPLEMENTO": 0, "NOME DIFERENTE": 0}
for c, entries in dups.items():
    nomes = list({e["via"] for e in entries})
    contagem[tipo_diferenca(nomes)] += 1


# ── escreve relatório ─────────────────────────────────────────────────────────
with SAIDA.open("w", encoding="utf-8") as f:
    def w(linha=""):
        f.write(linha + "\n")

    w("=" * 80)
    w("RELATÓRIO — VIAS COM CÓDIGO DUPLICADO")
    w(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    w("=" * 80)
    w()
    w(f"  Total de códigos com nome duplicado : {len(dups)}")
    w(f"  ├─ Diferença de acento              : {contagem['ACENTO']}")
    w(f"  ├─ Um tem complemento, outro não    : {contagem['COMPLEMENTO']}")
    w(f"  └─ Nomes realmente diferentes       : {contagem['NOME DIFERENTE']}")
    w()

    for tipo_label, tipo_key in [
        ("[ DIFERENÇA DE ACENTO ]",        "ACENTO"),
        ("[ COMPLEMENTO / SUFIXO ]",       "COMPLEMENTO"),
        ("[ NOMES REALMENTE DIFERENTES ]", "NOME DIFERENTE"),
    ]:
        grupo = {c: e for c, e in dups.items()
                 if tipo_diferenca(list({x["via"] for x in e})) == tipo_key}
        if not grupo:
            continue

        w("=" * 80)
        w(f"{tipo_label}  —  {len(grupo)} códigos")
        w("=" * 80)
        w()

        for codigo, entries in grupo.items():
            nomes_distintos = sorted({e["via"] for e in entries})
            bairro = entries[0]["bairro"]

            w(f"  Código {codigo}  [{bairro}]")
            for nome in nomes_distintos:
                w(f"    • {nome}")
            w()

    w("-" * 80)
    w("Gerado por python/gerar_relatorio_duplicatas.py")

print(f"[OK] {SAIDA.name}")
print(f"  {len(dups)} duplicatas  —  ACENTO:{contagem['ACENTO']}  "
      f"COMPLEMENTO:{contagem['COMPLEMENTO']}  NOME_DIFERENTE:{contagem['NOME DIFERENTE']}")
