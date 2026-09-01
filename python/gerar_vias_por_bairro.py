"""
Gera data/json/vias_por_bairro.json

1. Parseia o PDF "relatorio_via por bairro.pdf" → {codigo: bairro}
2. Cruza com dados_unificados.json usando o campo "codigo" de cada rua
3. Agrupa vias únicas por bairro (ordem alfabética)
4. Ao final: grupo "SEM CODIGO" com vias que têm codigo=null ou
   cujo código não aparece no PDF

Saída:
{
  "ANTARES": [{"via": "...", "codigo": "00270"}, ...],
  ...
  "SEM CODIGO": [{"via": "...", "codigo": null}, ...]
}
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pdfplumber

BASE     = Path(__file__).resolve().parents[1]
PDF_PATH = BASE / "data/vias-por-bairro/relatorio_via por bairro.pdf"
DU_PATH  = BASE / "data/json/dados_unificados.json"
OUT_PATH = BASE / "data/json/vias_por_bairro.json"

# ── 1. Parsear PDF → {codigo: bairro} ────────────────────────────────────────

# "ALTO DA ALEGRIA 00748 RUA EM PROJETO ... 0000 0001"
# bairro = tudo antes do primeiro codigo de 5 digitos (nao exige mais os dois
# grupos de 4 digitos finais no fim da linha -- fragil, falhava silenciosamente
# quando a extracao do PDF perdia/alterava espacamento no fim da linha)
RE_BAIRRO = re.compile(r"^([^\d]+?)\s+(\d{5})\s+(.*)$")
# "00749 RUA EM PROJETO ... 0000 0001"
RE_ENTRY = re.compile(r"^(\d{5})\s+(.*)$")

SKIP = re.compile(r"^(Sub-Total|Bairro|P.gina|\d{2}/\d{2}/\d{4}|N.*Inicial|VIAS POR BAIRRO|ViaPorBairro|\d{2}:\d{2}:\d{2}$|TOTAL:)")

# a fonte embutida no PDF da DMTT nao tem ToUnicode CMap valido pra algumas
# letras acentuadas -- pdfplumber (e qualquer lib de extracao estrutural)
# devolve U+FFFD nelas. Corrigido a mao, conferido letra a letra contra a
# leitura visual do PDF (Read tool renderiza certo, so a extracao de texto erra).
CORRECAO_BAIRRO = {
    "CANA�": "CANAÃ",
    "CH� DA JAQUEIRA": "CHÃ DA JAQUEIRA",
    "CH� DE BEBEDOURO": "CHÃ DE BEBEDOURO",
    "FERN�O VELHO": "FERNÃO VELHO",
    "GAR�A TORTA": "GARÇA TORTA",
    "JARAGU�": "JARAGUÁ",
    "JATI�CA": "JATIÚCA",
    "PAJU�ARA": "PAJUÇARA",
    "PO�O": "POÇO",
    "SANTA AM�LIA": "SANTA AMÉLIA",
    "SANTA L�CIA": "SANTA LÚCIA",
    "S�O JORGE": "SÃO JORGE",
}

codigo_bairro: dict[str, str] = {}   # "00270" → "ANTARES"

with pdfplumber.open(PDF_PATH) as pdf:
    bairro_atual = ""
    for page in pdf.pages:
        texto = page.extract_text() or ""
        for linha in texto.splitlines():
            linha = linha.strip()
            if not linha or SKIP.match(linha):
                continue

            # Linha que começa direto com 5 dígitos → entry do bairro atual
            m = RE_ENTRY.match(linha)
            if m:
                if bairro_atual:
                    codigo_bairro[m.group(1)] = bairro_atual
                continue

            # Linha que começa com texto de bairro + código
            m = RE_BAIRRO.match(linha)
            if m:
                bairro_atual = CORRECAO_BAIRRO.get(m.group(1).strip(), m.group(1).strip())
                codigo_bairro[m.group(2)] = bairro_atual

print(f"[PDF] {len(codigo_bairro)} codigos mapeados para {len(set(codigo_bairro.values()))} bairros")

# ── 2. Coletar vias únicas de dados_unificados ────────────────────────────────

du = json.loads(DU_PATH.read_text("utf-8"))

# via_unica: via (str) → codigo (str|None) — pega primeiro codigo encontrado
via_info: dict[str, str | None] = {}

for linha, dados in du.items():
    for sentido in ["ida", "volta"]:
        for r in dados.get(sentido, {}).get("ruas", []):
            via = r.get("via", "").strip()
            cod = r.get("codigo")
            if via and via not in via_info:
                via_info[via] = cod
            # se já existe mas sem código e agora tem, atualiza
            elif via and via_info[via] is None and cod:
                via_info[via] = cod

print(f"[DU]  {len(via_info)} vias únicas")

# ── 3. Agrupar por bairro ─────────────────────────────────────────────────────

bairros: dict[str, list[dict]] = defaultdict(list)
sem_codigo: list[dict] = []

for via, codigo in sorted(via_info.items()):
    if not codigo:
        sem_codigo.append({"via": via, "codigo": None})
        continue

    bairro = codigo_bairro.get(codigo)
    if bairro:
        bairros[bairro].append({"via": via, "codigo": codigo})
    else:
        # código existe mas não está no PDF
        sem_codigo.append({"via": via, "codigo": codigo})

# Ordena por nome de bairro e dentro do bairro por via
resultado = {}
for bairro in sorted(bairros.keys()):
    resultado[bairro] = sorted(bairros[bairro], key=lambda x: x["via"])

resultado["SEM CODIGO"] = sorted(sem_codigo, key=lambda x: x["via"])

# ── 4. Salvar ─────────────────────────────────────────────────────────────────

OUT_PATH.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

# Resumo
total_com_bairro = sum(len(v) for k, v in resultado.items() if k != "SEM CODIGO")
print(f"\n[OK] {OUT_PATH.name}")
print(f"  Bairros          : {len(resultado) - 1}")
print(f"  Vias com bairro  : {total_com_bairro}")
print(f"  SEM CODIGO       : {len(resultado['SEM CODIGO'])}")
print(f"\nTop bairros por qtd de vias:")
for b, vias in sorted(resultado.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"  {len(vias):>3}  {b}")
