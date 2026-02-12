"""
Script para extrair lista única de linhas do arquivo IDA.json
"""
import json
import re
from pathlib import Path

# Caminhos
BASE_DIR = Path(__file__).parent.parent
IDA_JSON = BASE_DIR / "data" / "json" / "dado-bruto" / "IDA.json"
OUTPUT_FILE = BASE_DIR / "matrix" / "lista_linhas.json"

def extrair_numero_linha(linha_str):
    """
    Extrai o número da linha do formato: "0604 T.I. Benedito Bentes / Cidade Sorriso I"
    Retorna apenas o número: "0604"
    """
    match = re.match(r'^(\d+)', linha_str.strip())
    if match:
        return match.group(1)
    return None

def extrair_linhas():
    """Extrai todas as linhas únicas do IDA.json"""
    
    print(f"📖 Lendo arquivo: {IDA_JSON}")
    
    with open(IDA_JSON, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    print(f"✅ Total de itens no JSON: {len(dados)}")
    
    # Extrair números únicos de linhas
    linhas_set = set()
    linhas_completas = {}
    
    for item in dados:
        linha_str = item.get('linha', '')
        numero = extrair_numero_linha(linha_str)
        
        if numero:
            linhas_set.add(numero)
            if numero not in linhas_completas:
                linhas_completas[numero] = {
                    'numero': numero,
                    'nome_completo': linha_str,
                    'nome': linha_str.replace(numero, '').strip()
                }
    
    # Ordenar linhas
    linhas_ordenadas = sorted(list(linhas_set), key=lambda x: int(x))
    
    print(f"\n📊 Total de linhas únicas encontradas: {len(linhas_ordenadas)}")
    print(f"\n📝 Primeiras 10 linhas:")
    for linha in linhas_ordenadas[:10]:
        info = linhas_completas[linha]
        print(f"  - {linha}: {info['nome']}")
    
    # Salvar resultado
    resultado = {
        'total': len(linhas_ordenadas),
        'data_extracao': '2026-02-12',
        'numeros': linhas_ordenadas,
        'detalhes': [linhas_completas[num] for num in linhas_ordenadas]
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Lista salva em: {OUTPUT_FILE}")
    
    return linhas_ordenadas, linhas_completas

if __name__ == '__main__':
    print("=" * 60)
    print("EXTRAÇÃO DE LISTA DE LINHAS - SISTEMA MATRIX")
    print("=" * 60)
    
    linhas, detalhes = extrair_linhas()
    
    print(f"\n{'=' * 60}")
    print(f"✅ Extração concluída!")
    print(f"📊 Total de linhas: {len(linhas)}")
    print(f"{'=' * 60}")
