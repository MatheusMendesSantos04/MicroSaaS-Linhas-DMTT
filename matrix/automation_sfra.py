"""
Automação MATRIX — Dados Gerais + Quadro Horário (SFRA)
========================================================
Processa linhas lidas de um arquivo TXT em DUAS fases:
  Fase 1 — Dados Gerais      (checkbox "Itinerário por Via" marcado)
  Fase 2 — Quadro Horário    (checkbox "Quadro Horário" marcado)

INSTRUÇÕES DE USO:
1. Abra o MATRIX e faça login
2. Navegue até: STC-MACEIO → Relatório → Cadastro → OSO → OSO
3. Configure:
     - Tipo de Pesquisa: "Nº da Linha"
     - Data de Referência: 12/02/2026
     - ☑ Itinerário por Via   (para Fase 1)
4. Execute este script:
     python matrix/automation_sfra.py
5. Após concluir a Fase 1, o script pausará — troque para ☑ Quadro Horário
   e confirme para iniciar a Fase 2.
"""

import time
import json
import sys
import pyautogui
import pyperclip
from pathlib import Path
from datetime import datetime
from pywinauto import Desktop

# ── Configuração ──────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).resolve().parent.parent
MATRIX_DIR = Path(__file__).resolve().parent

# Pastas de saída
PDF_DADOS_DIR   = BASE_DIR / "data" / "pdf-dados-gerais"
PDF_HORARIO_DIR = BASE_DIR / "data" / "pdf-horario"

# Coordenadas (compartilhadas entre as duas fases)
COORD_FILE = MATRIX_DIR / "coordenadas_horarios.json"

# Arquivos de progresso por fase
PROGRESS_DADOS   = MATRIX_DIR / "progress_sfra_dados_gerais.json"
PROGRESS_HORARIO = MATRIX_DIR / "progress_sfra_horarios.json"

# Logs
LOG_FILE = MATRIX_DIR / "automation_sfra_log.txt"

# Criar pastas se necessário
PDF_DADOS_DIR.mkdir(parents=True, exist_ok=True)
PDF_HORARIO_DIR.mkdir(parents=True, exist_ok=True)

pyautogui.FAILSAFE = True  # mover mouse para canto superior-esquerdo encerra

# ── Helpers ───────────────────────────────────────────────────────────────────

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


def ler_linhas_txt(caminho_txt: str) -> list[str]:
    """Lê números de linhas de um arquivo TXT (um por linha, ignora linhas vazias)."""
    p = Path(caminho_txt)
    if not p.exists():
        print(f"❌ Arquivo não encontrado: {p}")
        sys.exit(1)
    linhas = []
    with open(p, "r", encoding="utf-8") as f:
        for linha in f:
            numero = linha.strip()
            if numero:
                linhas.append(numero)
    return linhas


def carregar_progresso(arquivo: Path) -> dict:
    if arquivo.exists():
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processadas": [], "erros": []}


def salvar_progresso(prog: dict, arquivo: Path):
    with open(arquivo, "w", encoding="utf-8") as f:
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

def processar_linha(numero: str, coords: dict, pdf_dir: Path, prefixo: str, log_f) -> bool:
    """
    Processa uma linha no MATRIX e salva o PDF resultante.

    Args:
        numero:  número da linha (ex: '0612-a')
        coords:  dicionário de coordenadas de tela
        pdf_dir: pasta de destino do PDF
        prefixo: prefixo do nome do arquivo (ex: 'dados_gerais' ou 'horario')
        log_f:   arquivo de log aberto
    """
    log(f"\n{'─'*60}", log_f)
    log(f"  Processando linha: {numero}", log_f)

    try:
        # 1. Focar janela MATRIX
        if not focar_matrix():
            log("  ⚠️  Janela MATRIX não focada — continuando mesmo assim", log_f)
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
        clicar(*coords["botao_imprimir"], delay=3)

        # 4. Aguardar janela de visualização
        log("  [3] Aguardando visualização...", log_f)
        time.sleep(4)

        # 5. Exportar → ícone seta vermelha
        log("  [4] Clicando em Exportar...", log_f)
        clicar(*coords["icone_exportar"], delay=1.5)

        # 6. Diálogo 1: formato PDF → OK
        log("  [5] Confirmando formato PDF...", log_f)
        time.sleep(2)
        clicar(*coords["botao_ok_1"], delay=1.5)

        # 7. Diálogo 2: todas as páginas → OK
        log("  [6] Confirmando 'Todas' as páginas...", log_f)
        time.sleep(2.5)
        clicar(*coords["botao_ok_2"], delay=1.5)

        # 8. Diálogo Salvar Como — digitar caminho completo
        log("  [7] Salvando PDF...", log_f)
        time.sleep(3)
        clicar(*coords["campo_arquivo"], delay=0.5)

        nome_arquivo  = f"{prefixo}_{numero}"
        caminho_completo = str(pdf_dir / nome_arquivo)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("delete")
        time.sleep(0.1)
        pyperclip.copy(caminho_completo)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.4)

        # 9. Confirmar Salvar
        clicar(*coords["botao_salvar"], delay=2.5)
        log(f"  [8] PDF salvo: {caminho_completo}.pdf", log_f)

        time.sleep(2)

        # 10. Fechar visualização
        log("  [9] Fechando visualização...", log_f)
        clicar(*coords["botao_fechar"], delay=1.5)

        log(f"  ✅ Linha {numero} concluída!", log_f)
        return True

    except Exception as e:
        log(f"  ❌ Erro: {e}", log_f)
        return False

# ── Execução de uma fase ──────────────────────────────────────────────────────

def executar_fase(
    nome_fase: str,
    linhas: list[str],
    coords: dict,
    pdf_dir: Path,
    prefixo: str,
    progress_file: Path,
    modo_teste: bool,
    log_f,
):
    progresso = carregar_progresso(progress_file)

    pendentes = linhas[:] if modo_teste else [l for l in linhas if l not in progresso["processadas"]]

    print(f"\n  Linhas a processar: {len(pendentes)}")
    print(f"  Estimativa: ~{len(pendentes) * 25 // 60} min ({len(pendentes) * 25}s)")

    confirma = input("\n  Iniciar? (S/N): ").strip().upper()
    if confirma != "S":
        print("  Cancelado.")
        return 0, 0

    print("\n" + "=" * 60)
    sucessos = 0
    falhas   = 0
    inicio_ts = datetime.now()

    log(f"\n{'='*60}", log_f)
    log(f"{nome_fase} | Início: {inicio_ts} | Linhas: {len(pendentes)}", log_f)

    for i, numero in enumerate(pendentes, 1):
        log(f"\n[{i}/{len(pendentes)}] {numero}", log_f)

        ok = processar_linha(numero, coords, pdf_dir, prefixo, log_f)

        if ok:
            sucessos += 1
            if not modo_teste:
                progresso["processadas"].append(numero)
                salvar_progresso(progresso, progress_file)
        else:
            falhas += 1
            if not modo_teste:
                progresso["erros"].append({"linha": numero, "ts": datetime.now().isoformat()})
                salvar_progresso(progresso, progress_file)

        time.sleep(1)

    duracao = datetime.now() - inicio_ts
    log(f"\n{'='*60}", log_f)
    log(f"{nome_fase} | Fim: {datetime.now()} | Duração: {duracao}", log_f)
    log(f"Sucesso: {sucessos} | Falhas: {falhas}", log_f)

    return sucessos, falhas

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  AUTOMAÇÃO MATRIX — DADOS GERAIS + QUADRO HORÁRIO (SFRA)")
    print("=" * 60)

    # Carregar coordenadas
    coords = carregar_coordenadas()
    if not coords:
        return

    # Arquivo de linhas
    caminho_txt = input(
        "\n  Caminho do arquivo TXT com as linhas\n"
        f"  [Enter para usar padrão: c:\\Users\\matheus santos\\Downloads\\11-06\\SFRA\\LINHAS.TXT]: "
    ).strip()
    if not caminho_txt:
        caminho_txt = r"c:\Users\matheus santos\Downloads\11-06\SFRA\LINHAS.TXT"

    todas_linhas = ler_linhas_txt(caminho_txt)
    print(f"\n  Linhas carregadas: {len(todas_linhas)}")
    print(f"  Exemplos: {todas_linhas[:5]}")

    print("""
  ─────────────────────────────────────────────────
  ⚠️  ANTES DE INICIAR:
     • MATRIX aberto na tela de OSO
     • Tipo de Pesquisa: "Nº da Linha"
     • Data de Referência: 12/02/2026
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

    modo_teste = opcao == "3"

    if opcao == "2":
        inicio = input("  Número da linha inicial (ex: 0612-a): ").strip()
        if inicio not in todas_linhas:
            print(f"  ❌ Linha '{inicio}' não encontrada no arquivo.")
            return
        idx = todas_linhas.index(inicio)
        linhas = todas_linhas[idx:]
    elif opcao == "3":
        teste = input("  Número da linha para teste (ex: 0612-a): ").strip()
        if teste not in todas_linhas:
            print(f"  ❌ Linha '{teste}' não encontrada no arquivo.")
            return
        linhas = [teste]
    else:
        linhas = todas_linhas[:]

    with open(LOG_FILE, "a", encoding="utf-8") as log_f:

        # ── FASE 1: Dados Gerais ──────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  FASE 1 — DADOS GERAIS (Itinerário por Via)")
        print("=" * 60)
        print("""
  Configure o MATRIX agora:
     • ☑ Itinerário por Via   MARCADO
     • Outros checkboxes DESMARCADOS
""")

        s1, f1 = executar_fase(
            nome_fase     = "FASE 1 — Dados Gerais",
            linhas        = linhas,
            coords        = coords,
            pdf_dir       = PDF_DADOS_DIR,
            prefixo       = "dados_gerais",
            progress_file = PROGRESS_DADOS,
            modo_teste    = modo_teste,
            log_f         = log_f,
        )

        pdfs1 = list(PDF_DADOS_DIR.glob("dados_gerais_*.pdf"))
        print(f"""
{'='*60}
  FASE 1 CONCLUÍDA!
  ✅ Sucesso : {s1}
  ❌ Falhas  : {f1}
  📄 PDFs    : {len(pdfs1)} em {PDF_DADOS_DIR}
{'='*60}
""")

        if modo_teste:
            print("  Modo teste — pulando Fase 2.")
            return

        # ── FASE 2: Quadro Horário ────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  FASE 2 — QUADRO HORÁRIO")
        print("=" * 60)
        print("""
  AÇÃO NECESSÁRIA — Configure o MATRIX agora:
     • ☑ Quadro Horário       MARCADO
     • Outros checkboxes DESMARCADOS
""")
        input("  Pressione Enter quando o MATRIX estiver configurado para Fase 2... ")

        s2, f2 = executar_fase(
            nome_fase     = "FASE 2 — Quadro Horário",
            linhas        = linhas,
            coords        = coords,
            pdf_dir       = PDF_HORARIO_DIR,
            prefixo       = "horario",
            progress_file = PROGRESS_HORARIO,
            modo_teste    = modo_teste,
            log_f         = log_f,
        )

        pdfs2 = list(PDF_HORARIO_DIR.glob("horario_*.pdf"))
        print(f"""
{'='*60}
  FASE 2 CONCLUÍDA!
  ✅ Sucesso : {s2}
  ❌ Falhas  : {f2}
  📄 PDFs    : {len(pdfs2)} em {PDF_HORARIO_DIR}
{'='*60}
""")

        print(f"""
{'='*60}
  PROCESSO COMPLETO!
  Fase 1 (Dados Gerais) : ✅ {s1}  ❌ {f1}
  Fase 2 (Quad. Horário): ✅ {s2}  ❌ {f2}
  📋 Log: {LOG_FILE}
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
