"""
Cruza data/relatorios/vias_candidatas_duplicata.txt (pares de vias parecidas
em dados_unificados.json) com data/json/intinerario manual/itinerario_completo.json
-- pra cada par, mostra exatamente qual LINHA + SENTIDO usa cada grafia,
pra dar pra corrigir direto no manual sem precisar procurar.

So mostra pares onde pelo menos uma das duas grafias aparece literalmente no
manual (ou seja, e uma correcao que faz sentido fazer la).

Uso:
    python python/localizar_duplicatas_no_manual.py
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
MANUAL_PATH = ROOT / "data" / "json" / "intinerario manual" / "itinerario_completo.json"
CANDIDATOS_PATH = ROOT / "data" / "relatorios" / "vias_candidatas_duplicata.txt"
SAIDA_PATH = ROOT / "data" / "relatorios" / "vias_duplicatas_localizadas_no_manual.txt"


def carregar_pares(path: Path):
    texto = path.read_text(encoding="utf-8")
    blocos = texto.split("\n\n")
    pares = []
    for b in blocos:
        linhas = [l for l in b.splitlines() if l.strip()]
        if len(linhas) == 3 and linhas[0].startswith("["):
            score = float(linhas[0].strip("[]"))
            pares.append((score, linhas[1].strip(), linhas[2].strip()))
    return pares


def indice_manual(manual: dict):
    """via (maiusculo) -> lista de (nome_linha, sentido)"""
    idx = {}
    for nome, dados in manual.items():
        for sentido in ["ida", "volta"]:
            for via in dados.get(sentido, []):
                idx.setdefault(via.upper(), []).append((nome, sentido))
    return idx


def main():
    manual = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))
    pares = carregar_pares(CANDIDATOS_PATH)
    idx = indice_manual(manual)

    linhas_saida = [
        "Duplicatas localizadas no itinerario_completo.json (linha + sentido)",
        "=" * 78,
        "",
        "Pra cada par abaixo, mostra em quais linhas/sentidos do seu manual",
        "cada grafia aparece -- edite la pra deixar so uma versao.",
        "",
    ]
    encontrados = 0
    for score, a, b in pares:
        ocorr_a = idx.get(a.upper(), [])
        ocorr_b = idx.get(b.upper(), [])
        if not ocorr_a and not ocorr_b:
            continue
        encontrados += 1
        linhas_saida.append(f"[{score:.2f}]")
        linhas_saida.append(f"  \"{a}\"")
        for nome, sentido in ocorr_a:
            linhas_saida.append(f"      -> {nome}  [{sentido}]")
        linhas_saida.append(f"  \"{b}\"")
        for nome, sentido in ocorr_b:
            linhas_saida.append(f"      -> {nome}  [{sentido}]")
        linhas_saida.append("")

    SAIDA_PATH.write_text("\n".join(linhas_saida), encoding="utf-8")
    print(f"[OK] {SAIDA_PATH.relative_to(ROOT)} -- {encontrados} de {len(pares)} pares localizados no manual")


if __name__ == "__main__":
    main()
