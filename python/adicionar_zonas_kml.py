"""
Adiciona uma pasta "ZONAS" (poligonos de bairro, buscados no Nominatim) ao
"Mapa Reconstruido.kml" -- sem tocar nas pastas existentes (IDA/VOLTA/PONTOS/
terminal). Faz backup do KML antes de escrever.

As zonas vem de arquivos GeoJSON (resultado do Nominatim, ver
data/json/zonas/*.geojson) -- um por bairro, feature[0] com geometry Polygon.

Uso:
    python python/adicionar_zonas_kml.py
"""
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KML_PATH = ROOT / "Mapa Reconstruido.kml"
ZONAS_DIR = ROOT / "data" / "json" / "zonas"

KML_NS = "http://www.opengis.net/kml/2.2"
ET.register_namespace("", KML_NS)


def qn(tag: str) -> str:
    return f"{{{KML_NS}}}{tag}"


def coords_kml(coords_geojson) -> str:
    """[[lon,lat], ...] -> 'lon,lat,0 lon,lat,0 ...'"""
    return " ".join(f"{lon},{lat},0" for lon, lat in coords_geojson)


def criar_placemark_zona(nome: str, polygon_coords) -> ET.Element:
    pm = ET.Element(qn("Placemark"))
    ET.SubElement(pm, qn("name")).text = nome

    style = ET.SubElement(pm, qn("Style"))
    line_style = ET.SubElement(style, qn("LineStyle"))
    ET.SubElement(line_style, qn("color")).text = "ff2d7be0"  # laranja/dourado, ABGR
    ET.SubElement(line_style, qn("width")).text = "2"
    poly_style = ET.SubElement(style, qn("PolyStyle"))
    ET.SubElement(poly_style, qn("color")).text = "4d2d7be0"  # mesma cor, ~30% opacidade

    polygon = ET.SubElement(pm, qn("Polygon"))
    ET.SubElement(polygon, qn("tessellate")).text = "1"
    outer = ET.SubElement(polygon, qn("outerBoundaryIs"))
    ring = ET.SubElement(outer, qn("LinearRing"))
    # exterior ring = primeiro anel do Polygon GeoJSON
    ET.SubElement(ring, qn("coordinates")).text = coords_kml(polygon_coords[0])

    return pm


def main():
    zonas_arquivos = sorted(ZONAS_DIR.glob("*.geojson"))
    if not zonas_arquivos:
        raise SystemExit(f"Nenhum .geojson encontrado em {ZONAS_DIR}")

    tree = ET.parse(KML_PATH)
    root = tree.getroot()
    doc = root.find(qn("Document"))

    # remove pasta ZONAS antiga, se existir (pra rodar de novo sem duplicar)
    for folder in doc.findall(qn("Folder")):
        nome_el = folder.find(qn("name"))
        if nome_el is not None and nome_el.text == "ZONAS":
            doc.remove(folder)

    pasta_zonas = ET.SubElement(doc, qn("Folder"))
    ET.SubElement(pasta_zonas, qn("name")).text = "ZONAS"

    adicionadas = []
    for arq in zonas_arquivos:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        feature = dados["features"][0]
        nome = feature["properties"]["name"]
        geom = feature["geometry"]
        if geom["type"] != "Polygon":
            print(f"[PULADO] {nome}: geometria {geom['type']}, nao Polygon")
            continue
        pm = criar_placemark_zona(nome, geom["coordinates"])
        pasta_zonas.append(pm)
        adicionadas.append(nome)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = KML_PATH.with_suffix(f".{ts}.bak.kml")
    shutil.copy(KML_PATH, bak)

    tree.write(KML_PATH, encoding="utf-8", xml_declaration=True)

    print(f"Backup: {bak.name}")
    print(f"Zonas adicionadas ({len(adicionadas)}): {adicionadas}")


if __name__ == "__main__":
    main()
