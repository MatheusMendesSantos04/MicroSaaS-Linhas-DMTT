"""
Le um PDF de Resumo OSO e lista as linhas que NAO estao em itinerario_completo.json
e/ou em dados_unificados.json (e as que estao nos arquivos mas sumiram da OSO).

Uso:
    python python/comparar_oso_pdf.py "C:/caminho/sp_relatorio_resumooso.pdf"
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "data" / "json" / "intinerario manual" / "itinerario_completo.json"
SISTEMA = ROOT / "data" / "json" / "dados_unificados.json"

RE_OSO = re.compile(r"^(\d{4})-?([A-Z])?-?\s+-\s+(.+?)\s+\d+-\s+([A-ZÇÃ]+)\s+\d{2}/\d{2}/\d{4}")
RE_CODIGO = re.compile(r"^\s*(\d{4})(?:\s?-\s?([A-Za-z])(?=\s*-))?")


def codigo(nome: str) -> str:
    m = RE_CODIGO.match(nome)
    if not m:
        return nome.strip()
    return m.group(1) + (f"-{m.group(2).upper()}" if m.group(2) else "")


def ler_oso(pdf_path: str):
    linhas, tipo = {}, ""
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            for l in (pg.extract_text() or "").split("\n"):
                if l.startswith("Tipo Servi"):
                    tipo = l.split(":", 1)[1].strip()
                m = RE_OSO.match(l)
                if m:
                    cod = m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")
                    linhas[cod] = (m.group(3).strip(), tipo)
    return linhas


def main():
    oso = ler_oso(sys.argv[1])
    manual = {codigo(n) for n in json.loads(MANUAL.read_text(encoding="utf-8"))}
    sistema = {codigo(n) for n in json.loads(SISTEMA.read_text(encoding="utf-8"))}
    base4 = lambda s: {c[:4] for c in s}

    print(f"OSO: {len(oso)} linhas | manual: {len(manual)} | sistema: {len(sistema)}\n")

    def falta(cods, titulo):
        r = sorted(c for c in oso if c not in cods and (c[:4] not in base4(cods) or "-" in c))
        print(f"=== {titulo} ({len(r)}) ===")
        for c in r:
            print(f"  {c}  {oso[c][0]}  [{oso[c][1]}]")
        print()
        return set(r)

    fm = falta(manual, "Na OSO e FALTAM no itinerario_completo.json")
    fs = falta(sistema, "Na OSO e FALTAM no dados_unificados.json")
    print(f"=== Faltam em AMBOS ({len(fm & fs)}) ===")
    for c in sorted(fm & fs):
        print(f"  {c}  {oso[c][0]}  [{oso[c][1]}]")

    print()
    for nome, cods in (("itinerario_completo.json", manual), ("dados_unificados.json", sistema)):
        r = sorted(c for c in cods if c not in oso and not (c[:4] in base4(oso) and "-" not in c))
        print(f"=== Nao estao na OSO mas estao em {nome} ({len(r)}) ===")
        print("  " + ", ".join(r))


if __name__ == "__main__":
    main()
