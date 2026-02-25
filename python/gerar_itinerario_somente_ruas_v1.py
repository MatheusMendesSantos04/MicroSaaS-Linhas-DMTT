"""
Gera versão enxuta do itinerário contendo somente nomes de ruas.

Entrada:
- python/data/intinerario/itinerario_completo_rua_principal_v2.json

Saída:
- python/data/intinerario/itinerario_completo_rua_principal_somente_ruas_v1.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def dedupe_preservando_ordem(valores: list[str]) -> list[str]:
    vistos: set[str] = set()
    saida: list[str] = []
    for valor in valores:
        if valor not in vistos:
            vistos.add(valor)
            saida.append(valor)
    return saida


def extrair_ruas(payload_sentido: list[Any]) -> list[str]:
    ruas: list[str] = []
    for item in payload_sentido:
        if isinstance(item, dict):
            rua = item.get("rua")
            if isinstance(rua, str) and rua.strip():
                ruas.append(rua.strip())
        elif isinstance(item, str) and item.strip():
            ruas.append(item.strip())
    return dedupe_preservando_ordem(ruas)


def main() -> None:
    base_dir = Path(__file__).parent.parent
    pasta = base_dir / "python" / "data" / "intinerario"

    input_json = pasta / "itinerario_completo_rua_principal_v2.json"
    output_json = pasta / "itinerario_completo_rua_principal_somente_ruas_v1.json"

    if not input_json.exists():
        print(f"❌ Arquivo não encontrado: {input_json}")
        return

    data = json.loads(input_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("❌ Formato inválido no JSON de entrada.")
        return

    saida: dict[str, Any] = {}

    total_ida = 0
    total_volta = 0

    for linha, payload in data.items():
        ida = extrair_ruas(payload.get("ida", [])) if isinstance(payload, dict) else []
        volta = extrair_ruas(payload.get("volta", [])) if isinstance(payload, dict) else []

        total_ida += len(ida)
        total_volta += len(volta)

        saida[linha] = {
            "ida": ida,
            "volta": volta,
        }

    output_json.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    print("✅ JSON enxuto gerado")
    print(f"📄 Saída: {output_json}")
    print(f"🚌 Linhas: {len(saida)}")
    print(f"➡️  Ruas IDA: {total_ida}")
    print(f"⬅️  Ruas VOLTA: {total_volta}")


if __name__ == "__main__":
    main()
