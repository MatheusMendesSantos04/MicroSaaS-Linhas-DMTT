from pathlib import Path
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


def _kml_color_hex(aabbggrr: str) -> str:
    return aabbggrr


def _coords_latlon_to_kml(coords: List[List[float]]) -> str:
    parts = []
    for lat, lon in coords:
        parts.append(f"{lon},{lat},0")
    return " ".join(parts)


def _build_kml_root() -> ET.Element:
    return ET.Element(
        "kml",
        {
            "xmlns": "http://www.opengis.net/kml/2.2",
            "xmlns:gx": "http://www.google.com/kml/ext/2.2",
        },
    )


def _add_style(parent: ET.Element, style_id: str, color: str, width: int) -> None:
    style = ET.SubElement(parent, "Style", {"id": style_id})
    line_style = ET.SubElement(style, "LineStyle")
    ET.SubElement(line_style, "color").text = _kml_color_hex(color)
    ET.SubElement(line_style, "width").text = str(width)


def _add_point_style(parent: ET.Element, style_id: str, color: str, scale: float) -> None:
    style = ET.SubElement(parent, "Style", {"id": style_id})
    icon_style = ET.SubElement(style, "IconStyle")
    ET.SubElement(icon_style, "color").text = _kml_color_hex(color)
    ET.SubElement(icon_style, "scale").text = str(scale)


def _add_lines_folder(
    document: ET.Element,
    folder_name: str,
    style_url: str,
    lines: List[Dict[str, Any]],
) -> None:
    folder = ET.SubElement(document, "Folder")
    ET.SubElement(folder, "name").text = folder_name

    for item in lines:
        name = item.get("linha", "")
        coords = item.get("coordenadas", [])
        if not coords:
            continue

        placemark = ET.SubElement(folder, "Placemark")
        if name:
            ET.SubElement(placemark, "name").text = name
        ET.SubElement(placemark, "styleUrl").text = f"#{style_url}"

        line_string = ET.SubElement(placemark, "LineString")
        ET.SubElement(line_string, "tessellate").text = "1"
        ET.SubElement(line_string, "coordinates").text = _coords_latlon_to_kml(coords)


def _add_points_folder(
    document: ET.Element,
    folder_name: str,
    style_url: str,
    points: List[Dict[str, Any]],
) -> None:
    folder = ET.SubElement(document, "Folder")
    ET.SubElement(folder, "name").text = folder_name

    for item in points:
        name = item.get("nome", "")
        coords = item.get("coordenadas", [])
        if len(coords) < 2:
            continue

        lat, lon = coords[0], coords[1]
        placemark = ET.SubElement(folder, "Placemark")
        if name:
            ET.SubElement(placemark, "name").text = name
        ET.SubElement(placemark, "styleUrl").text = f"#{style_url}"

        point = ET.SubElement(placemark, "Point")
        ET.SubElement(point, "coordinates").text = f"{lon},{lat},0"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    json_dir = repo_root / "data" / "json"
    ida_path = json_dir / "IDA.json"
    volta_path = json_dir / "VOLTA.json"
    pontos_path = json_dir / "PONTOS.json"
    output_path = json_dir / "Mapa_Reconstruido.kml"

    with open(ida_path, "r", encoding="utf-8") as ida_file:
        ida_data = json.load(ida_file)

    with open(volta_path, "r", encoding="utf-8") as volta_file:
        volta_data = json.load(volta_file)

    with open(pontos_path, "r", encoding="utf-8") as pontos_file:
        pontos_data = json.load(pontos_file)

    root = _build_kml_root()
    document = ET.SubElement(root, "Document")
    ET.SubElement(document, "name").text = "Mapa Reconstruido"

    _add_style(document, "style_ida", "ff00ff00", 2)
    _add_style(document, "style_volta", "ff8b0000", 2)
    _add_point_style(document, "style_pontos", "ff00ffff", 1.2)

    _add_lines_folder(document, "IDA", "style_ida", ida_data)
    _add_lines_folder(document, "VOLTA", "style_volta", volta_data)
    _add_points_folder(document, "PONTOS", "style_pontos", pontos_data)

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    print(f"KML gerado: {output_path}")


if __name__ == "__main__":
    main()
