"""
Extrai os terminais de ônibus da pasta <Folder><name>terminal</name>
do Mapa Reconstruido.kml e salva em data/json/terminais.json.

Formato de saída:
[
  {"nome": "Terminal Cruz das Almas", "lat": -9.630269, "lon": -35.696814},
  ...
]

Uso:
    python python/extrair_terminais_kml.py
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
KML_PATH = BASE_DIR / "data" / "kml" / "Mapa Reconstruido.kml"
SAIDA    = BASE_DIR / "data" / "json" / "terminais.json"

NS = {"k": "http://www.opengis.net/kml/2.2"}


def pn(e):
    n = e.find("k:name", NS)
    return n.text.strip() if n is not None and n.text else ""


tree = ET.parse(KML_PATH)
root = tree.getroot()

terminais = []

for folder in root.findall(".//k:Folder", NS):
    if pn(folder).lower() != "terminal":
        continue
    for pm in folder.findall("k:Placemark", NS):
        nome = pn(pm)
        pt = pm.find(".//k:Point", NS)
        if pt is None:
            continue
        coords_el = pt.find("k:coordinates", NS)
        if coords_el is None or not coords_el.text:
            continue
        parts = coords_el.text.strip().split(",")
        if len(parts) < 2:
            continue
        try:
            lon = float(parts[0])
            lat = float(parts[1])
        except ValueError:
            continue
        terminais.append({"nome": nome, "lat": round(lat, 7), "lon": round(lon, 7)})

terminais.sort(key=lambda x: x["nome"])

SAIDA.parent.mkdir(parents=True, exist_ok=True)
with SAIDA.open("w", encoding="utf-8") as f:
    json.dump(terminais, f, ensure_ascii=False, indent=2)

print(f"[OK] {SAIDA}")
print(f"     {len(terminais)} terminais extraídos")
for t in terminais:
    print(f"  {t['nome'][:50]:<50}  {t['lat']:.6f}, {t['lon']:.6f}")
