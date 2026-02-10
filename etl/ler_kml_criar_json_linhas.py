from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import xml.etree.ElementTree as ET

from fastkml import kml
from shapely.geometry import LineString


def read_kml_file(path: str) -> kml.KML:
    with open(path, "rb") as file:
        k = kml.KML()
        k.from_string(file.read())
        return k


@dataclass(frozen=True)
class SimpleLineString:
    coords: List[Tuple[float, float, float]]


def _iter_features(parent) -> List:
    features = getattr(parent, "features", None)
    if features is None:
        return []
    return features() if callable(features) else list(features or [])


def _iter_all_features(root) -> List:
    queue = list(_iter_features(root))
    all_features = []

    while queue:
        feature = queue.pop(0)
        all_features.append(feature)
        queue.extend(_iter_features(feature))

    return all_features


def _is_linestring(geometry: Any) -> bool:
    geom_type = getattr(geometry, "geom_type", None)
    if geom_type == "LineString":
        return True
    return geometry.__class__.__name__ == "LineString"


def _extract_lines_from_geometry(geometry: Any, lines: List[Any]) -> None:
    if geometry is None:
        return

    if isinstance(geometry, LineString) or _is_linestring(geometry):
        lines.append(geometry)
        return

    nested = getattr(geometry, "geometry", None)
    if nested is not None and nested is not geometry:
        _extract_lines_from_geometry(nested, lines)
        return

    geoms = getattr(geometry, "geoms", None)
    if geoms is not None:
        for sub_geom in geoms:
            _extract_lines_from_geometry(sub_geom, lines)


def extract_linestrings(kml_data: kml.KML) -> List[Any]:
    lines: List[Any] = []

    for feature in _iter_all_features(kml_data):
        geom = getattr(feature, "geometry", None)
        _extract_lines_from_geometry(geom, lines)

    return lines


def collect_geometry_types(kml_data: kml.KML) -> List[str]:
    types: List[str] = []

    for feature in _iter_all_features(kml_data):
        geom = getattr(feature, "geometry", None)
        if geom is None:
            continue
        geom_type = getattr(geom, "geom_type", None)
        if geom_type is None:
            geom_type = geom.__class__.__name__
        types.append(str(geom_type))

    return types


def validate_coordinates(line: Any) -> bool:
    for lon, lat, *_ in line.coords:
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            return False
    return True


def extract_coordinates(line: Any) -> List[Tuple[float, float]]:
    return [(lat, lon) for lon, lat, *_ in line.coords]


def count_points(line: Any) -> int:
    return len(line.coords)


def _parse_coordinate_block(text: str) -> List[Tuple[float, float, float]]:
    coords: List[Tuple[float, float, float]] = []
    for item in text.replace("\n", " ").split():
        parts = item.split(",")
        if len(parts) < 2:
            continue
        lon = float(parts[0])
        lat = float(parts[1])
        alt = float(parts[2]) if len(parts) > 2 and parts[2] else 0.0
        coords.append((lon, lat, alt))
    return coords


def extract_linestrings_from_xml(path: str) -> List[SimpleLineString]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    lines: List[SimpleLineString] = []

    for coord_elem in root.findall(".//kml:LineString/kml:coordinates", ns):
        if coord_elem.text:
            coords = _parse_coordinate_block(coord_elem.text)
            if coords:
                lines.append(SimpleLineString(coords=coords))

    return lines


def extract_lines_by_direction_from_xml(
    path: str,
) -> Dict[str, List[Dict[str, Any]]]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    result: Dict[str, List[Dict[str, Any]]] = {"IDA": [], "VOLTA": []}

    for line_folder in root.findall(".//kml:Document/kml:Folder", ns):
        line_name_elem = line_folder.find("kml:name", ns)
        line_name = line_name_elem.text.strip() if line_name_elem is not None else ""
        if not line_name:
            continue

        for direction_folder in line_folder.findall("kml:Folder", ns):
            direction_elem = direction_folder.find("kml:name", ns)
            direction = direction_elem.text.strip() if direction_elem is not None else ""
            if direction not in result:
                continue

            coord_elems = direction_folder.findall(
                ".//kml:LineString/kml:coordinates", ns
            )
            for coord_elem in coord_elems:
                if not coord_elem.text:
                    continue
                coords = _parse_coordinate_block(coord_elem.text)
                if not coords:
                    continue
                line = SimpleLineString(coords=coords)
                if not validate_coordinates(line):
                    raise ValueError(
                        "Coordenadas invalidas detectadas para "
                        f"{line_name} ({direction})"
                    )
                result[direction].append(
                    {
                        "linha": line_name,
                        "coordenadas": extract_coordinates(line),
                    }
                )

    return result


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    kml_path = repo_root / "data" / "Mapa dos Intinerarios das Linhas de Maceio.kml"

    direction_data = extract_lines_by_direction_from_xml(str(kml_path))

    json_dir = repo_root / "data" / "json"
    ida_path = json_dir / "IDA.json"
    volta_path = json_dir / "VOLTA.json"

    with open(ida_path, "w", encoding="utf-8") as ida_file:
        json.dump(direction_data["IDA"], ida_file, ensure_ascii=True, indent=2)

    with open(volta_path, "w", encoding="utf-8") as volta_file:
        json.dump(direction_data["VOLTA"], volta_file, ensure_ascii=True, indent=2)

    print(
        "IDA: "
        + str(len(direction_data["IDA"]))
        + " linhas salvas em "
        + str(ida_path)
    )
    print(
        "VOLTA: "
        + str(len(direction_data["VOLTA"]))
        + " linhas salvas em "
        + str(volta_path)
    )

    kml_data = read_kml_file(str(kml_path))
    lines = extract_linestrings(kml_data)

    if not lines:
        lines = extract_linestrings_from_xml(str(kml_path))

    if not lines:
        types = collect_geometry_types(kml_data)
        unique_types = sorted(set(types))
        raise ValueError(
            "Nenhuma LineString encontrada no KML. Tipos detectados: "
            + ", ".join(unique_types)
        )

    print(f"Total de linhas (fallback): {len(lines)}")
