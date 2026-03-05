import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.upper().strip()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def build_line_id(line_name: str) -> str:
    normalized = normalize_text(line_name)
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"ln-{digest}"


@dataclass
class UnifiedLine:
    id: str
    nome: str
    ida_coordenadas: List[List[float]]
    volta_coordenadas: List[List[float]]
    ida_ruas: List[str]
    volta_ruas: List[str]


class DataStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.paths = {
            "ida_amostrado": root_dir / "data" / "json" / "dado-tratado" / "IDA_amostrado.json",
            "volta_amostrado": root_dir / "data" / "json" / "dado-tratado" / "VOLTA_amostrado.json",
            "itinerario_manual": root_dir
            / "python"
            / "dado principal"
            / "intinerario manual"
            / "itinerario_completo_rua_principal_somente_ruas_v1.json",
        }
        self.lines_by_id: Dict[str, UnifiedLine] = {}
        self.line_ids_by_name_norm: Dict[str, str] = {}
        self.rua_index: Dict[str, List[Tuple[str, str, str]]] = {}
        self._load()

    def _load_json(self, path: Path):
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load(self) -> None:
        ida_data = self._load_json(self.paths["ida_amostrado"])
        volta_data = self._load_json(self.paths["volta_amostrado"])
        manual_data = self._load_json(self.paths["itinerario_manual"])

        by_norm_name: Dict[str, UnifiedLine] = {}

        for item in ida_data:
            name = item.get("linha", "").strip()
            if not name:
                continue
            norm = normalize_text(name)
            line_id = build_line_id(name)
            by_norm_name[norm] = UnifiedLine(
                id=line_id,
                nome=name,
                ida_coordenadas=item.get("coordenadas", []),
                volta_coordenadas=[],
                ida_ruas=[],
                volta_ruas=[],
            )

        for item in volta_data:
            name = item.get("linha", "").strip()
            if not name:
                continue
            norm = normalize_text(name)
            current = by_norm_name.get(norm)
            if current is None:
                line_id = build_line_id(name)
                by_norm_name[norm] = UnifiedLine(
                    id=line_id,
                    nome=name,
                    ida_coordenadas=[],
                    volta_coordenadas=item.get("coordenadas", []),
                    ida_ruas=[],
                    volta_ruas=[],
                )
            else:
                current.volta_coordenadas = item.get("coordenadas", [])

        for manual_name, sentidos in manual_data.items():
            norm = normalize_text(manual_name)
            current = by_norm_name.get(norm)
            if current is None:
                line_id = build_line_id(manual_name)
                current = UnifiedLine(
                    id=line_id,
                    nome=manual_name,
                    ida_coordenadas=[],
                    volta_coordenadas=[],
                    ida_ruas=[],
                    volta_ruas=[],
                )
                by_norm_name[norm] = current

            current.ida_ruas = sentidos.get("ida-correto", [])
            current.volta_ruas = sentidos.get("volta-correto", [])

        for norm, line in by_norm_name.items():
            self.lines_by_id[line.id] = line
            self.line_ids_by_name_norm[norm] = line.id

        self._build_rua_index()

    def _build_rua_index(self) -> None:
        index: Dict[str, List[Tuple[str, str, str]]] = {}
        for line in self.lines_by_id.values():
            for rua in line.ida_ruas:
                key = normalize_text(rua)
                index.setdefault(key, []).append((line.id, line.nome, "ida"))
            for rua in line.volta_ruas:
                key = normalize_text(rua)
                index.setdefault(key, []).append((line.id, line.nome, "volta"))
        self.rua_index = index

    def list_lines(self) -> List[UnifiedLine]:
        return sorted(self.lines_by_id.values(), key=lambda line: line.nome)

    def get_line(self, line_id: str) -> UnifiedLine | None:
        return self.lines_by_id.get(line_id)

    def get_metadata(self) -> dict:
        return {
            "total_linhas": len(self.lines_by_id),
            "total_ruas_indexadas": len(self.rua_index),
            "arquivos_origem": {key: str(path) for key, path in self.paths.items()},
        }

    def search_ruas(self, query: str, limit: int = 100) -> List[Tuple[str, str, str, str]]:
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []

        results: List[Tuple[str, str, str, str]] = []
        seen = set()
        for key, items in self.rua_index.items():
            if normalized_query in key:
                for line_id, line_name, sentido in items:
                    dedup_key = (line_id, sentido, key)
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)
                    results.append((line_id, line_name, sentido, key))
                    if len(results) >= limit:
                        return results
        return results

    @staticmethod
    def _to_geojson_coords(coordenadas: List[List[float]]) -> List[List[float]]:
        geojson_coords: List[List[float]] = []
        for point in coordenadas:
            if len(point) < 2:
                continue
            lat, lon = point[0], point[1]
            geojson_coords.append([lon, lat])
        return geojson_coords

    def get_geojson_feature_collection(self, sentido: str | None = None) -> Dict[str, Any]:
        sentido_normalizado = (sentido or "").lower().strip()
        if sentido_normalizado not in {"", "ida", "volta", "ambos"}:
            raise ValueError("sentido deve ser um destes valores: ida, volta, ambos")

        features: List[Dict[str, Any]] = []
        for line in self.list_lines():
            include_ida = sentido_normalizado in {"", "ida", "ambos"}
            include_volta = sentido_normalizado in {"", "volta", "ambos"}

            if include_ida and line.ida_coordenadas:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": self._to_geojson_coords(line.ida_coordenadas),
                        },
                        "properties": {
                            "linha_id": line.id,
                            "linha_nome": line.nome,
                            "sentido": "ida",
                        },
                    }
                )

            if include_volta and line.volta_coordenadas:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": self._to_geojson_coords(line.volta_coordenadas),
                        },
                        "properties": {
                            "linha_id": line.id,
                            "linha_nome": line.nome,
                            "sentido": "volta",
                        },
                    }
                )

        return {"type": "FeatureCollection", "features": features}

    def get_linha_geojson(self, linha_id: str, sentido: str | None = None) -> Dict[str, Any] | None:
        line = self.get_line(linha_id)
        if line is None:
            return None

        sentido_normalizado = (sentido or "").lower().strip()
        if sentido_normalizado not in {"", "ida", "volta", "ambos"}:
            raise ValueError("sentido deve ser um destes valores: ida, volta, ambos")

        features: List[Dict[str, Any]] = []
        include_ida = sentido_normalizado in {"", "ida", "ambos"}
        include_volta = sentido_normalizado in {"", "volta", "ambos"}

        if include_ida and line.ida_coordenadas:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": self._to_geojson_coords(line.ida_coordenadas),
                    },
                    "properties": {
                        "linha_id": line.id,
                        "linha_nome": line.nome,
                        "sentido": "ida",
                    },
                }
            )

        if include_volta and line.volta_coordenadas:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": self._to_geojson_coords(line.volta_coordenadas),
                    },
                    "properties": {
                        "linha_id": line.id,
                        "linha_nome": line.nome,
                        "sentido": "volta",
                    },
                }
            )

        return {"type": "FeatureCollection", "features": features}
