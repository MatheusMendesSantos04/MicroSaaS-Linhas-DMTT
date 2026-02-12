"""
Automação MATRIX usando coordenadas do mouse
Funciona com múltiplas telas!
"""

import time
import json
import pyautogui
from pathlib import Path
from datetime import datetime
from pywinauto import Desktop

# Configurações
pyautogui.FAILSAFE = False
PDF_DIR = Path("data/pdf/matrix_export")
PDF_DIR.mkdir(parents=True, exist_ok=True)

def carregar_coordenadas():
    """Carrega coordenadas salvas"""
    coord_file = Path(__file__).parent / "coordenadas.json"
    
    if not coord_file.exists():
        print("❌ Arquivo de coordenadas não encontrado!")
        print("   Execute primeiro: python matrix/configurar_coordenadas.py")
        return None
    
    with open(coord_file, 'r') as f:
        return json.load(f)

def focar_janela_matrix():
    """Garante que janela MATRIX está em foco"""
    desktop = Desktop(backend="uia")
    
    for janela in desktop.windows():
        if janela.window_text().lower() == "matrix":
            janela.set_focus()
            time.sleep(0.3)
            return True
    
    return False

def processar_linha(numero_linha, coordenadas):
    """Processa uma linha usando coordenadas do mouse"""
    
    print(f"\n{'='*60}")
    print(f"PROCESSANDO LINHA: {numero_linha}")
    print(f"{'='*60}")
    
    # 1. Focar janela
    print("1. Focando janela MATRIX...")
    if not focar_janela_matrix():
        print("❌ Janela MATRIX não encontrada!")
        return False
    
    # 2. Clicar no campo Número
    print("2. Clicando no campo 'Número'...")
    x, y = coordenadas['campo_numero']
    pyautogui.click(x, y)
    time.sleep(0.3)
    
    # 3. Limpar campo
    print("3. Limpando campo...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.2)
    
    # 4. Digitar número
    print(f"4. Digitando '{numero_linha}'...")
    pyautogui.write(numero_linha, interval=0.1)
    time.sleep(0.3)
    
    # 5. Clicar em Imprimir
    print("5. Clicando em 'Imprimir'...")
    x, y = coordenadas['botao_imprimir']
    pyautogui.click(x, y)
    time.sleep(3)  # Aguardar relatório abrir
    
    # 6. Exportar PDF (comandos de teclado)
    print("6. Exportando PDF...")
    
    # Pressionar Ctrl+E (atalho exportar)
    pyautogui.hotkey('ctrl', 'e')
    time.sleep(1.5)
    
    # Selecionar PDF e confirmar
    pyautogui.press('down')  # Adobe Acrobat
    time.sleep(0.2)
    pyautogui.press('enter')
    time.sleep(1)
    
    # Confirmar "Todas"
    pyautogui.press('enter')
    time.sleep(1.5)
    
    # Salvar arquivo
    nome_arquivo = f"linha_{numero_linha}_{datetime.now().strftime('%Y%m%d')}.pdf"
    caminho_completo = str(PDF_DIR / nome_arquivo)
    
    print(f"7. Salvando como: {nome_arquivo}...")
    
    # Digitar caminho completo
    pyautogui.write(caminho_completo, interval=0.05)
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(1)
    
    # Fechar janela de visualização
    pyautogui.hotkey('alt', 'f4')
    time.sleep(1)
    
    print(f"✅ Linha {numero_linha} processada!")
    
    return True

def main():
    """Executa automação completa"""
    
    print("="*60)
    print("AUTOMAÇÃO MATRIX - VERSÃO COM MOUSE")
    print("="*60)
    
    # Carregar coordenadas
    print("\n1. Carregando coordenadas...")
    coordenadas = carregar_coordenadas()
    
    if not coordenadas:
        return
    
    print(f"   ✅ Coordenadas carregadas:")
    print(f"      - Campo Número: {coordenadas['campo_numero']}")
    print(f"      - Botão Imprimir: {coordenadas['botao_imprimir']}")
    
    # Carregar lista de linhas
    print("\n2. Carregando lista de linhas...")
    lista_file = Path(__file__).parent / "lista_linhas.json"
    
    with open(lista_file, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        linhas = dados['numeros']
    
    print(f"   ✅ {len(linhas)} linhas carregadas")
    print(f"   ✅ Primeira linha: {linhas[2]}")
    print(f"   ✅ Última linha: {linhas[-1]}")
    
    # Confirmar execução
    print("\n" + "="*60)
    print("ATENÇÃO")
    print("="*60)
    
    print(f"""
    Vou processar {len(linhas)} linhas automaticamente.
    
    ⚠️  IMPORTANTE:
    - NÃO minimize a janela MATRIX
    - NÃO mova a janela MATRIX
    - NÃO use o mouse/teclado durante o processo
    - Pode demorar cerca de {len(linhas) * 15} segundos (~{len(linhas) * 15 // 60} minutos)
    
    Pasta de destino: {PDF_DIR}
    """)
    
    resposta = input("\n✅ Iniciar automação? (S/N): ")
    
    if resposta.upper() != 'S':
        print("\n⚠️  Automação cancelada!")
        return
    
    # Executar automação
    print("\n" + "="*60)
    print("INICIANDO AUTOMAÇÃO")
    print("="*60)
    
    log_file = Path(__file__).parent / "automation_log.txt"
    
    sucessos = 0
    falhas = 0
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"Automação iniciada: {datetime.now()}\n")
        log.write("="*60 + "\n\n")
        
        for i, numero_linha in enumerate(linhas, 1):
            print(f"\n[{i}/{len(linhas)}] Processando {numero_linha}...")
            log.write(f"[{i}/{len(linhas)}] {numero_linha} - ")
            
            try:
                if processar_linha(numero_linha, coordenadas):
                    log.write("✅ Sucesso\n")
                    sucessos += 1
                else:
                    log.write("❌ Falha\n")
                    falhas += 1
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                log.write(f"❌ Erro: {e}\n")
                falhas += 1
            
            # Pequena pausa entre linhas
            time.sleep(1)
        
        # Resumo
        log.write("\n" + "="*60 + "\n")
        log.write(f"Automação concluída: {datetime.now()}\n")
        log.write(f"Sucessos: {sucessos}\n")
        log.write(f"Falhas: {falhas}\n")
    
    # Resultado final
    print("\n" + "="*60)
    print("AUTOMAÇÃO CONCLUÍDA!")
    print("="*60)
    
    print(f"""
    ✅ Processadas: {sucessos}
    ❌ Falhas: {falhas}
    
    Arquivos salvos em: {PDF_DIR}
    Log completo em: {log_file}
    """)
    
    # Listar arquivos criados
    pdfs = list(PDF_DIR.glob("*.pdf"))
    print(f"\n📄 Total de PDFs criados: {len(pdfs)}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Automação interrompida pelo usuário!")
    except Exception as e:
        print(f"\n\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
