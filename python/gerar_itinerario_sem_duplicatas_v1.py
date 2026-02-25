"""
Gera itinerário completo por linha (IDA/VOLTA) removendo nomes de ruas duplicados.

Entradas:
- data/json/dado-linhas/IDA_linhas_ruas.json
- data/json/dado-linhas/VOLTA_linhas_ruas.json

Saída:
- python/data/itinerario_completo_sem_ruas_duplicadas_v1.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


TIPOS_VIA = (
    "RUA",
    "AVENIDA",
    "TRAVESSA",
    "ALAMEDA",
    "ESTRADA",
    "RODOVIA",
    "LADEIRA",
    "PRAÇA",
    "PRACA",
    "TERMINAL",
    "CONJUNTO",
    "QUADRA",
    "ACESSO",
)


def remover_acentos(texto: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def normalizar_para_chave(nome_rua: str) -> str:
    texto = remover_acentos(nome_rua.upper())
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def extrair_nome_rua_curto(rua_completa: str) -> str:
    partes = [p.strip() for p in rua_completa.split(",") if p.strip()]
    if not partes:
        return rua_completa.strip()

    for parte in partes:
        parte_up = parte.upper()
        if any(parte_up.startswith(tipo) for tipo in TIPOS_VIA):
            return parte

    return partes[0]


def carregar_json(caminho: Path) -> list[dict[str, Any]]:
    with caminho.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Formato inválido em {caminho}. Esperado lista.")

    return data


def processar_sentido(
    registros: list[dict[str, Any]],
    sentido: str,
    resultado: dict[str, dict[str, Any]],
) -> dict[str, int]:
    total_itens = 0
    total_duplicados = 0

    for item in registros:
        if not isinstance(item, dict):
            continue

        linha = item.get("linha")
        coordenadas = item.get("coordenadas")
        rua = item.get("rua")

        if not isinstance(linha, str) or not linha.strip():
            continue
        if not isinstance(rua, str) or not rua.strip():
            continue
        if not isinstance(coordenadas, list) or len(coordenadas) != 2:
            continue

        linha = linha.strip()
        nome_curto = extrair_nome_rua_curto(rua.strip())
        chave_rua = normalizar_para_chave(nome_curto)
        if not chave_rua:
            continue

        total_itens += 1

        resultado.setdefault(linha, {"ida": [], "volta": [], "_seen": {"ida": set(), "volta": set()}})

        seen: set[str] = resultado[linha]["_seen"][sentido]
        if chave_rua in seen:
            total_duplicados += 1
            continue

        seen.add(chave_rua)
        resultado[linha][sentido].append(
            {
                "rua": nome_curto,
                "coordenada": coordenadas,
                "rua_original": rua.strip(),
            }
        )

    return {"itens_lidos": total_itens, "duplicados_removidos": total_duplicados}


def main() -> None:
    base_dir = Path(__file__).parent.parent

    ida_path = base_dir / "data" / "json" / "dado-linhas" / "IDA_linhas_ruas.json"
    volta_path = base_dir / "data" / "json" / "dado-linhas" / "VOLTA_linhas_ruas.json"

    output_path = base_dir / "python" / "data" / "itinerario_completo_sem_ruas_duplicadas_v1.json"

    if not ida_path.exists():
        print(f"❌ Arquivo não encontrado: {ida_path}")
        return
    if not volta_path.exists():
        print(f"❌ Arquivo não encontrado: {volta_path}")
        return

    print("📖 Carregando IDA...")
    ida_data = carregar_json(ida_path)
    print(f"   Registros IDA: {len(ida_data)}")

    print("📖 Carregando VOLTA...")
    volta_data = carregar_json(volta_path)
    print(f"   Registros VOLTA: {len(volta_data)}")

    resultado: dict[str, dict[str, Any]] = {}

    print("🧹 Removendo ruas duplicadas por linha/sentido...")
    stats_ida = processar_sentido(ida_data, "ida", resultado)
    stats_volta = processar_sentido(volta_data, "volta", resultado)

    saida_final: dict[str, Any] = {}
    for linha in sorted(resultado.keys()):
        ida_list = resultado[linha]["ida"]
        volta_list = resultado[linha]["volta"]
        saida_final[linha] = {
            "ida": ida_list,
            "volta": volta_list,
            "resumo": {
                "ruas_unicas_ida": len(ida_list),
                "ruas_unicas_volta": len(volta_list),
            },
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(saida_final, f, ensure_ascii=False, indent=2)

    print("\n✅ Arquivo gerado com sucesso")
    print(f"📄 Saída: {output_path}")
    print(f"🚌 Linhas processadas: {len(saida_final)}")
    print("\n📊 Estatísticas")
    print(f"- IDA   itens lidos: {stats_ida['itens_lidos']}")
    print(f"- IDA   duplicados removidos: {stats_ida['duplicados_removidos']}")
    print(f"- VOLTA itens lidos: {stats_volta['itens_lidos']}")
    print(f"- VOLTA duplicados removidos: {stats_volta['duplicados_removidos']}")


if __name__ == "__main__":
    main()
