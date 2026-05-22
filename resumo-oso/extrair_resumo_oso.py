"""
Extrai do sp_relatorio_resumooso.pdf a lista de linhas por tipo de servico
(CONVENCIONAL, CATRACA DE SOLO, MADRUGADAO, etc.) e gera
resumo-oso/relatorio_tipos_servico.txt

Uso:
    python resumo-oso/extrair_resumo_oso.py
"""

import re
from collections import defaultdict
from pathlib import Path

import pdfplumber

BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "sp_relatorio_resumooso.pdf"
SAIDA    = BASE_DIR / "relatorio_tipos_servico.txt"

# Tipos de operação que identificam linhas de dados no PDF
TIPOS_OP = re.compile(
    r"RADIAL|DIAMETRAL|PERIMETRAL|CIRCULAR|ALIMENTADO|DISTRIBUIDO|CATRACA|ESTRUTURA"
)

# Normaliza nomes de tipo de serviço (encoding quebrado do PDF)
TIPO_MAP = {
    "CONVENCIONAL":    "CONVENCIONAL",
    "INTEGRA":        "INTEGRACAO",   # INTEGRAÇÃO / INTEGRACAO
    "CATRACA DE SOLO": "CATRACA DE SOLO",
    "CATRACA DE":     "CATRACA DE SOLO",
    "MADRUG":         "MADRUGADAO",   # MADRUGADÃO / MADRUG?O
    "LINHA CIDAD":    "LINHA CIDADA",  # LINHA CIDADÃ
}


def norm_tipo(raw: str) -> str:
    raw = raw.strip().upper()
    raw = re.sub(r"\s+", " ", raw)
    for key, val in TIPO_MAP.items():
        if raw.startswith(key):
            return val
    return raw


def parse_empresa(line: str) -> str:
    m = re.match(r"Empresa:\s*(.+)", line)
    if not m:
        return ""
    emp = m.group(1).strip()
    # limpa lixo de encoding/layout apos o nome
    emp = re.split(r"\s{3,}", emp)[0].strip()
    return emp


def parse_tipo(line: str) -> str:
    m = re.match(r"Tipo Servi.o:\s*(.+)", line)
    if not m:
        return ""
    return norm_tipo(m.group(1))


def parse_linha(line: str):
    """
    Retorna (codigo, nome, oso) ou None se a linha nao for registro de dados.
    Formato do PDF: 'DDDD- - NOME OSO- TIPO DATA ...'
    ou com sufixo: '0612--A - NOME OSO- TIPO DATA ...'
    """
    if not re.match(r"^\d{4}", line):
        return None

    # Separa codigo do resto pelo primeiro ' - '
    parts = re.split(r"\s+-\s+", line, maxsplit=1)
    if len(parts) < 2:
        return None

    codigo_raw = parts[0].rstrip("-").replace("--", "-").strip()
    resto = parts[1]

    # Procura o numero OSO (4 digitos seguido de tipo de operacao)
    m_oso = TIPOS_OP.search(resto)
    if not m_oso:
        return None

    # Nome e tudo antes do OSO
    trecho_nome = resto[: m_oso.start()].strip()
    # O OSO vem logo antes do tipo: '6825- RADIAL' → OSO = 6825
    oso_match = re.search(r"(\d{4}[A-Z0-9-]*)-\s*$", trecho_nome)
    if oso_match:
        nome = trecho_nome[: oso_match.start()].strip()
        oso  = oso_match.group(1).rstrip("-")
    else:
        nome = trecho_nome
        oso  = ""

    # Limpa lixo residual de codigos duplicados no nome (ex: "6825-")
    nome = re.sub(r"\s+\d{4}[A-Z0-9-]*-?\s*$", "", nome).strip()

    return codigo_raw, nome, oso


# ---------------------------------------------------------------------------
# leitura do PDF
# ---------------------------------------------------------------------------

# dados: empresa -> tipo -> lista de {codigo, nome, oso}
dados: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

empresa_atual = "DESCONHECIDA"
tipo_atual    = "DESCONHECIDO"

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line in ("RA", "L"):   # sufixos soltos no PDF
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
                dados[empresa_atual][tipo_atual].append(
                    {"codigo": codigo, "nome": nome, "oso": oso}
                )


# ---------------------------------------------------------------------------
# totais consolidados
# ---------------------------------------------------------------------------

TIPOS_ORDEM = [
    "CONVENCIONAL",
    "CATRACA DE SOLO",
    "MADRUGADAO",
    "INTEGRACAO",
    "LINHA CIDADA",
]


def tipo_sort_key(t):
    try:
        return TIPOS_ORDEM.index(t)
    except ValueError:
        return 99


totais_tipo: dict[str, list] = defaultdict(list)
for emp, tipos in dados.items():
    for tipo, linhas in tipos.items():
        for linha in linhas:
            totais_tipo[tipo].append({**linha, "empresa": emp})

tipos_ordenados = sorted(totais_tipo.keys(), key=tipo_sort_key)
total_geral = sum(len(v) for v in totais_tipo.values())


# ---------------------------------------------------------------------------
# escreve relatorio
# ---------------------------------------------------------------------------

with SAIDA.open("w", encoding="utf-8") as f:

    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO — LINHAS POR TIPO DE SERVIÇO\n")
    f.write("Fonte: sp_relatorio_resumooso.pdf\n")
    f.write("=" * 80 + "\n\n")

    # RESUMO GERAL
    f.write("[ RESUMO GERAL ]\n\n")
    for tipo in tipos_ordenados:
        cnt = len(totais_tipo[tipo])
        barra = "█" * cnt
        f.write(f"  {tipo:<25} {cnt:>3} linhas  {barra}\n")
    f.write(f"\n  {'TOTAL GERAL':<25} {total_geral:>3} linhas\n\n")

    # POR EMPRESA
    f.write("=" * 80 + "\n")
    f.write("[ POR EMPRESA ]\n\n")
    for emp in sorted(dados.keys()):
        total_emp = sum(len(ls) for ls in dados[emp].values())
        f.write(f"  {emp}\n")
        f.write(f"  Total: {total_emp} linhas\n")
        for tipo in sorted(dados[emp].keys(), key=tipo_sort_key):
            f.write(f"    {tipo:<25}: {len(dados[emp][tipo])}\n")
        f.write("\n")

    # DETALHE DE CADA TIPO
    for tipo in tipos_ordenados:
        linhas = totais_tipo[tipo]
        f.write("=" * 80 + "\n")
        f.write(f"[ {tipo} ]  {len(linhas)} linhas\n")
        f.write("-" * 80 + "\n\n")

        por_empresa: dict[str, list] = defaultdict(list)
        for l in linhas:
            por_empresa[l["empresa"]].append(l)

        for emp in sorted(por_empresa.keys()):
            f.write(f"  {emp} ({len(por_empresa[emp])} linhas):\n")
            for l in sorted(por_empresa[emp], key=lambda x: x["codigo"]):
                f.write(f"    {l['codigo']:<12}  OSO {l['oso']:<6}  {l['nome']}\n")
            f.write("\n")

    f.write("-" * 80 + "\n")
    f.write("Gerado por resumo-oso/extrair_resumo_oso.py\n")


# resumo no terminal
print(f"[OK] {SAIDA.name}")
print()
print("RESUMO:")
for tipo in tipos_ordenados:
    cnt = len(totais_tipo[tipo])
    print(f"  {tipo:<25} {cnt:>3} linhas")
print(f"  {'TOTAL':<25} {total_geral:>3} linhas")
