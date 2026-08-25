"""
Relatorio de qualidade do data/json/intinerario manual/itinerario_completo.json
-- SO LEITURA, nao altera nada. Gera 3 diagnosticos pra revisao manual:

  1. Ruas repetidas dentro da mesma linha/sentido (duplicata provavel de
     copiar-colar, ou trajeto que passa duas vezes na mesma rua de verdade)
  2. Abreviacoes usadas no arquivo (R., AV., T.I., TRAV., PCA., etc.) --
     pra voce padronizar via busca-e-substitui direto no fonte
  3. Nomes parecidos (fuzzy) que provavelmente sao a MESMA rua escrita
     diferente, DENTRO do proprio manual (nao compara com o sistema)

Saida: data/json/intinerario manual/relatorio_duplicadas_e_nomes.txt

Uso:
    python python/relatorio_duplicadas_itinerario.py
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL_PATH = ROOT / "data" / "json" / "intinerario manual" / "itinerario_completo.json"
SAIDA_PATH = ROOT / "data" / "json" / "intinerario manual" / "relatorio_duplicadas_e_nomes.txt"

sys.stdout.reconfigure(encoding="utf-8")

LIMIAR_SIMILARIDADE = 0.5


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def palavras(s: str) -> set:
    return {w for w in normalizar(s).split() if len(w) >= 3}


def similaridade(a: str, b: str) -> float:
    pa, pb = palavras(a), palavras(b)
    if not pa or not pb:
        return 0.0
    return len(pa & pb) / len(pa | pb)


# padroes de abreviacao comuns -- (regex, "nome legivel do padrao")
ABREVIACOES = [
    (r"^R\.\s", "R."),
    (r"^AV\.\s", "AV."),
    (r"^AV\s+[A-ZÀ-Ú]", "AV (sem ponto)"),
    (r"^TRAV\.\s", "TRAV."),
    (r"^TRAV\s", "TRAV (sem ponto)"),
    (r"^P[ÇC]A\.\s", "PÇA."),
    (r"^LAD\.\s", "LAD."),
    (r"^EST\.\s", "EST."),
    (r"^AL\.\s", "AL."),
    (r"^TERM\.\s", "TERM."),
    (r"^T\.I\.?\s", "T.I."),
    (r"^T-", "T- (terminal)"),
    (r"^CONJ\.\s", "CONJ."),
    (r"^CONJ\s+[A-ZÀ-Ú]", "CONJ (sem ponto)"),
    (r"\bST[ºO]\.?\s", "STº/STO."),
    (r"\bSTA\.?\s", "STA."),
    (r"\bDR\.\s", "DR."),
    (r"\bDRA\.\s", "DRA."),
    (r"\bGAL\.\s", "GAL."),
    (r"\bCEL\.\s", "CEL."),
    (r"\bPROF\.\s", "PROF."),
    (r"\bENG\.\s", "ENG."),
    (r"\bGOV\.\s", "GOV."),
    (r"\bJD\.\s", "JD."),
]


def main():
    manual = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))

    # ---- 1. duplicatas dentro da mesma linha/sentido ----
    duplicatas_linha = []
    for nome_linha, dados in manual.items():
        for sentido in ("ida", "volta"):
            ruas = dados.get(sentido, [])
            vistos = {}
            for i, rua in enumerate(ruas):
                chave = normalizar(rua)
                if not chave:
                    continue
                vistos.setdefault(chave, []).append((i, rua))
            for chave, ocorrencias in vistos.items():
                if len(ocorrencias) > 1:
                    consecutivas = any(
                        ocorrencias[k + 1][0] - ocorrencias[k][0] == 1
                        for k in range(len(ocorrencias) - 1)
                    )
                    duplicatas_linha.append({
                        "linha": nome_linha, "sentido": sentido,
                        "rua": ocorrencias[0][1], "posicoes": [o[0] for o in ocorrencias],
                        "consecutivas": consecutivas,
                    })

    # ---- 2. abreviacoes usadas ----
    abreviacoes_encontradas = defaultdict(list)
    for nome_linha, dados in manual.items():
        for sentido in ("ida", "volta"):
            for rua in dados.get(sentido, []):
                for padrao, label in ABREVIACOES:
                    if re.search(padrao, rua, flags=re.IGNORECASE):
                        abreviacoes_encontradas[label].append((nome_linha, sentido, rua))
                        break  # so conta a primeira abreviacao batida por rua

    # ---- 3. nomes parecidos dentro do proprio manual ----
    ocorrencias_por_rua = defaultdict(list)  # rua original -> [(linha, sentido), ...]
    for nome_linha, dados in manual.items():
        for sentido in ("ida", "volta"):
            for rua in dados.get(sentido, []):
                ocorrencias_por_rua[rua].append((nome_linha, sentido))

    ruas_unicas = list(ocorrencias_por_rua.keys())
    print(f"Ruas unicas no manual: {len(ruas_unicas)} (revisando pares fuzzy...)")

    # agrupa por normalizado EXATO primeiro pra nao comparar duas vezes o que ja e identico
    por_normalizado = defaultdict(list)
    for rua in ruas_unicas:
        por_normalizado[normalizar(rua)].append(rua)

    chaves = list(por_normalizado.keys())
    clusters = []
    usados = set()
    for i, ka in enumerate(chaves):
        if ka in usados:
            continue
        grupo_variantes = set(por_normalizado[ka])
        grupo_chaves = {ka}
        for kb in chaves[i + 1:]:
            if kb in usados:
                continue
            if similaridade(ka, kb) >= LIMIAR_SIMILARIDADE:
                grupo_variantes.update(por_normalizado[kb])
                grupo_chaves.add(kb)
        if len(grupo_variantes) > 1:
            clusters.append(sorted(grupo_variantes, key=lambda r: -len(ocorrencias_por_rua[r])))
            usados.update(grupo_chaves)

    clusters.sort(key=lambda g: -sum(len(ocorrencias_por_rua[r]) for r in g))

    # ---- escreve relatorio ----
    linhas_saida = []
    linhas_saida.append("=" * 78)
    linhas_saida.append("1. RUAS REPETIDAS DENTRO DA MESMA LINHA/SENTIDO")
    linhas_saida.append("=" * 78)
    linhas_saida.append(f"Total: {len(duplicatas_linha)} ocorrencias\n")
    for d in sorted(duplicatas_linha, key=lambda x: (not x["consecutivas"], x["linha"])):
        marcador = "[CONSECUTIVAS -- provavel erro]" if d["consecutivas"] else "[nao consecutivas -- pode ser trajeto real]"
        linhas_saida.append(f"{marcador} {d['linha']} ({d['sentido']})")
        linhas_saida.append(f"    \"{d['rua']}\" aparece nas posicoes {d['posicoes']}")
    linhas_saida.append("")

    linhas_saida.append("=" * 78)
    linhas_saida.append("2. ABREVIACOES USADAS NO ARQUIVO (padronizar via busca-e-substitui)")
    linhas_saida.append("=" * 78)
    for label, ocorrencias in sorted(abreviacoes_encontradas.items(), key=lambda x: -len(x[1])):
        linhas_saida.append(f"\n{label} -- {len(ocorrencias)} ocorrencia(s):")
        exemplos = sorted(set(r for _, _, r in ocorrencias))[:15]
        for ex in exemplos:
            linhas_saida.append(f"    {ex}")
        if len(ocorrencias) > 15:
            linhas_saida.append(f"    ... e mais {len(ocorrencias) - 15}")
    linhas_saida.append("")

    linhas_saida.append("=" * 78)
    linhas_saida.append("3. NOMES PARECIDOS -- PROVAVEL MESMA RUA, GRAFIA DIFERENTE (dentro do manual)")
    linhas_saida.append("=" * 78)
    linhas_saida.append(f"Total: {len(clusters)} grupos\n")
    for grupo in clusters:
        total_ocorrencias = sum(len(ocorrencias_por_rua[r]) for r in grupo)
        linhas_saida.append(f"--- grupo com {len(grupo)} variantes, {total_ocorrencias} ocorrencias no total ---")
        for r in grupo:
            linhas_das = ocorrencias_por_rua[r]
            exemplo_linhas = "; ".join(f"{n} ({s})" for n, s in linhas_das[:3])
            mais = f" ... +{len(linhas_das)-3}" if len(linhas_das) > 3 else ""
            linhas_saida.append(f"    \"{r}\"  ({len(linhas_das)}x)  ex: {exemplo_linhas}{mais}")
        linhas_saida.append("")

    SAIDA_PATH.write_text("\n".join(linhas_saida), encoding="utf-8")
    print(f"\n[OK] {SAIDA_PATH.relative_to(ROOT)}")
    print(f"  1. Duplicatas dentro da linha: {len(duplicatas_linha)}")
    print(f"  2. Tipos de abreviacao encontrados: {len(abreviacoes_encontradas)}")
    print(f"  3. Grupos de nomes parecidos: {len(clusters)}")


if __name__ == "__main__":
    main()
