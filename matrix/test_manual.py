"""
Script de TESTE MANUAL - Executa apenas 1 linha com pausas para debug
"""

import time
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
import config

def pausa(mensagem="Pressione Enter para continuar..."):
    """Pausa para verificação manual"""
    input(f"\n⏸️  {mensagem}")

def main():
    print("="*60)
    print("TESTE MANUAL - DEBUG DA AUTOMAÇÃO")
    print("="*60)
    
    print("\n⚠️  CONFIGURAÇÃO NECESSÁRIA:")
    print("   ✅ Tipo de Pesquisa: 'Nº da Linha'")
    print("   ✅ Data: '12/02/2026'")
    print("   ✅ Checkbox 'Itinerário por Via' MARCADO")
    print("   ✅ Campo 'Número' vazio ou com qualquer valor")
    
    pausa("Tudo configurado? Pressione Enter...")
    
    # 1. Conectar à janela
    print("\n" + "="*60)
    print("Passo 1: CONECTANDO À JANELA")
    print("="*60)
    
    desktop = Desktop(backend="uia")
    janela = None
    
    for j in desktop.windows():
        titulo = j.window_text()
        if titulo.lower() == "matrix":
            janela = j
            print(f"✅ Conectado: {titulo}")
            break
    
    if not janela:
        print("❌ Janela não encontrada!")
        return
    
    pausa()
    
    # 2.5. Listar controles da janela
    print("\n" + "="*60)
    print("Passo 2.5: LISTANDO CONTROLES DA JANELA")
    print("="*60)
    
    print("Vou listar todos os controles para identificar o campo 'Número'...\n")
    
    try:
        janela.print_control_identifiers()
    except Exception as e:
        print(f"⚠️  Erro ao listar: {e}")
        print("Tentando método alternativo...")
        try:
            controles = janela.descendants()
            print(f"\nTotal de controles: {len(controles)}\n")
            for i, ctrl in enumerate(controles[:20]):  # Primeiros 20
                try:
                    print(f"{i+1}. {ctrl.window_text()} ({ctrl.control_type()})")
                except:
                    pass
        except Exception as e2:
            print(f"❌ Também falhou: {e2}")
    
    pausa("Viu o campo 'Número' na lista? Anote o tipo...")
    
    # 2. Focar na janela
    print("\n" + "="*60)
    print("Passo 2: FOCANDO NA JANELA")
    print("="*60)
    
    janela.set_focus()
    time.sleep(0.5)
    print("✅ Foco definido")
    
    pausa("Verifique se a janela Matrix está em foco...")
    
    # 3. Inserir número da linha
    print("\n" + "="*60)
    print("Passo 3: INSERINDO NÚMERO DA LINHA")
    print("="*60)
    
    numero_teste = "0604"
    print(f"Vou inserir: {numero_teste}")
    
    print("\n🔍 MÉTODO 1: Tentando encontrar o campo diretamente...")
    try:
        # Tentar encontrar o campo "Número" diretamente
        campo_numero = janela.child_window(title="Número", control_type="Edit")
        campo_numero.set_focus()
        time.sleep(0.3)
        campo_numero.set_text("")  # Limpar
        time.sleep(0.2)
        campo_numero.type_keys(numero_teste)
        print(f"✅ Método 1 funcionou! Número inserido: {numero_teste}")
    except Exception as e:
        print(f"❌ Método 1 falhou: {e}")
        
        print("\n🔍 MÉTODO 2: Tentando com Tab...")
        # Método alternativo: usar Tab múltiplas vezes
        print("Pressione Tab até o cursor chegar no campo 'Número'")
        print("Depois digite o número manualmente e pressione Enter aqui")
        
        for i in range(5):
            print(f"\nTentativa {i+1}:")
            print(f"   Pressionando Tab {i+1}x...")
            
            for _ in range(i+1):
                send_keys("{TAB}")
                time.sleep(0.2)
            
            resposta = input(f"   O cursor está no campo 'Número'? (S/N): ")
            
            if resposta.upper() == 'S':
                print(f"   Limpando campo...")
                send_keys("^a{DELETE}")
                time.sleep(0.2)
                
                print(f"   Digitando: {numero_teste}")
                send_keys(numero_teste)
                time.sleep(0.3)
                
                print(f"   ✅ Número inserido: {numero_teste}")
                break
            else:
                # Voltar para o início
                send_keys("+{TAB}" * (i+1))  # Shift+Tab para voltar
                time.sleep(0.2)
        else:
            print("\n⚠️  Não conseguimos acessar o campo automaticamente")
            print("   Por favor, digite manualmente: 0604")
            pausa("Digite '0604' no campo e pressione Enter...")
    
    pausa(f"Verifique se '{numero_teste}' apareceu no campo 'Número'...")
    
    # 4. Clicar em Imprimir
    print("\n" + "="*60)
    print("Passo 4: CLICANDO EM IMPRIMIR")
    print("="*60)
    
    print("Vou pressionar Tab + Enter para acionar o botão...")
    send_keys("{TAB}{ENTER}")
    time.sleep(2)
    
    print("✅ Comando enviado")
    
    pausa("O relatório abriu? Você vê a janela de visualização?")
    
    # 5. Identificar janela de visualização
    print("\n" + "="*60)
    print("Passo 5: PROCURANDO JANELA DE VISUALIZAÇÃO")
    print("="*60)
    
    print("\nListando janelas abertas...")
    time.sleep(1)
    
    for j in desktop.windows():
        try:
            titulo = j.window_text()
            if titulo:
                print(f"   • {titulo}")
        except:
            pass
    
    pausa("Qual janela abriu? Anote o nome...")
    
    # 6. Tentar exportar
    print("\n" + "="*60)
    print("Passo 6: TENTANDO EXPORTAR")
    print("="*60)
    
    print("""
    AGORA VOCÊ VAI FAZER MANUALMENTE:
    
    1. Clique no ícone de EXPORTAR (seta vermelha para baixo)
    2. Na janela que abrir, escolha 'Adobe Acrobat (PDF)'
    3. Clique OK
    4. Na próxima janela, deixe 'Todas' marcado
    5. Clique OK
    6. Na janela 'Salvar Como':
       - Anote ONDE está salvando (qual pasta?)
       - Veja o nome do arquivo sugerido
    7. NÃO salve ainda!
    """)
    
    pausa("Fez até o passo 6? Está na janela 'Salvar Como'?")
    
    print("\nINFORMAÇÕES IMPORTANTES:")
    print(f"   Pasta esperada: {config.PDF_DIR}")
    print(f"   Nome esperado: linha_0604_20260212.pdf")
    
    print("\n⚠️  PERGUNTAS:")
    print("   1. A pasta que apareceu é a mesma que a esperada?")
    print("   2. Você consegue navegar até a pasta correta?")
    print("   3. O nome do arquivo está correto?")
    
    pausa()
    
    print("\n" + "="*60)
    print("TESTE CONCLUÍDO!")
    print("="*60)
    
    print("""
    PRÓXIMOS PASSOS:
    
    1. Me informe ONDE o Windows quer salvar o arquivo
    2. Vou ajustar o script para navegar até a pasta correta
    3. Depois testamos novamente
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido!")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
