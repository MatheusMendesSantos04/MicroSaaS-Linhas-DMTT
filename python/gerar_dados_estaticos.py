"""Gera os JSONs estáticos consumidos pelo frontend (sem backend).

Lê data/json/dados_unificados.json + horarios/horarios.json + terminais.json
e escreve em frontend/public/data/:
  - linhas.json             lista resumida das linhas
  - linhas/{id}.json        detalhe de uma linha (coords + ruas IDA/VOLTA)
  - rua_index.json          nome da via -> ocorrências (linha/sentido/código)
  - horarios_por_linha.json horários por linha (keyed por linha_id)
  - terminais.json          cópia direta
  - geojson_todas.json      FeatureCollection com todas as linhas (visão padrão do mapa)

Rodar sempre que dados_unificados.json ou horarios.json mudarem, antes do
`npm run build` / upload do frontend.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS_UNIFICADOS = ROOT / "data" / "json" / "dados_unificados.json"
HORARIOS = ROOT / "data" / "json" / "horarios" / "horarios.json"
TERMINAIS = ROOT / "data" / "json" / "terminais.json"
OUT_DIR = ROOT / "frontend" / "public" / "data"


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


def to_geojson_coords(coordenadas):
    return [[point[1], point[0]] for point in coordenadas if len(point) >= 2]


def main() -> None:
    dados = json.loads(DADOS_UNIFICADOS.read_text(encoding="utf-8"))
    horarios = json.loads(HORARIOS.read_text(encoding="utf-8")) if HORARIOS.exists() else {}
    terminais = json.loads(TERMINAIS.read_text(encoding="utf-8")) if TERMINAIS.exists() else []

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "linhas").mkdir(parents=True, exist_ok=True)

    linhas_resumo = []
    rua_index: dict[str, list] = {}
    horarios_por_linha: dict[str, dict] = {}
    features_todas = []

    for nome, sentidos in dados.items():
        line_id = build_line_id(nome)
        ida = sentidos.get("ida", {})
        volta = sentidos.get("volta", {})
        ida_coords = ida.get("coordenadas", [])
        volta_coords = volta.get("coordenadas", [])
        ida_ruas = ida.get("ruas", [])
        volta_ruas = volta.get("ruas", [])

        linhas_resumo.append({
            "id": line_id,
            "nome": nome,
            "tem_ida": bool(ida_coords),
            "tem_volta": bool(volta_coords),
            "tem_itinerario_manual": bool(ida_ruas or volta_ruas),
        })

        detalhe = {
            "id": line_id,
            "nome": nome,
            "ida": {"coordenadas": ida_coords, "ruas": ida_ruas},
            "volta": {"coordenadas": volta_coords, "ruas": volta_ruas},
        }
        (OUT_DIR / "linhas" / f"{line_id}.json").write_text(
            json.dumps(detalhe, ensure_ascii=False), encoding="utf-8"
        )

        for sentido, ruas, coords in (("ida", ida_ruas, ida_coords), ("volta", volta_ruas, volta_coords)):
            seen = set()
            for rua in ruas:
                key = normalize_text(rua["via"])
                dedup_key = (line_id, sentido, key)
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                rua_index.setdefault(key, []).append({
                    "linha_id": line_id,
                    "linha_nome": nome,
                    "sentido": sentido,
                    "codigo": rua.get("codigo"),
                })
            if coords:
                features_todas.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": to_geojson_coords(coords)},
                    "properties": {"linha_id": line_id, "linha_nome": nome, "sentido": sentido},
                })

        m = re.match(r"^(\d{4})", nome)
        if m and m.group(1) in horarios:
            horarios_por_linha[line_id] = horarios[m.group(1)]

    linhas_resumo.sort(key=lambda x: x["nome"])

    (OUT_DIR / "linhas.json").write_text(
        json.dumps({"total": len(linhas_resumo), "itens": linhas_resumo}, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT_DIR / "rua_index.json").write_text(
        json.dumps(rua_index, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "horarios_por_linha.json").write_text(
        json.dumps(horarios_por_linha, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "terminais.json").write_text(
        json.dumps(terminais, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "geojson_todas.json").write_text(
        json.dumps({"type": "FeatureCollection", "features": features_todas}, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"{len(linhas_resumo)} linhas, {len(rua_index)} vias indexadas -> {OUT_DIR}")


if __name__ == "__main__":
    main()
