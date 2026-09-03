"""
Le data/kml/Mapa Reconstruido.kml e gera uma copia com as pastas IDA e VOLTA
ordenadas numericamente por codigo de linha (PONTOS e terminal ficam como
estao, ja que nao sao "linhas").

Saida: "Mapa Reconstruido - ordenado.kml" na raiz do projeto (nao mexe no
arquivo original).

Uso:
    python python/ordenar_kml_por_linha.py
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
KML_PATH = ROOT / "data" / "kml" / "Mapa Reconstruido.kml"
SAIDA_PATH = ROOT / "Mapa Reconstruido - ordenado.kml"

KML_NS = "http://www.opengis.net/kml/2.2"
ET.register_namespace("", KML_NS)


def qn(tag: str) -> str:
    return f"{{{KML_NS}}}{tag}"


def chave_ordenacao(nome: str):
    nome = nome.strip()
    # extrai o codigo do inicio: digitos, opcional sufixo de letra/M (com ou sem hifen/espaco)
    m = re.match(r"^(M)?0*(\d+)\s*-?\s*([A-Z])?\b", nome.upper())
    if not m:
        return (999999, "", nome)
    prefixo_m, numero, sufixo = m.groups()
    num = int(numero)
    if prefixo_m:  # "M001", "M002" etc -- madrugadao no formato antigo do KML
        num += 1000000
    ordem_sufixo = {None: 0, "A": 1, "B": 2}.get(sufixo, 3)
    return (num, ordem_sufixo, nome)


def main():
    tree = ET.parse(KML_PATH)
    root = tree.getroot()
    doc = root.find(qn("Document"))

    ordenadas = []
    for folder in doc.findall(qn("Folder")):
        nome_el = folder.find(qn("name"))
        nome_pasta = nome_el.text if nome_el is not None else ""
        if nome_pasta not in ("IDA", "VOLTA"):
            continue

        placemarks = folder.findall(qn("Placemark"))
        placemarks_ordenados = sorted(
            placemarks,
            key=lambda pm: chave_ordenacao((pm.find(qn("name")).text or "") if pm.find(qn("name")) is not None else ""),
        )

        for pm in placemarks:
            folder.remove(pm)
        for pm in placemarks_ordenados:
            folder.append(pm)

        ordenadas.append((nome_pasta, len(placemarks_ordenados)))

    tree.write(SAIDA_PATH, encoding="utf-8", xml_declaration=True)

    print(f"[OK] {SAIDA_PATH.name}")
    for nome_pasta, qtd in ordenadas:
        print(f"  pasta {nome_pasta}: {qtd} placemarks ordenados")


if __name__ == "__main__":
    main()
