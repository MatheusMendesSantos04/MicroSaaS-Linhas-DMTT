"""
Compara os PDFs nas pastas de itinerario e horario
contra as linhas do OSO, gerando relatorio detalhado.

Saida: I:\Micro-SaaS-DMTT\relatorio_pdfs_vs_oso.txt

Uso:
    python python/gerar_relatorio_pdfs_vs_oso.py
"""

import re
import pdfplumber
from pathlib import Path

BASE       = Path(__file__).resolve().parents[1]
IT_DIR     = BASE / "data" / "pdf-intinerarios-por-via-todas-linhas"
HR_DIR     = BASE / "data" / "pdf-horario"
OSO_PDF    = BASE / "resumo-oso" / "sp_relatorio_resumooso.pdf"
SAIDA      = Path(r"I:\Micro-SaaS-DMTT") / "relatorio_pdfs_vs_oso.txt"

TIPOS_OP = re.compile(
    r"RADIAL|DIAMETRAL|PERIMETRAL|CIRCULAR|ALIMENTADO|DISTRIBUIDO|CATRACA|ESTRUTURA"
)

LIXO = {
    "INTINERARIOPORVIA", "SRE_RELATORIO_VIA_LOGRADOURO-CODIGO-DAS-RUAS",
    "", "604", "INTINERARIOPORVIA-604",
}


def stem_to_cod(stem: str) -> str:
    n = re.sub(r"^(INTINERARIOPORVIA-|ITINERARIO_|HORARIO_|LINHA_)", "", stem.upper())
    n = re.sub(r"_\d{8}$", "", n).strip()
    return n


# --- PDFs nas pastas ---
it_cods = {stem_to_cod(f.stem) for f in IT_DIR.glob("*.pdf")} - LIXO
hr_cods = {stem_to_cod(f.stem) for f in HR_DIR.glob("*.pdf")} - LIXO

# --- Linhas do OSO (excluindo Catraca de Solo) ---
oso_linhas: list[dict] = []
tipo_atual = "DESCONHECIDO"

with pdfplumber.open(str(OSO_PDF)) as pdf:
    for page in pdf.pages:
        for linha in (page.extract_text() or "").splitlines():
            l = linha.strip()

            mt = re.match(r"Tipo Servi.o:\s*(.+)", l)
            if mt:
                raw = mt.group(1).strip().upper()
                if "MADRUG" in raw:    tipo_atual = "MADRUGADAO"
                elif "CONVENC" in raw: tipo_atual = "CONVENCIONAL"
                elif "INTEGRA" in raw: tipo_atual = "INTEGRACAO"
                elif "CIDAD" in raw:   tipo_atual = "LINHA CIDADA"
                elif "CATRACA" in raw: tipo_atual = "CATRACA DE SOLO"
                continue

            if re.match(r"^(Sub-Total|Total da Empresa|TOTAL):", l):
                continue

            parts = re.split(r"\s+-\s+", l, maxsplit=1)
            if len(parts) < 2 or not re.match(r"^\d{4}", parts[0]):
                continue

            cod = parts[0].rstrip("-").strip().upper()
            if not TIPOS_OP.search(parts[1]):
                continue
            if tipo_atual == "CATRACA DE SOLO":
                continue

            nome = re.split(r"\s+\d{4}[A-Z0-9-]*-\s+", parts[1])[0].strip()
            oso_linhas.append({
                "cod":  cod,
                "tipo": tipo_atual,
                "nome": nome[:60],
            })

oso_por_cod = {x["cod"]: x for x in oso_linhas}
oso_cods    = set(oso_por_cod.keys())

# --- cruzamentos ---
faltam_it     = sorted(oso_cods - it_cods)
faltam_hr     = sorted(oso_cods - hr_cods)
faltam_ambos  = sorted((oso_cods - it_cods) & (oso_cods - hr_cods))
so_falta_it   = sorted(oso_cods - it_cods - (oso_cods - hr_cods))
so_falta_hr   = sorted((oso_cods - hr_cods) - (oso_cods - it_cods))
extras_it     = sorted(it_cods - oso_cods)
extras_hr     = sorted(hr_cods - oso_cods)

# --- agrupa por tipo ---
def por_tipo(lista_cods):
    grupos: dict[str, list] = {}
    for cod in lista_cods:
        info = oso_por_cod.get(cod, {"tipo": "NAO ENCONTRADO NO OSO", "nome": ""})
        tipo = info["tipo"]
        grupos.setdefault(tipo, []).append((cod, info["nome"]))
    return grupos


# --- escreve relatorio ---
SAIDA.parent.mkdir(parents=True, exist_ok=True)

with SAIDA.open("w", encoding="utf-8") as f:

    f.write("=" * 80 + "\n")
    f.write("RELATORIO — PDFs vs LINHAS DO OSO\n")
    f.write("=" * 80 + "\n\n")

    f.write("[ RESUMO ]\n\n")
    f.write(f"  Linhas no OSO (sem catraca de solo)    : {len(oso_cods)}\n")
    f.write(f"  PDFs de itinerario (validos)            : {len(it_cods)}\n")
    f.write(f"  PDFs de horario (validos)               : {len(hr_cods)}\n\n")
    f.write(f"  Faltam nas DUAS pastas                  : {len(faltam_ambos)}\n")
    f.write(f"  Faltam somente no ITINERARIO            : {len(so_falta_it)}\n")
    f.write(f"  Faltam somente no HORARIO               : {len(so_falta_hr)}\n")
    f.write(f"  PDFs extras no IT (fora do OSO)         : {len(extras_it)}\n")
    f.write(f"  PDFs extras no HR (fora do OSO)         : {len(extras_hr)}\n\n")

    # FALTAM NOS DOIS
    f.write("=" * 80 + "\n")
    f.write(f"[ FALTAM NAS DUAS PASTAS ]  {len(faltam_ambos)} linhas\n")
    f.write("-" * 80 + "\n\n")
    for tipo, itens in sorted(por_tipo(faltam_ambos).items()):
        f.write(f"  {tipo}:\n")
        for cod, nome in sorted(itens):
            f.write(f"    {cod:<12}  {nome}\n")
        f.write("\n")

    # SOMENTE FALTA IT
    if so_falta_it:
        f.write("=" * 80 + "\n")
        f.write(f"[ FALTAM SO NO ITINERARIO ]  {len(so_falta_it)} linhas\n")
        f.write("-" * 80 + "\n\n")
        for cod in so_falta_it:
            info = oso_por_cod.get(cod, {})
            f.write(f"  {cod:<12}  {info.get('nome','')}\n")
        f.write("\n")

    # SOMENTE FALTA HR
    if so_falta_hr:
        f.write("=" * 80 + "\n")
        f.write(f"[ FALTAM SO NO HORARIO ]  {len(so_falta_hr)} linhas\n")
        f.write("-" * 80 + "\n\n")
        for cod in so_falta_hr:
            info = oso_por_cod.get(cod, {})
            f.write(f"  {cod:<12}  {info.get('nome','')}\n")
        f.write("\n")

    # EXTRAS IT
    if extras_it:
        f.write("=" * 80 + "\n")
        f.write(f"[ PDFs EXTRAS NO ITINERARIO (nao estao no OSO) ]  {len(extras_it)}\n")
        f.write("-" * 80 + "\n\n")
        for cod in extras_it:
            f.write(f"  {cod}\n")
        f.write("\n")

    # EXTRAS HR
    if extras_hr:
        f.write("=" * 80 + "\n")
        f.write(f"[ PDFs EXTRAS NO HORARIO (nao estao no OSO) ]  {len(extras_hr)}\n")
        f.write("-" * 80 + "\n\n")
        for cod in extras_hr:
            f.write(f"  {cod}\n")
        f.write("\n")

    # TODAS AS LINHAS DO OSO (status)
    f.write("=" * 80 + "\n")
    f.write(f"[ STATUS COMPLETO — TODAS AS LINHAS DO OSO ]\n")
    f.write("-" * 80 + "\n\n")
    f.write(f"  {'COD':<12}  {'TIPO':<16}  {'IT':^3}  {'HR':^3}  NOME\n")
    f.write(f"  {'-'*11}  {'-'*15}  {'-':^3}  {'-':^3}  {'-'*40}\n")
    for info in sorted(oso_linhas, key=lambda x: (x["tipo"], x["cod"])):
        cod = info["cod"]
        sit = "OK " if cod in it_cods else "---"
        shr = "OK " if cod in hr_cods else "---"
        f.write(f"  {cod:<12}  {info['tipo']:<16}  {sit}  {shr}  {info['nome']}\n")

    f.write("\n")
    f.write("-" * 80 + "\n")
    f.write("Gerado por python/gerar_relatorio_pdfs_vs_oso.py\n")

print(f"[OK] {SAIDA}")
print()
print(f"  OSO (sem catraca) : {len(oso_cods)}")
print(f"  IT PDFs           : {len(it_cods)}")
print(f"  HR PDFs           : {len(hr_cods)}")
print(f"  Faltam nas 2 pastas: {len(faltam_ambos)}")
print(f"  So falta IT        : {len(so_falta_it)}")
print(f"  So falta HR        : {len(so_falta_hr)}")
print()
print(f"  Faltam nos dois: {faltam_ambos}")
