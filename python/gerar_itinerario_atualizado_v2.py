from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

INPUT_FILE = Path(
    "MicroSaaS-Linhas-DMTT/python/dado principal/intinerario manual/itinerario_completo_rua_principal_somente_ruas_v1.json"
)
OUTPUT_FILE = Path(
    "MicroSaaS-Linhas-DMTT/python/dado principal/intinerario manual/itinerario_completo_rua_principal_somente_ruas_v2.json"
)

REPLACEMENTS = {
    "AVERNIDA": "AVENIDA",
    "LADERA": "LADEIRA",
    "TRAVESSA PROFESSOR": "TRAVESSA PROFESSOR",
    "RUA PAUL DARCO": "RUA PAU DARCO",
}


def normalize_street_name(name: str) -> str:
    normalized = unicodedata.normalize("NFC", name).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.upper()

    for old, new in REPLACEMENTS.items():
        normalized = normalized.replace(old, new)

    return normalized


def pick_route_fields(item: dict) -> tuple[list[str], list[str]]:
    ida = item.get("ida-correto") or item.get("ida") or []
    volta = item.get("volta-correto") or item.get("volta") or []
    return ida, volta


def main() -> None:
    source = json.loads(INPUT_FILE.read_text(encoding="utf-8"))

    updated: dict[str, dict[str, list[str]]] = {}
    for linha, payload in source.items():
        ida_raw, volta_raw = pick_route_fields(payload)

        ida = [normalize_street_name(street) for street in ida_raw if isinstance(street, str) and street.strip()]
        volta = [normalize_street_name(street) for street in volta_raw if isinstance(street, str) and street.strip()]

        updated[linha] = {
            "ida": ida,
            "volta": volta,
        }

    OUTPUT_FILE.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Arquivo gerado: {OUTPUT_FILE}")
    print(f"Total de linhas: {len(updated)}")


if __name__ == "__main__":
    main()
