"""
Gera uma versão do itinerário com nome principal de via por linha/sentido,
colapsando variações de trechos e removendo duplicidades.

Entrada:
- python/data/intinerario/itinerario_completo_sem_ruas_duplicadas_v1.json

Saídas (mesma pasta intinerario):
- itinerario_completo_rua_principal_v2.json
- relatorio_itinerario_rua_principal_v2.txt
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


TIPOS_VIA = {
    "RUA",
    "AVENIDA",
    "TRAVESSA",
    "ALAMEDA",
    "ESTRADA",
    "RODOVIA",
    "LADEIRA",
    "PRAÇA",
    "PRACA",
    "BECO",
    "TERMINAL",
    "ACESSO",
}

TIPO_PRIORIDADE = {
    "AVENIDA": 6,
    "RUA": 5,
    "ALAMEDA": 4,
    "ESTRADA": 4,
    "RODOVIA": 4,
    "LADEIRA": 4,
    "TRAVESSA": 3,
    "PRAÇA": 3,
    "PRACA": 3,
    "BECO": 2,
    "ACESSO": 2,
    "TERMINAL": 2,
}

BASES_GENERICAS = {
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "QUADRA",
    "BR",
    "AL",
    "TERMINAL",
}

ABREVIACOES = [
    (r"\bA\s+V\s*\.?\b", "AVENIDA"),
    (r"\bAV\.?\b", "AVENIDA"),
    (r"\bR\.?\b", "RUA"),
    (r"\bTV\.?\b", "TRAVESSA"),
    (r"\bTRAV\.?\b", "TRAVESSA"),
    (r"\bAL\.?\b", "ALAMEDA"),
    (r"\bEST\.?\b", "ESTRADA"),
    (r"\bROD\.?\b", "RODOVIA"),
    (r"\bPROF\.?\b", "PROFESSOR"),
    (r"\bDEP\.?\b", "DEPUTADO"),
    (r"\bDR\.?\b", "DOUTOR"),
    (r"\bDES\.?\b", "DESEMBARGADOR"),
    (r"\bCEL\.?\b", "CORONEL"),
    (r"\bMAJ\.?\b", "MAJOR"),
    (r"\bMAL\.?\b", "MARECHAL"),
    (r"\bJORN\.?\b", "JORNALISTA"),
    (r"\bSTA\.?\b", "SANTA"),
    (r"\bSTO\.?\b", "SANTO"),
]


def remover_acentos(texto: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def normalizar_texto(texto: str) -> str:
    t = remover_acentos(texto.upper())
    for pattern, repl in ABREVIACOES:
        t = re.sub(pattern, repl, t)
    t = re.sub(r"[^A-Z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def tipo_via(texto_norm: str) -> str | None:
    partes = texto_norm.split()
    if not partes:
        return None
    return partes[0] if partes[0] in TIPOS_VIA else None


def base_principal(texto_norm: str) -> str:
    partes = texto_norm.split()
    if not partes:
        return ""

    if partes[0] in TIPOS_VIA:
        partes = partes[1:]

    # Remove sufixos puramente numéricos no final (trechos, lotes, etc.)
    while partes and re.fullmatch(r"\d+[A-Z]?", partes[-1]):
        partes.pop()

    base = " ".join(partes).strip()
    return base


def chave_colapso(rua_original: str) -> str:
    norm = normalizar_texto(rua_original)
    if not norm:
        return ""

    base = base_principal(norm)

    # Evita colapsar demais em casos genéricos (ex.: QUADRA, A, BR)
    if not base or base in BASES_GENERICAS or len(base) < 4:
        return f"EXATO::{norm}"

    # evita bases de uma palavra curta demais
    if len(base.split()) == 1 and len(base) <= 6:
        return f"EXATO::{norm}"

    return f"BASE::{base}"


def escolher_nome_principal(
    variantes: list[str],
    freq_global_norm: dict[str, int],
) -> str:
    melhor = variantes[0]
    melhor_score = (-1, -1, -1)

    for v in variantes:
        norm = normalizar_texto(v)
        tipo = tipo_via(norm)
        prioridade_tipo = TIPO_PRIORIDADE.get(tipo or "", 1)
        freq = freq_global_norm.get(norm, 1)
        tamanho = len(norm)

        score = (freq, prioridade_tipo, tamanho)
        if score > melhor_score:
            melhor_score = score
            melhor = v

    return melhor


def gerar_v2(data_v1: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    # Frequência global para ajudar na escolha do nome principal
    freq_global_norm: dict[str, int] = defaultdict(int)
    for payload in data_v1.values():
        for sentido in ("ida", "volta"):
            for item in payload.get(sentido, []):
                if isinstance(item, dict) and isinstance(item.get("rua"), str):
                    freq_global_norm[normalizar_texto(item["rua"])] += 1

    saida_v2: dict[str, Any] = {}

    total_itens_antes = 0
    total_itens_depois = 0
    total_grupos_com_merge = 0

    detalhes_linhas: dict[str, Any] = {}

    for linha, payload in data_v1.items():
        linha_out = {"ida": [], "volta": [], "resumo": {}}
        detalhes_linhas[linha] = {"ida": [], "volta": []}

        for sentido in ("ida", "volta"):
            itens = payload.get(sentido, [])
            total_itens_antes += len(itens)

            grupos: dict[str, dict[str, Any]] = {}
            ordem_grupos: list[str] = []

            for item in itens:
                if not isinstance(item, dict):
                    continue

                rua = item.get("rua")
                coord = item.get("coordenada")
                rua_original = item.get("rua_original")

                if not isinstance(rua, str) or not rua.strip():
                    continue

                chave = chave_colapso(rua)
                if not chave:
                    continue

                if chave not in grupos:
                    grupos[chave] = {
                        "variantes": [],
                        "coords": [],
                        "originais": [],
                    }
                    ordem_grupos.append(chave)

                grupos[chave]["variantes"].append(rua)
                if isinstance(coord, list) and len(coord) == 2:
                    grupos[chave]["coords"].append(coord)
                if isinstance(rua_original, str) and rua_original.strip():
                    grupos[chave]["originais"].append(rua_original.strip())

            for chave in ordem_grupos:
                grupo = grupos[chave]
                variantes = grupo["variantes"]

                nome_principal = escolher_nome_principal(variantes, freq_global_norm)
                coord_principal = grupo["coords"][0] if grupo["coords"] else None

                variantes_unicas = []
                seen_var = set()
                for v in variantes:
                    if v not in seen_var:
                        seen_var.add(v)
                        variantes_unicas.append(v)

                originais_unicas = []
                seen_org = set()
                for o in grupo["originais"]:
                    if o not in seen_org:
                        seen_org.add(o)
                        originais_unicas.append(o)

                item_out = {
                    "rua": nome_principal,
                    "coordenada": coord_principal,
                    "qtd_trechos_colapsados": len(variantes),
                    "variantes_colapsadas": variantes_unicas,
                    "ruas_originais_colapsadas": originais_unicas[:12],
                }

                linha_out[sentido].append(item_out)

                if len(variantes_unicas) > 1:
                    total_grupos_com_merge += 1
                    detalhes_linhas[linha][sentido].append(
                        {
                            "rua_principal": nome_principal,
                            "qtd_variantes": len(variantes_unicas),
                            "variantes": variantes_unicas,
                        }
                    )

            total_itens_depois += len(linha_out[sentido])

        linha_out["resumo"] = {
            "ruas_ida_antes": len(payload.get("ida", [])),
            "ruas_ida_depois": len(linha_out["ida"]),
            "ruas_volta_antes": len(payload.get("volta", [])),
            "ruas_volta_depois": len(linha_out["volta"]),
        }

        saida_v2[linha] = linha_out

    resumo = {
        "linhas_total": len(saida_v2),
        "itens_antes": total_itens_antes,
        "itens_depois": total_itens_depois,
        "itens_colapsados": total_itens_antes - total_itens_depois,
        "grupos_com_merge": total_grupos_com_merge,
        "reducao_percentual": round(
            ((total_itens_antes - total_itens_depois) / total_itens_antes * 100)
            if total_itens_antes else 0,
            2,
        ),
    }

    return saida_v2, {"resumo": resumo, "detalhes_linhas": detalhes_linhas}


def escrever_relatorio_txt(meta: dict[str, Any], output_txt: Path) -> None:
    resumo = meta["resumo"]
    detalhes = meta["detalhes_linhas"]

    ranking: list[tuple[str, int]] = []
    for linha, payload in detalhes.items():
        qtd = len(payload.get("ida", [])) + len(payload.get("volta", []))
        ranking.append((linha, qtd))

    ranking.sort(key=lambda x: x[1], reverse=True)

    linhas: list[str] = []
    linhas.append("RELATÓRIO - ITINERÁRIO COM NOME PRINCIPAL DE VIA (V2)")
    linhas.append("=" * 78)
    linhas.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    linhas.append("")

    linhas.append("RESUMO")
    linhas.append("-" * 78)
    linhas.append(f"Linhas processadas: {resumo['linhas_total']}")
    linhas.append(f"Itens antes : {resumo['itens_antes']}")
    linhas.append(f"Itens depois: {resumo['itens_depois']}")
    linhas.append(f"Itens colapsados: {resumo['itens_colapsados']}")
    linhas.append(f"Redução percentual: {resumo['reducao_percentual']}%")
    linhas.append(f"Grupos com merge real (>=2 variantes): {resumo['grupos_com_merge']}")
    linhas.append("")

    linhas.append("TOP LINHAS COM MAIS AGRUPAMENTOS DE VARIANTES")
    linhas.append("-" * 78)
    for linha, qtd in ranking[:20]:
        linhas.append(f"{linha}: {qtd} agrupamentos")
    linhas.append("")

    linhas.append("AMOSTRA DE AGRUPAMENTOS")
    linhas.append("-" * 78)
    mostrados = 0
    for linha, _ in ranking:
        if mostrados >= 12:
            break

        ida = detalhes[linha].get("ida", [])
        volta = detalhes[linha].get("volta", [])
        if not ida and not volta:
            continue

        linhas.append(f"Linha: {linha}")
        for sentido, blocos in (("IDA", ida), ("VOLTA", volta)):
            for b in blocos[:4]:
                linhas.append(
                    f"  {sentido} | principal: {b['rua_principal']} | variantes: {b['qtd_variantes']}"
                )
                for v in b["variantes"][:4]:
                    linhas.append(f"    - {v}")
        linhas.append("")
        mostrados += 1

    output_txt.write_text("\n".join(linhas), encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).parent.parent
    pasta_itinerario = base_dir / "python" / "data" / "intinerario"

    input_json = pasta_itinerario / "itinerario_completo_sem_ruas_duplicadas_v1.json"
    output_json = pasta_itinerario / "itinerario_completo_rua_principal_v2.json"
    output_txt = pasta_itinerario / "relatorio_itinerario_rua_principal_v2.txt"

    if not input_json.exists():
        print(f"❌ Arquivo não encontrado: {input_json}")
        return

    data_v1 = json.loads(input_json.read_text(encoding="utf-8"))
    if not isinstance(data_v1, dict):
        print("❌ Formato inválido no JSON de entrada.")
        return

    print("🧠 Agrupando variações para nome principal de via...")
    saida_v2, meta = gerar_v2(data_v1)

    output_json.write_text(json.dumps(saida_v2, ensure_ascii=False, indent=2), encoding="utf-8")
    escrever_relatorio_txt(meta, output_txt)

    resumo = meta["resumo"]
    print("✅ Concluído")
    print(f"📄 JSON: {output_json}")
    print(f"📝 TXT : {output_txt}")
    print(
        f"📊 Antes={resumo['itens_antes']} | Depois={resumo['itens_depois']} | "
        f"Redução={resumo['reducao_percentual']}%"
    )


if __name__ == "__main__":
    main()
