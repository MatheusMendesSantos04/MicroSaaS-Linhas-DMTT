# Documentação do Projeto - MicroSaaS Linhas DMTT

## 📋 Resumo do Projeto

MicroSaaS para gerenciamento e visualização de linhas de transporte público de Maceió/AL, com dados extraídos de arquivos KML e processados para análise geoespacial.

---

## ✅ O que já foi feito

### **DIA 2 - Leitura de KML e Extração de Dados**

#### Scripts Criados:
1. **`etl/ler_kml_criar_json_linhas.py`**
   - Lê o arquivo KML de itinerários das linhas
   - Extrai traçados de IDA e VOLTA para cada linha de ônibus
   - Gera dois arquivos JSON separados por direção
   
   **Entradas:**
   - `data/Mapa dos Intinerarios das Linhas de Maceio.kml`
   
   **Saídas:**
   - `data/json/dado-bruto/IDA.json` - Traçados de ida de todas as linhas
   - `data/json/dado-bruto/VOLTA.json` - Traçados de volta de todas as linhas
   
   **Estrutura dos dados:**
   ```json
   [
     {
       "linha": "0804 T.I. Benedito Bentes / Cidade Sorriso I",
       "coordenadas": [[lat, lon], [lat, lon], ...]
     }
   ]
   ```

2. **`etl/ler_kml_criar_json_pontos.py`**
   - Lê o arquivo KML de pontos e paradas
   - Extrai coordenadas e nomes dos pontos
   
   **Entradas:**
   - `data/PONTOS E PARADAS.kml`
   
   **Saídas:**
   - `data/json/PONTOS.json`
   
   **Estrutura dos dados:**
   ```json
   [
     {
       "nome": "Nome do Ponto",
       "coordenadas": [lat, lon]
     }
   ]
   ```

3. **`etl/criar_kml_mapa.py`**
   - Reconstrói um arquivo KML a partir dos JSONs processados
   - Organiza por pastas: IDA (verde), VOLTA (azul escuro), PONTOS (amarelo)
   
   **Entradas:**
   - `data/json/dado-bruto/IDA.json`
   - `data/json/dado-bruto/VOLTA.json`
   - `data/json/PONTOS.json`
   
   **Saídas:**
   - `data/json/Mapa_Reconstruido.kml`

---

### **DIA 3 - Tratamento Geométrico (Amostragem)**

#### Script Criado:
1. **`etl/amostrar_linha.py`**
   - Transforma traçados em pontos regularmente espaçados
   - Usa projeção métrica (EPSG:3857) para precisão
   - Espaçamento padrão: **25 metros**
   
   **Ferramentas:**
   - `shapely` - manipulação geométrica
   - `pyproj` - projeção e transformação de coordenadas
   
   **Entradas:**
   - `data/json/dado-bruto/IDA.json`
   - `data/json/dado-bruto/VOLTA.json`
   
   **Saídas:**
   - `data/json/dado-tratado/IDA_amostrado.json`
   - `data/json/dado-tratado/VOLTA_amostrado.json`
   
   **Estrutura dos dados:**
   ```json
   [
     {
       "linha": "0804 T.I. Benedito Bentes / Cidade Sorriso I",
       "coordenadas": [[lat, lon], [lat, lon], ...] // pontos a cada 25m
     }
   ]
   ```

---

### **DIA 4 - Reverse Geocoding**

#### Script Criado:
1. **`etl/reverse_geocode.py`**
   - Converte coordenadas em nomes de ruas
   - Usa OpenStreetMap (Nominatim) via `geopy`
   - Rate limit: 1 requisição por segundo
   - Sistema de cache para evitar chamadas duplicadas
   - Tratamento de timeouts e erros de rede
   
   **Ferramentas:**
   - `geopy` - geocodificação reversa
   
   **Entradas:**
   - `data/json/dado-tratado/IDA_amostrado.json`
   - `data/json/dado-tratado/VOLTA_amostrado.json`
   
   **Saídas:**
   - `data/json/dados-ruas/IDA_ruas.json`
   - `data/json/dados-ruas/VOLTA_ruas.json`
   - `data/json/dados-ruas/geocode_cache.json` (cache)
   
   **Estrutura dos dados:**
   ```json
   [
     {
       "coordenadas": [lat, lon],
       "rua": "Nome completo do endereço retornado pelo Nominatim"
     }
   ]
   ```

---

### **Integração - Merge de Dados**

#### Script Criado:
1. **`etl/merge_linhas_ruas.py`**
   - Combina informações de linha + coordenadas + ruas
   - Processamento sequencial baseado na ordem garantida dos pontos
   - Atribui nome da linha para cada coordenada geocodificada
   
   **Entradas:**
   - `data/json/dado-tratado/IDA_amostrado.json` (nomes das linhas)
   - `data/json/dados-ruas/IDA_ruas.json` (nomes das ruas)
   - `data/json/dado-tratado/VOLTA_amostrado.json`
   - `data/json/dados-ruas/VOLTA_ruas.json`
   
   **Saídas:**
   - `data/json/dado-linhas/IDA_linhas_ruas.json`
   - `data/json/dado-linhas/VOLTA_linhas_ruas.json`
   
   **Estrutura dos dados:**
   ```json
   [
     {
       "linha": "0804 T.I. Benedito Bentes / Cidade Sorriso I",
       "coordenadas": [lat, lon],
       "rua": "Terminal Integrado do Benedito Bentes, Rua Quarenta e Três, ..."
     }
   ]
   ```

---

### **Normalização de Nomes de Ruas com PDF Oficial**

#### Script Criado:
1. **`etl/normalizar_ruas_com_pdf.py`**
   - Normaliza nomes de ruas do Nominatim para formato oficial do PDF
   - Extração completa do PDF usando padrão de código de 5 dígitos
   - Normalização de abreviações (A V . → AVENIDA, R. → RUA, TRAV. → TRAVESSA, etc.)
   - Matching fuzzy com `rapidfuzz` (WRatio scorer, threshold 80%)
   - Agrupa dados por linha de ônibus para estrutura organizada
   
   **Ferramentas:**
   - `pypdf` - extração de texto do PDF
   - `rapidfuzz` - matching fuzzy de strings
   
   **Entradas:**
   - `data/pdf/sre_relatorio_via_logradouro-codigo-das-ruas.pdf` (PDF oficial)
   - `data/json/dado-linhas/IDA_linhas_ruas.json`
   - `data/json/dado-linhas/VOLTA_linhas_ruas.json`
   
   **Saídas:**
   - `data/vias-normalizadas/IDA_linhas_ruas.json` (96.2% normalizado)
   - `data/vias-normalizadas/VOLTA_linhas_ruas.json` (96.3% normalizado)
   - `data/vias-normalizadas/dicionario_ruas.json` (611 ruas únicas)
   - `data/vias-normalizadas/nao_encontrados.json` (53 ruas para revisão)
   
   **Estrutura dos dados:**
   ```json
   [
     {
       "linha": "0804 T.I. Benedito Bentes / Cidade Sorriso I",
       "pontos": [
         {
           "coordenadas": [lat, lon],
           "rua": "00044 RUA SENADOR ARNON DE MELO(VILLAGE II)",
           "match_score": 95.2
         }
       ]
     }
   ]
   ```
   
   **Abreviações Normalizadas:**
   - `A V .` / `A V` / `AV.` / `AV` → `AVENIDA`
   - `R.` / `R` → `RUA`
   - `TRAV.` → `TRAVESSA`
   - `AL.` → `ALAMEDA`
   - `PÇA.` / `PC.` → `PRAÇA`
   - `LAD.` → `LADEIRA`
   - `PROF.` → `PROFESSOR`
   - `DR.` → `DOUTOR`
   - `CEL.` → `CORONEL`
   - E muitas outras...
   
   **Resultados:**
   - **2.981 ruas oficiais** extraídas do PDF
   - **96.2% de match** em IDA (65.591/68.207 pontos)
   - **96.3% de match** em VOLTA (64.921/67.448 pontos)
   - **53 ruas únicas** não encontradas (8.7%) - casos legítimos:
     - Quadras internas (QD A01, QD B3, etc.)
     - Rodovias federais/estaduais (BR-104, BR-316, AL-101)
     - Nomes de bairros (Barro Duro, Fernão Velho)
     - Condomínios (Residencial Vila Madalena)
     - Estabelecimentos (escolas, empresas)
     - Infraestrutura (Canteiro Central)

---

## 📁 Estrutura de Diretórios

```
MicroSaaS-Linhas-DMTT/
├── data/
│   ├── Mapa dos Intinerarios das Linhas de Maceio.kml (entrada)
│   ├── PONTOS E PARADAS.kml (entrada)
│   ├── pdf/
│   │   └── sre_relatorio_via_logradouro-codigo-das-ruas.pdf (entrada)
│   └── json/
│       ├── dado-bruto/          # Dados extraídos diretamente do KML
│       │   ├── IDA.json
│       │   └── VOLTA.json
│       ├── dado-tratado/        # Dados amostrados (25m)
│       │   ├── IDA_amostrado.json
│       │   └── VOLTA_amostrado.json
│       ├── dados-ruas/          # Dados com reverse geocoding
│       │   ├── IDA_ruas.json
│       │   ├── VOLTA_ruas.json
│       │   └── geocode_cache.json
│       ├── dado-linhas/         # Dados finais integrados
│       │   ├── IDA_linhas_ruas.json
│       │   └── VOLTA_linhas_ruas.json
│       ├── vias-normalizadas/   # Dados com ruas normalizadas (FINAL)
│       │   ├── IDA_linhas_ruas.json (96.2% normalizado)
│       │   ├── VOLTA_linhas_ruas.json (96.3% normalizado)
│       │   ├── dicionario_ruas.json (611 ruas)
│       │   └── nao_encontrados.json (53 ruas revisão)
│       ├── PONTOS.json
│       ├── linha.schema.json
│       ├── pontos.schema.json
│       └── Mapa_Reconstruido.kml
├── etl/
│   ├── ler_kml_criar_json_linhas.py
│   ├── ler_kml_criar_json_pontos.py
│   ├── criar_kml_mapa.py
│   ├── amostrar_linha.py
│   ├── reverse_geocode.py
│   ├── merge_linhas_ruas.py
│   └── normalizar_ruas_com_pdf.py
├── backend/
├── frontend/
├── docs/
│   ├── arquitetura.md
│   └── PROGRESSO.md (este arquivo)
└── requirements.txt
```

---

## 📦 Dependências Instaladas

```
fastkml     # Leitura/escrita de arquivos KML
lxml        # Parser XML (usado pelo fastkml)
shapely     # Manipulação geométrica
pyproj      # Projeções cartográficas
geopy       # Geocodificação reversa
pypdf       # Extração de texto de PDFs
rapidfuzz   # Matching fuzzy de strings
```

---

## 🔄 Pipeline de Processamento Atual

```
KML Itinerários  →  [ler_kml_criar_json_linhas.py]  →  IDA.json / VOLTA.json
                                ↓
                    [amostrar_linha.py]
                                ↓
                    IDA_amostrado.json / VOLTA_amostrado.json
                                ↓
                    [reverse_geocode.py] (~18h de processamento)
                                ↓
                    IDA_ruas.json / VOLTA_ruas.json
                                ↓
                    [merge_linhas_ruas.py]
                                ↓
                    IDA_linhas_ruas.json / VOLTA_linhas_ruas.json
                                ↓
                    [normalizar_ruas_com_pdf.py] + PDF oficial
                                ↓
                    vias-normalizadas/IDA_linhas_ruas.json (96.2% normalizado)
                    vias-normalizadas/VOLTA_linhas_ruas.json (96.3% normalizado)
                    vias-normalizadas/dicionario_ruas.json (611 ruas)
                    vias-normalizadas/nao_encontrados.json (53 ruas revisão)
                                ↓
                            DADOS PRONTOS PARA USO
```

---

## 🚧 O que falta fazer

### **DIA 5 - Validação e Limpeza** ✅ PARCIALMENTE CONCLUÍDO
- [x] Normalização de nomes de ruas com PDF oficial
- [x] Matching fuzzy com 96%+ de taxa de sucesso
- [x] Tratamento de abreviações
- [ ] Revisão manual das 53 ruas não encontradas (opcional)
- [ ] Script de validação adicional dos dados finais
- [ ] Conferir se a ordem sequencial está correta
- [ ] Detectar coordenadas duplicadas ou faltantes

### **DIA 6 - Backend (FastAPI)**
- [ ] Configurar estrutura do backend
- [ ] Criar endpoints REST:
  - `GET /linhas` - listar todas as linhas
  - `GET /linhas/{id}` - detalhes de uma linha
  - `GET /linhas/{id}/ida` - traçado de ida com ruas
  - `GET /linhas/{id}/volta` - traçado de volta com ruas
  - `GET /pontos` - listar pontos/paradas
  - `GET /pontos/proximos?lat=&lon=&raio=` - pontos próximos
- [ ] Banco de dados (PostgreSQL/PostGIS ou MongoDB)
- [ ] Documentação automática (Swagger)

### **DIA 7 - Frontend**
- [ ] Definir framework (React, Vue, Next.js, etc.)
- [ ] Integração com biblioteca de mapas (Leaflet, Mapbox, Google Maps)
- [ ] Visualização de linhas e pontos no mapa
- [ ] Filtros e busca de linhas
- [ ] Interface responsiva

### **DIA 8 - Análises e Funcionalidades Avançadas**
- [ ] Cálculo de distância entre pontos
- [ ] Detecção de linhas que passam próximas a um endereço
- [ ] Análise de cobertura geográfica
- [ ] Exportação de dados (CSV, GeoJSON, KML)

### **DIA 9 - Deploy e Infraestrutura**
- [ ] Containerização (Docker)
- [ ] CI/CD
- [ ] Deploy (Vercel, Railway, AWS, etc.)
- [ ] Monitoramento e logs

### **DIA 10 - Otimizações e Melhorias**
- [ ] Cache de consultas frequentes
- [ ] Indexação espacial
- [ ] Compressão de dados
- [ ] Testes automatizados

---

## 📊 Estatísticas do Processamento

- **Total de linhas processadas:** 91 linhas × 2 sentidos = 182 traçados
- **Total de pontos originais:** ~135.655 pontos (IDA + VOLTA)
- **Total de pontos amostrados:** ~68.207 pontos (IDA + VOLTA)
- **Tempo de reverse geocoding:** ~18-20 horas
- **Espaçamento entre pontos:** 25 metros
- **Precisão das coordenadas:** 6 casas decimais (~10cm)
- **Ruas do PDF oficial:** 2.981 ruas cadastradas
- **Taxa de normalização:** 96.2% (IDA) e 96.3% (VOLTA)
- **Ruas únicas normalizadas:** 611 ruas
- **Ruas para revisão manual:** 53 (8.7%) - casos legítimos não cadastrados

---

## ⚠️ Observações Importantes

1. **Ordem dos dados**: Os arquivos `*_ruas.json` e `*_amostrado.json` mantêm a mesma ordem sequencial de pontos, garantindo o merge correto.

2. **Cache de geocoding**: O arquivo `geocode_cache.json` evita chamadas duplicadas ao Nominatim. Não deletar sem necessidade.

3. **Rate limit**: O Nominatim tem limite de 1 req/s. Respeitar para evitar bloqueio.

4. **Timeouts**: O reverse geocoding trata erros de timeout automaticamente, continuando o processamento.

5. **Normalização de ruas**: Os dados em `vias-normalizadas/` são os dados finais prontos para uso no backend. O matching fuzzy alcançou 96%+ de precisão.

6. **Ruas não encontradas**: As 53 ruas em `nao_encontrados.json` são casos legítimos que não existem no cadastro oficial (quadras, rodovias, estabelecimentos). Podem ser mantidas como estão ou revisadas manualmente.

7. **Abreviações**: O sistema normaliza automaticamente abreviações comuns (A V . → AVENIDA, R. → RUA, etc.) antes do matching, garantindo melhor precisão.

---

## 📝 Próximos Passos Imediatos

1. ✅ ~~Normalizar nomes de ruas com PDF oficial~~ **CONCLUÍDO (96%+ match rate)**
2. (Opcional) Revisar manualmente as 53 ruas não encontradas  
3. Criar script de validação adicional (DIA 5)
4. Iniciar estrutura do backend FastAPI (DIA 6)
5. Definir modelo de dados para banco
6. Planejar arquitetura do frontend

---

**Última atualização:** 12 de fevereiro de 2026
