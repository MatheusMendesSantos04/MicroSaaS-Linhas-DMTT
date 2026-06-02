"""
Automacao MATRIX para as LINHAS NOVAS (coordenadas do mouse).

Baseado em automation_matrix_mouse_completo.py — usa pyautogui com
coordenadas ja mapeadas em coordenadas.json.

Antes de rodar:
  1. Abra o Matrix e faca login
  2. Navegue: STC-MACEIO -> Relatorio -> Cadastro -> OSO -> OSO
  3. Configure:
       Tipo de Pesquisa : No da Linha
       Data             : hoje
       Checkboxes       : [x] Itinerario por Via   [x] Quadro Horario
  4. Deixe a tela aberta, nao mexa no mouse/teclado
  5. Execute este script (cd matrix && python automation_novas_linhas.py)

PDFs salvos em: data/pdf/matrix_export/novas/
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pyautogui
from pywinauto import Desktop

pyautogui.FAILSAFE = False

BASE_DIR  = Path(__file__).resolve().parents[1]
PDF_DIR   = BASE_DIR / "data" / "pdf" / "matrix_export" / "novas"
COORD_FILE = Path(__file__).parent / "coordenadas.json"
LOG_FILE   = Path(__file__).parent / "automation_novas_log.txt"
PROG_FILE  = Path(__file__).parent / "progress_novas.json"

PDF_DIR.mkdir(parents=True, exist_ok=True)

# Linhas convencionais novas
LINHAS_CONVENCIONAIS = [
    "0036",
    "0065",
    "0301",
    "0402",
    "1020",
    "1022",
    "1023",
]

# Madrugadao — formato confirmado pelo usuario: "0001-m"
LINHAS_MADRUG = [
    "0001-m",
    "0002-m",
    "0003-m",
    "0004-m",
    "0005-m",
]

# Todas as linhas a processar
TODAS_LINHAS = LINHAS_CONVENCIONAIS + LINHAS_MADRUG


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def clicar(x, y, delay=0.4):
    pyautogui.click(x, y)
    time.sleep(delay)


def digitar(texto, intervalo=0.07):
    pyautogui.write(texto, interval=intervalo)


def focar_matrix():
    try:
        desktop = Desktop(backend="uia")
        for janela in desktop.windows():
            t = (janela.window_text() or "").lower()
            if t == "matrix" or "relatorio" in t or "relatório" in t:
                janela.set_focus()
                time.sleep(0.4)
                return True
    except Exception:
        pass
    return False


def carregar_coords() -> dict:
    if not COORD_FILE.exists():
        raise FileNotFoundError(f"coordenadas.json nao encontrado em {COORD_FILE}")
    return json.loads(COORD_FILE.read_text())


def carregar_progresso() -> dict:
    if PROG_FILE.exists():
        return json.loads(PROG_FILE.read_text(encoding="utf-8"))
    return {"processadas": [], "erros": []}


def salvar_progresso(prog: dict):
    PROG_FILE.write_text(json.dumps(prog, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# processamento de uma linha
# ---------------------------------------------------------------------------

def processar_linha(codigo: str, coords: dict, log) -> bool:
    def escrever(msg):
        print(msg)
        log.write(msg + "\n")
        log.flush()

    escrever(f"\n{'='*50}\nLinha: {codigo}")
    try:
        # Foca janela
        focar_matrix()

        # Campo Numero
        escrever("  1. Campo Numero")
        clicar(*coords["campo_numero"])
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.press("delete")
        time.sleep(0.2)
        digitar(codigo)
        time.sleep(0.5)

        # Imprimir
        escrever("  2. Imprimir")
        clicar(*coords["botao_imprimir"], delay=4)  # aguarda relatorio abrir

        # Aguarda janela de visualizacao
        escrever("  3. Aguardando visualizacao...")
        time.sleep(3)

        # Icone exportar
        escrever("  4. Exportar")
        clicar(*coords["icone_exportar"], delay=3)

        # OK formato (PDF)
        escrever("  5. OK formato")
        time.sleep(2)
        clicar(*coords["botao_ok_1"], delay=1.5)

        # OK paginas (Todas)
        escrever("  6. OK paginas")
        time.sleep(3)
        clicar(*coords["botao_ok_2"], delay=1.5)

        # Campo arquivo — digita caminho completo
        escrever("  7. Nome do arquivo")
        time.sleep(3)
        clicar(*coords["campo_arquivo"], delay=0.5)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)

        nome = f"linha_{codigo}_{datetime.now().strftime('%Y%m%d')}"
        caminho = str(PDF_DIR / nome)
        digitar(caminho, intervalo=0.04)
        time.sleep(0.5)

        # Salvar
        escrever("  8. Salvar")
        time.sleep(2)
        clicar(*coords["botao_salvar"], delay=3)

        # Fechar visualizacao
        escrever("  9. Fechar")
        clicar(*coords["botao_fechar"], delay=1.5)

        escrever(f"  OK: {nome}.pdf")
        return True

    except Exception as e:
        escrever(f"  ERRO: {e}")
        return False


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("AUTOMACAO MATRIX - LINHAS NOVAS")
    print("=" * 60)

    coords   = carregar_coords()
    progresso = carregar_progresso()

    pendentes = [l for l in TODAS_LINHAS if l not in progresso["processadas"]]
    ja_feitas = [l for l in TODAS_LINHAS if l in progresso["processadas"]]

    print(f"\nTotal de linhas : {len(TODAS_LINHAS)}")
    print(f"Ja processadas  : {len(ja_feitas)} {ja_feitas}")
    print(f"A processar     : {len(pendentes)} {pendentes}")
    print(f"PDFs em         : {PDF_DIR}")
    print(f"\nNao mexa no mouse/teclado durante a execucao!")

    resp = input("\nIniciar? (S/N): ").strip().upper()
    if resp != "S":
        print("Cancelado.")
        return

    ok_count = 0
    err_count = 0

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n{'='*60}\nInicio: {datetime.now()}\n")

        for i, codigo in enumerate(pendentes, 1):
            print(f"\n[{i}/{len(pendentes)}]")
            if processar_linha(codigo, coords, log):
                progresso["processadas"].append(codigo)
                ok_count += 1
            else:
                progresso["erros"].append(codigo)
                err_count += 1
            salvar_progresso(progresso)

        log.write(f"\nConcluido: {ok_count} OK | {err_count} erros\n")

    print(f"\n{'='*60}")
    print(f"Concluido: {ok_count} OK | {err_count} erros")
    if progresso["erros"]:
        print(f"Erros: {progresso['erros']}")

    pdfs = list(PDF_DIR.glob("*.pdf"))
    print(f"PDFs criados: {len(pdfs)}")


if __name__ == "__main__":
    main()
