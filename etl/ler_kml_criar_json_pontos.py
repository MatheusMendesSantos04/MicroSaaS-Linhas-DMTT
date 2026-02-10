from pathlib import Path
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple


def _parse_point_coordinates(text: str) -> Tuple[float, float]:
    parts = text.strip().split(",")
    if len(parts) < 2:
        raise ValueError("Coordenadas invalidas no ponto")
    lon = float(parts[0])
    lat = float(parts[1])
    return lat, lon


def _validate_lat_lon(lat: float, lon: float) -> None:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError(f"Coordenadas invalidas: ({lat}, {lon})")


def extract_points_from_kml(path: str) -> List[Dict[str, object]]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    points: List[Dict[str, object]] = []

    for placemark in root.findall(".//kml:Placemark", ns):
        coord_elem = placemark.find(".//kml:Point/kml:coordinates", ns)
        if coord_elem is None or not coord_elem.text:
            continue

        name_elem = placemark.find("kml:name", ns)
        name = name_elem.text.strip() if name_elem is not None else ""

        lat, lon = _parse_point_coordinates(coord_elem.text)
        _validate_lat_lon(lat, lon)

        points.append({"nome": name, "coordenadas": [lat, lon]})

    return points


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    kml_path = repo_root / "data" / "PONTOS E PARADAS.kml"
    json_dir = repo_root / "data" / "json"
    output_path = json_dir / "PONTOS.json"

    points = extract_points_from_kml(str(kml_path))

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(points, output_file, ensure_ascii=True, indent=2)

    print(f"Pontos salvos: {len(points)}")
    print(f"Arquivo: {output_path}")


if __name__ == "__main__":
    main()
