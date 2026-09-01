"""
Le a pasta "ZONAS" do Mapa Reconstruido.kml e gera
frontend/public/data/zonas.json (GeoJSON FeatureCollection de poligonos)
pro frontend consumir direto, sem precisar reprocessar KML no navegador.

Uso:
    python python/gerar_zonas_estaticas.py
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KML_PATH = ROOT / "Mapa Reconstruido.kml"
SAIDA = ROOT / "frontend" / "public" / "data" / "zonas.json"

NS = {"k": "http://www.opengis.net/kml/2.2"}


def parse_coords(texto: str):
    pontos = []
    for token in texto.strip().split():
        partes = token.split(",")
        if len(partes) < 2:
            continue
        lon, lat = float(partes[0]), float(partes[1])
        pontos.append([lon, lat])  # GeoJSON = [lon, lat]
    return pontos


def main():
    tree = ET.parse(KML_PATH)
    root = tree.getroot()
    doc = root.find(f"{{{NS['k']}}}Document")

    pasta_zonas = None
    for folder in doc.findall("k:Folder", NS):
        nome = folder.find("k:name", NS)
        if nome is not None and nome.text == "ZONAS":
            pasta_zonas = folder
            break

    if pasta_zonas is None:
        raise SystemExit("Pasta ZONAS nao encontrada no KML.")

    features = []
    for pm in pasta_zonas.findall("k:Placemark", NS):
        nome = pm.find("k:name", NS).text
        coords_el = pm.find(".//k:coordinates", NS)
        pontos = parse_coords(coords_el.text)
        if pontos and pontos[0] != pontos[-1]:
            pontos.append(pontos[0])  # fecha o anel se preciso
        features.append({
            "type": "Feature",
            "properties": {"nome": nome},
            "geometry": {"type": "Polygon", "coordinates": [pontos]},
        })

    saida = {"type": "FeatureCollection", "features": features}
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {SAIDA.relative_to(ROOT)} -- {len(features)} zonas")


if __name__ == "__main__":
    main()
