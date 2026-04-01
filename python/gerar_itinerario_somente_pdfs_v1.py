from __future__ import annotations

import json
import re
import unicodedata
from difflib import get_close_matches
from pathlib import Path

from pypdf import PdfReader


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
    (r"\bPCA\.?\b", "PRAÇA"),
    (r"\bPCA\.?\b", "PRAÇA"),
    (r"\bPÇA\.?\b", "PRAÇA"),
    (r"\bPC\.?\b", "PRAÇA"),
    (r"\bLAD\.?\b", "LADEIRA"),
    (r"\bVILA\.?\b", "VILA"),
]

RUIDOS_EXATOS = {
    "SUB",
    "TOTAL",
    "SUBTOTAL",
    "RECURSOS",
    "INFORMATICA",
    "INTINERARIOPORVIA",
    "ITINERARIOPORVIA",
}

TIPOS_VIA_TOKENS = {
    "RUA",
    "AVENIDA",
    "TRAVESSA",
    "ALAMEDA",
    "ESTRADA",
    "RODOVIA",
    "LADEIRA",
    "PRAÇA",
    "PRACA",
    "VILA",
    "LARGO",
    "TERMINAL",
}


def remover_acentos(texto: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def dedupe_preservando_ordem(itens: list[str]) -> list[str]:
    vistos: set[str] = set()
    saida: list[str] = []
    for item in itens:
        if item not in vistos:
            vistos.add(item)
            saida.append(item)
    return saida


def normalizar_via(texto: str) -> str:
    if not texto:
        return ""

    t = unicodedata.normalize("NFC", texto.upper())
    t = t.replace("A VENIDA", "AVENIDA")
    t = t.replace("TRA VESSA", "TRAVESSA")
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"\b([A-Z]{3,})\s+([A-Z])\s+([A-Z]{3,})\b", r"\1 \2\3", t)

    def juntar_ultimo_fragmento(match: re.Match[str]) -> str:
        esquerda = match.group(1)
        direita = match.group(2)
        if esquerda in TIPOS_VIA_TOKENS:
            return f"{esquerda} {direita}"
        return f"{esquerda}{direita}"

    t = re.sub(r"\b([A-Z]{3,})\s+([A-Z])\b", juntar_ultimo_fragmento, t)
    t = re.sub(r"\bIDA\b", " ", t)
    t = re.sub(r"\bVOLTA\b", " ", t)

    for pattern, repl in ABREVIACOES:
        t = re.sub(pattern, repl, t)

    t = re.sub(r"[^A-Z0-9À-ÖØ-Ý\s'-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    t_sem_acentos = remover_acentos(t)
    tokens = [tok for tok in t_sem_acentos.split() if tok not in RUIDOS_EXATOS]
    t_sem_ruido = " ".join(tokens).strip()

    if not t_sem_ruido or t_sem_ruido in {"0", "SUB TOTAL", "TOTAL"}:
        return ""

    return t_sem_ruido


def extrair_itinerario_pdf(pdf_path: Path) -> dict[str, list[str]]:
    reader = PdfReader(pdf_path)
    texto = "\n".join((page.extract_text() or "") for page in reader.pages)

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

        match = re.match(r"^\d+\s+\d{3,6}\s+(?:IDA|VOLTA)?\s*(.+?)\s*$", line, flags=re.IGNORECASE)
        if not match:
            continue

        via = normalizar_via(match.group(1).strip())
        if not via:
            continue

        if sentido == "ida":
            ida.append(via)
        else:
            volta.append(via)

    return {
        "ida": dedupe_preservando_ordem(ida),
        "volta": dedupe_preservando_ordem(volta),
    }


def chave_comparacao(texto: str) -> str:
    base = remover_acentos(unicodedata.normalize("NFC", texto.upper()))
    for pattern, repl in ABREVIACOES:
        base = re.sub(pattern, repl, base)
    base = re.sub(r"[^A-Z0-9\s'-]", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    return base


def carregar_ruas_canonicas(referencia_path: Path) -> tuple[list[str], dict[str, str]]:
    if not referencia_path.exists():
        return [], {}

    data = json.loads(referencia_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return [], {}

    ruas: list[str] = []
    chave_para_canonica: dict[str, str] = {}

    for payload in data.values():
        if not isinstance(payload, dict):
            continue
        for sentido in ("ida", "volta"):
            for rua in payload.get(sentido, []):
                if not isinstance(rua, str) or not rua.strip():
                    continue
                rua_clean = rua.strip().upper()
                ruas.append(rua_clean)
                key = chave_comparacao(rua_clean)
                if key and key not in chave_para_canonica:
                    chave_para_canonica[key] = rua_clean

    ruas_unicas = dedupe_preservando_ordem(ruas)
    return ruas_unicas, chave_para_canonica


def padronizar_com_canonico(via: str, chave_para_canonica: dict[str, str], chaves_canonicas: list[str]) -> str:
    if not via:
        return via

    chave = chave_comparacao(via)
    if chave in chave_para_canonica:
        return chave_para_canonica[chave]

    candidatos = get_close_matches(chave, chaves_canonicas, n=1, cutoff=0.88)
    if candidatos:
        return chave_para_canonica[candidatos[0]]

    return via


def carregar_nomes_linhas_por_codigo(referencia_path: Path) -> dict[str, str]:
    if not referencia_path.exists():
        return {}

    data = json.loads(referencia_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}

    mapa: dict[str, str] = {}
    for nome_linha in data.keys():
        if not isinstance(nome_linha, str):
            continue
        match = re.search(r"(\d{4})", nome_linha)
        if not match:
            continue
        codigo = match.group(1)
        mapa[codigo] = nome_linha

    return mapa


def main() -> None:
    base_dir = Path(__file__).parent.parent

    pasta_pdfs = base_dir / "data" / "pdf-intinerarios-por-via-todas-linhas"
    referencia_v2 = (
        base_dir
        / "python"
        / "dado principal"
        / "intinerario manual"
        / "itinerario_completo_rua_principal_somente_ruas_v2.json"
    )
    output_json = (
        base_dir
        / "python"
        / "dado principal"
        / "intinerario manual"
        / "itinerario_completo_rua_principal_somente_ruas_pdf_v1.json"
    )

    if not pasta_pdfs.exists():
        print(f"❌ Pasta de PDFs não encontrada: {pasta_pdfs}")
        return

    nomes_por_codigo = carregar_nomes_linhas_por_codigo(referencia_v2)
    _, chave_para_canonica = carregar_ruas_canonicas(referencia_v2)
    chaves_canonicas = list(chave_para_canonica.keys())

    saida: dict[str, dict[str, list[str] | str]] = {}

    for pdf in sorted(pasta_pdfs.glob("linha_*.pdf")):
        match_code = re.search(r"linha_(\d{4})", pdf.name)
        if not match_code:
            continue

        codigo = match_code.group(1)
        nome_linha = nomes_por_codigo.get(codigo, f"{codigo} - LINHA {codigo}")

        itinerario = extrair_itinerario_pdf(pdf)
        ida = [padronizar_com_canonico(via, chave_para_canonica, chaves_canonicas) for via in itinerario["ida"]]
        volta = [padronizar_com_canonico(via, chave_para_canonica, chaves_canonicas) for via in itinerario["volta"]]
        saida[nome_linha] = {
            "ida": dedupe_preservando_ordem(ida),
            "volta": dedupe_preservando_ordem(volta),
            "versao": "pdf_v1",
        }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(saida, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total_ida = sum(len(v["ida"]) for v in saida.values())
    total_volta = sum(len(v["volta"]) for v in saida.values())

    print("✅ Itinerário somente dos PDFs gerado com sucesso")
    print(f"📄 Saída: {output_json}")
    print(f"🚌 Linhas processadas: {len(saida)}")
    print(f"➡️  Total de vias IDA: {total_ida}")
    print(f"⬅️  Total de vias VOLTA: {total_volta}")


if __name__ == "__main__":
    main()
