"""
Parser de PDFs — Quadro Horário DMTT
=====================================
Converte os PDFs de "Quadro Horário" exportados do sistema MATRIX
para um JSON estruturado pronto para consumo pelo backend FastAPI.

USO:
    python matrix/parse_horarios.py                   # processa todos os PDFs em data/pdf/horarios/
    python matrix/parse_horarios.py --linha 0024      # processa apenas a linha 0024
    python matrix/parse_horarios.py --debug           # mostra texto bruto extraído

SAÍDA:
    data/json/horarios/horarios.json

FORMATO DO JSON DE SAÍDA:
{
  "0024": {
    "nome": "0024 - Gruta / Centro / Term. Rotary",
    "dia_util": {
      "ida":   ["05:00", "05:30", "06:00", ...],
      "volta": ["05:15", "05:45", ...]
    },
    "sabado":  { "ida": [...], "volta": [...] },
    "domingo": { "ida": [...], "volta": [...] }
  },
  ...
}
"""

import re
import json
import argparse
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERRO pdfplumber não instalado. Execute:")
    print("   pip install pdfplumber")
    raise

# ── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).resolve().parent.parent
PDF_DIR     = BASE_DIR / "data" / "pdf-horario"
OUTPUT_DIR  = BASE_DIR / "data" / "json" / "horarios"
OUTPUT_FILE = OUTPUT_DIR / "horarios.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Regex ────────────────────────────────────────────────────────────────────

RE_HORA        = re.compile(r"\b([0-2]\d):([0-5]\d)\b")
RE_LINHA_NUM   = re.compile(r"\b(\d{4})\b")
RE_DIA_UTIL    = re.compile(r"DIA\s*[ÚU]TIL|DIAS?\s*[ÚU]TEIS|ÚTEIS|UTIL", re.IGNORECASE)
RE_SABADO      = re.compile(r"S[AÁ]BADO", re.IGNORECASE)
RE_DOMINGO     = re.compile(r"DOMINGO", re.IGNORECASE)
RE_IDA         = re.compile(r"\bIDA\b", re.IGNORECASE)
RE_VOLTA       = re.compile(r"\bVOLTA\b|\bRETORNO\b", re.IGNORECASE)
RE_LINHA_NOME  = re.compile(r"(\d{4})\s*[-–]\s*(.+?)(?=\n|Data|$)", re.IGNORECASE)

# ── Estrutura padrão ──────────────────────────────────────────────────────────

def horario_vazio() -> dict:
    return {
        "dia_util": {"ida": [], "volta": []},
        "sabado":   {"ida": [], "volta": []},
        "domingo":  {"ida": [], "volta": []},
    }


def normalizar_hora(h: str, m: str) -> str:
    hora = int(h)
    minu = int(m)
    if 0 <= hora <= 23 and 0 <= minu <= 59:
        return f"{hora:02d}:{minu:02d}"
    return None

# ── Parsing principal ─────────────────────────────────────────────────────────

def detectar_dia_tipo(texto: str) -> str | None:
    """Detecta o tipo de dia dominante em um bloco de texto."""
    if RE_DIA_UTIL.search(texto):
        return "dia_util"
    if RE_SABADO.search(texto):
        return "sabado"
    if RE_DOMINGO.search(texto):
        return "domingo"
    return None


def detectar_sentido(texto: str) -> str | None:
    if RE_IDA.search(texto) and not RE_VOLTA.search(texto):
        return "ida"
    if RE_VOLTA.search(texto) and not RE_IDA.search(texto):
        return "volta"
    return None


def extrair_horarios_do_texto(texto: str) -> list[str]:
    """Extrai todos os horários HH:MM de um bloco de texto."""
    horarios = []
    for h, m in RE_HORA.findall(texto):
        hora = normalizar_hora(h, m)
        if hora:
            horarios.append(hora)
    return sorted(set(horarios))


def parse_pdf(pdf_path: Path, debug: bool = False) -> dict | None:
    """
    Extrai dados de horário de um PDF do MATRIX.
    Retorna dict com estrutura {dia_util, sabado, domingo} ou None em caso de falha.
    """
    numero_linha = None
    nome_linha   = None
    dados        = horario_vazio()

    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto_completo = ""
            for page in pdf.pages:
                texto_page = page.extract_text() or ""
                texto_completo += texto_page + "\n"

            if debug:
                print(f"\n{'─'*60}")
                print(f"  Arquivo: {pdf_path.name}")
                print(f"  Texto bruto:\n{texto_completo[:2000]}")
                print("─"*60)

            # Extrair número e nome da linha do cabeçalho
            m = RE_LINHA_NOME.search(texto_completo)
            if m:
                numero_linha = m.group(1).zfill(4)
                nome_linha   = f"{numero_linha} - {m.group(2).strip()}"
            else:
                # Tentar extrair do nome do arquivo
                stem = pdf_path.stem  # ex: "horario_0024"
                match_num = RE_LINHA_NUM.search(stem)
                if match_num:
                    numero_linha = match_num.group(1).zfill(4)
                    nome_linha   = numero_linha

            # Estratégia 1: parsing por blocos / seções ──────────────────────
            # Divide o texto em linhas e rastreia estado (dia, sentido)
            dia_atual     = "dia_util"  # padrão se não detectado
            sentido_atual = "ida"

            for linha in texto_completo.splitlines():
                linha_strip = linha.strip()
                if not linha_strip:
                    continue

                # Atualizar estado de dia
                dia_detectado = detectar_dia_tipo(linha_strip)
                if dia_detectado:
                    dia_atual = dia_detectado

                # Atualizar estado de sentido
                sent_detectado = detectar_sentido(linha_strip)
                if sent_detectado:
                    sentido_atual = sent_detectado

                # Extrair horários da linha
                horarios_linha = extrair_horarios_do_texto(linha_strip)
                for h in horarios_linha:
                    lista = dados[dia_atual][sentido_atual]
                    if h not in lista:
                        lista.append(h)

            # Estratégia 2: tabelas (pdfplumber) ─────────────────────────────
            # Tenta extrair tabelas estruturadas da primeira página
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tabelas = page.extract_tables()
                    for tabela in tabelas:
                        _processar_tabela(tabela, dados, debug)

            # Ordenar horários de cada sessão
            for dia in dados:
                for sentido in dados[dia]:
                    dados[dia][sentido] = sorted(set(dados[dia][sentido]))

    except Exception as e:
        print(f"  ERRO Erro ao processar {pdf_path.name}: {e}")
        return None

    if not numero_linha:
        # Último recurso: usar nome do arquivo
        stem = pdf_path.stem
        match_num = RE_LINHA_NUM.search(stem)
        numero_linha = match_num.group(1).zfill(4) if match_num else stem

    total_horarios = sum(len(v) for d in dados.values() for v in d.values())
    if debug:
        print(f"  Linha: {numero_linha}  |  Nome: {nome_linha}")
        print(f"  Total de horários extraídos: {total_horarios}")

    return {"numero": numero_linha, "nome": nome_linha, "dados": dados}


def _processar_tabela(tabela: list, dados: dict, debug: bool = False):
    """
    Tenta extrair horários de uma tabela pdfplumber.
    Cada linha da tabela é uma lista de células.
    """
    if not tabela:
        return

    # Detectar cabeçalho de colunas
    cabecalho = [str(c or "").strip().upper() for c in (tabela[0] if tabela else [])]

    dia_cols     = {}  # índice de coluna → dia_tipo
    sentido_cols = {}  # índice de coluna → sentido

    for i, cab in enumerate(cabecalho):
        if RE_DIA_UTIL.search(cab):
            dia_cols[i] = "dia_util"
        elif RE_SABADO.search(cab):
            dia_cols[i] = "sabado"
        elif RE_DOMINGO.search(cab):
            dia_cols[i] = "domingo"
        if RE_IDA.search(cab):
            sentido_cols[i] = "ida"
        elif RE_VOLTA.search(cab):
            sentido_cols[i] = "volta"

    # Processar linhas de dados
    for linha in tabela[1:]:
        for i, celula in enumerate(linha):
            texto_celula = str(celula or "").strip()
            horarios = extrair_horarios_do_texto(texto_celula)
            if not horarios:
                continue

            dia     = dia_cols.get(i, "dia_util")
            sentido = sentido_cols.get(i, "ida")

            for h in horarios:
                lista = dados[dia][sentido]
                if h not in lista:
                    lista.append(h)

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Parser de PDFs de Quadro Horário DMTT")
    parser.add_argument("--linha",  help="Processar apenas esta linha (ex: 0024)")
    parser.add_argument("--debug",  action="store_true", help="Mostrar texto bruto extraído")
    parser.add_argument("--output", help=f"Arquivo de saída (padrão: {OUTPUT_FILE})")
    args = parser.parse_args()

    saida = Path(args.output) if args.output else OUTPUT_FILE

    # Selecionar PDFs
    if args.linha:
        num = args.linha.zfill(4)
        pdfs = list(PDF_DIR.glob(f"horario_{num}*.pdf"))
        if not pdfs:
            print(f"ERRO PDF não encontrado para linha {num} em {PDF_DIR}")
            return
    else:
        pdfs = sorted(PDF_DIR.glob("horario_*.pdf"))

    if not pdfs:
        print(f"ERRO Nenhum PDF encontrado em {PDF_DIR}")
        print("   Execute primeiro: python matrix/automation_horarios.py")
        return

    print(f"[PDF] PDFs encontrados: {len(pdfs)}")

    # Carregar JSON existente para fazer merge (não perder dados já processados)
    resultado = {}
    if saida.exists():
        with open(saida, "r", encoding="utf-8") as f:
            resultado = json.load(f)
        print(f"  OK JSON existente carregado: {len(resultado)} linhas")

    # Processar
    ok     = 0
    falhas = 0

    for pdf_path in pdfs:
        print(f"\n  > {pdf_path.name}...", end=" ", flush=True)
        parsed = parse_pdf(pdf_path, debug=args.debug)

        if parsed:
            numero = parsed["numero"]
            total  = sum(len(v) for d in parsed["dados"].values() for v in d.values())
            print(f"OK  {total} horários extraídos")

            resultado[numero] = {
                "nome":     parsed["nome"] or numero,
                "dia_util": parsed["dados"]["dia_util"],
                "sabado":   parsed["dados"]["sabado"],
                "domingo":  parsed["dados"]["domingo"],
            }
            ok += 1
        else:
            print("ERRO")
            falhas += 1

    # Salvar JSON
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"""
{'='*60}
  Parser concluído!
  OK Processados com sucesso : {ok}
  ERRO Falhas                  : {falhas}
  [DIR] JSON salvo em           : {saida}
  [INFO] Linhas no JSON          : {len(resultado)}
{'='*60}
""")

    if falhas > 0:
        print("  AVISO:  Para linhas com 0 horários, verifique o formato do PDF")
        print("      com: python matrix/parse_horarios.py --linha XXXX --debug")


if __name__ == "__main__":
    main()
