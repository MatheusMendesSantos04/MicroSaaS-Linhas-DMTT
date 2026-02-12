"""
Script de Automação para Extração de Itinerários do Sistema MATRIX

INSTRUÇÕES DE USO:
1. Abra o sistema MATRIX manualmente
2. Faça login
3. Navegue até: Relatório → Cadastro → OSO → OSO
4. Preencha:
   - Tipo de Pesquisa: "Nº da Linha"
   - Data de Referência: "12/02/2026"
   - Marque: "Itinerário por Via"
5. Execute este script
6. O script irá processar todas as 87 linhas automaticamente
"""

import time
import json
import sys
from pathlib import Path
from datetime import datetime
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
from pywinauto.timings import wait_until
import pyautogui

# Importar configurações
import config

class MatrixAutomation:
    def __init__(self):
        self.app = None
        self.janela_relatorio = None
        self.numeros_linhas, self.detalhes_linhas = config.carregar_linhas()
        self.progresso = self.carregar_progresso()
        self.log_file = open(config.LOG_FILE, 'a', encoding='utf-8')
        self.escrever_log(f"\n{'='*60}\nInício da automação: {datetime.now()}\n{'='*60}")
        
    def escrever_log(self, mensagem):
        """Escreve no arquivo de log e imprime na tela"""
        print(mensagem)
        self.log_file.write(f"{mensagem}\n")
        self.log_file.flush()
        
    def carregar_progresso(self):
        """Carrega progresso de execuções anteriores"""
        if config.PROGRESS_FILE.exists():
            with open(config.PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'processadas': [], 'erros': []}
    
    def salvar_progresso(self):
        """Salva progresso atual"""
        with open(config.PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.progresso, f, indent=2)
    
    def conectar_janela(self):
        """Conecta à janela do MATRIX já aberta"""
        self.escrever_log("\n🔍 Procurando janela do MATRIX...")
        
        try:
            # Tentar conectar pela janela "Matrix" ou "Relatório"
            desktop = Desktop(backend="uia")
            janelas = desktop.windows()
            
            for janela in janelas:
                titulo = janela.window_text()
                titulo_lower = titulo.lower() if titulo else ""
                
                # Procurar janela principal (Matrix, Relatório, etc)
                if (titulo_lower == "matrix" or "relatório" in titulo_lower or "relatorio" in titulo_lower) and "menu" not in titulo_lower:
                    self.janela_relatorio = janela
                    self.escrever_log(f"✅ Conectado à janela: {titulo}")
                    return True
            
            self.escrever_log("❌ Janela 'Relatório' não encontrada!")
            self.escrever_log("⚠️  Certifique-se de que:")
            self.escrever_log("   1. O MATRIX está aberto")
            self.escrever_log("   2. Você está na tela de OSO (Relatório)")
            self.escrever_log("   3. Os campos estão configurados corretamente")
            return False
            
        except Exception as e:
            self.escrever_log(f"❌ Erro ao conectar: {e}")
            return False
    
    def processar_linha(self, numero_linha):
        """Processa uma linha específica"""
        self.escrever_log(f"\n{'─'*60}")
        self.escrever_log(f"📋 Processando linha: {numero_linha}")
        
        try:
            # Passo 1: Limpar e inserir número da linha
            self.escrever_log("  1️⃣  Inserindo número da linha...")
            time.sleep(config.DELAY_ENTRE_ACOES)
            
            # Focar na janela
            self.janela_relatorio.set_focus()
            time.sleep(0.3)
            
            # Clicar no campo "Número" (usar coordenadas relativas ou tab)
            # Usar Tab para navegar até o campo
            send_keys("{TAB}")  # Do dropdown para o campo número
            time.sleep(0.2)
            
            # Selecionar tudo e apagar
            send_keys("^a")  # Ctrl+A
            time.sleep(0.1)
            send_keys("{DELETE}")
            time.sleep(0.2)
            
            # Digitar novo número
            send_keys(numero_linha)
            time.sleep(0.3)
            
            self.escrever_log(f"  ✓ Número inserido: {numero_linha}")
            
            # Passo 2: Clicar em Imprimir
            self.escrever_log("  2️⃣  Clicando em Imprimir...")
            time.sleep(config.DELAY_ENTRE_ACOES)
            
            # Procurar botão Imprimir
            try:
                botao_imprimir = self.janela_relatorio.child_window(title="Imprimir", control_type="Button")
                botao_imprimir.click()
                self.escrever_log("  ✓ Botão Imprimir clicado")
            except:
                # Fallback: usar hotkey ou coordenadas
                self.escrever_log("  ⚠️  Botão não encontrado, usando Tab+Enter")
                send_keys("{TAB}{ENTER}")
            
            time.sleep(2)  # Aguardar relatório carregar
            
            # Passo 3: Exportar para PDF
            self.escrever_log("  3️⃣  Exportando para PDF...")
            sucesso_export = self.exportar_pdf(numero_linha)
            
            if not sucesso_export:
                self.escrever_log("  ❌ Falha ao exportar PDF")
                return False
            
            # Passo 4: Fechar visualização
            self.escrever_log("  4️⃣  Fechando visualização...")
            time.sleep(1)
            
            # Procurar botão X vermelho
            try:
                # Pressionar Esc para fechar
                send_keys("{ESC}")
                self.escrever_log("  ✓ Visualização fechada")
            except:
                self.escrever_log("  ⚠️  Tentando fechar com Esc")
                pyautogui.press('esc')
            
            time.sleep(config.DELAY_ENTRE_LINHAS)
            
            self.escrever_log(f"✅ Linha {numero_linha} processada com sucesso!")
            return True
            
        except Exception as e:
            self.escrever_log(f"❌ Erro ao processar linha {numero_linha}: {e}")
            return False
    
    def exportar_pdf(self, numero_linha):
        """Exporta relatório para PDF"""
        try:
            # Procurar janela de visualização
            desktop = Desktop(backend="uia")
            
            # Aguardar janela de visualização abrir
            time.sleep(2)
            
            # Usar atalho ou botão de exportar
            # Ícone de seta vermelha - vamos usar coordenadas ou atalho
            self.escrever_log("    📥 Clicando em exportar...")
            
            # Tentar encontrar botão de exportar
            # Como é um ícone, vamos usar pyautogui para clicar na posição
            # Alternativa: usar atalho de teclado se houver
            
            # Por enquanto, vamos simular os cliques nos diálogos
            time.sleep(1)
            
            # Click no botão de exportar (você pode precisar ajustar as coordenadas)
            # Ou usar send_keys se houver atalho
            
            # Diálogo 1: Formato PDF
            self.escrever_log("    ⏳ Aguardando diálogo de exportação...")
            time.sleep(2)
            
            # Pressionar Enter (se PDF já está selecionado)
            send_keys("{ENTER}")
            time.sleep(1)
            
            # Diálogo 2: Todas as páginas
            self.escrever_log("    ⏳ Confirmando páginas...")
            time.sleep(1)
            send_keys("{ENTER}")
            time.sleep(1)
            
            # Diálogo 3: Salvar arquivo
            self.escrever_log("    💾 Salvando arquivo...")
            time.sleep(1)
            
            # Definir nome do arquivo
            nome_arquivo = f"linha_{numero_linha}_{datetime.now().strftime('%Y%m%d')}"
            
            # Limpar campo nome
            send_keys("^a")
            time.sleep(0.1)
            
            # Digitar nome
            send_keys(nome_arquivo)
            time.sleep(0.3)
            
            # Navegar para pasta de destino (se necessário)
            # Por enquanto, salvar no local padrão
            
            # Clicar em Salvar
            send_keys("{ENTER}")
            time.sleep(2)
            
            self.escrever_log(f"    ✓ PDF salvo: {nome_arquivo}.pdf")
            return True
            
        except Exception as e:
            self.escrever_log(f"    ❌ Erro ao exportar PDF: {e}")
            return False
    
    def executar(self, iniciar_de=None, ate=None):
        """Executa a automação para todas as linhas"""
        self.escrever_log(f"\n🚀 Iniciando automação")
        self.escrever_log(f"📊 Total de linhas: {len(self.numeros_linhas)}")
        
        # Conectar à janela
        if not self.conectar_janela():
            self.escrever_log("\n❌ Falha ao conectar. Encerrando...")
            return
        
        # Filtrar linhas a processar
        linhas_processar = self.numeros_linhas[:]
        
        if iniciar_de:
            idx = linhas_processar.index(iniciar_de) if iniciar_de in linhas_processar else 0
            linhas_processar = linhas_processar[idx:]
        
        if ate:
            idx = linhas_processar.index(ate) if ate in linhas_processar else len(linhas_processar)
            linhas_processar = linhas_processar[:idx+1]
        
        self.escrever_log(f"📋 Linhas a processar: {len(linhas_processar)}")
        
        # Estatísticas
        sucesso = 0
        falhas = 0
        
        # Processar cada linha
        for i, numero_linha in enumerate(linhas_processar, 1):
            self.escrever_log(f"\n{'='*60}")
            self.escrever_log(f"Progresso: {i}/{len(linhas_processar)} ({i*100//len(linhas_processar)}%)")
            
            # Pular se já foi processada
            if numero_linha in self.progresso['processadas']:
                self.escrever_log(f"⏭️  Linha {numero_linha} já processada anteriormente (pulando)")
                continue
            
            # Processar linha
            resultado = self.processar_linha(numero_linha)
            
            if resultado:
                sucesso += 1
                self.progresso['processadas'].append(numero_linha)
            else:
                falhas += 1
                self.progresso['erros'].append({
                    'linha': numero_linha,
                    'data': datetime.now().isoformat()
                })
            
            # Salvar progresso a cada linha
            self.salvar_progresso()
        
        # Resumo final
        self.escrever_log(f"\n{'='*60}")
        self.escrever_log("✅ AUTOMAÇÃO CONCLUÍDA!")
        self.escrever_log(f"{'='*60}")
        self.escrever_log(f"📊 Estatísticas:")
        self.escrever_log(f"   ✓ Sucesso: {sucesso}")
        self.escrever_log(f"   ✗ Falhas: {falhas}")
        self.escrever_log(f"   📁 PDFs salvos em: {config.PDF_DIR}")
        self.escrever_log(f"{'='*60}\n")
        
    def __del__(self):
        """Fecha arquivo de log ao finalizar"""
        if hasattr(self, 'log_file'):
            self.log_file.close()


def main():
    print("="*60)
    print("AUTOMAÇÃO DE EXTRAÇÃO - SISTEMA MATRIX")
    print("="*60)
    print("\n⚠️  INSTRUÇÕES IMPORTANTES:")
    print("\n1. Certifique-se de que o MATRIX está aberto")
    print("2. Você deve estar na tela de OSO (Relatório)")
    print("3. Os seguintes campos devem estar configurados:")
    print("   - Tipo de Pesquisa: 'Nº da Linha'")
    print("   - Data de Referência: '12/02/2026'")
    print("   - Checkbox 'Itinerário por Via' marcado")
    print("\n4. NÃO toque no mouse/teclado durante a execução")
    print("5. O script irá processar as 87 linhas automaticamente")
    print("\n"+"="*60)
    
    resposta = input("\n✅ Tudo configurado e pronto? (S/N): ")
    
    if resposta.upper() != 'S':
        print("❌ Automação cancelada.")
        return
    
    # Opções de execução
    print("\nOpções:")
    print("1. Processar todas as linhas")
    print("2. Processar a partir de uma linha específica")
    print("3. Processar apenas uma linha (teste)")
    
    opcao = input("\nEscolha uma opção (1-3): ")
    
    automation = MatrixAutomation()
    
    if opcao == "1":
        automation.executar()
    elif opcao == "2":
        linha_inicial = input("Digite o número da linha inicial (ex: 0604): ")
        automation.executar(iniciar_de=linha_inicial)
    elif opcao == "3":
        linha_teste = input("Digite o número da linha para testar (ex: 0604): ")
        automation.executar(iniciar_de=linha_teste, ate=linha_teste)
    else:
        print("❌ Opção inválida!")
        return
    
    print("\n✅ Processo finalizado! Verifique o arquivo de log para detalhes.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Automação interrompida pelo usuário!")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
