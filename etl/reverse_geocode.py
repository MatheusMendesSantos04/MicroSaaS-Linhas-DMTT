from pathlib import Path
import json
import time
from typing import Dict, List, Tuple, Any

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut


def _round_key(lat: float, lon: float, precision: int = 6) -> str:
    return f"{round(lat, precision)},{round(lon, precision)}"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=True, indent=2)


def reverse_geocode_points(
    points: List[Tuple[float, float]],
    cache: Dict[str, str],
    rate_seconds: float = 1.0,
) -> List[str]:
    geolocator = Nominatim(user_agent="micro_saas_dmtt")
    reverse = RateLimiter(
        geolocator.reverse,
        min_delay_seconds=rate_seconds,
        error_wait_seconds=rate_seconds,
        max_retries=2,
        swallow_exceptions=False,
    )

    results: List[str] = []
    for index, (lat, lon) in enumerate(points, start=1):
        key = _round_key(lat, lon)
        if key in cache:
            results.append(cache[key])
            if index % 100 == 0:
                print(f"Progresso: {index}/{len(points)} (cache)")
            continue

        address = ""
        try:
            location = reverse((lat, lon), zoom=18, language="pt", timeout=10)
            if location and location.raw:
                address = location.raw.get("display_name", "")
        except (GeocoderTimedOut, GeocoderServiceError):
            address = ""

        cache[key] = address
        results.append(address)

        if index % 25 == 0 or not address:


            
            status = "ok" if address else "falha"
            print(f"Progresso: {index}/{len(points)} ({status})")

        time.sleep(0.0)

    return results


def extract_points_from_lines(lines: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    for line in lines:
        coords = line.get("coordenadas", [])
        for lat, lon in coords:
            points.append((lat, lon))
    return points


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    json_dir = repo_root / "data" / "json"
    input_dir = json_dir / "dado-tratado"
    output_dir = json_dir / "dados-ruas"

    cache_path = output_dir / "geocode_cache.json"

    cache = _load_json(cache_path, default={})

    for prefix in ["VOLTA"]:
        input_path = input_dir / f"{prefix}_amostrado.json"
        output_path = output_dir / f"{prefix}_ruas.json"

        lines_data = _load_json(input_path, default=[])
        points = extract_points_from_lines(lines_data)
        addresses = reverse_geocode_points(points, cache, rate_seconds=1.0)

        output = []
        for (lat, lon), address in zip(points, addresses):
            output.append({"coordenadas": [lat, lon], "rua": address})

        _save_json(output_path, output)

        print(f"{prefix}: registros geocodificados: {len(output)}")
        print(f"{prefix}: saida: {output_path}")

    _save_json(cache_path, cache)
    print(f"Cache: {cache_path}")


if __name__ == "__main__":
    main()
