"""
Script para normalizar nomes de ruas usando matching fuzzy com o PDF oficial
Agrupa dados por linha para estrutura mais organizada
"""
import json
from pathlib import Path
from pypdf import PdfReader
from rapidfuzz import process, fuzz
from collections import defaultdict
import re


def normalizar_abreviacoes(texto):
    """
    Normaliza abreviações comuns em nomes de ruas
    
    Padrões tratados:
    - R. / R → RUA
    - A V . / A V / AV. / AV → AVENIDA
    - TRAV. → TRAVESSA
    - AL. → ALAMEDA
    - PÇA. / PC. → PRAÇA
    - LAD. → LADEIRA
    - etc.
    """
    if not texto:
        return texto
    
    texto_normalizado = texto.upper().strip()
    
    # Dicionário de abreviações (ordem importa: mais específicas primeiro)
    abreviacoes = [
        # Avenida com espaços (padrão "A V ." ou "A V")
        (r'\bA\s+V\s*\.?\s+', 'AVENIDA '),
        (r'^A\s+V\s*\.?\s+', 'AVENIDA '),
        
        # Outras abreviações comuns
        (r'\bAV\.\s+', 'AVENIDA '),
        (r'^AV\.\s+', 'AVENIDA '),
        (r'\bAV\s+', 'AVENIDA '),
        (r'^AV\s+', 'AVENIDA '),
        
        (r'\bR\.\s+', 'RUA '),
        (r'^R\.\s+', 'RUA '),
        (r'^R\s+', 'RUA '),
        
        (r'\bTRAV\.\s+', 'TRAVESSA '),
        (r'^TRAV\.\s+', 'TRAVESSA '),
        
        (r'\bAL\.\s+', 'ALAMEDA '),
        (r'^AL\.\s+', 'ALAMEDA '),
        
        (r'\bPÇA\.\s+', 'PRAÇA '),
        (r'^PÇA\.\s+', 'PRAÇA '),
        (r'\bPC\.\s+', 'PRAÇA '),
        (r'^PC\.\s+', 'PRAÇA '),
        
        (r'\bLAD\.\s+', 'LADEIRA '),
        (r'^LAD\.\s+', 'LADEIRA '),
        
        (r'\bLGO\.\s+', 'LARGO '),
        (r'^LGO\.\s+', 'LARGO '),
        
        (r'\bPQ\.\s+', 'PARQUE '),
        (r'^PQ\.\s+', 'PARQUE '),
        
        (r'\bEST\.\s+', 'ESTRADA '),
        (r'^EST\.\s+', 'ESTRADA '),
        
        (r'\bROD\.\s+', 'RODOVIA '),
        (r'^ROD\.\s+', 'RODOVIA '),
        
        (r'\bVLA\.\s+', 'VILA '),
        (r'^VLA\.\s+', 'VILA '),
        
        (r'\bJD\.\s+', 'JARDIM '),
        (r'^JD\.\s+', 'JARDIM '),
        
        (r'\bPROF\.\s+', 'PROFESSOR '),
        (r'^PROF\.\s+', 'PROFESSOR '),
        
        (r'\bSEN\.\s+', 'SENADOR '),
        (r'^SEN\.\s+', 'SENADOR '),
        
        (r'\bDR\.\s+', 'DOUTOR '),
        (r'^DR\.\s+', 'DOUTOR '),
        
        (r'\bENG\.\s+', 'ENGENHEIRO '),
        (r'^ENG\.\s+', 'ENGENHEIRO '),
        
        (r'\bCEL\.\s+', 'CORONEL '),
        (r'^CEL\.\s+', 'CORONEL '),
        
        (r'\bMAJ\.\s+', 'MAJOR '),
        (r'^MAJ\.\s+', 'MAJOR '),
        
        (r'\bCOM\.\s+', 'COMENDADOR '),
        (r'^COM\.\s+', 'COMENDADOR '),
        
        (r'\bDES\.\s+', 'DESEMBARGADOR '),
        (r'^DES\.\s+', 'DESEMBARGADOR '),
        
        (r'\bGOV\.\s+', 'GOVERNADOR '),
        (r'^GOV\.\s+', 'GOVERNADOR '),
        
        (r'\bPRES\.\s+', 'PRESIDENTE '),
        (r'^PRES\.\s+', 'PRESIDENTE '),
        
        (r'\bDEP\.\s+', 'DEPUTADO '),
        (r'^DEP\.\s+', 'DEPUTADO '),
        
        (r'\bSTO\.\s+', 'SANTO '),
        (r'^STO\.\s+', 'SANTO '),
        
        (r'\bSTA\.\s+', 'SANTA '),
        (r'^STA\.\s+', 'SANTA '),
        
        (r'\bVER\.\s+', 'VEREADOR '),
        (r'^VER\.\s+', 'VEREADOR '),
        
        (r'\bINDL\.\s+', 'INDUSTRIAL '),
        (r'^INDL\.\s+', 'INDUSTRIAL '),
        
        (r'\bTEN\.\s+', 'TENENTE '),
        (r'^TEN\.\s+', 'TENENTE '),
    ]
    
    # Aplicar todas as substituições
    for padrao, substituicao in abreviacoes:
        texto_normalizado = re.sub(padrao, substituicao, texto_normalizado)
    
    # Limpar espaços múltiplos
    texto_normalizado = re.sub(r'\s+', ' ', texto_normalizado).strip()
    
    return texto_normalizado


def extrair_nome_rua_do_endereco(endereco_completo):
    """
    Extrai apenas o nome da rua do endereço completo do Nominatim
    
    Exemplo:
    Input: "Terminal Integrado, Rua Quarenta e Três, Benedito Bentes, Maceió..."
    Output: "RUA QUARENTA E TRÊS"
    """
    if not endereco_completo or endereco_completo == "":
        return "RUA NÃO IDENTIFICADA"
    
    # Quebrar por vírgulas
    partes = endereco_completo.split(',')
    
    # Tipos de vias para procurar
    tipos_via = ['RUA', 'AVENIDA', 'TRAVESSA', 'ALAMEDA', 'PRAÇA', 'LARGO', 
                 'ESTRADA', 'RODOVIA', 'VIA', 'LADEIRA', 'BECO', 'VIELA']
    
    # Procurar pela parte que contém o tipo de via
    for parte in partes:
        parte_upper = parte.strip().upper()
        for tipo in tipos_via:
            # Verificar se começa com o tipo de via ou contém " TIPO "
            if parte_upper.startswith(tipo + ' ') or ' ' + tipo + ' ' in parte_upper:
                return parte_upper
    
    # Se não encontrou nenhum tipo de via, tentar encontrar algo que pareça endereço
    # Evitar partes que são claramente não-endereços
    filtros_excluir = ['REGIÃO GEOGRÁFICA', 'BRASIL', 'ALAGOAS', 'MACEIÓ', 'MCZ']
    for parte in partes[:3]:  # Verificar apenas as 3 primeiras partes
        parte_upper = parte.strip().upper()
        parte_limpa = parte_upper.split()[0] if parte_upper else ''  # Primeira palavra
        
        # Pular se for número, CEP, ou filtro
        if parte_limpa.isdigit() or any(f in parte_upper for f in filtros_excluir):
            continue
            
        # Se passou os filtros e tem conteúdo razoável, usar
        if len(parte_upper) > 3:
            return parte_upper
    
    # Fallback: primeira parte
    return partes[0].strip().upper()


def extrair_ruas_do_pdf(pdf_path):
    """
    Extrai TODAS as ruas do PDF oficial usando padrão de código de 5 dígitos
    
    O PDF tem formato: "CÓDIGO NOME DA RUA [dados adicionais]"
    onde CÓDIGO é um número de 5 dígitos (ex: 00044, 06715)
    """
    print(f"📄 Lendo PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    
    ruas_oficiais = set()
    
    # Padrão: linha que começa com 5 dígitos seguido de espaço
    # Ex: "00044 RUA SENADOR. ARNON DE MELO(VILLAGE II) 959 0000 0001"
    padrao_codigo = re.compile(r'^(\d{5})\s+(.+?)\s*\d{3,4}\s+\d{4}', re.MULTILINE)
    
    # Padrão alternativo para linhas sem código numérico no final
    padrao_simples = re.compile(r'^(\d{5})\s+(.+?)\s*$', re.MULTILINE)
    
    total_paginas = len(reader.pages)
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        
        # Tentar com padrão completo (com códigos no final)
        matches = padrao_codigo.findall(text)
        for codigo, nome in matches:
            nome_limpo = nome.strip().upper()
            # Remover possíveis números soltos no final que não foram capturados
            nome_limpo = re.sub(r'\s+\d+\s*$', '', nome_limpo)
            if len(nome_limpo) > 3:  # Evitar strings muito curtas
                # Normalizar abreviações no nome extraído
                nome_normalizado = normalizar_abreviacoes(nome_limpo)
                ruas_oficiais.add(f"{codigo} {nome_normalizado}")
        
        # Tentar com padrão simples para linhas sem código no final
        matches_simples = padrao_simples.findall(text)
        for codigo, nome in matches_simples:
            nome_limpo = nome.strip().upper()
            # Remover possíveis números soltos no final
            nome_limpo = re.sub(r'\s+\d+\s*$', '', nome_limpo)
            if len(nome_limpo) > 3:  # Evitar strings muito curtas
                # Normalizar abreviações no nome extraído
                nome_normalizado = normalizar_abreviacoes(nome_limpo)
                ruas_oficiais.add(f"{codigo} {nome_normalizado}")
    
    ruas_lista = sorted(list(ruas_oficiais))
    print(f"✅ {len(ruas_lista)} ruas encontradas no PDF")
    
    # Mostrar algumas amostras
    print("\n📋 Exemplos de ruas do PDF (com abreviações normalizadas):")
    for rua in ruas_lista[:10]:
        print(f"   - {rua}")
    
    if len(ruas_lista) > 10:
        print("   ...")
        for rua in ruas_lista[-5:]:
            print(f"   - {rua}")
    
    return ruas_lista


def encontrar_melhor_match(nome_atual, ruas_oficiais, cache, threshold=80):
    """
    Encontra o melhor match usando fuzzy matching com cache
    
    Args:
        nome_atual: Nome da rua atual (dos nossos dados)
        ruas_oficiais: Lista de nomes oficiais do PDF
        cache: Dicionário de cache para evitar reprocessamento
        threshold: Score mínimo para considerar match válido (0-100)
    
    Returns:
        tuple (nome_oficial, score) ou (None, 0) se não encontrar
    """
    if nome_atual in cache:
        return cache[nome_atual]
    
    # Fazer matching fuzzy
    resultado = process.extractOne(
        nome_atual,
        ruas_oficiais,
        scorer=fuzz.WRatio,  # WRatio é bom para strings de tamanhos diferentes
        score_cutoff=threshold
    )
    
    if resultado:
        nome_oficial, score, _ = resultado
        cache[nome_atual] = (nome_oficial, score)
        return nome_oficial, score
    
    cache[nome_atual] = (None, 0)
    return None, 0


def agrupar_por_linha(dados):
    """
    Agrupa dados flat por linha
    
    Input: [{"linha": "X", "coordenadas": [...], "rua": "..."}, ...]
    Output: [{"linha": "X", "pontos": [{"coordenadas": [...], "rua": "..."}, ...]}, ...]
    """
    linhas_dict = defaultdict(list)
    
    for item in dados:
        linha_nome = item['linha']
        ponto = {
            'coordenadas': item['coordenadas'],
            'rua': item['rua']
        }
        linhas_dict[linha_nome].append(ponto)
    
    # Converter para lista de objetos
    resultado = [
        {
            'linha': linha_nome,
            'pontos': pontos
        }
        for linha_nome, pontos in linhas_dict.items()
    ]
    
    return resultado


def processar_e_normalizar(input_path, ruas_oficiais, cache_matching, threshold=80):
    """
    Processa arquivo de linhas_ruas e normaliza com matching fuzzy
    """
    print(f"\n📂 Processando: {input_path.name}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    print(f"   Total de registros: {len(dados)}")
    
    # Estatísticas
    total_processados = 0
    matches_encontrados = 0
    nao_encontrados = []
    ruas_unicas = set()
    
    # Normalizar cada item
    for item in dados:
        rua_endereco_completo = item['rua']
        ruas_unicas.add(rua_endereco_completo)
        
        # Extrair apenas o nome da rua (primeira parte antes da vírgula)
        rua_extraida = extrair_nome_rua_do_endereco(rua_endereco_completo)
        
        # Normalizar abreviações na rua extraída antes do matching
        rua_extraida_normalizada = normalizar_abreviacoes(rua_extraida)
        
        # Tentar encontrar match
        rua_oficial, score = encontrar_melhor_match(rua_extraida_normalizada, ruas_oficiais, cache_matching, threshold)
        
        if rua_oficial:
            item['rua'] = rua_oficial
            item['match_score'] = round(score, 1)
            matches_encontrados += 1
        else:
            # Manter pelo menos o nome extraído normalizado, não o endereço completo
            item['rua'] = f"REVISAR: {rua_extraida_normalizada}"
            item['match_score'] = 0
            if rua_extraida_normalizada not in [n['extraida'] for n in nao_encontrados]:
                nao_encontrados.append({
                    'original': rua_endereco_completo,
                    'extraida': rua_extraida_normalizada,
                    'sugestao': 'Match não encontrado'
                })
        
        total_processados += 1
    
    # Agrupar por linha
    dados_agrupados = agrupar_por_linha(dados)
    
    print(f"   ✅ Matches encontrados: {matches_encontrados}/{total_processados} ({matches_encontrados/total_processados*100:.1f}%)")
    print(f"   ⚠️  Não encontrados: {len(nao_encontrados)} ruas únicas")
    print(f"   📊 Linhas agrupadas: {len(dados_agrupados)}")
    
    return dados_agrupados, nao_encontrados, ruas_unicas


def main():
    # Caminhos
    base_path = Path(__file__).parent.parent
    pdf_path = base_path / "data" / "pdf" / "sre_relatorio_via_logradouro-codigo-das-ruas.pdf"
    
    input_dir = base_path / "data" / "json" / "dado-linhas"
    input_ida = input_dir / "IDA_linhas_ruas.json"
    input_volta = input_dir / "VOLTA_linhas_ruas.json"
    
    output_dir = base_path / "data" / "vias-normalizadas"
    output_dir.mkdir(exist_ok=True)
    
    output_ida = output_dir / "IDA_linhas_ruas.json"
    output_volta = output_dir / "VOLTA_linhas_ruas.json"
    output_dicionario = output_dir / "dicionario_ruas.json"
    output_nao_encontrados = output_dir / "nao_encontrados.json"
    
    print("=" * 60)
    print("🚀 NORMALIZAÇÃO DE RUAS COM MATCHING FUZZY")
    print("=" * 60)
    
    # 1. Extrair ruas do PDF
    ruas_oficiais = extrair_ruas_do_pdf(pdf_path)
    
    # 2. Cache de matching
    cache_matching = {}
    
    # 3. Processar IDA
    dados_ida, nao_encontrados_ida, ruas_ida = processar_e_normalizar(
        input_ida, ruas_oficiais, cache_matching
    )
    
    # 4. Processar VOLTA
    dados_volta, nao_encontrados_volta, ruas_volta = processar_e_normalizar(
        input_volta, ruas_oficiais, cache_matching
    )
    
    # 5. Combinar não encontrados (sem duplicatas)
    todos_nao_encontrados = nao_encontrados_ida + nao_encontrados_volta
    nao_encontrados_unicos = []
    nomes_vistos = set()
    for item in todos_nao_encontrados:
        if item['original'] not in nomes_vistos:
            nao_encontrados_unicos.append(item)
            nomes_vistos.add(item['original'])
    
    # 6. Criar dicionário com todas as ruas únicas (após normalização)
    todas_ruas_normalizadas = set()
    for linha in dados_ida:
        for ponto in linha['pontos']:
            todas_ruas_normalizadas.add(ponto['rua'])
    for linha in dados_volta:
        for ponto in linha['pontos']:
            todas_ruas_normalizadas.add(ponto['rua'])
    
    ruas_ordenadas = sorted(list(todas_ruas_normalizadas))
    dicionario = [
        {"id": idx + 1, "nome": rua}
        for idx, rua in enumerate(ruas_ordenadas)
    ]
    
    # 7. Salvar arquivos
    print("\n💾 Salvando arquivos...")
    
    with open(output_ida, 'w', encoding='utf-8') as f:
        json.dump(dados_ida, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {output_ida.name}")
    
    with open(output_volta, 'w', encoding='utf-8') as f:
        json.dump(dados_volta, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {output_volta.name}")
    
    with open(output_dicionario, 'w', encoding='utf-8') as f:
        json.dump(dicionario, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {output_dicionario.name} ({len(dicionario)} ruas)")
    
    with open(output_nao_encontrados, 'w', encoding='utf-8') as f:
        json.dump(nao_encontrados_unicos, f, ensure_ascii=False, indent=2)
    print(f"   ⚠️  {output_nao_encontrados.name} ({len(nao_encontrados_unicos)} ruas)")
    
    # 8. Resumo final
    print("\n" + "=" * 60)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    print("=" * 60)
    print(f"📁 Arquivos salvos em: {output_dir}")
    print(f"\n📊 Estatísticas:")
    print(f"   • Ruas do PDF: {len(ruas_oficiais)}")
    print(f"   • Linhas IDA: {len(dados_ida)}")
    print(f"   • Linhas VOLTA: {len(dados_volta)}")
    print(f"   • Ruas únicas normalizadas: {len(dicionario)}")
    print(f"   • Ruas não encontradas: {len(nao_encontrados_unicos)}")
    
    if nao_encontrados_unicos:
        print(f"\n⚠️  Revisar manualmente em: {output_nao_encontrados.name}")
        print("\n📋 Primeiras 10 ruas não encontradas:")
        for item in nao_encontrados_unicos[:10]:
            print(f"   - {item['extraida']}")


if __name__ == "__main__":
    main()
