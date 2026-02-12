"""
Script de teste usando COORDENADAS DO MOUSE
Funciona com múltiplas telas!
"""

import time
import pyautogui
from pathlib import Path

# Desabilitar fail-safe (mover mouse para canto não paort\linha_0001_20260212.pdf
# ra script)
pyautogui.FAILSAFE = False

def main():
    print("="*60)
    print("CONFIGURADOR DE COORDENADAS - AUTOMAÇÃO MATRIX")
    print("="*60)
    
    print("""
    Este script vai MAPEAR as coordenadas dos elementos na tela.
    
    INSTRUÇÕES:
    1. Deixe a janela MATRIX visível (não minimizada)
    2. Vou te pedir para mover o mouse até cada elemento
    3. Quando o mouse estiver sobre o elemento, pressione ESPAÇO
    4. Vou salvar as coordenadas
    
    ⚠️  IMPORTANTE: NÃO mova a janela depois de configurar!
    """)
    
    input("\n✅ Pressione Enter para começar...")
    
    print("\n" + "="*60)
    print("POSIÇÃO ATUAL DO MOUSE")
    print("="*60)
    
    print("\nVou mostrar a posição do mouse em tempo real.")
    print("Pressione Ctrl+C para parar e continuar.\n")
    
    try:
        for i in range(10):
            x, y = pyautogui.position()
            print(f"   Posição: X={x}, Y={y}", end='\r')
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n✅ Entendido!")
    
    coordenadas = {}
    
    # 1. Campo "Número"
    print("\n" + "="*60)
    print("1. CAMPO 'Número'")
    print("="*60)
    
    print("""
    Mova o mouse até o CENTRO do campo 'Número'
    (onde você digita o número da linha)
    
    Quando estiver posicionado, pressione ENTER...
    """)
    
    input()
    x, y = pyautogui.position()
    coordenadas['campo_numero'] = (x, y)
    print(f"✅ Coordenadas salvas: X={x}, Y={y}")
    
    # 2. Botão "Imprimir"
    print("\n" + "="*60)
    print("2. BOTÃO 'Imprimir'")
    print("="*60)
    
    print("""
    Mova o mouse até o CENTRO do botão 'Imprimir'
    
    Quando estiver posicionado, pressione ENTER...
    """)
    
    input()
    x, y = pyautogui.position()
    coordenadas['botao_imprimir'] = (x, y)
    print(f"✅ Coordenadas salvas: X={x}, Y={y}")
    
    # 3. Salvar coordenadas
    print("\n" + "="*60)
    print("SALVANDO COORDENADAS")
    print("="*60)
    
    import json
    coord_file = Path(__file__).parent / "coordenadas.json"
    
    with open(coord_file, 'w') as f:
        json.dump(coordenadas, f, indent=2)
    
    print(f"\n✅ Coordenadas salvas em: {coord_file}")
    
    # 4. Teste
    print("\n" + "="*60)
    print("TESTE DAS COORDENADAS")
    print("="*60)
    
    print("\nVou testar as coordenadas configuradas.")
    print("Você vai ver o mouse se mover automaticamente!\n")
    
    input("Pressione Enter para iniciar teste...")
    
    print("\n1. Indo para campo 'Número'...")
    time.sleep(1)
    pyautogui.click(coordenadas['campo_numero'])
    time.sleep(0.5)
    
    print("2. Selecionando tudo...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    
    print("3. Digitando '0604'...")
    pyautogui.write('0604', interval=0.1)
    time.sleep(0.5)
    
    print("\n✅ Teste 1 concluído!")
    print(f"   O número '0604' apareceu no campo?")
    
    resposta = input("\n   Funcionou? (S/N): ")
    
    if resposta.upper() == 'S':
        print("\n🎉 PERFEITO! As coordenadas estão corretas!")
        print("\nAgora vou testar o botão Imprimir...")
        
        input("\nPressione Enter para continuar...")
        
        print("\n4. Indo para botão 'Imprimir'...")
        time.sleep(1)
        pyautogui.click(coordenadas['botao_imprimir'])
        time.sleep(0.5)
        
        print("\n✅ Teste 2 concluído!")
        print("   O relatório abriu?")
        
        resposta2 = input("\n   Funcionou? (S/N): ")
        
        if resposta2.upper() == 'S':
            print("\n" + "="*60)
            print("✅ CONFIGURAÇÃO CONCLUÍDA!")
            print("="*60)
            
            print(f"""
            Coordenadas salvas:
            - Campo Número: {coordenadas['campo_numero']}
            - Botão Imprimir: {coordenadas['botao_imprimir']}
            
            Agora você pode executar a automação completa!
            
            PRÓXIMO PASSO:
            Execute: python matrix/automation_matrix_mouse.py
            """)
        else:
            print("\n⚠️  Botão Imprimir não funcionou.")
            print("   Execute novamente e ajuste as coordenadas.")
    else:
        print("\n⚠️  Campo Número não funcionou.")
        print("   Execute novamente e ajuste as coordenadas.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuração interrompida!")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
