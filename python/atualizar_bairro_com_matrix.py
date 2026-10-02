"""
Cruza data/json/bairros/bairro-codigo.json com data/json/bairros/matrix-codigos.json
(gerado por extrair_codigos_matrix.py) e grava em cada via do bairro-codigo:

  codigo_matrix : codigo(s) DMTT do Matrix quando o nome bate (ignorando acento/caixa/pontuacao)
  via_matrix    : como o Matrix escreve a via (nome expandido)

Vias sem correspondencia ficam sem esses campos (so tem o codigo novo). O codigo novo
(sequencial) nao e alterado. Rodar de novo apos regenerar o bairro-codigo.json.

Uso:
    python python/atualizar_bairro_com_matrix.py
"""
import json
import difflib
import difflib
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BAIRRO = ROOT / "data" / "json" / "bairros" / "bairro-codigo.json"
MATRIX = ROOT / "data" / "json" / "bairros" / "matrix-codigos.json"


def chave(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", s)).strip()


def main():
    bairros = json.loads(BAIRRO.read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))["vias"]
    idx = defaultdict(list)
    for m in matrix:
        idx[chave(m["via"])].append(m)

    total = achou = multi = 0
    usados = set()
    sem = []
    for nome, b in bairros["bairros"].items():
        for v in b["vias"]:
            total += 1
            v.pop("codigo_matrix", None)
            v.pop("via_matrix", None)
            ms = idx.get(chave(v["via"]))
            if not ms:
                sem.append((nome, v["codigo"], v["via"]))
                continue
            achou += 1
            cods = [m["codigo"] for m in ms]
            usados.update(cods)
            v["codigo_matrix"] = cods[0] if len(cods) == 1 else cods
            v["via_matrix"] = ms[0]["via"]
            multi += len(cods) > 1

    bairros["total_com_codigo_matrix"] = achou
    BAIRRO.write_text(json.dumps(bairros, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{achou}/{total} vias do bairro-codigo tem codigo no Matrix ({multi} com mais de um codigo)")
    print(f"{total - achou} sem correspondencia exata; {len(matrix) - len(usados)} codigos do Matrix nao usados no bairro-codigo")
    # candidatos aproximados (NAO aplicados): so pra conferir e decidir
    mk = {chave(m["via"]): m for m in matrix}
    linhas = []
    for n, c, via in sem:
        melhor = difflib.get_close_matches(chave(via), list(mk), n=1, cutoff=0.85)
        if melhor:
            m = mk[melhor[0]]
            linhas.append(f"{n}\t{c}\t{via}\t=>\t{m['codigo']}\t{m['via']}")
    (ROOT / "data" / "json" / "bairros" / "bairro-matrix-candidatos.txt").write_text(
        "bairro\tcodigo_novo\tvia_bairro\t\tcodigo_matrix\tvia_matrix\n" + "\n".join(linhas), encoding="utf-8")
    print(f"{len(linhas)} candidatos aproximados em bairro-matrix-candidatos.txt (nao aplicados)")
    (ROOT / "data" / "json" / "bairros" / "bairro-sem-matrix.txt").write_text(
        "\n".join(f"{n}\t{c}\t{via}" for n, c, via in sem), encoding="utf-8")


if __name__ == "__main__":
    main()
