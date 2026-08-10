"""
Mescla data/json/intinerario manual/itinerario_completo.json (fonte confiavel,
revisada manualmente) com data/json/dados_unificados.json (sistema), expande
abreviacoes comuns de logradouro, e gera:

  data/json/intinerario manual/itinerario_mesclado.json
      -- mesma estrutura do itinerario_completo.json, mas com abreviacoes
         expandidas. O manual e a base (e a fonte de verdade); ruas do
         sistema so entram se nao houver NENHUM correspondente (nem exato
         nem fuzzy) no manual, marcadas para revisao.

  data/relatorios/fuzzy_itinerarios.txt
      -- por linha, os pares (rua do manual / rua do sistema) que so
         bateram por similaridade de palavras, nao por igualdade exata --
         provavelmente a MESMA rua escrita diferente, para conferencia
         manual.

Uso:
    python python/mesclar_itinerarios.py
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sincronizar_mapa_reconstruido import normalizar_codigo

ROOT = Path(__file__).resolve().parents[1]
MANUAL_PATH = ROOT / "data" / "json" / "intinerario manual" / "itinerario_completo.json"
SISTEMA_PATH = ROOT / "data" / "json" / "dados_unificados.json"
SAIDA_JSON = ROOT / "data" / "json" / "intinerario manual" / "itinerario_mesclado.json"
SAIDA_RELATORIO = ROOT / "data" / "json" / "intinerario manual" / "fuzzy_itinerarios_por_linha.txt"
SAIDA_RELATORIO_PROJETO = ROOT / "data" / "json" / "intinerario manual" / "fuzzy_itinerarios_projeto.txt"

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# expansao de abreviacoes de logradouro
# ---------------------------------------------------------------------------

ABREVIACOES = [
    (r"^R\.\s+", "RUA "),
    (r"^AV\.\s+", "AVENIDA "),
    (r"^AV\s+", "AVENIDA "),
    (r"^TRAV\.\s+", "TRAVESSA "),
    (r"^TRAV\s+", "TRAVESSA "),
    (r"^P[ÇC]A\.\s+", "PRAÇA "),
    (r"^PRACA\s+", "PRAÇA "),
    (r"^LAD\.\s+", "LADEIRA "),
    (r"^EST\.\s+", "ESTRADA "),
    (r"^AL\.\s+", "ALAMEDA "),
    (r"^TERM\.\s+DE\s+", "TERMINAL DE "),
    (r"^TERM\.\s+", "TERMINAL "),
    (r"^TERM\s+DE\s+", "TERMINAL DE "),
    (r"^T\.I\.?\s+", "TERMINAL INTEGRADO "),
    (r"^T-", "TERMINAL "),
    (r"^CONJ\.\s+", "CONJUNTO "),
    (r"^CONJ\s+", "CONJUNTO "),
    (r"\bST[ºO]\.?\s+", "SANTO "),
    (r"\bSTA\.?\s+", "SANTA "),
    (r"\bDR\.\s+", "DOUTOR "),
    (r"\bDRA\.\s+", "DOUTORA "),
    (r"\bGAL\.\s+", "GENERAL "),
    (r"\bCEL\.\s+", "CORONEL "),
    (r"\bPROF\.\s+", "PROFESSOR "),
    (r"\bENG\.\s+", "ENGENHEIRO "),
    (r"\bGOV\.\s+", "GOVERNADOR "),
    (r"\bPÇA\.\s+", "PRAÇA "),
    (r"\bJD\.\s+", "JARDIM "),
]


def expandir_abreviacoes(nome: str) -> str:
    resultado = nome.strip()
    for padrao, subst in ABREVIACOES:
        resultado = re.sub(padrao, subst, resultado, flags=re.IGNORECASE)
    resultado = re.sub(r"\s+", " ", resultado).strip()
    return resultado


def norm_chave(s: str) -> str:
    """normaliza so pra COMPARAR (maiusculo, sem acento) -- nao usado na saida"""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def palavras(s: str) -> set:
    return {w for w in norm_chave(s).split() if len(w) >= 3}


def melhor_fuzzy(rua_m: str, ruas_s_restantes: list, limiar=0.4):
    pm = palavras(rua_m)
    if not pm:
        return None, 0.0
    melhor, melhor_score = None, 0.0
    for rs in ruas_s_restantes:
        ps = palavras(rs)
        if not ps:
            continue
        score = len(pm & ps) / len(pm | ps)
        if score > melhor_score:
            melhor, melhor_score = rs, score
    if melhor_score >= limiar:
        return melhor, melhor_score
    return None, 0.0


def mesclar_sentido(ruas_manual: list, ruas_sistema: list):
    """Retorna (lista_final, pares_fuzzy, extras_sistema_sem_match)"""
    manual_exp = [expandir_abreviacoes(r) for r in ruas_manual]
    sistema_exp = [expandir_abreviacoes(r) for r in ruas_sistema]

    chaves_manual = {norm_chave(r) for r in manual_exp}
    pares_fuzzy = []
    sistema_restante = list(sistema_exp)

    for rm in manual_exp:
        if norm_chave(rm) in chaves_manual and any(norm_chave(rm) == norm_chave(rs) for rs in sistema_exp):
            continue  # match exato, nada a reportar
        candidato, score = melhor_fuzzy(rm, sistema_restante)
        if candidato:
            pares_fuzzy.append({"manual": rm, "sistema": candidato, "score": round(score, 2)})

    # ruas do sistema que nao bateram nem exato nem fuzzy com nada do manual
    extras_sistema = []
    for rs in sistema_exp:
        if norm_chave(rs) in chaves_manual:
            continue
        pm_match, score = melhor_fuzzy(rs, manual_exp)
        if not pm_match:
            extras_sistema.append(rs)

    return manual_exp, pares_fuzzy, extras_sistema


def main():
    manual = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))
    sistema = json.loads(SISTEMA_PATH.read_text(encoding="utf-8"))

    manual_por_cod = {}
    for nome, dados in manual.items():
        cod = normalizar_codigo(nome)
        if cod:
            manual_por_cod.setdefault(cod, []).append((nome, dados))

    sistema_por_cod = {}
    for nome, dados in sistema.items():
        cod = normalizar_codigo(nome)
        if cod:
            sistema_por_cod[cod] = (nome, dados)

    saida = {}
    relatorio_linhas = []
    total_fuzzy = 0
    # agrega por par (manual, sistema) unico, independente de quantas linhas usam essa rua
    pares_projeto: dict[tuple, dict] = {}

    for cod in sorted(manual_por_cod.keys()):
        entradas = manual_por_cod[cod]
        s = sistema_por_cod.get(cod)
        ruas_ida_s = [r["via"] for r in s[1].get("ida", {}).get("ruas", [])] if s else []
        ruas_volta_s = [r["via"] for r in s[1].get("volta", {}).get("ruas", [])] if s else []

        for nome_m, dados_m in entradas:
            ida_final, fuzzy_ida, extra_ida = mesclar_sentido(dados_m.get("ida", []), ruas_ida_s)
            volta_final, fuzzy_volta, extra_volta = mesclar_sentido(dados_m.get("volta", []), ruas_volta_s)

            saida[nome_m] = {"ida": ida_final, "volta": volta_final}

            for p in fuzzy_ida + fuzzy_volta:
                chave = (norm_chave(p["manual"]), norm_chave(p["sistema"]))
                if chave not in pares_projeto:
                    pares_projeto[chave] = {
                        "manual": p["manual"], "sistema": p["sistema"],
                        "score": p["score"], "linhas": set(),
                    }
                pares_projeto[chave]["linhas"].add(f"{cod} - {nome_m}")
                pares_projeto[chave]["score"] = max(pares_projeto[chave]["score"], p["score"])

            if fuzzy_ida or fuzzy_volta:
                total_fuzzy += len(fuzzy_ida) + len(fuzzy_volta)
                relatorio_linhas.append(f"\n{'='*78}\n{nome_m}  (codigo {cod})\n{'='*78}")
                if fuzzy_ida:
                    relatorio_linhas.append(f"  IDA -- {len(fuzzy_ida)} par(es) fuzzy:")
                    for p in sorted(fuzzy_ida, key=lambda x: -x["score"]):
                        relatorio_linhas.append(f"    [{p['score']:.2f}] MANUAL:  {p['manual']}")
                        relatorio_linhas.append(f"           SISTEMA: {p['sistema']}")
                if fuzzy_volta:
                    relatorio_linhas.append(f"  VOLTA -- {len(fuzzy_volta)} par(es) fuzzy:")
                    for p in sorted(fuzzy_volta, key=lambda x: -x["score"]):
                        relatorio_linhas.append(f"    [{p['score']:.2f}] MANUAL:  {p['manual']}")
                        relatorio_linhas.append(f"           SISTEMA: {p['sistema']}")
                if extra_ida:
                    relatorio_linhas.append(f"  IDA -- ruas so no sistema, sem match nenhum no manual ({len(extra_ida)}):")
                    for r in extra_ida:
                        relatorio_linhas.append(f"    - {r}")
                if extra_volta:
                    relatorio_linhas.append(f"  VOLTA -- ruas so no sistema, sem match nenhum no manual ({len(extra_volta)}):")
                    for r in extra_volta:
                        relatorio_linhas.append(f"    - {r}")

    SAIDA_JSON.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    SAIDA_RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_RELATORIO.write_text("\n".join(relatorio_linhas), encoding="utf-8")

    pares_ordenados = sorted(pares_projeto.values(), key=lambda p: (-len(p["linhas"]), -p["score"]))
    projeto_linhas = [
        f"Pares fuzzy unicos no projeto inteiro (deduplicados) -- {len(pares_ordenados)} pares",
        "Ordenado por quantas linhas usam esse par (mais impactante primeiro).",
        "",
    ]
    for p in pares_ordenados:
        projeto_linhas.append("=" * 78)
        projeto_linhas.append(f"[{p['score']:.2f}]  em {len(p['linhas'])} linha(s)")
        projeto_linhas.append(f"  MANUAL:  {p['manual']}")
        projeto_linhas.append(f"  SISTEMA: {p['sistema']}")
        projeto_linhas.append("  linhas: " + "; ".join(sorted(p["linhas"])[:6]) + (" ..." if len(p["linhas"]) > 6 else ""))
        projeto_linhas.append("")

    SAIDA_RELATORIO_PROJETO.write_text("\n".join(projeto_linhas), encoding="utf-8")

    print(f"[OK] {SAIDA_JSON.relative_to(ROOT)}  ({len(saida)} linhas)")
    print(f"[OK] {SAIDA_RELATORIO_PROJETO.relative_to(ROOT)}  ({len(pares_ordenados)} pares unicos)")
    print(f"[OK] {SAIDA_RELATORIO.relative_to(ROOT)}  ({total_fuzzy} pares fuzzy no total)")


if __name__ == "__main__":
    main()
