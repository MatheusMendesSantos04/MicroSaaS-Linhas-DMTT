"""
AUTOMAÇÃO COMPLETA MATRIX - 100% COM MOUSE
Usa coordenadas para todas as ações
"""

import time
import json
import pyautogui
from pathlib import Path
from datetime import datetime
from pywinauto import Desktop

pyautogui.FAILSAFE = False

# Configurações
PDF_DIR = Path("data/pdf/matrix_export")
PDF_DIR.mkdir(parents=True, exist_ok=True)

def carregar_coordenadas():
    """Carrega coordenadas salvas"""
    coord_file = Path(__file__).parent / "coordenadas.json"
    
    if not coord_file.exists():
        print("❌ Arquivo de coordenadas não encontrado!")
        print("   Execute primeiro: python matrix/configurar_coordenadas_completo.py")
        return None
    
    with open(coord_file, 'r') as f:
        return json.load(f)

def focar_janela_matrix():
    """Garante que janela MATRIX está em foco"""
    try:
        desktop = Desktop(backend="uia")
        
        for janela in desktop.windows():
            if janela.window_text().lower() == "matrix":
                janela.set_focus()
                time.sleep(0.3)
                return True
    except:
        pass
    
    return False

def clicar(x, y, delay=0.3):
    """Clica em uma coordenada"""
    pyautogui.click(x, y)
    time.sleep(delay)

def digitar(texto, intervalo=0.05):
    """Digita um texto lentamente"""
    pyautogui.write(texto, interval=intervalo)

def processar_linha(numero_linha, coordenadas):
    """Processa uma linha usando coordenadas do mouse"""
    
    print(f"\n{'='*60}")
    print(f"PROCESSANDO LINHA: {numero_linha}")
    print(f"{'='*60}")
    
    try:
        # 1. Focar janela
        print("1. Focando janela MATRIX...")
        if not focar_janela_matrix():
            print("⚠️  Janela não focada, continuando mesmo assim...")
        time.sleep(0.5)
        
        # 2. Clicar no campo Número
        print("2. Clicando no campo 'Número'...")
        clicar(*coordenadas['campo_numero'])
        
        # 3. Limpar e digitar número
        print(f"3. Digitando '{numero_linha}'...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(0.2)
        digitar(numero_linha)
        time.sleep(0.5)
        
        # 4. Clicar em Imprimir
        print("4. Clicando em 'Imprimir'...")
        clicar(*coordenadas['botao_imprimir'], delay=2)
        
        # 5. Aguardar janela de visualização abrir
        print("5. Aguardando janela de visualização abrir...")
        time.sleep(4)  # DELAY: Aguardar relatório abrir
        
        # 6. Clicar em Exportar
        print("6. Clicando em 'Exportar'...")
        clicar(*coordenadas['icone_exportar'], delay=1)
        
        # 7. Aguardar diálogo de exportação
        print("7. Aguardando diálogo de exportação...")
        time.sleep(3)  # DELAY: Aguardar Menu de opções aparecer
        
        # 8. Aguardar antes de OK
        print("8. Aguardando antes de confirmar...")
        time.sleep(2)  # DELAY: Aguardar seleção ser registrada
        
        # 9. Clicar OK (primeira caixa)
        print("9. Clicando OK (seleção de formato)...")
        clicar(*coordenadas['botao_ok_1'], delay=1.5)
        
        # 10. Aguardar próximo diálogo
        print("10. Aguardando diálogo de 'Todas'...")
        time.sleep(3)  # DELAY: Aguardar diálogo aparecer
        
        # 11. Clicar OK (confirmar "Todas")
        print("11. Confirmando 'Todas'...")
        clicar(*coordenadas['botao_ok_2'], delay=1.5)
        
        # 12. Aguardar diálogo Salvar Como
        print("12. Aguardando diálogo 'Salvar Como'...")
        time.sleep(3)  # DELAY: Aguardar caixa de salvar aparecer
        
        # 13. Clicar no campo do arquivo
        print("13. Clicando no campo do arquivo...")
        clicar(*coordenadas['campo_arquivo'], delay=0.5)
        
        # 14. Digitar nome do arquivo (apenas a linha)
        numero_apenas = numero_linha.lstrip('0') or '0'  # Remove zeros à esquerda
        nome_do_arquivo = f"linha_{numero_linha}"
        
        print(f"14. Digitando nome: {nome_do_arquivo}...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        digitar(nome_do_arquivo, intervalo=0.05)
        time.sleep(0.5)
        
        # 15. Aguardar antes de salvar
        print("15. Aguardando antes de salvar...")
        time.sleep(2)  # DELAY: Garantir que nome foi inserido
        
        # 16. Clicar Salvar
        print("16. Clicando 'Salvar'...")
        clicar(*coordenadas['botao_salvar'], delay=2)
        
        # 17. Aguardar arquivo ser salvo
        print("17. Aguardando arquivo ser salvo...")
        time.sleep(3)  # DELAY: Arquivo sendo escrito no disco
        
        # 18. Clicar no botão X para fechar
        print("18. Fechando janela com botão X...")
        clicar(*coordenadas['botao_fechar'], delay=1)
        
        print(f"✅ Linha {numero_linha} processada com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar linha {numero_linha}: {e}")
        return False

def main():
    """Executa automação completa"""
    
    print("="*60)
    print("AUTOMAÇÃO MATRIX 100% COM MOUSE")
    print("="*60)
    
    # 1. Carregar coordenadas
    print("\n1. Carregando coordenadas...")
    coordenadas = carregar_coordenadas()
    
    if not coordenadas:
        return
    
    print("   ✅ Coordenadas carregadas:")
    for nome in coordenadas:
        x, y = coordenadas[nome]
        print(f"      {nome:20} → ({x}, {y})")
    
    # 2. Carregar lista de linhas
    print("\n2. Carregando lista de linhas...")
    lista_file = Path(__file__).parent / "lista_linhas.json"
    
    with open(lista_file, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        todas_linhas = dados['numeros']
    
    # Encontrar índice da linha 0012 e começar de lá
    indice_inicio = todas_linhas.index("0012")
    linhas = todas_linhas[indice_inicio:]
    
    print(f"   ✅ {len(linhas)} linhas carregadas")
    print(f"   ✅ Primeira linha (será processada): {linhas[0]}")
    print(f"   ✅ Última linha: {linhas[-1]}")
    
    # 3. Confirmar execução
    print("\n" + "="*60)
    print("ATENÇÃO - INSTRUÇÕES IMPORTANTES")
    print("="*60)
    
    print(f"""
    Vou processar {len(linhas)} linhas automaticamente (a partir da linha 0012).
    
    ⚠️  CRÍTICO:
    ✓ Janela MATRIX deve estar VISÍVEL (não minimizada)
    ✓ NÃO mova a janela MATRIX durante o processo
    ✓ NÃO use o mouse ou teclado
    ✓ NÃO clique em outras janelas
    ✓ Deixe o script rodar até o fim
    
    ⏱️  Estimativa: ~{len(linhas) * 20} segundos (~{len(linhas) * 20 // 60} minutos)
    
    📁 Pasta de destino: {PDF_DIR}
    """)
    
    resposta = input("\n✅ Iniciar automação? (S/N): ")
    
    if resposta.upper() != 'S':
        print("\n⚠️  Automação cancelada!")
        return
    
    # 4. Executar automação
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
                    log.flush()
                    sucessos += 1
                else:
                    log.write("❌ Falha\n")
                    log.flush()
                    falhas += 1
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                log.write(f"❌ Erro: {e}\n")
                log.flush()
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
    
    # Contar PDFs criados
    pdfs = list(PDF_DIR.glob("*.pdf"))
    
    print(f"""
    ✅ Processadas com sucesso: {sucessos}
    ❌ Falhas: {falhas}
    📄 PDFs encontrados: {len(pdfs)}
    
    📁 Pasta: {PDF_DIR}
    📋 Log completo: {log_file}
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Automação interrompida pelo usuário!")
    except Exception as e:
        print(f"\n\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
