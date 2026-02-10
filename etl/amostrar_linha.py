from pathlib import Path
import json
from typing import List, Tuple, Dict, Any

from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import transform


def sample_line_coords(
    coords_latlon: List[Tuple[float, float]], spacing_m: float = 25.0
) -> List[Tuple[float, float]]:
    if len(coords_latlon) < 2:
        return coords_latlon

    to_m = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    to_deg = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    line_ll = LineString([(lon, lat) for lat, lon in coords_latlon])
    line_m = transform(to_m.transform, line_ll)

    if line_m.length == 0:
        return coords_latlon

    distances = [0.0]
    current = spacing_m
    while current < line_m.length:
        distances.append(current)
        current += spacing_m
    if distances[-1] != line_m.length:
        distances.append(line_m.length)

    sampled = []
    for dist in distances:
        point_m = line_m.interpolate(dist)
        lon, lat = transform(to_deg.transform, point_m).coords[0]
        sampled.append((lat, lon))

    return sampled


def sample_lines_from_json(
    input_path: str,
    output_path: str,
    spacing_m: float = 25.0,
) -> None:
    with open(input_path, "r", encoding="utf-8") as input_file:
        lines_data = json.load(input_file)

    sampled_data: List[Dict[str, Any]] = []
    for item in lines_data:
        coords = item.get("coordenadas", [])
        if not coords:
            continue
        sampled_coords = sample_line_coords(coords, spacing_m=spacing_m)
        sampled_item = {
            "linha": item.get("linha", ""),
            "coordenadas": sampled_coords,
        }
        sampled_data.append(sampled_item)

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(sampled_data, output_file, ensure_ascii=True, indent=2)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    json_dir = repo_root / "data" / "json"

    ida_in = json_dir / "IDA.json"
    ida_out = json_dir / "IDA_amostrado.json"
    volta_in = json_dir / "VOLTA.json"
    volta_out = json_dir / "VOLTA_amostrado.json"

    sample_lines_from_json(str(ida_in), str(ida_out), spacing_m=25.0)
    sample_lines_from_json(str(volta_in), str(volta_out), spacing_m=25.0)

    print(f"Amostragem concluida: {ida_out}")
    print(f"Amostragem concluida: {volta_out}")


if __name__ == "__main__":
    main()
