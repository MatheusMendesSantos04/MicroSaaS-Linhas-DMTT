import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
class RuaItem:
    via: str
    codigo: Optional[str]
    match: str


@dataclass
class UnifiedLine:
    id: str
    nome: str
    ida_coordenadas: List[List[float]]
    volta_coordenadas: List[List[float]]
    ida_ruas: List[RuaItem] = field(default_factory=list)
    volta_ruas: List[RuaItem] = field(default_factory=list)


class DataStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.paths = {
            "ida_amostrado": root_dir / "data" / "json" / "dado-tratado" / "IDA_amostrado.json",
            "volta_amostrado": root_dir / "data" / "json" / "dado-tratado" / "VOLTA_amostrado.json",
            "itinerario_com_codigos": root_dir / "data" / "json" / "intinerario-com-codigo-rua" / "itinerario_com_codigos.json",
        }
        self.lines_by_id: Dict[str, UnifiedLine] = {}
        self.line_ids_by_name_norm: Dict[str, str] = {}
        # rua_index: normalized_via → [(line_id, line_nome, sentido, codigo)]
        self.rua_index: Dict[str, List[Tuple[str, str, str, Optional[str]]]] = {}
        # codigo_index: codigo → [(line_id, line_nome, sentido, via)]
        self.codigo_index: Dict[str, List[Tuple[str, str, str, str]]] = {}
        self._load()

    def _load_json(self, path: Path):
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load(self) -> None:
        ida_data = self._load_json(self.paths["ida_amostrado"])
        volta_data = self._load_json(self.paths["volta_amostrado"])
        itinerario_data = self._load_json(self.paths["itinerario_com_codigos"])

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
                )
            else:
                current.volta_coordenadas = item.get("coordenadas", [])

        for itinerario_key, sentidos in itinerario_data.items():
            norm = normalize_text(itinerario_key)
            current = by_norm_name.get(norm)
            if current is None:
                line_id = build_line_id(itinerario_key)
                current = UnifiedLine(
                    id=line_id,
                    nome=itinerario_key,
                    ida_coordenadas=[],
                    volta_coordenadas=[],
                )
                by_norm_name[norm] = current

            current.ida_ruas = [
                RuaItem(via=r["via"], codigo=r.get("codigo"), match=r.get("match", ""))
                for r in sentidos.get("ida", [])
            ]
            current.volta_ruas = [
                RuaItem(via=r["via"], codigo=r.get("codigo"), match=r.get("match", ""))
                for r in sentidos.get("volta", [])
            ]

        for norm, line in by_norm_name.items():
            self.lines_by_id[line.id] = line
            self.line_ids_by_name_norm[norm] = line.id

        self._build_indexes()

    def _build_indexes(self) -> None:
        rua_index: Dict[str, List[Tuple[str, str, str, Optional[str]]]] = {}
        codigo_index: Dict[str, List[Tuple[str, str, str, str]]] = {}

        for line in self.lines_by_id.values():
            for rua in line.ida_ruas:
                key = normalize_text(rua.via)
                rua_index.setdefault(key, []).append((line.id, line.nome, "ida", rua.codigo))
                if rua.codigo:
                    codigo_index.setdefault(rua.codigo, []).append(
                        (line.id, line.nome, "ida", rua.via)
                    )
            for rua in line.volta_ruas:
                key = normalize_text(rua.via)
                rua_index.setdefault(key, []).append((line.id, line.nome, "volta", rua.codigo))
                if rua.codigo:
                    codigo_index.setdefault(rua.codigo, []).append(
                        (line.id, line.nome, "volta", rua.via)
                    )

        self.rua_index = rua_index
        self.codigo_index = codigo_index

    def list_lines(self) -> List[UnifiedLine]:
        return sorted(self.lines_by_id.values(), key=lambda line: line.nome)

    def get_line(self, line_id: str) -> Optional[UnifiedLine]:
        return self.lines_by_id.get(line_id)

    def get_metadata(self) -> dict:
        return {
            "total_linhas": len(self.lines_by_id),
            "total_ruas_indexadas": len(self.rua_index),
            "arquivos_origem": {key: str(path) for key, path in self.paths.items()},
        }

    def search_ruas(
        self, query: str, limit: int = 100
    ) -> List[Tuple[str, str, str, str, Optional[str]]]:
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []

        results: List[Tuple[str, str, str, str, Optional[str]]] = []
        seen = set()
        for key, items in self.rua_index.items():
            if normalized_query in key:
                for line_id, line_name, sentido, codigo in items:
                    dedup_key = (line_id, sentido, key)
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)
                    results.append((line_id, line_name, sentido, key, codigo))
                    if len(results) >= limit:
                        return results
        return results

    def search_by_codigo(
        self, codigo: str
    ) -> List[Tuple[str, str, str, str]]:
        return self.codigo_index.get(codigo, [])

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
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": self._to_geojson_coords(line.ida_coordenadas),
                    },
                    "properties": {"linha_id": line.id, "linha_nome": line.nome, "sentido": "ida"},
                })

            if include_volta and line.volta_coordenadas:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": self._to_geojson_coords(line.volta_coordenadas),
                    },
                    "properties": {"linha_id": line.id, "linha_nome": line.nome, "sentido": "volta"},
                })

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
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": self._to_geojson_coords(line.ida_coordenadas),
                },
                "properties": {"linha_id": line.id, "linha_nome": line.nome, "sentido": "ida"},
            })

        if include_volta and line.volta_coordenadas:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": self._to_geojson_coords(line.volta_coordenadas),
                },
                "properties": {"linha_id": line.id, "linha_nome": line.nome, "sentido": "volta"},
            })

        return {"type": "FeatureCollection", "features": features}
