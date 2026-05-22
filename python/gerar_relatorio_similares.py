"""
Gera relatório aprimorado de nomes similares com sugestão de código DMTT.

Para cada par de vias com grafia parecida:
  - Mostra os códigos de cada uma
  - Cruza com dicionario_ruas.json para mostrar o nome canônico DMTT
  - Classifica o par:
      [MESMO CÓDIGO]     → definitivamente a mesma rua, grafia diferente
      [SUGERIR CÓDIGO]   → uma tem código, outra não → sugestão automática
      [VERIFICAR]        → ambas têm códigos diferentes → podem ser ruas distintas
      [SEM CÓDIGO]       → nenhuma tem código → buscar no cadastro DMTT
  - Ordena por prioridade de ação

Saída: data/relatorios/nomes_similares_possiveis_duplicatas.txt

Uso:
    python python/gerar_relatorio_similares.py
"""

import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
UNIFICADO_PATH  = BASE_DIR / "data" / "json" / "dados_unificados.json"
DICIONARIO_PATH = BASE_DIR / "data" / "vias-normalizadas" / "dicionario_ruas.json"
SAIDA_PATH      = BASE_DIR / "data" / "relatorios" / "nomes_similares_possiveis_duplicatas.txt"

SIMILARITY_THRESHOLD = 0.82
MIN_CORE_LEN = 5


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.upper().strip()
    t = re.sub(r"[^A-Z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


PREFIX_WORDS = {
    "AVENIDA", "RUA", "TRAVESSA", "TRAV", "ALAMEDA", "LADEIRA",
    "PRACA", "LARGO", "ESTRADA", "ESTR", "RODOVIA", "VIADUTO",
    "RETORNO", "TERMINAL", "ACESSO", "CONJ", "CONJUNTO",
    "LOTEAMENTO", "QUADRA", "QD", "VIA",
}


def core_name(s: str) -> str:
    words = s.split()
    while words and words[0] in PREFIX_WORDS:
        words.pop(0)
    return " ".join(words)


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def classify_pair(cod_a, cod_b):
    if cod_a and cod_b:
        if cod_a == cod_b:
            return "MESMO_CODIGO"
        else:
            return "CODIGOS_DIFERENTES"
    elif cod_a and not cod_b:
        return "SUGERIR_A_PARA_B"
    elif cod_b and not cod_a:
        return "SUGERIR_B_PARA_A"
    else:
        return "SEM_CODIGO"


# ---------------------------------------------------------------------------
# carrega dados
# ---------------------------------------------------------------------------

with UNIFICADO_PATH.open(encoding="utf-8") as f:
    unificado = json.load(f)

with DICIONARIO_PATH.open(encoding="utf-8") as f:
    dicionario_raw = json.load(f)

# monta dicionário: codigo → lista de nomes canônicos
codigo_to_nomes: dict[str, list[str]] = defaultdict(list)
# e também: norm_nome_limpo → codigo (para busca reversa por nome)
dic_norm_to_codigo: dict[str, str] = {}

for entry in dicionario_raw:
    raw = entry["nome"]
    if raw.upper().startswith("REVISAR:"):
        continue
    m = re.match(r"^(\d{5})\s*(.*)", raw)
    if not m:
        continue
    cod = m.group(1)
    nome_limpo = m.group(2).strip()
    # ignora variantes com " 0000" no final (duplicatas do sistema)
    if nome_limpo.endswith(" 0000"):
        nome_limpo = nome_limpo[:-5].strip()
    if nome_limpo and nome_limpo not in codigo_to_nomes[cod]:
        codigo_to_nomes[cod].append(nome_limpo)
    n = norm(nome_limpo)
    if n and n not in dic_norm_to_codigo:
        dic_norm_to_codigo[n] = cod


def nome_canonico(codigo: str) -> str:
    nomes = codigo_to_nomes.get(codigo, [])
    if not nomes:
        return "(não encontrado no dicionário)"
    return " / ".join(nomes[:2])


# ---------------------------------------------------------------------------
# extrai todas as vias do unificado (deduplicado)
# ---------------------------------------------------------------------------

all_ruas: dict[str, dict] = {}   # norm → {via, codigo, match, ocorrencias}
rua_por_linha: dict[str, list] = defaultdict(list)

for nome_linha, sentidos in unificado.items():
    for sentido in ("ida", "volta"):
        for r in sentidos.get(sentido, {}).get("ruas", []):
            via = r.get("via", "").strip()
            if not via:
                continue
            nv = norm(via)
            if nv not in all_ruas:
                all_ruas[nv] = {
                    "via": via,
                    "codigo": r.get("codigo"),
                    "match": r.get("match", ""),
                    "ocorrencias": 0,
                }
            else:
                if not all_ruas[nv]["codigo"] and r.get("codigo"):
                    all_ruas[nv]["codigo"] = r.get("codigo")
            all_ruas[nv]["ocorrencias"] += 1
            rua_por_linha[nv].append((nome_linha, sentido))


# ---------------------------------------------------------------------------
# compara todos os pares
# ---------------------------------------------------------------------------

cores = {nv: core_name(nv) for nv in all_ruas}
candidates = [nv for nv in all_ruas if len(cores[nv]) >= MIN_CORE_LEN]

pairs: list[dict] = []

for nv_a, nv_b in combinations(candidates, 2):
    ca, cb = cores[nv_a], cores[nv_b]
    tok_a = set(ca.split())
    tok_b = set(cb.split())
    if not tok_a.intersection(tok_b):
        continue
    score = similarity(nv_a, nv_b)
    if score < SIMILARITY_THRESHOLD or score >= 1.0:
        continue

    ea = all_ruas[nv_a]
    eb = all_ruas[nv_b]
    cod_a = ea["codigo"]
    cod_b = eb["codigo"]
    tipo = classify_pair(cod_a, cod_b)

    # tenta buscar código no dicionário por nome normalizado (para SEM_CODIGO)
    dic_cod_a = dic_norm_to_codigo.get(nv_a)
    dic_cod_b = dic_norm_to_codigo.get(nv_b)

    # determina motivo da similaridade
    if sorted(tok_a) == sorted(tok_b):
        motivo = "mesmas palavras, ordem diferente"
    elif tok_a.issubset(tok_b) or tok_b.issubset(tok_a):
        motivo = "uma contém a outra (possível abreviação)"
    elif abs(len(nv_a) - len(nv_b)) <= 4:
        motivo = "diferença minima de caracteres (possivel typo)"
    else:
        motivo = f"alta similaridade ({score:.0%})"

    pairs.append({
        "tipo": tipo,
        "score": score,
        "motivo": motivo,
        "via_a": ea["via"],
        "via_b": eb["via"],
        "nv_a": nv_a,
        "nv_b": nv_b,
        "cod_a": cod_a,
        "cod_b": cod_b,
        "dic_cod_a": dic_cod_a,
        "dic_cod_b": dic_cod_b,
        "ocorr_a": ea["ocorrencias"],
        "ocorr_b": eb["ocorrencias"],
    })

# ---------------------------------------------------------------------------
# ordena: SUGERIR primeiro (mais acionável), depois MESMO_CODIGO,
# depois CODIGOS_DIFERENTES, depois SEM_CODIGO; dentro de cada grupo por score
# ---------------------------------------------------------------------------

PRIORIDADE = {
    "SUGERIR_A_PARA_B": 0,
    "SUGERIR_B_PARA_A": 1,
    "MESMO_CODIGO": 2,
    "CODIGOS_DIFERENTES": 3,
    "SEM_CODIGO": 4,
}

pairs.sort(key=lambda p: (PRIORIDADE[p["tipo"]], -p["score"]))

# ---------------------------------------------------------------------------
# agrupa por tipo para o relatório
# ---------------------------------------------------------------------------

grupos = {k: [] for k in PRIORIDADE}
for p in pairs:
    grupos[p["tipo"]].append(p)

# ---------------------------------------------------------------------------
# escreve relatório
# ---------------------------------------------------------------------------

def linhas_str(nv, limit=4):
    ls = rua_por_linha[nv]
    res = "; ".join(f"{l} ({s})" for l, s in ls[:limit])
    if len(ls) > limit:
        res += f" ... (+{len(ls)-limit})"
    return res


def fmt_pair_block(p, acao=""):
    lines = []
    lines.append(f"  Similaridade : {p['score']:.1%}  [{p['motivo']}]")
    if acao:
        lines.append(f"  ACAO         : {acao}")
    lines.append(f"  Via A : {p['via_a']}")
    cod_a_str = p["cod_a"] if p["cod_a"] else "(sem codigo)"
    lines.append(f"          codigo={cod_a_str}  ocorrencias={p['ocorr_a']}")
    if p["cod_a"]:
        lines.append(f"          nome DMTT: {nome_canonico(p['cod_a'])}")
    elif p["dic_cod_a"]:
        lines.append(f"          encontrado no dicionario como cod {p['dic_cod_a']}: {nome_canonico(p['dic_cod_a'])}")
    lines.append(f"  Via B : {p['via_b']}")
    cod_b_str = p["cod_b"] if p["cod_b"] else "(sem codigo)"
    lines.append(f"          codigo={cod_b_str}  ocorrencias={p['ocorr_b']}")
    if p["cod_b"]:
        lines.append(f"          nome DMTT: {nome_canonico(p['cod_b'])}")
    elif p["dic_cod_b"]:
        lines.append(f"          encontrado no dicionario como cod {p['dic_cod_b']}: {nome_canonico(p['dic_cod_b'])}")
    return "\n".join(lines)


with SAIDA_PATH.open("w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("RELATORIO — NOMES SIMILARES COM SUGESTAO DE CODIGO DMTT\n")
    f.write("=" * 80 + "\n\n")
    f.write(
        f"Total de pares suspeitos : {len(pairs)}\n"
        f"Limiar de similaridade   : {SIMILARITY_THRESHOLD:.0%}\n\n"
    )
    f.write("LEGENDA DAS SECOES:\n")
    f.write("  [SUGERIR CODIGO]    uma via tem codigo, a outra nao -> atribuir o mesmo\n")
    f.write("  [MESMO CODIGO]      ambas ja tem o mesmo codigo -> corrigir a grafia\n")
    f.write("  [CODIGOS DIFERENTES] ambas tem codigos distintos -> ruas distintas ou erro\n")
    f.write("  [SEM CODIGO]        nenhuma tem codigo -> buscar no cadastro DMTT\n\n")
    f.write("=" * 80 + "\n\n")

    # --- SUGERIR CODIGO ---
    sugerir = grupos["SUGERIR_A_PARA_B"] + grupos["SUGERIR_B_PARA_A"]
    f.write(f"[SUGERIR CODIGO]  {len(sugerir)} pares  ← MAIS ACIONAVEIS\n")
    f.write("-" * 80 + "\n\n")
    f.write(
        "Uma das vias ja tem codigo DMTT. A outra parece ser a mesma rua\n"
        "escrita de forma diferente. Verifique e, se confirmar, aplique o codigo.\n\n"
    )
    for p in sugerir:
        if p["tipo"] == "SUGERIR_A_PARA_B":
            acao = f"Atribuir codigo {p['cod_a']} ({nome_canonico(p['cod_a'])}) para \"{p['via_b']}\""
        else:
            acao = f"Atribuir codigo {p['cod_b']} ({nome_canonico(p['cod_b'])}) para \"{p['via_a']}\""
        f.write(fmt_pair_block(p, acao) + "\n\n")

    # --- MESMO CODIGO ---
    f.write("\n" + "=" * 80 + "\n")
    f.write(f"[MESMO CODIGO]  {len(grupos['MESMO_CODIGO'])} pares\n")
    f.write("-" * 80 + "\n\n")
    f.write(
        "Ambas as vias ja possuem o MESMO codigo DMTT — sao definitivamente\n"
        "o mesmo logradouro escrito de duas formas. Padronizar a grafia no itinerario.\n\n"
    )
    for p in grupos["MESMO_CODIGO"]:
        acao = (
            f"Padronizar grafia para o nome canônico DMTT: {nome_canonico(p['cod_a'])}\n"
            f"          (ambas usam codigo {p['cod_a']})"
        )
        f.write(fmt_pair_block(p, acao) + "\n\n")

    # --- CODIGOS DIFERENTES ---
    f.write("\n" + "=" * 80 + "\n")
    f.write(f"[CODIGOS DIFERENTES]  {len(grupos['CODIGOS_DIFERENTES'])} pares\n")
    f.write("-" * 80 + "\n\n")
    f.write(
        "Ambas tem codigos DMTT distintos. Podem ser ruas realmente diferentes\n"
        "com nomes parecidos, OU um dos codigos esta errado. Requer verificacao manual.\n\n"
    )
    for p in grupos["CODIGOS_DIFERENTES"]:
        acao = f"Verificar: cod {p['cod_a']} ({nome_canonico(p['cod_a'])}) vs cod {p['cod_b']} ({nome_canonico(p['cod_b'])})"
        f.write(fmt_pair_block(p, acao) + "\n\n")

    # --- SEM CODIGO ---
    f.write("\n" + "=" * 80 + "\n")
    f.write(f"[SEM CODIGO]  {len(grupos['SEM_CODIGO'])} pares\n")
    f.write("-" * 80 + "\n\n")
    f.write(
        "Nenhuma das duas tem codigo. Verificar se aparecem no dicionario_ruas.json\n"
        "com outra grafia, ou buscar no cadastro DMTT.\n\n"
    )
    for p in grupos["SEM_CODIGO"]:
        dic_hint = ""
        if p["dic_cod_a"]:
            dic_hint = f"Via A encontrada no dicionario: cod {p['dic_cod_a']} ({nome_canonico(p['dic_cod_a'])})"
        elif p["dic_cod_b"]:
            dic_hint = f"Via B encontrada no dicionario: cod {p['dic_cod_b']} ({nome_canonico(p['dic_cod_b'])})"
        f.write(fmt_pair_block(p, dic_hint or "Buscar codigo no cadastro DMTT") + "\n\n")

    f.write("-" * 80 + "\n")
    f.write("Gerado por python/gerar_relatorio_similares.py\n")

print(f"[OK] {len(pairs)} pares -> {SAIDA_PATH}")
print(f"  SUGERIR CODIGO    : {len(sugerir)}")
print(f"  MESMO CODIGO      : {len(grupos['MESMO_CODIGO'])}")
print(f"  CODIGOS DIFERENTES: {len(grupos['CODIGOS_DIFERENTES'])}")
print(f"  SEM CODIGO        : {len(grupos['SEM_CODIGO'])}")
