"""
Atualiza data/json/horarios/horarios.json com os PDFs de Quadro Horario mais
recentes gerados por matrix/automation_horarios_ativas.py, para as linhas
ativas do OSO.

A chave de horarios.json passa a ser o codigo NORMALIZADO (maiusculo, sem
hifen/espaco) -- ex: "0012", "0001M", "0612A", "1000B" -- em vez de sempre 4
digitos. Isso evita que linhas com sufixo (madrugadao, variantes -A/-B, que
tem horario proprio e diferente) colidam com a linha base de mesmo prefixo
numerico. gerar_dados_estaticos.py foi ajustado pra usar a mesma normalizacao
na hora de casar cada linha com seu horario.

Uso:
    python python/atualizar_horarios_ativas.py
"""
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "pdf-horario"
HORARIOS_PATH = ROOT / "data" / "json" / "horarios" / "horarios.json"

sys.path.insert(0, str(ROOT / "matrix"))
from automation_horarios_ativas import LINHAS  # noqa: E402

RE_HORA = re.compile(r"\b(\d{2}:\d{2})\b")
RE_DIA_UTIL = re.compile(r"Dia\s+[UÚúu]til", re.IGNORECASE)
RE_SABADO = re.compile(r"[SÁsá]bado", re.IGNORECASE)
RE_DOMINGO = re.compile(r"Domingo", re.IGNORECASE)
RE_TERMINAL_I = re.compile(r"TERMINAL\s+INICIAL", re.IGNORECASE)
RE_TERMINAL_F = re.compile(r"PONTO\s+FINAL|RETORNO", re.IGNORECASE)


def normalizar(codigo: str) -> str:
    return codigo.upper().replace("-", "").replace(" ", "")


def encontrar_pdf_mais_recente(codigo: str) -> Path | None:
    matches = sorted(PDF_DIR.glob(f"horario_{codigo}_*.pdf"))
    return matches[-1] if matches else None


def parsear_pdf(pdf_path: Path) -> dict | None:
    estrutura = {
        "dia_util": {"ida": [], "volta": []},
        "sabado":   {"ida": [], "volta": []},
        "domingo":  {"ida": [], "volta": []},
    }

    dia_atual = None
    secao_atual = None
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


def main():
    horarios = json.loads(HORARIOS_PATH.read_text(encoding="utf-8")) if HORARIOS_PATH.exists() else {}

    atualizadas, sem_pdf, vazias = [], [], []

    for codigo in LINHAS:
        pdf = encontrar_pdf_mais_recente(codigo)
        if pdf is None:
            sem_pdf.append(codigo)
            continue

        estrutura = parsear_pdf(pdf)
        if estrutura is None:
            vazias.append(codigo)
            continue

        chave = normalizar(codigo)
        horarios[chave] = estrutura
        du = len(estrutura["dia_util"]["ida"])
        sa = len(estrutura["sabado"]["ida"])
        do = len(estrutura["domingo"]["ida"])
        print(f"  [OK] {codigo:<10} -> {chave:<8}  DU={du:>3}  SAB={sa:>3}  DOM={do:>3}   ({pdf.name})")
        atualizadas.append(chave)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = HORARIOS_PATH.with_suffix(f".{ts}.bak.json")
    shutil.copy(HORARIOS_PATH, bak)
    HORARIOS_PATH.write_text(json.dumps(horarios, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nBackup salvo em: {bak.name}")
    print(f"Atualizadas ({len(atualizadas)}): {atualizadas}")
    if sem_pdf:
        print(f"Sem PDF encontrado ({len(sem_pdf)}): {sem_pdf}")
    if vazias:
        print(f"PDF sem horarios extraiveis ({len(vazias)}): {vazias}")
    print(f"Total de chaves em horarios.json agora: {len(horarios)}")
    print("\nProximo passo: python python/gerar_dados_estaticos.py")


if __name__ == "__main__":
    main()
