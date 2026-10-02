"""
Gera data/json/bairros/bairro-codigo.json a partir de data/json/bairros/bairro-manual.json:
bairros em ordem alfabetica (ignorando acento), vias de cada bairro em ordem alfabetica,
codigo sequencial de 4 digitos continuo (0001, 0002, ...). Entradas vazias/duplicadas no mesmo
bairro sao descartadas.

Depois rode: python python/atualizar_bairro_com_matrix.py  e  python python/gerar_pdf_bairro_codigo.py

Uso:
    python python/gerar_bairro_codigo.py
"""
import json
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "json" / "bairros" / "bairro-manual.json"
OUT = ROOT / "data" / "json" / "bairros" / "bairro-codigo.json"


def chave(s: str) -> str:
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().upper()
    return s.strip()


def main():
    src = json.loads(SRC.read_text(encoding="utf-8"))["bairros"]
    out, n = {}, 1
    for bairro in sorted(src, key=chave):
        vias = sorted({v.strip() for v in src[bairro] if v.strip()}, key=lambda v: (chave(v), v))
        if not vias:
            continue
        lst = []
        for v in vias:
            lst.append({"codigo": f"{n:04d}", "via": v})
            n += 1
        out[bairro] = {"codigo_inicial": lst[0]["codigo"], "codigo_final": lst[-1]["codigo"], "vias": lst}
    OUT.write_text(
        json.dumps({"total_bairros": len(out), "total_vias": n - 1, "bairros": out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(out)} bairros, {n - 1} vias -> {OUT}")


if __name__ == "__main__":
    main()
