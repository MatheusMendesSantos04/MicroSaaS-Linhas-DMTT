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
            "dados_unificados": root_dir / "data" / "json" / "dados_unificados.json",
            "horarios": root_dir / "data" / "json" / "horarios" / "horarios.json",
        }
        self.lines_by_id: Dict[str, UnifiedLine] = {}
        self.line_ids_by_name_norm: Dict[str, str] = {}
        # rua_index: normalized_via → [(line_id, line_nome, sentido, codigo)]
        self.rua_index: Dict[str, List[Tuple[str, str, str, Optional[str]]]] = {}
        # codigo_index: codigo → [(line_id, line_nome, sentido, via)]
        self.codigo_index: Dict[str, List[Tuple[str, str, str, str]]] = {}
        # horario_index: numero_4dig → {dia_util, sabado, domingo}
        self.horario_index: Dict[str, dict] = {}
        self._load()

    def _load_json(self, path: Path):
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load(self) -> None:
        dados = self._load_json(self.paths["dados_unificados"])

        for nome, sentidos in dados.items():
            line_id = build_line_id(nome)
            ida   = sentidos.get("ida",   {})
            volta = sentidos.get("volta", {})
            line = UnifiedLine(
                id=line_id,
                nome=nome,
                ida_coordenadas=ida.get("coordenadas", []),
                volta_coordenadas=volta.get("coordenadas", []),
                ida_ruas=[
                    RuaItem(via=r["via"], codigo=r.get("codigo"), match=r.get("match", ""))
                    for r in ida.get("ruas", [])
                ],
                volta_ruas=[
                    RuaItem(via=r["via"], codigo=r.get("codigo"), match=r.get("match", ""))
                    for r in volta.get("ruas", [])
                ],
            )
            self.lines_by_id[line_id] = line
            self.line_ids_by_name_norm[normalize_text(nome)] = line_id

        horarios_path = self.paths["horarios"]
        if horarios_path.exists():
            self.horario_index = self._load_json(horarios_path)

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

    def suggest_ruas(self, query: str, limit: int = 10) -> List[str]:
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []
        matches = [key for key in self.rua_index if normalized_query in key]
        matches.sort()
        return matches[:limit]

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

    @staticmethod
    def _horario_to_minutos(h: str) -> int:
        parts = h.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    def search_ruas_horario(
        self,
        query: str,
        horario: str,
        dia: str,
        janela: int = 20,
        limit: int = 100,
    ) -> List[Tuple[str, str, str, str, Optional[str], List[str]]]:
        target = self._horario_to_minutos(horario)
        base = self.search_ruas(query, limit=limit)
        enriched: List[Tuple[str, str, str, str, Optional[str], List[str]]] = []
        for line_id, line_name, sentido, rua_norm, codigo in base:
            m = re.match(r"^(\d{4})", line_name)
            if not m:
                continue
            horarios_linha = self.horario_index.get(m.group(1))
            if not horarios_linha:
                continue
            tempos: List[str] = horarios_linha.get(dia, {}).get(sentido, [])
            proximos = [t for t in tempos if abs(self._horario_to_minutos(t) - target) <= janela]
            if proximos:
                enriched.append((line_id, line_name, sentido, rua_norm, codigo, proximos))
        return enriched

    def get_horarios(self, linha_id: str) -> Optional[dict]:
        line = self.get_line(linha_id)
        if line is None:
            return None
        m = re.match(r"^(\d{4})", line.nome)
        if not m:
            return None
        return self.horario_index.get(m.group(1))

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
