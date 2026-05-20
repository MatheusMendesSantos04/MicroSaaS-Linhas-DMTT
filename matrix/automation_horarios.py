"""
Automação MATRIX — Extração de Quadro Horário
=============================================
Extrai o relatório "Quadro Horário" para todas as linhas do itinerário.
A diferença em relação ao script de itinerário é o checkbox marcado na
tela de OSO: "Quadro Horário" ao invés de "Itinerário por Via".

INSTRUÇÕES DE USO:
1. Abra o MATRIX e faça login
2. Navegue até: STC-MACEIO → Relatório → Cadastro → OSO → OSO
3. Configure a tela:
   - Tipo de Pesquisa: "Nº da Linha"
   - Data de Referência: "12/02/2026"
   - Marque APENAS: ☑ Quadro Horário   (desmarque os outros)
4. Ajuste as coordenadas se necessário:
      python matrix/configurar_coordenadas_horarios.py
5. Execute este script
"""

import time
import json
import sys
import pyautogui
from pathlib import Path
from datetime import datetime
from pywinauto import Desktop

# ── Configuração ─────────────────────────────────────────────────────────────

BASE_DIR     = Path(__file__).resolve().parent.parent
PDF_DIR      = BASE_DIR / "data" / "pdf-horario"
COORD_FILE   = Path(__file__).parent / "coordenadas_horarios.json"
LISTA_FILE   = Path(__file__).parent / "lista_linhas_horarios.json"
PROGRESS_FILE= Path(__file__).parent / "progress_horarios.json"
LOG_FILE     = Path(__file__).parent / "automation_horarios_log.txt"

PDF_DIR.mkdir(parents=True, exist_ok=True)

pyautogui.FAILSAFE = True   # mover mouse para canto superior-esquerdo encerra

# ── Helpers ──────────────────────────────────────────────────────────────────

def log(msg: str, arquivo=None):
    print(msg)
    if arquivo:
        arquivo.write(msg + "\n")
        arquivo.flush()


def carregar_coordenadas() -> dict | None:
    if not COORD_FILE.exists():
        print(f"❌ Arquivo de coordenadas não encontrado: {COORD_FILE}")
        print("   Execute primeiro: python matrix/configurar_coordenadas_horarios.py")
        return None
    with open(COORD_FILE, "r") as f:
        return json.load(f)


def carregar_linhas() -> list[str]:
    with open(LISTA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["numeros"]


def carregar_progresso() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processadas": [], "erros": []}


def salvar_progresso(prog: dict):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(prog, f, indent=2, ensure_ascii=False)


def focar_matrix() -> bool:
    try:
        for janela in Desktop(backend="uia").windows():
            titulo = (janela.window_text() or "").lower()
            if "matrix" in titulo or "relatório" in titulo or "relatorio" in titulo:
                janela.set_focus()
                time.sleep(0.4)
                return True
    except Exception:
        pass
    return False


def clicar(x: int, y: int, delay: float = 0.35):
    pyautogui.click(x, y)
    time.sleep(delay)


def digitar(texto: str, intervalo: float = 0.05):
    pyautogui.write(texto, interval=intervalo)

# ── Processamento por linha ───────────────────────────────────────────────────

def processar_linha(numero: str, coords: dict, log_f) -> bool:
    log(f"\n{'─'*60}", log_f)
    log(f"  Processando linha: {numero}", log_f)

    try:
        # 1. Focar janela
        if not focar_matrix():
            log("  ⚠️  Janela não focada — continuando mesmo assim", log_f)
        time.sleep(0.5)

        # 2. Clicar no campo Número e inserir a linha
        log("  [1] Inserindo número da linha...", log_f)
        clicar(*coords["campo_numero"])
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.press("delete")
        time.sleep(0.15)
        digitar(numero)
        time.sleep(0.4)

        # 3. Clicar em Imprimir (gera o relatório)
        log("  [2] Clicando em Imprimir...", log_f)
        clicar(*coords["botao_imprimir"], delay=3)   # relatório pode demorar

        # 4. Aguardar janela de visualização
        log("  [3] Aguardando visualização...", log_f)
        time.sleep(4)

        # 5. Exportar → seta vermelha
        log("  [4] Clicando em Exportar...", log_f)
        clicar(*coords["icone_exportar"], delay=1.5)

        # 6. Diálogo 1: escolha de formato (PDF já selecionado) → OK
        log("  [5] Confirmando formato PDF...", log_f)
        time.sleep(2)
        clicar(*coords["botao_ok_1"], delay=1.5)

        # 7. Diálogo 2: páginas "Todas" → OK
        log("  [6] Confirmando 'Todas' as páginas...", log_f)
        time.sleep(2.5)
        clicar(*coords["botao_ok_2"], delay=1.5)

        # 8. Diálogo Salvar Como
        log("  [7] Salvando PDF...", log_f)
        time.sleep(3)
        clicar(*coords["campo_arquivo"], delay=0.5)

        # Digitar o caminho COMPLETO no campo de nome — o Windows navega para a pasta certa
        caminho_completo = str(PDF_DIR / f"horario_{numero}")
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        # pyautogui.write não lida bem com '\' — usar pyperclip via teclado
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("delete")
        time.sleep(0.1)
        import pyperclip
        pyperclip.copy(caminho_completo)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.4)

        # 9. Salvar
        clicar(*coords["botao_salvar"], delay=2.5)
        log(f"  [8] PDF salvo: {caminho_completo}.pdf", log_f)

        # 10. Aguardar arquivo ser gravado no disco
        time.sleep(2)

        # 11. Fechar visualização (botão X)
        log("  [9] Fechando visualização...", log_f)
        clicar(*coords["botao_fechar"], delay=1.5)

        log(f"  ✅ Linha {numero} concluída!", log_f)
        return True

    except Exception as e:
        log(f"  ❌ Erro: {e}", log_f)
        return False

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  AUTOMAÇÃO MATRIX — QUADRO HORÁRIO")
    print("=" * 60)

    # Carregar dados
    coords = carregar_coordenadas()
    if not coords:
        return

    todas_linhas = carregar_linhas()
    progresso    = carregar_progresso()

    print(f"\n  Coordenadas carregadas  : {list(coords.keys())}")
    print(f"  Total de linhas         : {len(todas_linhas)}")
    print(f"  Já processadas          : {len(progresso['processadas'])}")
    print(f"  Pasta de saída (PDFs)   : {PDF_DIR}")

    print("""
  ─────────────────────────────────────────────────
  ⚠️  ANTES DE INICIAR:
     • MATRIX aberto e na tela de OSO
     • Tipo de Pesquisa: "Nº da Linha"
     • Data de Referência: 12/02/2026
     • ☑ Quadro Horário  marcado
     • Outros checkboxes DESMARCADOS
     • NÃO mover a janela MATRIX durante a execução
     • NÃO usar mouse ou teclado
  ─────────────────────────────────────────────────
""")

    # Modo de execução
    print("  Opções:")
    print("  1. Processar todas as linhas pendentes")
    print("  2. Iniciar a partir de uma linha específica")
    print("  3. Testar com uma única linha")
    opcao = input("\n  Escolha (1-3): ").strip()

    if opcao == "2":
        inicio = input("  Número da linha inicial (ex: 0024): ").strip()
        if inicio not in todas_linhas:
            print(f"  ❌ Linha {inicio} não encontrada na lista.")
            return
        idx = todas_linhas.index(inicio)
        linhas = todas_linhas[idx:]
    elif opcao == "3":
        teste = input("  Número da linha para teste (ex: 0024): ").strip()
        if teste not in todas_linhas:
            print(f"  ❌ Linha {teste} não encontrada.")
            return
        linhas = [teste]
        # Não persistir progresso no modo teste
        progresso = {"processadas": [], "erros": []}
    else:
        linhas = todas_linhas[:]

    # Filtrar já processadas (exceto modo teste)
    pendentes = [l for l in linhas if l not in progresso["processadas"]] if opcao != "3" else linhas

    print(f"\n  Linhas a processar: {len(pendentes)}")
    print(f"  Estimativa: ~{len(pendentes) * 25 // 60} min ({len(pendentes) * 25}s)")

    confirma = input("\n  Iniciar? (S/N): ").strip().upper()
    if confirma != "S":
        print("  Cancelado.")
        return

    # Executar
    print("\n" + "=" * 60)
    sucessos = 0
    falhas   = 0
    inicio_ts = datetime.now()

    with open(LOG_FILE, "a", encoding="utf-8") as log_f:
        log(f"\n{'='*60}", log_f)
        log(f"Início: {inicio_ts}  |  Linhas: {len(pendentes)}", log_f)

        for i, numero in enumerate(pendentes, 1):
            log(f"\n[{i}/{len(pendentes)}] {numero}", log_f)

            ok = processar_linha(numero, coords, log_f)

            if ok:
                sucessos += 1
                if opcao != "3":
                    progresso["processadas"].append(numero)
                    salvar_progresso(progresso)
            else:
                falhas += 1
                if opcao != "3":
                    progresso["erros"].append({"linha": numero, "ts": datetime.now().isoformat()})
                    salvar_progresso(progresso)

            # Pausa entre linhas
            time.sleep(1)

        duracao = datetime.now() - inicio_ts
        log(f"\n{'='*60}", log_f)
        log(f"Fim: {datetime.now()}  |  Duração: {duracao}", log_f)
        log(f"Sucesso: {sucessos}  |  Falhas: {falhas}", log_f)

    # Resumo
    pdfs = list(PDF_DIR.glob("horario_*.pdf"))
    print(f"""
{'='*60}
  CONCLUÍDO!
  ✅ Sucesso : {sucessos}
  ❌ Falhas  : {falhas}
  📄 PDFs    : {len(pdfs)} em {PDF_DIR}
  📋 Log     : {LOG_FILE}
{'='*60}
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário.")
    except Exception as e:
        import traceback
        print(f"\n❌ Erro crítico: {e}")
        traceback.print_exc()
