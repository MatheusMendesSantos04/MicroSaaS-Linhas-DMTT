"""
Une IDA_amostrado.json + VOLTA_amostrado.json + itinerario_com_codigos.json
em um único data/json/dados_unificados.json.

Formato de saída:
{
  "0024 - Gruta / Centro / Term. Rotary": {
    "ida":   { "coordenadas": [[lat, lon], ...], "ruas": [{via, codigo, match}] },
    "volta": { "coordenadas": [[lat, lon], ...], "ruas": [{via, codigo, match}] }
  },
  ...
}

Uso:
    python python/gerar_dados_unificados.py
"""

import json
import re
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

IDA_PATH       = BASE_DIR / "data" / "json" / "dado-tratado"           / "IDA_amostrado.json"
VOLTA_PATH     = BASE_DIR / "data" / "json" / "dado-tratado"           / "VOLTA_amostrado.json"
ITIN_PATH      = BASE_DIR / "data" / "json" / "intinerario-com-codigo-rua" / "itinerario_com_codigos.json"
SAIDA          = BASE_DIR / "data" / "json"                            / "dados_unificados.json"


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.upper().strip()
    t = re.sub(r"[^A-Z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    with IDA_PATH.open(encoding="utf-8") as f:
        ida_list = json.load(f)
    with VOLTA_PATH.open(encoding="utf-8") as f:
        volta_list = json.load(f)
    with ITIN_PATH.open(encoding="utf-8") as f:
        itinerario = json.load(f)

    # Indexa coords pelo nome normalizado
    ida_coords   = {normalize(i["linha"]): i["coordenadas"] for i in ida_list   if i.get("linha")}
    volta_coords = {normalize(i["linha"]): i["coordenadas"] for i in volta_list if i.get("linha")}

    unified = {}
    sem_ida, sem_volta = [], []

    for nome, sentidos in itinerario.items():
        norm  = normalize(nome)
        ida_c = ida_coords.get(norm, [])
        vol_c = volta_coords.get(norm, [])

        if not ida_c:
            sem_ida.append(nome)
        if not vol_c:
            sem_volta.append(nome)

        unified[nome] = {
            "ida": {
                "coordenadas": ida_c,
                "ruas": sentidos.get("ida", []),
            },
            "volta": {
                "coordenadas": vol_c,
                "ruas": sentidos.get("volta", []),
            },
        }

    with SAIDA.open("w", encoding="utf-8") as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)

    print(f"[OK] {len(unified)} linhas salvas em {SAIDA.name}")

    if sem_ida:
        print(f"\n[AVISO] {len(sem_ida)} linha(s) sem coordenadas de IDA:")
        for n in sem_ida:
            print(f"  - {n}")
    if sem_volta:
        print(f"\n[AVISO] {len(sem_volta)} linha(s) sem coordenadas de VOLTA:")
        for n in sem_volta:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
