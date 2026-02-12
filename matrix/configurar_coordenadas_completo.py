"""
Configurador COMPLETO de coordenadas do mouse
Mapeia todos os elementos necessários para automação total
"""

import time
import json
import pyautogui
import threading
from pathlib import Path

pyautogui.FAILSAFE = False

def mapear_elemento(nome, descricao):
    """Mapeia coordenada de um elemento"""
    print(f"\n{'='*60}")
    print(f"{nome}")
    print(f"{'='*60}")
    
    print(f"\n{descricao}")
    print("""
    Instruções:
    1. Mova o mouse até o CENTRO do elemento
    2. Você verá as coordenadas atualizando em tempo real abaixo
    3. Quando estiver na posição correta, pressione ENTER
    """)
    
    # Thread para mostrar posição em tempo real
    parado = threading.Event()
    
    def mostrar_posicao_tempo_real():
        while not parado.is_set():
            x, y = pyautogui.position()
            print(f"   X={x:4},  Y={y:4}          ", end='\r', flush=True)
            time.sleep(0.05)
        x, y = pyautogui.position()
        print(f"\n✅ Coordenada salva: X={x}, Y={y}")
    
    # Iniciar thread
    thread = threading.Thread(target=mostrar_posicao_tempo_real, daemon=True)
    thread.start()
    
    # Aguardar Enter
    input()
    
    # Parar thread e pegar coordenada final
    parado.set()
    time.sleep(0.1)
    x, y = pyautogui.position()
    thread.join(timeout=0.5)
    
    return (x, y)

def main():
    print("="*60)
    print("CONFIGURADOR COMPLETO DE COORDENADAS")
    print("="*60)
    
    print("""
    Este script vai mapear TODOS os elementos necessários para
    automatizar 100% do processo (inclusive exportação).
    
    Lista de elementos a configurar:
    1. Campo "Número"
    2. Botão "Imprimir"
    3. Ícone/Botão "Exportar" (seta vermelha)
    4. Botão "OK" (após selecionar PDF)
    5. Botão "OK" (confirmar "Todas")
    6. Campo de nome do arquivo (Salvar Como)
    7. Botão "Salvar"
    8. Botão "X" (fechar - lado esquerdo superior)
    """)
    
    input("\n✅ Pressione ENTER para começar...")
    
    coordenadas = {}
    
    # 1. Campo Número
    coordenadas['campo_numero'] = mapear_elemento(
        "1. CAMPO 'Número'",
        "Posicione o mouse no campo onde você digita o número da linha (ex: 0604)"
    )
    
    # 2. Botão Imprimir
    coordenadas['botao_imprimir'] = mapear_elemento(
        "2. BOTÃO 'Imprimir'",
        "Posicione o mouse no botão IMPRIMIR (geralmente um ícone de impressora)"
    )
    
    # 3. Ícone Exportar
    coordenadas['icone_exportar'] = mapear_elemento(
        "3. ÍCONE 'Exportar'",
        "Posicione o mouse no ícone de EXPORTAR (seta vermelha para baixo)\nÉ geralmente no topo da janela de visualização"
    )
    
    # 4. Botão OK (após selecionar PDF)
    coordenadas['botao_ok_1'] = mapear_elemento(
        "4. BOTÃO 'OK' (primeira caixa)",
        "Posicione o mouse no botão OK após selecionar 'Adobe Acrobat (PDF)'"
    )
    
    # 5. Botão OK (confirmar "Todas")
    coordenadas['botao_ok_2'] = mapear_elemento(
        "5. BOTÃO 'OK' (caixa de 'Todas')",
        "Posicione o mouse no botão OK na caixa que pergunta sobre as páginas (deixe 'Todas' marcado)"
    )
    
    # 6. Campo do nome do arquivo (Salvar Como)
    coordenadas['campo_arquivo'] = mapear_elemento(
        "6. CAMPO 'Nome do arquivo' (Salvar Como)",
        "Posicione o mouse no campo onde você digita o nome do arquivo\n(Na típica caixa 'Salvar Como')"
    )
    
    # 7. Botão Salvar
    coordenadas['botao_salvar'] = mapear_elemento(
        "7. BOTÃO 'Salvar'",
        "Posicione o mouse no botão SALVAR (na caixa 'Salvar Como')"
    )
    
    # 8. Botão X (fechar)
    coordenadas['botao_fechar'] = mapear_elemento(
        "8. BOTÃO 'X' (fechar)",
        "Posicione o mouse no botão X para fechar a janela (lado esquerdo superior)"
    )
    
    # Salvar coordenadas
    print("\n" + "="*60)
    print("SALVANDO COORDENADAS")
    print("="*60)
    
    coord_file = Path(__file__).parent / "coordenadas.json"
    
    with open(coord_file, 'w') as f:
        json.dump(coordenadas, f, indent=2)
    
    print(f"\n✅ Coordenadas salvas em: {coord_file}")
    
    # Exibir coordenadas
    print("\n" + "="*60)
    print("COORDENADAS CONFIGURADAS")
    print("="*60)
    
    for nome, (x, y) in coordenadas.items():
        print(f"{nome:20} → X={x:4}, Y={y:4}")
    
    print("\n✅ CONFIGURAÇÃO CONCLUÍDA!")
    print("""
    Agora você pode executar a automação completa:
    
    python matrix/automation_matrix_mouse_completo.py
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuração interrompida!")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
