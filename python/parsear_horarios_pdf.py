"""
Fase D do pipeline — parseia PDFs de Quadro Horário do Matrix.

Lê todos os PDFs em data/pdf-horario/ que correspondem às linhas novas
e gera: data/json/novos_trajetos/horarios_novos.json

Formato de saída (mesmo do horarios.json existente):
{
  "0036": {
    "dia_util": {"ida": ["05:40","06:00",...], "volta": []},
    "sabado":   {"ida": [...], "volta": []},
    "domingo":  {"ida": [...], "volta": []}
  }
}

Uso:
    python python/parsear_horarios_pdf.py
"""

import json
import re
from pathlib import Path

import pdfplumber

BASE_DIR = Path(__file__).resolve().parents[1]
PDF_DIR  = BASE_DIR / "data" / "pdf-horario"
SAIDA    = BASE_DIR / "data" / "json" / "novos_trajetos" / "horarios_novos.json"

PREFIXOS_NOVAS = [
    "horario_0036_", "horario_0065_", "horario_0301_", "horario_0402_",
    "horario_1020_", "horario_1022_", "horario_1023_",
    "horario_0001-m_", "horario_0002-m_", "horario_0003-m_",
    "horario_0004-m_", "horario_0005-m_",
    # sessão 6
    "horario_0014_", "horario_0109_", "horario_0209_",
    "horario_0612_", "horario_0617_",
    "horario_1000-b_", "horario_2058_", "horario_4000_",
    "horario_0612-a_",
]

RE_HORA   = re.compile(r"\b(\d{2}:\d{2})\b")
RE_DIA_UTIL = re.compile(r"Dia\s+[UÚúu]til", re.IGNORECASE)
RE_SABADO   = re.compile(r"[SÁsá]bado", re.IGNORECASE)
RE_DOMINGO  = re.compile(r"Domingo", re.IGNORECASE)
RE_TERMINAL_I = re.compile(r"TERMINAL\s+INICIAL", re.IGNORECASE)
RE_TERMINAL_F = re.compile(r"PONTO\s+FINAL|RETORNO", re.IGNORECASE)


def extrair_codigo(nome_arquivo: str) -> str:
    m = re.match(r"horario_(.+?)_\d{8}", nome_arquivo)
    return m.group(1) if m else nome_arquivo


def parsear_pdf(pdf_path: Path) -> dict | None:
    estrutura = {
        "dia_util": {"ida": [], "volta": []},
        "sabado":   {"ida": [], "volta": []},
        "domingo":  {"ida": [], "volta": []},
    }

    dia_atual    = None
    secao_atual  = None  # "terminal_inicial" ou "ponto_final"
    buffer_horas: list[str] = []

    def flush(dia, secao, horas):
        if not dia or not horas:
            return
        chave = "ida" if secao == "terminal_inicial" else "volta"
        if dia in estrutura:
            estrutura[dia][chave].extend(horas)

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                texto = page.extract_text() or ""
                for linha in texto.splitlines():
                    ln = linha.strip()

                    if RE_TERMINAL_I.search(ln):
                        flush(dia_atual, secao_atual, buffer_horas)
                        secao_atual = "terminal_inicial"
                        dia_atual = None
                        buffer_horas = []
                        continue

                    if RE_TERMINAL_F.search(ln):
                        flush(dia_atual, secao_atual, buffer_horas)
                        secao_atual = "ponto_final"
                        dia_atual = None
                        buffer_horas = []
                        continue

                    if secao_atual is None:
                        continue

                    if RE_DIA_UTIL.search(ln):
                        flush(dia_atual, secao_atual, buffer_horas)
                        dia_atual = "dia_util"
                        buffer_horas = []
                        continue

                    if RE_SABADO.search(ln) and not RE_HORA.search(ln):
                        flush(dia_atual, secao_atual, buffer_horas)
                        dia_atual = "sabado"
                        buffer_horas = []
                        continue

                    if RE_DOMINGO.search(ln) and not RE_HORA.search(ln):
                        flush(dia_atual, secao_atual, buffer_horas)
                        dia_atual = "domingo"
                        buffer_horas = []
                        continue

                    horas = RE_HORA.findall(ln)
                    if horas:
                        buffer_horas.extend(horas)

        flush(dia_atual, secao_atual, buffer_horas)

    except Exception as e:
        print(f"  ERRO ao ler {pdf_path.name}: {e}")
        return None

    total = sum(len(v["ida"]) + len(v["volta"]) for v in estrutura.values())
    if total == 0:
        return None
    return estrutura


def encontrar_pdf(prefixo: str) -> Path | None:
    matches = sorted(PDF_DIR.glob(f"{prefixo}*.pdf"))
    return matches[-1] if matches else None


resultado = {}
sem_pdf = []

for pref in PREFIXOS_NOVAS:
    pdf = encontrar_pdf(pref)
    if pdf is None:
        cod = pref.replace("horario_", "").rstrip("_")
        sem_pdf.append(cod)
        continue

    r = parsear_pdf(pdf)
    if r is None:
        print(f"  [VAZIO] {pdf.name}")
        continue

    cod = extrair_codigo(pdf.stem)
    resultado[cod] = r
    du = len(r["dia_util"]["ida"])
    sa = len(r["sabado"]["ida"])
    do = len(r["domingo"]["ida"])
    print(f"  [OK] {cod:<12}  DU={du:>3}  SAB={sa:>3}  DOM={do:>3}")

SAIDA.parent.mkdir(parents=True, exist_ok=True)
with SAIDA.open("w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print(f"\n[OK] {SAIDA}")
print(f"     {len(resultado)} linhas parseadas")
if sem_pdf:
    print(f"     SEM PDF: {sem_pdf}")
