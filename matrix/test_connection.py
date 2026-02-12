"""
Script de teste para validar conexão com o MATRIX
Execute este script ANTES da automação completa para verificar se tudo está funcionando.
"""

from pywinauto import Desktop
import time

def listar_janelas():
    """Lista todas as janelas abertas"""
    print("\n" + "="*60)
    print("🔍 LISTANDO TODAS AS JANELAS ABERTAS")
    print("="*60 + "\n")
    
    desktop = Desktop(backend="uia")
    janelas = desktop.windows()
    
    print(f"Total de janelas encontradas: {len(janelas)}\n")
    
    for i, janela in enumerate(janelas, 1):
        try:
            titulo = janela.window_text()
            if titulo:  # Mostrar apenas janelas com título
                print(f"{i}. {titulo}")
                
                # Se for a janela do MATRIX, mostrar mais detalhes
                if "relatório" in titulo.lower() or "relatorio" in titulo.lower():
                    print(f"   ⭐ MATRIX ENCONTRADO!")
                    print(f"   Classe: {janela.class_name()}")
                    print(f"   Visível: {janela.is_visible()}")
                    print(f"   Ativa: {janela.is_active()}")
        except:
            pass
    
    print("\n" + "="*60)

def testar_conexao_matrix():
    """Testa conexão específica com a janela do MATRIX"""
    print("\n" + "="*60)
    print("🧪 TESTANDO CONEXÃO COM MATRIX")
    print("="*60 + "\n")
    
    desktop = Desktop(backend="uia")
    
    # Mostrar TODAS as janelas para debug
    print("🔍 Buscando janelas abertas...\n")
    janelas_encontradas = []
    
    for janela in desktop.windows():
        try:
            titulo = janela.window_text()
            if titulo:
                janelas_encontradas.append((titulo, janela))
                print(f"   • {titulo}")
        except:
            pass
    
    print(f"\n📊 Total de janelas: {len(janelas_encontradas)}\n")
    
    # Procurar janela com "Relat" ou "Matrix" no nome
    for titulo, janela in janelas_encontradas:
        titulo_lower = titulo.lower()
        # Procurar janela Matrix (mas não menu)
        if ("relat" in titulo_lower or titulo_lower == "matrix") and "menu" not in titulo_lower and "stc-maceio" not in titulo_lower:
            print(f"✅ Janela CORRETA encontrada: '{titulo}'")
            print(f"   Tipo: {janela.class_name()}")
            print(f"   Focando na janela...")
            
            try:
                janela.set_focus()
                time.sleep(0.5)
                
                print(f"   ✓ Foco definido com sucesso!")
                print(f"   ✓ Pronto para automação!")
                
                return True
            except Exception as e:
                print(f"   ⚠️  Erro ao focar: {e}")
                return False
    
    print("\n⚠️  Não encontrei a janela 'Relatório'")
    print("   Janelas do MATRIX visíveis:")
    for titulo, _ in janelas_encontradas:
        if "matrix" in titulo.lower() or "stc" in titulo.lower() or "menu" in titulo.lower():
            print(f"     - {titulo}")
    
    return False

def teste_interacao():
    """Teste básico de interação"""
    print("\n" + "="*60)
    print("🎯 TESTE DE INTERAÇÃO")  
    print("="*60 + "\n")
    
    print("Este teste vai:")
    print("1. Focar na janela do MATRIX")
    print("2. Pressionar Tab (para navegar)")
    print("3. Aguardar 2 segundos")
    print("\nVocê verá o foco mudando entre os campos.")
    
    resposta = input("\nIniciar teste? (S/N): ")
    
    if resposta.upper() != 'S':
        print("Teste cancelado.")
        return
    
    desktop = Desktop(backend="uia")
    
    for janela in desktop.windows():
        try:
            titulo = janela.window_text()
            if "relatório" in titulo.lower() or "relatorio" in titulo.lower():
                print(f"\n✅ Focando na janela...")
                janela.set_focus()
                time.sleep(1)
                
                from pywinauto.keyboard import send_keys
                
                print("   Pressionando Tab...")
                send_keys("{TAB}")
                time.sleep(1)
                
                print("   Pressionando Tab novamente...")
                send_keys("{TAB}")
                time.sleep(1)
                
                print("\n✅ Teste de interação concluído!")
                print("   Se viu o foco mudando, a automação deve funcionar.")
                
                return True
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    return False

def main():
    print("\n" + "="*70)
    print(" "*15 + "TESTE DE AUTOMAÇÃO MATRIX")
    print("="*70)
    
    print("\n⚠️  ANTES DE EXECUTAR:")
    print("   • Abra o sistema MATRIX")
    print("   • Faça login")
    print("   • Navegue até a tela de OSO (Relatório)")
    print("   • Configure os campos conforme instruções")
    
    input("\n✅ Pressione Enter quando estiver pronto...")
    
    # Teste 1: Listar janelas
    listar_janelas()
    input("\n▶️  Pressione Enter para continuar...")
    
    # Teste 2: Conexão específica
    sucesso = testar_conexao_matrix()
    
    if not sucesso:
        print("\n❌ Não foi possível conectar ao MATRIX.")
        print("   Verifique as instruções e tente novamente.")
        return
    
    input("\n▶️  Pressione Enter para teste de interação...")
    
    # Teste 3: Interação básica
    teste_interacao()
    
    print("\n" + "="*70)
    print("✅ TESTES CONCLUÍDOS!")
    print("="*70)
    print("\nSe todos os testes passaram, você pode executar:")
    print("   python matrix/automation_matrix.py")
    print("\n" + "="*70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário!")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
