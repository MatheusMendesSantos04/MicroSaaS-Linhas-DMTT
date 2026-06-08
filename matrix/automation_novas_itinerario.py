"""
SCRIPT 1 — Itinerario por Via das linhas novas

Antes de rodar:
  1. Abra Matrix, faca login, navegue: STC-MACEIO > Relatorio > Cadastro > OSO > OSO
  2. Tipo de Pesquisa: No da Linha
  3. Checkboxes: marque SOMENTE [x] Itinerario por Via  (desmarque Quadro Horario)
  4. Nao mexa no mouse/teclado durante a execucao

PDFs salvos em: data/pdf-intinerarios-por-via-todas-linhas/

Uso:
    cd matrix
    python automation_novas_itinerario.py
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pyautogui
from pywinauto import Desktop

pyautogui.FAILSAFE = False

BASE_DIR   = Path(__file__).resolve().parents[1]
PDF_DIR    = BASE_DIR / "data" / "pdf-intinerarios-por-via-todas-linhas"
COORD_FILE = Path(__file__).parent / "coordenadas.json"
LOG_FILE   = Path(__file__).parent / "log_novas_itinerario.txt"
PROG_FILE  = Path(__file__).parent / "progress_novas_itinerario.json"

PDF_DIR.mkdir(parents=True, exist_ok=True)

LINHAS = [
    # pipeline sessão 5
    "0036",
    "0065",
    "0301",
    "0402",
    "1020",
    "1022",
    "1023",
    "0001-m",
    "0002-m",
    "0003-m",
    "0004-m",
    "0005-m",
    # linhas complementares sessão 6
    "0014",
    "0109",
    "0209",
    "0617",
    "2058",
    "4000",
    "1000-b",   # verificar formato exato no Matrix
]


def clicar(x, y, delay=0.4):
    pyautogui.click(x, y)
    time.sleep(delay)


def digitar(texto, intervalo=0.07):
    pyautogui.write(texto, interval=intervalo)


def focar_matrix():
    try:
        for janela in Desktop(backend="uia").windows():
            t = (janela.window_text() or "").lower()
            if "matrix" in t or "relatorio" in t or "relatório" in t:
                janela.set_focus()
                time.sleep(0.4)
                return True
    except Exception:
        pass
    return False


def carregar_progresso():
    if PROG_FILE.exists():
        return json.loads(PROG_FILE.read_text(encoding="utf-8"))
    return {"processadas": [], "erros": []}


def salvar_progresso(prog):
    PROG_FILE.write_text(json.dumps(prog, indent=2), encoding="utf-8")


def processar_linha(codigo, coords, log):
    def w(msg):
        print(msg); log.write(msg + "\n"); log.flush()

    w(f"\n{'='*50}\nLinha: {codigo}")
    try:
        focar_matrix()

        # 1. Campo Numero
        w("  1. Digitando numero")
        clicar(*coords["campo_numero"])
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.press("delete")
        time.sleep(0.2)
        digitar(codigo)
        time.sleep(0.5)

        # 2. Imprimir
        w("  2. Imprimir")
        clicar(*coords["botao_imprimir"], delay=4)
        time.sleep(3)

        # 3. Exportar
        w("  3. Exportar")
        clicar(*coords["icone_exportar"], delay=3)
        time.sleep(2)

        # 4. OK formato PDF
        w("  4. OK formato")
        clicar(*coords["botao_ok_1"], delay=1.5)
        time.sleep(3)

        # 5. OK paginas
        w("  5. OK paginas")
        clicar(*coords["botao_ok_2"], delay=1.5)
        time.sleep(3)

        # 6. Campo nome arquivo — caminho completo
        w("  6. Nome arquivo")
        clicar(*coords["campo_arquivo"], delay=0.5)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        nome = f"itinerario_{codigo}_{datetime.now().strftime('%Y%m%d')}"
        caminho = str(PDF_DIR / nome)
        digitar(caminho, intervalo=0.04)
        time.sleep(0.5)

        # 7. Salvar
        w("  7. Salvar")
        time.sleep(2)
        clicar(*coords["botao_salvar"], delay=3)

        # 8. Fechar
        w("  8. Fechar visualizacao")
        clicar(*coords["botao_fechar"], delay=1.5)

        w(f"  OK: {nome}.pdf")
        return True

    except Exception as e:
        w(f"  ERRO: {e}")
        return False


def main():
    print("=" * 60)
    print("ITINERARIO POR VIA — LINHAS NOVAS")
    print("=" * 60)
    print("\nCertifique que no Matrix esta marcado SOMENTE:")
    print("  [x] Itinerario por Via")
    print("  [ ] Quadro Horario  (desmarcado)")

    coords    = json.loads(COORD_FILE.read_text())
    progresso = carregar_progresso()

    pendentes = [l for l in LINHAS if l not in progresso["processadas"]]
    feitas    = [l for l in LINHAS if l in progresso["processadas"]]

    print(f"\nTotal   : {len(LINHAS)}")
    print(f"Feitas  : {len(feitas)}  {feitas}")
    print(f"Faltam  : {len(pendentes)}  {pendentes}")
    print(f"Pasta   : {PDF_DIR}")
    print("\nNao mexa no mouse/teclado!")

    resp = input("\nIniciar? (S/N): ").strip().upper()
    if resp != "S":
        print("Cancelado.")
        return

    ok = err = 0
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n{'='*60}\nInicio: {datetime.now()}\n")
        for i, cod in enumerate(pendentes, 1):
            print(f"\n[{i}/{len(pendentes)}]")
            if processar_linha(cod, coords, log):
                progresso["processadas"].append(cod)
                ok += 1
            else:
                progresso["erros"].append(cod)
                err += 1
            salvar_progresso(progresso)
        log.write(f"\nConcluido: {ok} OK | {err} erros\n")

    print(f"\nConcluido: {ok} OK | {err} erros")
    if progresso["erros"]:
        print(f"Erros: {progresso['erros']}")
    print(f"PDFs: {len(list(PDF_DIR.glob('itinerario_*.pdf')))}")


if __name__ == "__main__":
    main()
