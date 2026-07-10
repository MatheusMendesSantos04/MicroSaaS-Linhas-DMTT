"""
Compara as linhas ativas no PDF de Resumo OSO contra as linhas presentes em
data/json/dados_unificados.json (fonte de verdade do sistema).

Gera um relatorio em linhas/relatorios/ apontando:
  - linhas ativas no OSO mas ausentes no sistema (candidatas a inclusao)
  - linhas presentes no sistema mas nao encontradas como ativas no OSO
  - linhas em ambos (OK)
  - Catraca de Solo listada a parte (convencao do projeto: nao entra no sistema)

Uso:
    python python/comparar_oso_dados_unificados.py <caminho_do_pdf_oso>
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
DADOS_UNIFICADOS = ROOT / "data" / "json" / "dados_unificados.json"
SAIDA_DIR = ROOT / "linhas" / "relatorios"

TIPOS_OP = re.compile(
    r"RADIAL|DIAMETRAL|PERIMETRAL|CIRCULAR|ALIMENTADO|DISTRIBUIDO|CATRACA|ESTRUTURA"
)

TIPO_MAP = {
    "CONVENCIONAL":    "CONVENCIONAL",
    "INTEGRA":         "INTEGRACAO",
    "CATRACA DE SOLO": "CATRACA DE SOLO",
    "CATRACA DE":      "CATRACA DE SOLO",
    "MADRUG":          "MADRUGADAO",
    "LINHA CIDAD":     "LINHA CIDADA",
}

LIXO_LINHAS = {"RA", "L", "SOLO"}

# Linhas com decisao explicita de projeto (ver CLAUDE.md) de NAO entrar no sistema
EXCLUSOES_CONHECIDAS = {
    "0006-M": "Decisao de projeto registrada no CLAUDE.md: nao sera adicionada ao sistema.",
}


def norm_tipo(raw: str) -> str:
    raw = re.sub(r"\s+", " ", raw.strip().upper())
    for key, val in TIPO_MAP.items():
        if raw.startswith(key):
            return val
    return raw


def parse_empresa(line: str) -> str:
    m = re.match(r"Empresa:\s*(.+)", line)
    if not m:
        return ""
    return re.split(r"\s{3,}", m.group(1).strip())[0].strip()


def parse_tipo(line: str) -> str:
    m = re.match(r"Tipo Servi.o:\s*(.+)", line)
    if not m:
        return ""
    return norm_tipo(m.group(1))


def parse_linha(line: str):
    if not re.match(r"^\d{4}", line):
        return None
    parts = re.split(r"\s+-\s+", line, maxsplit=1)
    if len(parts) < 2:
        return None

    codigo = parts[0].rstrip("-").replace("--", "-").strip().upper()
    resto = parts[1]

    m_oso = TIPOS_OP.search(resto)
    if not m_oso:
        return None

    trecho_nome = resto[: m_oso.start()].strip()
    oso_match = re.search(r"(\d{4}[A-Z0-9-]*)-\s*$", trecho_nome)
    if oso_match:
        nome = trecho_nome[: oso_match.start()].strip()
        oso = oso_match.group(1).rstrip("-")
    else:
        nome = trecho_nome
        oso = ""

    nome = re.sub(r"\s+\d{4}[A-Z0-9-]*-?\s*$", "", nome).strip()
    return codigo, nome, oso


def extrair_oso(pdf_path: Path) -> list[dict]:
    linhas: list[dict] = []
    empresa_atual = "DESCONHECIDA"
    tipo_atual = "DESCONHECIDO"

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line or line in LIXO_LINHAS:
                    continue

                emp = parse_empresa(line)
                if emp:
                    empresa_atual = emp
                    continue

                tp = parse_tipo(line)
                if tp:
                    tipo_atual = tp
                    continue

                if re.match(r"^(Sub-Total|Total da Empresa|TOTAL):", line):
                    continue

                resultado = parse_linha(line)
                if resultado:
                    codigo, nome, oso = resultado
                    linhas.append({
                        "codigo": codigo,
                        "nome": nome,
                        "oso": oso,
                        "tipo": tipo_atual,
                        "empresa": empresa_atual,
                    })
    return linhas


def extrair_codigos_sistema(path: Path) -> dict[str, str]:
    dados = json.loads(path.read_text(encoding="utf-8"))
    codigos = {}
    for chave in dados.keys():
        m = re.match(r"^(\S+)", chave.strip())
        codigo = (m.group(1) if m else chave).upper()
        codigos[codigo] = chave
    return codigos


def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python python/comparar_oso_dados_unificados.py <caminho_do_pdf_oso>"
        )
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        raise SystemExit(f"PDF nao encontrado: {pdf_path}")

    oso_linhas = extrair_oso(pdf_path)
    oso_por_codigo = {l["codigo"]: l for l in oso_linhas if l["tipo"] != "CATRACA DE SOLO"}
    catraca = [l for l in oso_linhas if l["tipo"] == "CATRACA DE SOLO"]

    sistema_codigos = extrair_codigos_sistema(DADOS_UNIFICADOS)

    oso_cods = set(oso_por_codigo.keys())
    sistema_cods = set(sistema_codigos.keys())

    faltam_no_sistema = sorted(oso_cods - sistema_cods)
    extras_no_sistema = sorted(sistema_cods - oso_cods)
    em_ambos = sorted(oso_cods & sistema_cods)

    # separa exclusoes conhecidas das genuinamente faltantes
    faltam_reais = [c for c in faltam_no_sistema if c not in EXCLUSOES_CONHECIDAS]
    faltam_excluidas = [c for c in faltam_no_sistema if c in EXCLUSOES_CONHECIDAS]

    def por_tipo(cods):
        grupos: dict[str, list] = defaultdict(list)
        for c in cods:
            info = oso_por_codigo.get(c, {"tipo": "?", "nome": "", "empresa": ""})
            grupos[info["tipo"]].append((c, info["nome"], info["empresa"]))
        return grupos

    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    data_ref = datetime.now().strftime("%Y-%m-%d")
    saida = SAIDA_DIR / f"relatorio_oso_vs_sistema_{data_ref}.txt"

    with saida.open("w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RELATORIO — LINHAS ATIVAS (OSO) vs SISTEMA (dados_unificados.json)\n")
        f.write(f"Fonte OSO: {pdf_path.name}\n")
        f.write(f"Fonte sistema: {DADOS_UNIFICADOS.relative_to(ROOT)}\n")
        f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("[ RESUMO ]\n\n")
        f.write(f"  Linhas ativas no OSO (excl. Catraca de Solo) : {len(oso_cods)}\n")
        f.write(f"  Linhas no sistema (dados_unificados.json)     : {len(sistema_cods)}\n")
        f.write(f"  Presentes nos dois (OK)                       : {len(em_ambos)}\n")
        f.write(f"  Ativas no OSO e AUSENTES no sistema           : {len(faltam_reais)}\n")
        f.write(f"  ...das quais excluidas por decisao de projeto : {len(faltam_excluidas)}\n")
        f.write(f"  No sistema mas NAO ativas no OSO atual        : {len(extras_no_sistema)}\n")
        f.write(f"  Catraca de Solo (fora do escopo do sistema)   : {len(catraca)}\n\n")

        f.write("=" * 80 + "\n")
        f.write(f"[ ATIVAS NO OSO E AUSENTES NO SISTEMA ]  {len(faltam_reais)} linhas\n")
        f.write("-" * 80 + "\n")
        f.write("Precisam ser incorporadas ao sistema (ver Fase A-F do CLAUDE.md).\n\n")
        grupos = por_tipo(faltam_reais)
        for tipo in sorted(grupos.keys()):
            f.write(f"  {tipo}:\n")
            for cod, nome, emp in sorted(grupos[tipo]):
                f.write(f"    {cod:<10}  {nome:<55}  [{emp}]\n")
            f.write("\n")
        if not faltam_reais:
            f.write("  (nenhuma — sistema cobre todas as linhas ativas do OSO)\n\n")

        if faltam_excluidas:
            f.write("=" * 80 + "\n")
            f.write(f"[ ATIVAS NO OSO, AUSENTES NO SISTEMA, MAS EXCLUIDAS DE PROPOSITO ]  {len(faltam_excluidas)}\n")
            f.write("-" * 80 + "\n\n")
            for cod in sorted(faltam_excluidas):
                info = oso_por_codigo.get(cod, {})
                f.write(f"  {cod:<10}  {info.get('nome',''):<55}\n")
                f.write(f"    -> {EXCLUSOES_CONHECIDAS[cod]}\n")
            f.write("\n")

        f.write("=" * 80 + "\n")
        f.write(f"[ NO SISTEMA MAS NAO ENCONTRADAS COMO ATIVAS NO OSO ]  {len(extras_no_sistema)} linhas\n")
        f.write("-" * 80 + "\n")
        f.write("Podem estar descontinuadas, ter mudado de codigo, ou o nome no sistema\n")
        f.write("nao bate com o formato de codigo do OSO — checar manualmente.\n\n")
        for cod in extras_no_sistema:
            f.write(f"    {cod:<10}  {sistema_codigos.get(cod, '')}\n")
        if not extras_no_sistema:
            f.write("  (nenhuma)\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write(f"[ CATRACA DE SOLO ]  {len(catraca)} linhas (fora do escopo do sistema)\n")
        f.write("-" * 80 + "\n\n")
        for l in catraca:
            f.write(f"    {l['codigo']:<10}  {l['nome']:<55}  [{l['empresa']}]\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write(f"[ STATUS COMPLETO — TODAS AS LINHAS ATIVAS NO OSO ]\n")
        f.write("-" * 80 + "\n\n")
        f.write(f"  {'COD':<10}  {'TIPO':<16}  {'SISTEMA':^8}  NOME\n")
        f.write(f"  {'-'*9}  {'-'*15}  {'-'*8}  {'-'*45}\n")
        for l in sorted(oso_linhas, key=lambda x: (x["tipo"], x["codigo"])):
            if l["tipo"] == "CATRACA DE SOLO":
                continue
            sit = "OK" if l["codigo"] in sistema_cods else "FALTA"
            f.write(f"  {l['codigo']:<10}  {l['tipo']:<16}  {sit:^8}  {l['nome']}\n")

        f.write("\n" + "-" * 80 + "\n")
        f.write("Gerado por python/comparar_oso_dados_unificados.py\n")

    print(f"[OK] {saida.relative_to(ROOT)}")
    print()
    print(f"  Ativas no OSO (excl. catraca) : {len(oso_cods)}")
    print(f"  No sistema                    : {len(sistema_cods)}")
    print(f"  OK (nos dois)                  : {len(em_ambos)}")
    print(f"  Faltam no sistema              : {len(faltam_reais)}  {faltam_reais}")
    print(f"  Excluidas por decisao          : {len(faltam_excluidas)}  {faltam_excluidas}")
    print(f"  No sistema mas nao ativas OSO  : {len(extras_no_sistema)}  {extras_no_sistema}")


if __name__ == "__main__":
    main()
