"""
Versao enxuta do relatorio de nomes parecidos (secao 3 de
relatorio_duplicadas_itinerario.py), sem a lista de linhas-exemplo -- so o
essencial pra decidir qual grafia vira a canonica.

Saida: data/json/intinerario manual/nomes_parecidos.txt

Uso:
    python python/gerar_nomes_parecidos.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relatorio_duplicadas_itinerario import (  # noqa: E402
    MANUAL_PATH, normalizar, similaridade, LIMIAR_SIMILARIDADE,
)
import json
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
SAIDA_PATH = ROOT / "data" / "json" / "intinerario manual" / "nomes_parecidos.txt"

sys.stdout.reconfigure(encoding="utf-8")


def main():
    manual = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))

    ocorrencias_por_rua = defaultdict(int)
    for nome_linha, dados in manual.items():
        for sentido in ("ida", "volta"):
            for rua in dados.get(sentido, []):
                ocorrencias_por_rua[rua] += 1

    por_normalizado = defaultdict(list)
    for rua in ocorrencias_por_rua:
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
            clusters.append(sorted(grupo_variantes, key=lambda r: -ocorrencias_por_rua[r]))
            usados.update(grupo_chaves)

    clusters.sort(key=lambda g: -sum(ocorrencias_por_rua[r] for r in g))

    linhas_saida = [
        "NOMES PARECIDOS -- candidatos a mesma rua com grafia diferente",
        "(revisar manualmente -- alguns grupos juntam ruas REALMENTE diferentes",
        " que so compartilham uma palavra, ex: ruas que so tem 'AVENIDA'+'LIMA' em comum)",
        "",
        f"{len(clusters)} grupos, ordenados do mais frequente pro menos frequente",
        "",
    ]

    for i, grupo in enumerate(clusters, 1):
        total = sum(ocorrencias_por_rua[r] for r in grupo)
        linhas_saida.append("=" * 80)
        linhas_saida.append(f"GRUPO {i:03d} — {total} ocorrências totais, {len(grupo)} variantes")
        linhas_saida.append("-" * 80)
        for r in grupo:
            n = ocorrencias_por_rua[r]
            linhas_saida.append(f"  {n:>4}x  {r}")
        linhas_saida.append("")

    SAIDA_PATH.write_text("\n".join(linhas_saida), encoding="utf-8")
    print(f"[OK] {SAIDA_PATH.relative_to(ROOT)}  ({len(clusters)} grupos)")


if __name__ == "__main__":
    main()
