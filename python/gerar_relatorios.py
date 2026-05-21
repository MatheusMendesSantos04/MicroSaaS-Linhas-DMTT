"""
Gera 3 relatórios de qualidade dos dados em data/relatorios/:
  1. ruas_sem_codigo_e_sem_dicionario.txt  — vias sem código DMTT e ausentes no dicionário
  2. nomes_similares_possiveis_duplicatas.txt — pares com grafia parecida (possíveis erros)
  3. atencao_geral.txt                      — diagnóstico geral de problemas detectados

Uso:
    python python/gerar_relatorios.py
"""

import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

UNIFICADO_PATH = BASE_DIR / "data" / "json" / "dados_unificados.json"
DICIONARIO_PATH = BASE_DIR / "data" / "vias-normalizadas" / "dicionario_ruas.json"
RELATORIOS_DIR = BASE_DIR / "data" / "relatorios"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.upper().strip()
    t = re.sub(r"[^A-Z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def strip_prefix(nome: str) -> str:
    """Remove código numérico no início de entradas do dicionário."""
    return re.sub(r"^\d{5}\s*", "", nome).strip()


def tokens(s: str) -> set:
    return set(s.split())


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


PREFIX_WORDS = {"AVENIDA", "RUA", "TRAVESSA", "TRAV", "TRAVESSA", "ALAMEDA",
                "LADEIRA", "PRAÇA", "LARGO", "ESTRADA", "ESTR", "RODOVIA",
                "VIADUTO", "RETORNO", "TERMINAL", "ACESSO", "CONJ",
                "CONJUNTO", "LOTEAMENTO", "QUADRA", "QD"}


def core_name(s: str) -> str:
    """Remove palavras de prefixo para comparação do nome em si."""
    words = s.split()
    while words and words[0] in PREFIX_WORDS:
        words.pop(0)
    return " ".join(words)


# ---------------------------------------------------------------------------
# carrega dados
# ---------------------------------------------------------------------------

with UNIFICADO_PATH.open(encoding="utf-8") as f:
    unificado = json.load(f)

with DICIONARIO_PATH.open(encoding="utf-8") as f:
    dicionario_raw = json.load(f)

# dicionário normalizado: norm(nome_sem_codigo) → entrada original
dic_norms: dict[str, str] = {}
for entry in dicionario_raw:
    raw_nome = entry["nome"]
    # ignora entradas "REVISAR:" — ainda não têm código oficial
    if raw_nome.upper().startswith("REVISAR:"):
        continue
    nome_limpo = strip_prefix(raw_nome)
    dic_norms[norm(nome_limpo)] = raw_nome

# conjunto de códigos válidos do dicionário (para cruzar)
dic_codigos: set[str] = set()
for entry in dicionario_raw:
    raw_nome = entry["nome"]
    if raw_nome.upper().startswith("REVISAR:"):
        continue
    m = re.match(r"^(\d{5})", raw_nome)
    if m:
        dic_codigos.add(m.group(1))

# ---------------------------------------------------------------------------
# extrai todas as ruas do unificado
# ---------------------------------------------------------------------------

# rua_entry: { norm_via, via_original, codigo, match, linhas_afetadas, sentidos }
RuaEntry = dict

all_ruas: dict[str, RuaEntry] = {}      # norm_via → entry (deduplicado)
rua_por_linha: dict[str, list] = defaultdict(list)  # norm_via → [(linha, sentido)]

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
                # mantém código se ainda não tiver
                if not all_ruas[nv]["codigo"] and r.get("codigo"):
                    all_ruas[nv]["codigo"] = r.get("codigo")
            all_ruas[nv]["ocorrencias"] += 1
            rua_por_linha[nv].append((nome_linha, sentido))

# ---------------------------------------------------------------------------
# RELATÓRIO 1 — sem código E sem dicionário
# ---------------------------------------------------------------------------

sem_codigo = {nv: e for nv, e in all_ruas.items() if not e["codigo"]}

# separa: está no dicionário (por nome) vs completamente ausente
sem_codigo_e_sem_dic: list[tuple] = []   # (via, ocorrencias, linhas)
sem_codigo_mas_no_dic: list[tuple] = []  # (via, ocorrencias, entrada_dic)

for nv, e in sorted(sem_codigo.items(), key=lambda x: -x[1]["ocorrencias"]):
    linhas = rua_por_linha[nv]
    if nv in dic_norms:
        sem_codigo_mas_no_dic.append((e["via"], e["ocorrencias"], dic_norms[nv]))
    else:
        sem_codigo_e_sem_dic.append((e["via"], e["ocorrencias"], linhas))

r1_path = RELATORIOS_DIR / "ruas_sem_codigo_e_sem_dicionario.txt"
with r1_path.open("w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO 1 — RUAS SEM CÓDIGO DMTT E AUSENTES NO DICIONÁRIO\n")
    f.write("=" * 80 + "\n\n")
    f.write(
        "Estas vias aparecem nos itinerários mas NÃO possuem código DMTT\n"
        "e NÃO foram encontradas em dicionario_ruas.json.\n"
        "São as que exigem maior atenção: precisam ser identificadas e\n"
        "cadastradas no sistema DMTT ou corrigidas no itinerário.\n\n"
    )
    f.write(f"Total: {len(sem_codigo_e_sem_dic)} vias\n\n")
    f.write("-" * 80 + "\n\n")

    for via, ocorr, linhas in sem_codigo_e_sem_dic:
        linhas_str = "; ".join(f"{l} ({s})" for l, s in linhas[:5])
        if len(linhas) > 5:
            linhas_str += f" ... (+{len(linhas)-5})"
        f.write(f"  Via        : {via}\n")
        f.write(f"  Ocorrências: {ocorr}\n")
        f.write(f"  Linhas     : {linhas_str}\n\n")

    f.write("\n" + "=" * 80 + "\n")
    f.write("COMPLEMENTO — SEM CÓDIGO MAS PRESENTE NO DICIONÁRIO\n")
    f.write("=" * 80 + "\n\n")
    f.write(
        "Estas vias não têm código no itinerário, mas o nome existe no\n"
        "dicionario_ruas.json — provavelmente o código pode ser preenchido.\n\n"
    )
    f.write(f"Total: {len(sem_codigo_mas_no_dic)} vias\n\n")
    f.write("-" * 80 + "\n\n")
    for via, ocorr, dic_entrada in sem_codigo_mas_no_dic:
        f.write(f"  Via no itinerário : {via}\n")
        f.write(f"  No dicionário     : {dic_entrada}\n")
        f.write(f"  Ocorrências       : {ocorr}\n\n")

print(f"[OK] Relatorio 1 -> {r1_path.name}")

# ---------------------------------------------------------------------------
# RELATÓRIO 2 — nomes similares / possíveis duplicatas
# ---------------------------------------------------------------------------

unique_vias = list(all_ruas.keys())  # list of norm strings

SIMILARITY_THRESHOLD = 0.82
MIN_CORE_LEN = 5   # ignora nomes muito curtos (ex: "RUA A", "RUA H")

suspicious_pairs: list[tuple] = []   # (nv_a, nv_b, score, motivo)

# agrupa por primeiro token do core para reduzir combinações
from itertools import combinations

cores = {nv: core_name(nv) for nv in unique_vias}

# compara apenas pares com core não-vazio e tamanho mínimo
candidates = [nv for nv in unique_vias if len(cores[nv]) >= MIN_CORE_LEN]

for a, b in combinations(candidates, 2):
    ca, cb = cores[a], cores[b]
    if a == b:
        continue
    # pré-filtro rápido: primeiro token do core igual (mesmo sobrenome/palavra-chave)
    tok_a = set(ca.split())
    tok_b = set(cb.split())
    if not tok_a.intersection(tok_b):
        continue
    score = similarity(a, b)
    if score >= SIMILARITY_THRESHOLD and score < 1.0:
        # determina provável motivo
        motivo = ""
        if sorted(tok_a) == sorted(tok_b) and tok_a != tok_b:
            motivo = "mesmas palavras, ordem diferente"
        elif abs(len(a) - len(b)) <= 3:
            motivo = "diferença mínima de caracteres (possível typo)"
        elif tok_a.issubset(tok_b) or tok_b.issubset(tok_a):
            motivo = "uma contém a outra (possível abreviação)"
        else:
            motivo = f"similaridade alta ({score:.0%})"
        suspicious_pairs.append((
            all_ruas[a]["via"], all_ruas[b]["via"],
            all_ruas[a]["codigo"], all_ruas[b]["codigo"],
            score, motivo
        ))

# ordena por score desc
suspicious_pairs.sort(key=lambda x: -x[4])

r2_path = RELATORIOS_DIR / "nomes_similares_possiveis_duplicatas.txt"
with r2_path.open("w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO 2 — NOMES SIMILARES / POSSÍVEIS DUPLICATAS\n")
    f.write("=" * 80 + "\n\n")
    f.write(
        "Pares de vias com grafia parecida. Podem ser:\n"
        "  - O mesmo logradouro escrito de formas diferentes\n"
        "  - Abreviações vs. nome completo\n"
        "  - Erros de digitação\n\n"
        "Para cada par é exibido o código DMTT (se houver) — se os dois\n"
        "tiverem códigos DIFERENTES, podem realmente ser ruas distintas.\n"
        "Se um tiver código e o outro não, o sem código pode ser corrigido.\n\n"
    )
    f.write(f"Total de pares suspeitos: {len(suspicious_pairs)}\n")
    f.write(f"Limiar de similaridade  : {SIMILARITY_THRESHOLD:.0%}\n\n")
    f.write("-" * 80 + "\n\n")

    for via_a, via_b, cod_a, cod_b, score, motivo in suspicious_pairs:
        cod_a_str = cod_a if cod_a else "(sem código)"
        cod_b_str = cod_b if cod_b else "(sem código)"
        f.write(f"  Similaridade : {score:.1%}  [{motivo}]\n")
        f.write(f"  Via A : {via_a}  [cód. {cod_a_str}]\n")
        f.write(f"  Via B : {via_b}  [cód. {cod_b_str}]\n\n")

print(f"[OK] Relatorio 2 -> {r2_path.name}")

# ---------------------------------------------------------------------------
# RELATÓRIO 3 — atenção geral
# ---------------------------------------------------------------------------

# coleta dados para o relatório
total_ruas_unicas = len(all_ruas)
total_com_codigo = sum(1 for e in all_ruas.values() if e["codigo"])
total_sem_codigo = total_ruas_unicas - total_com_codigo
total_sem_codigo_sem_dic = len(sem_codigo_e_sem_dic)
total_sem_codigo_com_dic = len(sem_codigo_mas_no_dic)

# match quality distribution
match_counter: dict[str, int] = defaultdict(int)
for _, sentidos in unificado.items():
    for sentido in ("ida", "volta"):
        for r in sentidos.get(sentido, {}).get("ruas", []):
            match_counter[r.get("match", "desconhecido")] += 1

total_entradas = sum(match_counter.values())

# linhas sem coordenadas
linhas_sem_ida_coord = [n for n, s in unificado.items() if not s.get("ida", {}).get("coordenadas")]
linhas_sem_volta_coord = [n for n, s in unificado.items() if not s.get("volta", {}).get("coordenadas")]

# linhas com anotações suspeitas no nome
linhas_suspeitas = [n for n in unificado if any(kw in n.upper() for kw in ["FALTA", "PRECISA", "REVISAR", "TODO", "FIXME"])]

# ruas com código que NÃO existe no dicionário (código inválido?)
codigos_invalidos: list[tuple] = []
for nv, e in all_ruas.items():
    if e["codigo"] and e["codigo"] not in dic_codigos:
        codigos_invalidos.append((e["via"], e["codigo"], all_ruas[nv]["ocorrencias"]))
codigos_invalidos.sort(key=lambda x: -x[2])

# ruas com match "nao_encontrado"
nao_encontrado = {nv: e for nv, e in all_ruas.items() if e["match"] == "nao_encontrado"}

r3_path = RELATORIOS_DIR / "atencao_geral.txt"
with r3_path.open("w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO 3 — DIAGNÓSTICO GERAL DE QUALIDADE DOS DADOS\n")
    f.write("=" * 80 + "\n\n")

    # --- resumo executivo ---
    f.write("[ RESUMO EXECUTIVO ]\n\n")
    f.write(f"  Linhas no sistema         : {len(unificado)}\n")
    f.write(f"  Vias únicas indexadas      : {total_ruas_unicas}\n")
    f.write(f"  Vias com código DMTT       : {total_com_codigo} ({total_com_codigo/total_ruas_unicas:.0%})\n")
    f.write(f"  Vias sem código            : {total_sem_codigo} ({total_sem_codigo/total_ruas_unicas:.0%})\n")
    f.write(f"    → Sem código + sem dic   : {total_sem_codigo_sem_dic}  ← MAIOR PRIORIDADE\n")
    f.write(f"    → Sem código + no dic    : {total_sem_codigo_com_dic}  ← código pode ser preenchido\n")
    f.write(f"  Pares com grafia suspeita  : {len(suspicious_pairs)}\n")
    f.write(f"  Linhas sem coord. IDA      : {len(linhas_sem_ida_coord)}\n")
    f.write(f"  Linhas sem coord. VOLTA    : {len(linhas_sem_volta_coord)}\n")
    f.write(f"  Linhas com anotações       : {len(linhas_suspeitas)}\n\n")

    # --- qualidade dos matches ---
    f.write("-" * 80 + "\n")
    f.write("[ QUALIDADE DOS MATCHES (como os itinerários foram vinculados ao cadastro) ]\n\n")
    for match_tipo, cnt in sorted(match_counter.items(), key=lambda x: -x[1]):
        pct = cnt / total_entradas * 100
        barra = "█" * int(pct / 2)
        f.write(f"  {match_tipo:<28} {cnt:>5} ({pct:>5.1f}%)  {barra}\n")
    f.write(f"\n  Total de entradas de itinerário: {total_entradas}\n\n")
    f.write(
        "  OBS: 'exato' e 'exato_global' = alta confiança.\n"
        "       'fuzzy' e 'contem' = precisa verificação humana.\n"
        "       'nao_encontrado' = código não achado no cadastro DMTT.\n\n"
    )

    # --- match nao_encontrado ---
    if nao_encontrado:
        f.write("-" * 80 + "\n")
        f.write("[ VIAS COM match='nao_encontrado' — CÓDIGO NÃO VALIDADO ]\n\n")
        f.write(
            "  O script de geração encontrou um código no PDF mas não conseguiu\n"
            "  confirmar no cadastro. Pode ser código digitado errado no PDF.\n\n"
        )
        for nv, e in sorted(nao_encontrado.items(), key=lambda x: -x[1]["ocorrencias"])[:30]:
            linhas = "; ".join(f"{l} ({s})" for l, s in rua_por_linha[nv][:3])
            f.write(f"  {e['via']} [cód. {e['codigo']}]  — {linhas}\n")
        if len(nao_encontrado) > 30:
            f.write(f"  ... e mais {len(nao_encontrado)-30} vias\n")
        f.write("\n")

    # --- códigos não presentes no dicionário ---
    if codigos_invalidos:
        f.write("-" * 80 + "\n")
        f.write("[ CÓDIGOS DO ITINERÁRIO QUE NÃO EXISTEM NO DICIONÁRIO ]\n\n")
        f.write(
            "  Estas vias têm um código preenchido, mas esse código não aparece\n"
            "  no dicionario_ruas.json. Pode ser código incorreto ou via nova\n"
            "  ainda não cadastrada.\n\n"
        )
        for via, cod, ocorr in codigos_invalidos[:40]:
            f.write(f"  {via:<50}  cód: {cod}  ({ocorr}x)\n")
        if len(codigos_invalidos) > 40:
            f.write(f"  ... e mais {len(codigos_invalidos)-40}\n")
        f.write("\n")

    # --- linhas sem coordenadas ---
    if linhas_sem_ida_coord or linhas_sem_volta_coord:
        f.write("-" * 80 + "\n")
        f.write("[ LINHAS SEM COORDENADAS GPS ]\n\n")
        f.write("  Essas linhas não aparecem no mapa (traçado vazio).\n\n")
        if linhas_sem_ida_coord:
            f.write("  Sem IDA:\n")
            for n in linhas_sem_ida_coord:
                f.write(f"    - {n}\n")
        if linhas_sem_volta_coord:
            f.write("\n  Sem VOLTA:\n")
            for n in linhas_sem_volta_coord:
                f.write(f"    - {n}\n")
        f.write("\n")

    # --- linhas com anotações ---
    if linhas_suspeitas:
        f.write("-" * 80 + "\n")
        f.write("[ LINHAS COM ANOTAÇÕES PENDENTES NO NOME ]\n\n")
        f.write(
            "  O nome da linha contém palavras como FALTA/PRECISA/REVISAR.\n"
            "  Isso indica trabalho pendente e pode aparecer no frontend.\n\n"
        )
        for n in linhas_suspeitas:
            f.write(f"  - {n}\n")
        f.write("\n")

    # --- recomendações ---
    f.write("-" * 80 + "\n")
    f.write("[ RECOMENDAÇÕES POR PRIORIDADE ]\n\n")

    prio = 1

    if linhas_suspeitas:
        f.write(f"  {prio}. URGENTE — Remover as anotações dos nomes de linha\n")
        f.write( "     Os nomes com 'FALTA FAZER' e 'PRECISA DE ALTERAÇÃO' aparecem\n")
        f.write( "     no frontend para o usuário. Corrija ou remova as linhas.\n\n")
        prio += 1

    if total_sem_codigo_sem_dic > 0:
        f.write(f"  {prio}. ALTA — Mapear {total_sem_codigo_sem_dic} vias sem código e sem dicionário\n")
        f.write( "     Ver Relatório 1 (parte principal). São vias completamente\n")
        f.write( "     desconhecidas ao sistema DMTT — buscar o código ou corrigir o nome.\n\n")
        prio += 1

    if len(suspicious_pairs) > 0:
        f.write(f"  {prio}. ALTA — Revisar {len(suspicious_pairs)} pares de nomes similares\n")
        f.write( "     Ver Relatório 2. Podem ser o mesmo logradouro com grafia diferente,\n")
        f.write( "     causando fragmentação nos resultados de busca.\n\n")
        prio += 1

    if total_sem_codigo_com_dic > 0:
        f.write(f"  {prio}. MÉDIA — Preencher código de {total_sem_codigo_com_dic} vias presentes no dicionário\n")
        f.write( "     Ver Relatório 1 (complemento). O nome já existe no dicionário,\n")
        f.write( "     basta pegar o código de lá e incluir no itinerário.\n\n")
        prio += 1

    if codigos_invalidos:
        f.write(f"  {prio}. MÉDIA — Verificar {len(codigos_invalidos)} códigos sem correspondência no dicionário\n")
        f.write( "     Pode ser código digitado errado no PDF de origem.\n\n")
        prio += 1

    if linhas_sem_ida_coord or linhas_sem_volta_coord:
        total_sem = len(set(linhas_sem_ida_coord) | set(linhas_sem_volta_coord))
        f.write(f"  {prio}. MÉDIA — Completar GPS de {total_sem} linhas sem traçado\n")
        f.write( "     Sem coordenadas essas linhas existem no sistema mas não\n")
        f.write( "     aparecem no mapa. Precisam de levantamento em campo.\n\n")
        prio += 1

    f.write("-" * 80 + "\n")
    f.write("Gerado automaticamente por python/gerar_relatorios.py\n")

print(f"[OK] Relatorio 3 -> {r3_path.name}")
print(f"\nTodos os relatorios salvos em: {RELATORIOS_DIR}")
