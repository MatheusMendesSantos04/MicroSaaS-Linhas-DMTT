"""
Compara itinerários antigos (PDF por linha) com o itinerário novo gerado no JSON,
mostrando diferenças por linha e por sentido (IDA/VOLTA).

Entradas:
- data/pdf-intinerarios-por-via-todas-linhas/linha_*.pdf
- python/data/intinerario/itinerario_completo_sem_ruas_duplicadas_v1.json

Saídas:
- python/data/resto/relatorio_comparacao_itinerario_antigo_vs_novo_v1.txt
- python/data/resto/comparacao_itinerario_antigo_vs_novo_v1.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from rapidfuzz import fuzz, process


ABREVIACOES: list[tuple[str, str]] = [
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
    "ACESSO",
    "TERMINAL",
    "CONJUNTO",
}

RUÍDOS = {
    "SUB",
    "TOTAL",
    "SUBTOTAL",
    "RECURSOS",
    "INFORMATICA",
    "INTINERARIOPORVIA",
    "ITINERARIOPORVIA",
}


def remover_acentos(texto: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def limpar_ocr(texto: str) -> str:
    t = texto.upper()
    t = t.replace("A VENIDA", "AVENIDA")
    t = re.sub(r"\b([A-Z]{3,})\s+([A-Z])\b", r"\1\2", t)
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"\bIDA\b", " ", t)
    t = re.sub(r"\bVOLTA\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalizar_via(texto: str) -> str:
    t = limpar_ocr(texto)
    t = remover_acentos(t)

    for pattern, repl in ABREVIACOES:
        t = re.sub(pattern, repl, t)

    t = re.sub(r"[^A-Z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    tokens = [tok for tok in t.split() if tok not in RUÍDOS]
    t = " ".join(tokens).strip()
    return t


def sem_tipo_via(texto_norm: str) -> str:
    partes = texto_norm.split()
    if partes and partes[0] in TIPOS_VIA:
        return " ".join(partes[1:]).strip()
    return texto_norm


def dedupe_preservando_ordem(lista: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in lista:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def extrair_antigo_por_codigo(pasta_pdf: Path) -> dict[str, dict[str, list[str]]]:
    resultado: dict[str, dict[str, list[str]]] = {}

    for pdf in sorted(pasta_pdf.glob("linha_*.pdf")):
        m_code = re.search(r"linha_(\d{4})", pdf.name)
        if not m_code:
            continue
        codigo = m_code.group(1)

        reader = PdfReader(pdf)
        texto = "\n".join((p.extract_text() or "") for p in reader.pages)

        sentido = "ida"
        ida: list[str] = []
        volta: list[str] = []

        for raw in texto.splitlines():
            line = re.sub(r"\s+", " ", raw).strip()
            if not line:
                continue

            line = re.sub(r"(\d{3,6})(IDA|VOLTA)\b", r"\1 \2 ", line, flags=re.IGNORECASE)

            line_up = line.upper()
            if " VOLTA " in f" {line_up} " or line_up.startswith("VOLTA "):
                sentido = "volta"
            elif " IDA " in f" {line_up} " or line_up.startswith("IDA "):
                sentido = "ida"

            m = re.match(r"^\d+\s+\d{3,6}\s+(?:IDA|VOLTA)?\s*(.+?)\s*$", line, flags=re.IGNORECASE)
            if not m:
                continue

            via = m.group(1).strip()
            via_norm = normalizar_via(via)
            if not via_norm:
                continue
            if via_norm in {"SUB TOTAL", "TOTAL", "0"}:
                continue

            if sentido == "ida":
                ida.append(via_norm)
            else:
                volta.append(via_norm)

        resultado[codigo] = {
            "ida": dedupe_preservando_ordem(ida),
            "volta": dedupe_preservando_ordem(volta),
        }

    return resultado


def extrair_novo_por_codigo(json_novo: Path) -> dict[str, dict[str, list[str]]]:
    data = json.loads(json_novo.read_text(encoding="utf-8"))
    resultado: dict[str, dict[str, list[str]]] = {}

    for linha_nome, payload in data.items():
        m = re.search(r"(\d{4})", linha_nome)
        if not m:
            continue
        codigo = m.group(1)

        ida: list[str] = []
        volta: list[str] = []

        for item in payload.get("ida", []):
            if isinstance(item, dict) and isinstance(item.get("rua"), str):
                via_norm = normalizar_via(item["rua"])
                if via_norm:
                    ida.append(via_norm)

        for item in payload.get("volta", []):
            if isinstance(item, dict) and isinstance(item.get("rua"), str):
                via_norm = normalizar_via(item["rua"])
                if via_norm:
                    volta.append(via_norm)

        resultado[codigo] = {
            "ida": dedupe_preservando_ordem(ida),
            "volta": dedupe_preservando_ordem(volta),
        }

    return resultado


def fuzzy_match_um_para_um(old_list: list[str], new_list: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
    mapa: dict[str, str] = {}

    new_candidates = list(dict.fromkeys(new_list))
    new_set = set(new_candidates)
    old_set = set(old_list)

    exato = old_set & new_set

    usados_new = set(exato)
    faltando_old = [x for x in old_list if x not in exato]

    # match por sem tipo de via
    idx_sem_tipo: dict[str, str] = {}
    for n in new_candidates:
        chave = sem_tipo_via(n)
        if chave and chave not in idx_sem_tipo:
            idx_sem_tipo[chave] = n

    restantes_old: list[str] = []
    for o in faltando_old:
        chave = sem_tipo_via(o)
        if chave in idx_sem_tipo and idx_sem_tipo[chave] not in usados_new:
            mapa[o] = idx_sem_tipo[chave]
            usados_new.add(idx_sem_tipo[chave])
        else:
            restantes_old.append(o)

    # fuzzy final
    pool = [n for n in new_candidates if n not in usados_new]
    for o in restantes_old:
        if not pool:
            break
        candidato = process.extractOne(o, pool, scorer=fuzz.token_set_ratio)
        if not candidato:
            continue
        alvo, score, _ = candidato

        score_ratio = fuzz.ratio(o, alvo)
        score_partial = fuzz.partial_ratio(o, alvo)

        if score >= 88 and score_ratio >= 78 and score_partial >= 80:
            mapa[o] = alvo
            usados_new.add(alvo)
            pool = [x for x in pool if x != alvo]

    old_matched = set(exato) | set(mapa.keys())
    new_matched = set(exato) | set(mapa.values())

    old_unmatched = [x for x in old_list if x not in old_matched]
    new_unmatched = [x for x in new_list if x not in new_matched]

    return mapa, old_unmatched, new_unmatched


def comparar(antigo: dict[str, dict[str, list[str]]], novo: dict[str, dict[str, list[str]]]) -> dict[str, Any]:
    codigos_antigo = set(antigo.keys())
    codigos_novo = set(novo.keys())
    codigos_comuns = sorted(codigos_antigo & codigos_novo)

    resultado: dict[str, Any] = {
        "resumo": {},
        "por_linha": {},
    }

    total_old = 0
    total_old_match = 0
    total_new = 0

    for codigo in codigos_comuns:
        resultado["por_linha"][codigo] = {}

        for sentido in ("ida", "volta"):
            old_list = antigo.get(codigo, {}).get(sentido, [])
            new_list = novo.get(codigo, {}).get(sentido, [])

            mapa_fuzzy, old_unmatched, new_unmatched = fuzzy_match_um_para_um(old_list, new_list)
            exato = sorted(set(old_list) & set(new_list))

            matched_old_count = len(exato) + len(mapa_fuzzy)

            total_old += len(old_list)
            total_old_match += matched_old_count
            total_new += len(new_list)

            resultado["por_linha"][codigo][sentido] = {
                "old_total": len(old_list),
                "new_total": len(new_list),
                "match_exato": len(exato),
                "match_aproximado": len(mapa_fuzzy),
                "old_nao_encontradas": old_unmatched,
                "new_extras": new_unmatched,
                "aproximadas": [{"antigo": k, "novo": v} for k, v in sorted(mapa_fuzzy.items())],
            }

    cobertura = (total_old_match / total_old * 100) if total_old else 0.0

    resultado["resumo"] = {
        "codigos_antigo": len(codigos_antigo),
        "codigos_novo": len(codigos_novo),
        "codigos_comuns": len(codigos_comuns),
        "codigos_apenas_antigo": sorted(codigos_antigo - codigos_novo),
        "codigos_apenas_novo": sorted(codigos_novo - codigos_antigo),
        "vias_antigo_total": total_old,
        "vias_novo_total": total_new,
        "vias_antigo_encontradas_no_novo": total_old_match,
        "cobertura_percentual": round(cobertura, 2),
    }

    return resultado


def escrever_relatorio_txt(comparacao: dict[str, Any], output_txt: Path) -> None:
    resumo = comparacao["resumo"]
    por_linha = comparacao["por_linha"]

    linhas: list[str] = []
    linhas.append("RELATÓRIO - ITINERÁRIO ANTIGO (PDF) x NOVO (JSON)")
    linhas.append("=" * 76)
    linhas.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    linhas.append("")

    linhas.append("RESUMO GERAL")
    linhas.append("-" * 76)
    linhas.append(f"Códigos no antigo: {resumo['codigos_antigo']}")
    linhas.append(f"Códigos no novo  : {resumo['codigos_novo']}")
    linhas.append(f"Códigos em comum : {resumo['codigos_comuns']}")
    linhas.append(f"Vias total antigo: {resumo['vias_antigo_total']}")
    linhas.append(f"Vias total novo  : {resumo['vias_novo_total']}")
    linhas.append(f"Vias antigas encontradas no novo: {resumo['vias_antigo_encontradas_no_novo']}")
    linhas.append(f"Cobertura estimada: {resumo['cobertura_percentual']}%")
    linhas.append("")

    if resumo["codigos_apenas_antigo"]:
        linhas.append("CÓDIGOS APENAS NO ANTIGO")
        linhas.append("-" * 76)
        linhas.append(", ".join(resumo["codigos_apenas_antigo"]))
        linhas.append("")

    if resumo["codigos_apenas_novo"]:
        linhas.append("CÓDIGOS APENAS NO NOVO")
        linhas.append("-" * 76)
        linhas.append(", ".join(resumo["codigos_apenas_novo"]))
        linhas.append("")

    linhas.append("TOP LINHAS COM MAIOR DIFERENÇA (ANTIGO NÃO ENCONTRADO)")
    linhas.append("-" * 76)

    ranking: list[tuple[str, int]] = []
    for codigo, info in por_linha.items():
        faltas = len(info["ida"]["old_nao_encontradas"]) + len(info["volta"]["old_nao_encontradas"])
        ranking.append((codigo, faltas))

    ranking.sort(key=lambda x: x[1], reverse=True)
    for codigo, faltas in ranking[:20]:
        linhas.append(f"{codigo}: {faltas} vias antigas não encontradas")
    linhas.append("")

    linhas.append("AMOSTRA DE DIFERENÇAS POR LINHA")
    linhas.append("-" * 76)

    for codigo, _ in ranking[:12]:
        info = por_linha[codigo]
        linhas.append(f"Linha {codigo}")
        for sentido in ("ida", "volta"):
            s = info[sentido]
            linhas.append(
                f"  {sentido.upper()} -> old={s['old_total']}, new={s['new_total']}, "
                f"exato={s['match_exato']}, aprox={s['match_aproximado']}, faltando_old={len(s['old_nao_encontradas'])}"
            )
            for rua in s["old_nao_encontradas"][:6]:
                linhas.append(f"    - antigo não encontrado: {rua}")
            for par in s["aproximadas"][:4]:
                linhas.append(f"    ~ aprox: {par['antigo']} -> {par['novo']}")
        linhas.append("")

    linhas.append("OBSERVAÇÃO")
    linhas.append("-" * 76)
    linhas.append("A cobertura é estimada com normalização de OCR/abreviações e fuzzy match por linha/sentido.")
    linhas.append("Diferenças podem refletir segmentação de via, atualização de nomenclatura ou geocodificação parcial.")

    output_txt.write_text("\n".join(linhas), encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).parent.parent

    pasta_antigo = base_dir / "data" / "pdf-intinerarios-por-via-todas-linhas"
    json_novo = base_dir / "python" / "data" / "intinerario" / "itinerario_completo_sem_ruas_duplicadas_v1.json"

    out_txt = base_dir / "python" / "data" / "resto" / "relatorio_comparacao_itinerario_antigo_vs_novo_v1.txt"
    out_json = base_dir / "python" / "data" / "resto" / "comparacao_itinerario_antigo_vs_novo_v1.json"

    if not pasta_antigo.exists():
        print(f"❌ Pasta antiga não encontrada: {pasta_antigo}")
        return

    if not json_novo.exists():
        print(f"❌ JSON novo não encontrado: {json_novo}")
        return

    print("📖 Lendo itinerários antigos (PDF)...")
    antigo = extrair_antigo_por_codigo(pasta_antigo)
    print(f"   Linhas antigas lidas: {len(antigo)}")

    print("🗂️  Lendo itinerário novo (JSON)...")
    novo = extrair_novo_por_codigo(json_novo)
    print(f"   Linhas novas lidas: {len(novo)}")

    print("🔎 Comparando por linha/sentido...")
    comparacao = comparar(antigo, novo)

    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(comparacao, ensure_ascii=False, indent=2), encoding="utf-8")
    escrever_relatorio_txt(comparacao, out_txt)

    print("✅ Comparação concluída")
    print(f"📝 Relatório TXT: {out_txt}")
    print(f"🧾 Detalhe JSON : {out_json}")


if __name__ == "__main__":
    main()
