"""
Fase D do pipeline — parseia PDFs de Itinerário por Via do Matrix.

Lê todos os PDFs em data/pdf-intinerarios-por-via-todas-linhas/
que correspondem às linhas novas e gera:
    data/json/novos_trajetos/itinerario_rascunho.json

Formato de saída:
{
  "0036 - DUBEAUX LEAO/CENTRO": {
    "ida":   [{"seq": 1, "via": "TERMINAL CONJ. CLETO MARQUES LUZ", "codigo": "00929"}],
    "volta": [{"seq": 1, "via": "RUA DO COMERCIO", "codigo": "00642"}]
  }
}

Uso:
    python python/parsear_itinerario_pdf.py
"""

import json
import re
from pathlib import Path

import pdfplumber

BASE_DIR = Path(__file__).resolve().parents[1]
PDF_DIR  = BASE_DIR / "data" / "pdf-intinerarios-por-via-todas-linhas"
SAIDA    = BASE_DIR / "data" / "json" / "novos_trajetos" / "itinerario_rascunho.json"

# Linhas a processar neste pipeline (prefixo dos arquivos)
PREFIXOS_NOVAS = [
    "itinerario_0036_", "itinerario_0065_", "itinerario_0301_", "itinerario_0402_",
    "itinerario_1020_", "itinerario_1022_", "itinerario_1023_",
    "itinerario_0001-m_", "itinerario_0002-m_", "itinerario_0003-m_",
    "itinerario_0004-m_", "itinerario_0005-m_",
    # sessão 6
    "itinerario_0014_", "itinerario_0109_", "itinerario_0209_",
    "itinerario_0612_", "itinerario_0617_",
    "itinerario_1000-b_", "itinerario_2058_", "itinerario_4000_",
    "itinerario_0612-a_",
]

RE_LINHA  = re.compile(r"Linha:\s*(.+)", re.IGNORECASE)
RE_ENTRADA = re.compile(r"^(?:(IDA|VOLTA)\s+)?(\d{3})\s+(\d{5})\s+(.+)$")
RE_SUBTOT  = re.compile(r"^Sub-Total", re.IGNORECASE)


def parsear_pdf(pdf_path: Path) -> dict | None:
    result = {"ida": [], "volta": [], "nome_linha": ""}
    sentido_atual = None

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                texto = page.extract_text() or ""
                for linha in texto.splitlines():
                    linha = linha.strip()

                    # captura nome da linha
                    m = RE_LINHA.match(linha)
                    if m and not result["nome_linha"]:
                        result["nome_linha"] = m.group(1).strip()
                        continue

                    if RE_SUBTOT.match(linha):
                        continue

                    m = RE_ENTRADA.match(linha)
                    if not m:
                        continue

                    if m.group(1):
                        sentido_atual = m.group(1).upper()

                    if sentido_atual not in ("IDA", "VOLTA"):
                        continue

                    entrada = {
                        "seq":    int(m.group(2)),
                        "codigo": m.group(3),
                        "via":    m.group(4).strip(),
                    }
                    result[sentido_atual.lower()].append(entrada)

    except Exception as e:
        print(f"  ERRO ao ler {pdf_path.name}: {e}")
        return None

    if not result["ida"] and not result["volta"]:
        return None
    return result


def encontrar_pdf(prefixo: str) -> Path | None:
    matches = sorted(PDF_DIR.glob(f"{prefixo}*.pdf"))
    return matches[-1] if matches else None


resultado = {}
sem_pdf = []

for pref in PREFIXOS_NOVAS:
    pdf = encontrar_pdf(pref)
    if pdf is None:
        cod = pref.replace("itinerario_", "").rstrip("_")
        sem_pdf.append(cod)
        continue

    r = parsear_pdf(pdf)
    if r is None:
        print(f"  [VAZIO] {pdf.name}")
        continue

    nome = r["nome_linha"] or pref.replace("itinerario_", "").rstrip("_")
    resultado[nome] = {"ida": r["ida"], "volta": r["volta"]}
    print(f"  [OK] {nome:<45}  IDA={len(r['ida']):>3}  VOLTA={len(r['volta']):>3}")

SAIDA.parent.mkdir(parents=True, exist_ok=True)
with SAIDA.open("w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print(f"\n[OK] {SAIDA}")
print(f"     {len(resultado)} linhas parseadas")
if sem_pdf:
    print(f"     SEM PDF: {sem_pdf}")
