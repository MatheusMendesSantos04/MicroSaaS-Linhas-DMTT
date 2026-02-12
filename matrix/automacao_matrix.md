# Automação do Sistema MATRIX - Extração de Itinerários

## Objetivo
Automatizar a extração dos dados de itinerários (ruas) das 99 linhas de ônibus do sistema MATRIX do DMTT.

## Informações do Sistema

**Nome do Sistema:** MATRIX  
**Desenvolvedor:** © 2010 Grupo Recursos - Todos os direitos reservados  
**Tipo:** Aplicação Desktop Windows  

## Credenciais de Acesso

```
Nome de usuário: matheus mendes
Senha: dmtt2025
```

## Fluxo de Automação

### Passo 1: Tela de Login

**Descrição:** Tela inicial do sistema MATRIX com campos de autenticação.

**Elementos da Interface:**
- Campo "Nome de usuário": Campo de texto para inserir o usuário
- Campo "Senha": Campo de texto para inserir a senha
- Botão "Continuar": Executa o login
- Botão "Sair": Fecha a aplicação

**Ações a Automatizar:**
1. Localizar campo "Nome de usuário"
2. Inserir texto: `matheus mendes`
3. Localizar campo "Senha"
4. Inserir texto: `dmtt2025`
5. Clicar no botão "Continuar"
6. Aguardar carregamento da próxima tela

**Observações:**
- Tela tem fundo cinza claro
- Logo MATRIX no topo esquerdo
- Ícone de cubos no topo direito

---

### Passo 2: Tela Principal (Desktop)

**Descrição:** Tela principal do sistema após login bem-sucedido. Exibe módulos disponíveis.

**Elementos da Interface:**
- Barra superior: Menu "Suporte" e botão "Sair"
- Logo MATRIX no topo
- Área central: Desktop com ícones de módulos
  - Ícone azul: "SGTA" (Sistema de Gestão de Transporte)
  - **Ícone preto: "STC-MACEIO"** (Sistema de Transporte Coletivo - Maceió)
- Barra inferior: 
  - Esquerda: Nome do usuário logado "Matheus Mendes Santos"
  - Centro: "© 2010 Grupo Recursos"
  - Direita: Hora e data atual

**Ações a Automatizar:**
1. Localizar o ícone preto (pasta) com label "STC-MACEIO"
2. **Dar duplo clique** no ícone para abrir o módulo
3. Aguardar abertura da próxima janela

**Observações:**
- O ícone STC-MACEIO é o módulo de transporte coletivo onde estão os dados das linhas
- Desktop tem fundo degradê cinza/preto

---

### Passo 3: Menu STC-MACEIO (Navegação em Árvore)

**Descrição:** Janela "Menu - STC-MACEIO" com título "PESQUISAR MENU". Estrutura de menu hierárquico em árvore.

**Estrutura do Menu Completa:**
```
▸ STC-MACEIO
  ├─ ▸ Cadastro
  └─ ▸ Relatório
      └─ ▸ Cadastro
          ├─ ▸ OSO
          │   ├─ ◆ Quadro Horário Completo
          │   ├─ ◆ OSO Completa
          │   ├─ ◆ OSO
          │   ├─ ◆ Resumo de OSO
          │   ├─ ◆ OSO Ativas
          │   ├─ ◆ OSO Desativadas
          │   └─ ◆ OSO Assinatura
          ├─ ▸ Veículo
          ├─ ▸ Rede
          └─ ▸ Linha
```

**Ações a Automatizar (Sequência de Navegação):**

1. **Expandir "STC-MACEIO"**
   - Dar duplo clique no item "STC-MACEIO"
   - Resultado: Exibe submenus "Cadastro" e "Relatório"

2. **Expandir "Relatório"**
   - Dar duplo clique no item "Relatório"
   - Resultado: Exibe submenu "Cadastro" (dentro de Relatório)

3. **Expandir "Cadastro" (dentro de Relatório)**
   - Dar duplo clique no item "Cadastro" (filho de Relatório)
   - Resultado: Exibe opções "OSO", "Veículo", "Rede", "Linha"

4. **Expandir "OSO" (primeiro nível)**
   - Dar duplo clique no item "OSO" (primeiro)
   - Resultado: Exibe subopções de OSO:
     - Quadro Horário Completo
     - OSO Completa
     - OSO (relatório específico)
     - Resumo de OSO
     - OSO Ativas
     - OSO Desativadas
     - OSO Assinatura

5. **Abrir relatório "OSO"**
   - Dar duplo clique no item "OSO" (segundo, dentro da lista expandida)
   - Resultado: Abre tela de consulta/relatório de OSO

**Observações:**
- Menu em árvore expansível/colapsável
- Caminho completo: STC-MACEIO → Relatório → Cadastro → OSO → OSO
- OSO = Ordem de Serviço Operacional (contém informações das linhas)

---

### Passo 4: Tela de Relatório OSO (Consulta de Linhas) ⭐

**Descrição:** Janela "Relatório" para consulta de OSO (Ordem de Serviço Operacional). Esta é a tela principal onde extrairemos os itinerários.

**Elementos da Interface:**

**Barra Superior:**
- Botão "Novo" (ícone +)
- Botão "Imprimir" 
- Botão "Fechar" (ícone X vermelho)

**Campos de Filtro:**

1. **Tipo de Pesquisa** (Dropdown)
   - Opções disponíveis:
     - "Nº da OSO"
     - "Nº da Linha" ⭐ (selecionar esta)

2. **Número** (Campo de texto)
   - Para inserir o número da linha (ex: 604, 700, etc.)

3. **Data de Referência** (Campo de data)
   - Formato: DD/MM/AAAA
   - Inserir: `12/02/2026`

**Tipos de Relatórios** (Checkboxes):
- ☐ Dados Gerais
- ☐ Quadro Horário
- ☐ **Itinerário por Via** ⭐ (ESTE É O QUE CONTÉM AS RUAS!)
- ☐ Itinerário por Ponto

---

### Ações a Automatizar (CRÍTICO PARA EXTRAÇÃO):

**1. Selecionar Tipo de Pesquisa:**
   - Clicar no dropdown "Tipo de Pesquisa"
   - Selecionar opção: **"Nº da Linha"**

**2. Inserir Número da Linha:**
   - Clicar no campo "Número"
   - Digitar o número da linha (ex: `604`, `700`, `010`, etc.)
   - Deve ser iterado para todas as 99 linhas

**3. Definir Data de Referência:**
   - Clicar no campo "Data de Referência"
   - Inserir data: `12/02/2026`
   - Formato: DD/MM/AAAA

**4. Marcar Tipos de Relatórios:**
   - Marcar checkbox **"Itinerário por Via"** ✓ (contém as ruas do itinerário)
   - Deixar desmarcados: Dados Gerais, Quadro Horário, Itinerário por Ponto

**5. Gerar Relatório:**
   - Clicar no botão **"Imprimir"** (ícone de impressora na barra superior)
   - Resultado: Abre/gera o relatório com o itinerário da linha

**Exemplo de Preenchimento:**
```
Tipo de Pesquisa: Nº da Linha
Número: 0604
Data de Referência: 12/02/2026
☑ Itinerário por Via
```

---

### Observações Importantes:

- **"Itinerário por Via"** é o relatório que contém a sequência de ruas
- Precisamos automatizar para as **99 linhas** do sistema
- Data de referência garante que pegamos o itinerário atual/válido
- O número da linha pode ter formato variado (ex: 604, 010, 700A)
- Formato do número: pode ter zeros à esquerda (ex: "0604")

---

### Passo 5: Visualização do Relatório - Itinerário por Via ⭐⭐⭐

**Descrição:** Janela de visualização do relatório "ITINERÁRIO POR VIA OSO Nº 6862" gerado pelo sistema.

**Informações do Relatório:**

**Cabeçalho:**
- Título: "ITINERÁRIO POR VIA OSO Nº 6862"
- Brasão do DMTT (Departamento Municipal de Transportes e Trânsito)
- Linha: **0604 - EUST. GOMEZ/C. DAS ALMAS/VIA UFAL-ROTARY**
- Data de Referência: **12/02/2026**

**Estrutura da Tabela:**
| Sentido | Sequência | Código | Via (Rua) |
|---------|-----------|--------|-----------|
| IDA | 001 | 00526 | TERMINAL INTEGRADO EUSTAQUIO GOMES |
| IDA | 002 | 06127 | RUA DR. FABIO WANDERLEY |
| IDA | 003 | 06128 | RUA X - CJ. EUSTAQUIO GOMES I |
| IDA | 004 | 00145 | RUA G. JURACI PEREIRA |
| IDA | 005 | 00305 | BR 104 (AV. LOURIVAL MELO COSTA) |
| IDA | 006 | 00307 | CIDADE UNIVERSITARIA-UFAL |
| IDA | 007 | 00305 | BR 104 (AV. LOURIVAL MELO COSTA) |
| IDA | 008 | 00154 | AV. DURVAL DE GOES MONTEIRO |
| IDA | 009 | 00032 | AV. ASSIS CHATEAUBRIAND LIMA |
| IDA | 010 | 06496 | AV. COMENDADOR FRANCISCO AMORIM LEÃO |
| ... | ... | ... | ... |

**Controles de Visualização:**

**Barra de Navegação:**
- Botão X (fechar visualização)
- Setas de navegação: ◄◄ ◄ ► ►►
- Indicador de página: "1 de 2" (relatório tem 2 páginas)
- Botão pause ⏸
- **Ícone de impressora 🖨**
- **Ícone com seta vermelha para baixo 🔻** (EXPORTAR/SALVAR) ⭐
- Ícone de disquete 💾
- Zoom: 100%
- Total de páginas: "Total 49" / "100%" / "49 de 49"

**Ações a Automatizar:**

**1. Exportar/Salvar Relatório:**
   - Clicar no **ícone com seta vermelha para baixo** 🔻
   - Resultado: Permite salvar o relatório em formato exportável (provavelmente PDF, XLS, CSV, etc.)
   - **Este é o passo crítico para capturar os dados!**

**2. Escolher Formato de Exportação:**
   - [Aguardando próximo print - deve aparecer opções de formato]

---

### Dados Extraídos do Relatório:

**Estrutura dos Dados:**
- **Sentido**: IDA ou VOLTA
- **Sequência**: Ordem numérica (001, 002, 003...)
- **Código**: Código único da via (00526, 06127, etc.)
- **Via**: Nome completo da rua/avenida/logradouro

**Exemplo de Itinerário (IDA - Linha 604):**
1. TERMINAL INTEGRADO EUSTAQUIO GOMES
2. RUA DR. FABIO WANDERLEY
3. RUA X - CJ. EUSTAQUIO GOMES I
4. RUA G. JURACI PEREIRA
5. BR 104 (AV. LOURIVAL MELO COSTA)
6. CIDADE UNIVERSITARIA-UFAL
7. ... (continua)

---

### Passo 6: Exportar Relatório (Janelas de Diálogo)

**Descrição:** Após clicar no ícone de exportação (seta vermelha), aparecem duas janelas de configuração.

---

#### Janela 1: "Exportar" - Escolha de Formato

**Elementos:**

1. **Formato:** (Dropdown)
   - Opção selecionada: **"Adobe Acrobat (PDF)"** ⭐
   - Descrição: "O formato Adobe Acrobat é um formato baseado em páginas que produz documentos para impressão e redistribuição. O formato Acrobat exporta a formatação e o layout de maneira consistente com a aparência do relatório na guia Visualização."

2. **Destino:** (Dropdown)
   - Opção selecionada: **"Arquivo de disco"**

3. **Botões:**
   - **OK** (confirma exportação)
   - **Cancelar** (cancela exportação)

**Ação:**
- Clicar no botão **"OK"**
- Resultado: Abre segunda janela "Opções de exportação"

---

#### Janela 2: "Opções de exportação" - Intervalo de Páginas

**Elementos:**

1. **Intervalo de páginas:**
   - ☑ **Todas** (exportar todas as páginas)
   - ☐ Intervalo de páginas
     - De: [campo numérico]
     - Para: [campo numérico]

2. **Opção adicional:**
   - ☐ Criar marcadores a partir da árvore do grupo

3. **Botões:**
   - **OK** (confirma e prossegue para salvar arquivo)
   - **Cancelar** (cancela exportação)

**Ação:**
- Manter "Todas" marcado (para exportar relatório completo)
- Clicar no botão **"OK"**
- Resultado: Abre janela de "Salvar Como" para escolher local e nome do arquivo

---

### Passo 7: Salvar Arquivo PDF

**Descrição:** Janela "Escolha o arquivo de exportação" do Windows para salvar o PDF do relatório.

**Elementos:**

1. **Localização Padrão:**
   - Pasta: "Área de Trabalho" (Desktop)
   - Pode ser alterado para qualquer pasta

2. **Nome do Arquivo:**
   - Nome sugerido: **"IntinerarioPorVia"**
   - Campo editável (pode ser renomeado)
   - Sugestão para automação: usar padrão como `intinerario_linha_{numero}.pdf`
     - Exemplo: `intinerario_linha_0604.pdf`

3. **Tipo:**
   - **Portable Document Format (*.pdf)**
   - Formato fixo

4. **Arquivos Existentes Visíveis:**
   - `intinerarioporvia-604` (67 KB)
   - `sre_relatorio_via_logradouro-codigo-das...` (112 KB)

5. **Botões:**
   - **Salvar** (confirma e salva o arquivo)
   - **Cancelar** (cancela operação)

---

**Ações a Automatizar:**

1. **Definir Nome do Arquivo:**
   - Renomear para padrão consistente: `intinerario_linha_XXXX.pdf`
   - Onde XXXX = número da linha (ex: 0604, 0700, 0010)

2. **Definir Local de Salvamento:**
   - Escolher pasta de destino (ex: `I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT\data\pdf\`)
   - Criar subpastas por data se necessário

3. **Confirmar Salvamento:**
   - Clicar no botão **"Salvar"**
   - Resultado: Arquivo PDF é salvo no local especificado
   - Retorna para a janela de visualização do relatório

4. **Fechar Visualização:**
   - Clicar no botão **X** (vermelho, lado esquerdo, acima de "Visualizar")
   - Resultado: Fecha a janela de visualização e retorna para a tela de consulta
   - Agora pode processar a próxima linha

---

### Observações Importantes para Automação:

**Nomenclatura de Arquivos:**
- Padrão sugerido: `linha_{numero}_{sentido}_{data}.pdf`
  - Exemplo: `linha_0604_ida_20260212.pdf`
  - Exemplo: `linha_0604_volta_20260212.pdf`

**Organização de Pastas:**
```
data/
  pdf/
    raw/                    # PDFs brutos do sistema
      linha_0604.pdf
      linha_0700.pdf
      ...
    processed/              # PDFs processados/extraídos
```

**Loop de Automação (CICLO COMPLETO) 🔄:**

Para processar cada linha sequencialmente:

1. **Modificar Número da Linha:**
   - Clicar no campo "Número"
   - Selecionar todo o texto (Ctrl+A)
   - Apagar o valor atual
   - Digitar novo número (ex: 0700, 0010, 0200, etc.)

2. **Gerar Relatório:**
   - Clicar no botão "Imprimir"

3. **Exportar PDF:**
   - Clicar no ícone de exportação (seta vermelha para baixo)
   - OK na janela de formato
   - OK na janela de páginas

4. **Salvar Arquivo:**
   - Definir nome: `linha_XXXX.pdf`
   - Clicar em "Salvar"

5. **Fechar Visualização:**
   - Clicar no X vermelho (acima de "Visualizar")

6. **Retorna para Tela de Consulta:**
   - Os campos permanecem preenchidos
   - "Nº da Linha" ainda selecionado ✓
   - "Itinerário por Via" ainda marcado ✓
   - Data permanece: 12/02/2026 ✓
   - **Apenas o número da linha precisa ser alterado!**

7. **Repetir:** Voltar para o passo 1 com próxima linha

**Total de iterações:** 99 linhas (todas as linhas de ônibus de Maceió)

---

### Passo 8: [FIM DO FLUXO]

Após salvar, o arquivo PDF está disponível para:
- Extração de texto via OCR ou parsing de PDF
- Conversão para JSON estruturado
- Comparação com dados existentes
- Armazenamento em banco de dados

---

## Resumo Completo do Fluxo de Automação

### Sequência Completa:

1. ✅ **Login** → Usuário: `matheus mendes` / Senha: `dmtt2025`
2. ✅ **Abrir STC-MACEIO** → Duplo clique no ícone
3. ✅ **Navegar Menu** → STC-MACEIO → Relatório → Cadastro → OSO → OSO
4. ✅ **Configurar Consulta:**
   - Tipo de Pesquisa: `Nº da Linha`
   - Número: `XXXX` (número da linha)
   - Data: `12/02/2026`
   - Marcar: ☑ Itinerário por Via
5. ✅ **Gerar Relatório** → Botão "Imprimir"
6. ✅ **Exportar PDF** → Botão com seta vermelha
7. ✅ **Configurar Exportação:**
   - Formato: Adobe Acrobat (PDF)
   - Páginas: Todas
8. ✅ **Salvar Arquivo** → Nome padronizado + local de destino

### Tecnologias Recomendadas para Automação:

**Windows Desktop:**
- `pywinauto` - Controle de elementos da UI
- `pyautogui` - Automação de cliques (fallback)
- `pdfplumber` ou `PyPDF2` - Extração de texto dos PDFs
- `pandas` - Estruturação dos dados extraídos

**Estrutura do Script:**
```python
def extrair_linha(numero_linha):
    # 1. Navegar até tela de consulta
    # 2. Preencher formulário
    # 3. Gerar relatório
    # 4. Exportar PDF
    # 5. Salvar com nome padronizado
    # 6. Extrair dados do PDF
    # 7. Converter para JSON
    return dados_linha

# Loop para 99 linhas
for linha in lista_linhas:
    dados = extrair_linha(linha)
    salvar_json(dados)
```

---

## Próximos Passos

1. **Criar script de automação** usando pywinauto
2. **Testar com 3-5 linhas** para validar o fluxo
3. **Implementar parser de PDF** para extrair tabelas
4. **Estruturar dados em JSON** no formato desejado
5. **Executar para todas as 99 linhas**
6. **Validar dados** comparando com dados existentes

