from pathlib import Path
import json
from typing import List, Dict, Any


def merge_line_and_street_data_sequential(
    amostrado_path: Path,
    ruas_path: Path,
    output_path: Path,
) -> None:
    with open(amostrado_path, "r", encoding="utf-8") as file:
        lines_data = json.load(file)

    with open(ruas_path, "r", encoding="utf-8") as file:
        ruas_data = json.load(file)

    merged: List[Dict[str, Any]] = []
    ruas_index = 0

    for line_item in lines_data:
        linha_nome = line_item.get("linha", "")
        coordenadas_linha = line_item.get("coordenadas", [])
        num_points = len(coordenadas_linha)

        for _ in range(num_points):
            if ruas_index >= len(ruas_data):
                break

            rua_item = ruas_data[ruas_index]
            coords = rua_item.get("coordenadas", [])
            rua = rua_item.get("rua", "")

            merged.append({
                "linha": linha_nome,
                "coordenadas": coords,
                "rua": rua,
            })

            ruas_index += 1

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(merged, output_file, ensure_ascii=True, indent=2)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    json_dir = repo_root / "data" / "json"
    tratado_dir = json_dir / "dado-tratado"
    ruas_dir = json_dir / "dados-ruas"
    output_dir = json_dir / "dado-linhas"

    for prefix in ["IDA", "VOLTA"]:
        amostrado_path = tratado_dir / f"{prefix}_amostrado.json"
        ruas_path = ruas_dir / f"{prefix}_ruas.json"
        output_path = output_dir / f"{prefix}_linhas_ruas.json"

        merge_line_and_street_data_sequential(amostrado_path, ruas_path, output_path)

        print(f"{prefix}: arquivo gerado: {output_path}")


if __name__ == "__main__":
    main()
