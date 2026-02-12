"""
Script para localizar o executável do sistema MATRIX no Windows
"""
import os
import subprocess
from pathlib import Path

def encontrar_matrix():
    """Procura o executável do MATRIX em locais comuns"""
    
    print("🔍 Procurando executável do MATRIX...")
    print("=" * 60)
    
    # Locais comuns onde aplicações são instaladas
    locais_comuns = [
        r"C:\Program Files\Matrix",
        r"C:\Program Files (x86)\Matrix",
        r"C:\Matrix",
        r"C:\Recursos\Matrix",
        r"C:\GrupoRecursos\Matrix",
    ]
    
    executaveis_encontrados = []
    
    # Procurar em locais comuns
    print("\n📂 Verificando locais comuns...")
    for local in locais_comuns:
        caminho = Path(local)
        if caminho.exists():
            print(f"  ✓ Pasta encontrada: {local}")
            # Procurar arquivos .exe
            for arquivo in caminho.rglob("*.exe"):
                if "matrix" in arquivo.name.lower():
                    executaveis_encontrados.append(str(arquivo))
                    print(f"    → Executável: {arquivo}")
    
    print("\n" + "=" * 60)
    
    if executaveis_encontrados:
        print(f"\n✅ Encontrado(s) {len(executaveis_encontrados)} executável(is):")
        for exe in executaveis_encontrados:
            print(f"  - {exe}")
    else:
        print("\n⚠️  Não encontrei o executável automaticamente.")
    
    print("\n" + "=" * 60)
    print("\n💡 COMO ENCONTRAR MANUALMENTE:")
    print("""
    Opção 1 - Usando o Gerenciador de Tarefas:
    1. Abra o sistema MATRIX
    2. Pressione Ctrl+Shift+Esc (Gerenciador de Tarefas)
    3. Aba "Detalhes" ou "Processos"
    4. Localize o processo do MATRIX
    5. Clique direito → "Abrir local do arquivo"
    6. Copie o caminho completo

    Opção 2 - Procurando no Menu Iniciar:
    1. Clique em Iniciar
    2. Procure por "Matrix"
    3. Clique direito no ícone
    4. "Mais" → "Abrir local do arquivo"
    5. Clique direito no atalho → "Propriedades"
    6. Copie o campo "Destino:"

    Opção 3 - Usando o Prompt de Comando (execute abaixo):
    """)
    
    print("\n📋 COMANDOS A EXECUTAR NO TERMINAL:\n")
    print('    dir "C:\\Program Files\\*matrix*.exe" /s')
    print('    dir "C:\\Program Files (x86)\\*matrix*.exe" /s')
    print('    dir "C:\\*matrix*.exe" /s')
    print("\n" + "=" * 60)
    
    return executaveis_encontrados

def verificar_processo_matrix():
    """Verifica se o MATRIX está em execução"""
    print("\n🔎 Verificando se o MATRIX está em execução...\n")
    
    try:
        resultado = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq matrix*', '/FO', 'CSV'],
            capture_output=True,
            text=True
        )
        
        if 'matrix' in resultado.stdout.lower():
            print("✅ O MATRIX está em execução!")
            print(resultado.stdout)
        else:
            print("❌ O MATRIX não está em execução.")
    except Exception as e:
        print(f"⚠️  Erro ao verificar processos: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("LOCALIZADOR DO SISTEMA MATRIX")
    print("=" * 60)
    
    executaveis = encontrar_matrix()
    verificar_processo_matrix()
    
    input("\n\nPressione Enter para sair...")
