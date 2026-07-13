"""
Quadro Horario -- TODAS as linhas ativas (fonte: OSO 08/07/2026)

Lista de linhas gerada a partir de "linhas/resumo de oso 08-07-2026.pdf" via
python/comparar_oso_dados_unificados.py -- 102 linhas ativas, excluindo
Catraca de Solo. Regenerar a lista (ver bloco no fim deste arquivo) sempre
que houver um OSO mais recente.

Formato dos codigos com sufixo (madrugadao "-m", "1000-a/b", "0612-a"): usa
minusculo, mesma convencao ja validada em automation_novas_horario.py para
"-m" e "1000-b". O sufixo "-a" (0612-a, 1000-a) ainda NAO foi confirmado
contra o Matrix -- se o campo "Numero" rejeitar ou nao encontrar a linha,
teste variacoes (maiusculo, com espaco "0612 A", sem hifen) e ajuste aqui.

Antes de rodar:
  1. Abra Matrix, faca login, navegue: STC-MACEIO > Relatorio > Cadastro > OSO > OSO
  2. Tipo de Pesquisa: No da Linha
  3. Checkboxes: marque SOMENTE [x] Quadro Horario  (desmarque Itinerario por Via)
  4. Deixe a janela do Matrix em FOCO (clique nela) antes de iniciar -- o
     auto-foco por janela (pywinauto) so funciona se a DLL mfc140u.dll
     estiver presente; sem ela, o script cai pra clique por coordenada puro
     e conta com o Matrix ja estar em primeiro plano
  5. Nao mexa no mouse/teclado durante a execucao

PDFs salvos em: data/pdf-horario/

Uso:
    cd matrix
    python automation_horarios_ativas.py
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pyautogui

try:
    from pywinauto import Desktop
except ImportError:
    Desktop = None  # pywinauto exige a DLL mfc140u.dll (ausente nesta maquina) --
    # sem ela, so perdemos o auto-foco da janela; os cliques por coordenada
    # (calibrados em coordenadas.json) funcionam do mesmo jeito. Deixe o
    # Matrix em foco manualmente antes de iniciar.

pyautogui.FAILSAFE = True  # mover o mouse pro canto superior-esquerdo aborta

BASE_DIR   = Path(__file__).resolve().parents[1]
PDF_DIR    = BASE_DIR / "data" / "pdf-horario"
COORD_FILE = Path(__file__).parent / "coordenadas.json"
LOG_FILE   = Path(__file__).parent / "log_horarios_ativas.txt"
PROG_FILE  = Path(__file__).parent / "progress_horarios_ativas.json"

PDF_DIR.mkdir(parents=True, exist_ok=True)

# 102 linhas ativas no OSO de 08/07/2026 (exclui Catraca de Solo).
# Regenerar com:
#   python -c "import sys; sys.path.insert(0,'python'); from comparar_oso_dados_unificados import extrair_oso; from pathlib import Path; \
#              l = extrair_oso(Path('linhas/resumo de oso <DATA>.pdf')); \
#              print(sorted({x['codigo'].lower() for x in l if x['tipo'] != 'CATRACA DE SOLO'}))"
LINHAS = [
    "0001-m", "0002-m", "0003-m", "0004-m", "0005-m", "0006-m",
    "0012", "0014", "0027", "0033", "0036", "0037", "0039", "0041", "0042",
    "0046", "0048", "0051", "0052", "0053", "0056", "0057", "0058", "0065",
    "0068", "0069", "0101", "0102", "0104", "0105", "0108", "0109", "0110",
    "0112", "0113", "0114", "0115", "0116", "0117", "0209", "0214", "0217",
    "0301", "0401", "0402", "0403", "0404", "0501", "0502", "0504", "0601",
    "0602", "0603", "0604", "0606", "0607", "0610", "0612", "0612-a", "0615",
    "0617", "0700", "0703", "0704", "0706", "0707", "0708", "0709", "0710",
    "0712", "0714", "0716", "0719", "0720", "0723", "0727", "0802", "0804",
    "0805", "0807", "0809", "0812", "0900", "0901", "0903", "0999", "1000-a",
    "1000-b", "1018", "1019", "1020", "1022", "1023", "1024", "2058", "4000",
    "4003", "4006", "4011", "4013", "4014", "4015",
]


def clicar(x, y, delay=0.4):
    pyautogui.click(x, y)
    time.sleep(delay)


def digitar(texto, intervalo=0.07):
    pyautogui.write(texto, interval=intervalo)


def focar_matrix():
    if Desktop is None:
        return False  # sem pywinauto -- assume que o Matrix ja esta em foco
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

        w("  1. Digitando numero")
        clicar(*coords["campo_numero"])
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.press("delete")
        time.sleep(0.2)
        digitar(codigo)
        time.sleep(0.5)

        w("  2. Imprimir")
        clicar(*coords["botao_imprimir"], delay=4)
        time.sleep(3)

        w("  3. Exportar")
        clicar(*coords["icone_exportar"], delay=3)
        time.sleep(2)

        w("  4. OK formato")
        clicar(*coords["botao_ok_1"], delay=1.5)
        time.sleep(3)

        w("  5. OK paginas")
        clicar(*coords["botao_ok_2"], delay=1.5)
        time.sleep(3)

        w("  6. Nome arquivo")
        clicar(*coords["campo_arquivo"], delay=0.5)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        nome = f"horario_{codigo}_{datetime.now().strftime('%Y%m%d')}"
        caminho = str(PDF_DIR / nome)
        digitar(caminho, intervalo=0.04)
        time.sleep(0.5)

        w("  7. Salvar")
        time.sleep(2)
        clicar(*coords["botao_salvar"], delay=3)

        w("  8. Fechar visualizacao")
        clicar(*coords["botao_fechar"], delay=1.5)

        w(f"  OK: {nome}.pdf")
        return True

    except Exception as e:
        w(f"  ERRO: {e}")
        return False


def main():
    print("=" * 60)
    print("QUADRO DE HORARIO -- LINHAS ATIVAS (OSO 08/07/2026)")
    print("=" * 60)
    print("\nCertifique que no Matrix esta marcado SOMENTE:")
    print("  [ ] Itinerario por Via  (desmarcado)")
    print("  [x] Quadro Horario")

    coords = json.loads(COORD_FILE.read_text())
    progresso = carregar_progresso()

    pendentes = [l for l in LINHAS if l not in progresso["processadas"]]
    feitas = [l for l in LINHAS if l in progresso["processadas"]]

    print(f"\nTotal ativas : {len(LINHAS)}")
    print(f"Feitas       : {len(feitas)}")
    print(f"Faltam       : {len(pendentes)}")
    print(f"Pasta        : {PDF_DIR}")
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
    print(f"PDFs: {len(list(PDF_DIR.glob('horario_*.pdf')))}")


if __name__ == "__main__":
    main()
