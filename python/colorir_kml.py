"""
Aplica cor consistente nas pastas IDA (verde) e VOLTA (azul) do
"Mapa Reconstruido - ordenado.kml" -- o arquivo original usa um estilo do
Google Earth (gx:CascadingStyle) com uma cor DIFERENTE e as vezes nem verde/
azul por placemark (cada linha tinha a cor de quando foi desenhada). Aqui
troca isso por 2 estilos fixos, mesma paleta do projeto (IDA #22c55e,
VOLTA #1e40af -- ver CLAUDE.md).

Uso:
    python python/colorir_kml.py
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ALVO_PATH = ROOT / "Mapa Reconstruido - ordenado.kml"

KML_NS = "http://www.opengis.net/kml/2.2"
ET.register_namespace("", KML_NS)


def qn(tag: str) -> str:
    return f"{{{KML_NS}}}{tag}"


# #22c55e (IDA, verde) e #1e40af (VOLTA, azul) -- RGB -> KML usa AABBGGRR
COR_IDA = "ff5ec522"
COR_VOLTA = "ffaf401e"


def criar_style(style_id: str, cor: str) -> ET.Element:
    st = ET.Element(qn("Style"))
    st.set("id", style_id)
    line = ET.SubElement(st, qn("LineStyle"))
    ET.SubElement(line, qn("color")).text = cor
    ET.SubElement(line, qn("width")).text = "4"
    poly = ET.SubElement(st, qn("PolyStyle"))
    ET.SubElement(poly, qn("color")).text = "00ffffff"
    return st


def main():
    tree = ET.parse(ALVO_PATH)
    root = tree.getroot()
    doc = root.find(qn("Document"))

    # remove estilos IDA/VOLTA de uma rodada anterior, se existirem (idempotente)
    for st in list(doc.findall(qn("Style"))):
        sid = st.get("id")
        if sid in ("ida_style", "volta_style"):
            doc.remove(st)

    doc.insert(0, criar_style("volta_style", COR_VOLTA))
    doc.insert(0, criar_style("ida_style", COR_IDA))

    alterados = {"IDA": 0, "VOLTA": 0}
    for folder in doc.findall(qn("Folder")):
        nome_el = folder.find(qn("name"))
        nome_pasta = nome_el.text if nome_el is not None else ""
        if nome_pasta not in ("IDA", "VOLTA"):
            continue
        style_ref = "#ida_style" if nome_pasta == "IDA" else "#volta_style"
        for pm in folder.findall(qn("Placemark")):
            style_url = pm.find(qn("styleUrl"))
            if style_url is None:
                style_url = ET.SubElement(pm, qn("styleUrl"))
            style_url.text = style_ref
            alterados[nome_pasta] += 1

    tree.write(ALVO_PATH, encoding="utf-8", xml_declaration=True)

    print(f"[OK] {ALVO_PATH.name}")
    print(f"  IDA:   {alterados['IDA']} placemarks -> verde ({COR_IDA})")
    print(f"  VOLTA: {alterados['VOLTA']} placemarks -> azul ({COR_VOLTA})")


if __name__ == "__main__":
    main()
