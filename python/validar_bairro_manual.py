"""
Valida data/json/bairros/bairro-manual.json contra
data/json/intinerario manual/itinerario_completo.json:

1. Vias no bairro-manual que NAO batem exatamente com nenhuma via do manual
   (possivel erro de digitacao) -- mostra o candidato mais parecido se achar.
2. Vias do manual (itinerario_completo.json) que NAO aparecem em nenhum
   bairro do bairro-manual.json (faltando classificar).
3. Vias duplicadas (mesma via em mais de um bairro) dentro do bairro-manual.

Uso:
    python python/validar_bairro_manual.py
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BAIRRO_MANUAL_PATH = ROOT / "data" / "json" / "bairros" / "bairro-manual.json"
ITINERARIO_PATH = ROOT / "data" / "json" / "intinerario manual" / "itinerario_completo.json"


def norm_chave(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    bairro_manual = json.loads(BAIRRO_MANUAL_PATH.read_text(encoding="utf-8"))
    itinerario = json.loads(ITINERARIO_PATH.read_text(encoding="utf-8"))

    # 1. coleta todas as vias do bairro-manual, com (bairro, texto original)
    vias_bm = []  # (bairro, via)
    for bairro, vias in bairro_manual.get("bairros", {}).items():
        for v in vias:
            v = v.strip()
            if v:
                vias_bm.append((bairro, v))

    # 2. coleta todas as vias unicas do itinerario_completo.json (ida+volta, todas linhas)
    vias_manual = set()
    for nome_linha, dados in itinerario.items():
        for sentido in ("ida", "volta"):
            for v in dados.get(sentido, []):
                v = v.strip()
                if v:
                    vias_manual.add(v)

    print(f"Vias no bairro-manual.json: {len(vias_bm)}")
    print(f"Vias unicas no itinerario_completo.json: {len(vias_manual)}")
    print()

    # indice normalizado do itinerario pra achar match exato (ignorando acento/caixa)
    idx_manual_norm = defaultdict(list)
    for v in vias_manual:
        idx_manual_norm[norm_chave(v)].append(v)

    # ---- 1. possiveis erros de digitacao no bairro-manual ----
    sem_match = []
    for bairro, via in vias_bm:
        if via in vias_manual:
            continue  # match exato perfeito
        norm = norm_chave(via)
        if norm in idx_manual_norm:
            # bate normalizado mas nao exato (diferenca so de acento/caixa/pontuacao)
            sem_match.append((bairro, via, idx_manual_norm[norm][0], "acento/pontuacao"))
            continue
        # procura o mais parecido por similaridade de texto
        melhor, melhor_score = None, 0.0
        for v in vias_manual:
            score = SequenceMatcher(None, norm, norm_chave(v)).ratio()
            if score > melhor_score:
                melhor, melhor_score = v, score
        sem_match.append((bairro, via, melhor, f"{melhor_score:.2f}"))

    print(f"=== Vias no bairro-manual SEM correspondencia exata no itinerario_completo.json ({len(sem_match)}) ===")
    for bairro, via, candidato, info in sem_match:
        print(f"  [{bairro}] {via!r}")
        print(f"      candidato mais proximo ({info}): {candidato!r}")
    print()

    # ---- 2. vias do manual que faltam no bairro-manual ----
    vias_bm_norm = {norm_chave(via) for _, via in vias_bm}
    faltando = sorted(v for v in vias_manual if norm_chave(v) not in vias_bm_norm)
    print(f"=== Vias do itinerario_completo.json QUE FALTAM no bairro-manual.json ({len(faltando)}) ===")
    for v in faltando:
        print(f"  - {v}")
    print()

    # ---- 3. vias duplicadas em mais de um bairro ----
    por_via = defaultdict(list)
    for bairro, via in vias_bm:
        por_via[norm_chave(via)].append((bairro, via))
    duplicadas = {k: v for k, v in por_via.items() if len({b for b, _ in v}) > 1}
    print(f"=== Vias que aparecem em MAIS DE UM bairro no bairro-manual.json ({len(duplicadas)}) ===")
    for k, ocorrencias in duplicadas.items():
        print(f"  {ocorrencias[0][1]!r}:")
        for bairro, via in ocorrencias:
            print(f"      -> {bairro}: {via!r}")


if __name__ == "__main__":
    main()
