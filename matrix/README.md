# 🤖 Automação MATRIX - Extração de Itinerários

Sistema de automação para extrair itinerários de todas as linhas de ônibus do sistema MATRIX (DMTT Maceió).

## 📋 Arquivos

- `automation_matrix.py` - Script principal de automação
- `config.py` - Configurações e parâmetros
- `extrair_lista_linhas.py` - Extrai lista de linhas do IDA.json
- `localizar_matrix.py` - Localiza executável do MATRIX
- `lista_linhas.json` - Lista das 87 linhas a processar
- `automacao_matrix.md` - Documentação completa do fluxo

## 🚀 Como Usar

### Passo 1: Preparar o MATRIX

1. **Abra o sistema MATRIX** manualmente
2. **Faça login** com suas credenciais
3. **Navegue** até o módulo de OSO:
   - Clique 2x em: `STC-MACEIO`
   - Clique 2x em: `Relatório`
   - Clique 2x em: `Cadastro`
   - Clique 2x em: `OSO`
   - Clique 2x em: `OSO` (segundo item)

### Passo 2: Configurar a Tela

Na tela "Relatório", configure:

✅ **Tipo de Pesquisa:** `Nº da Linha`  
✅ **Número:** (deixe vazio ou com qualquer valor)  
✅ **Data de Referência:** `12/02/2026`  
✅ **Marque o checkbox:** `☑ Itinerário por Via`

**IMPORTANTE:** Deixe a tela pronta nessa configuração antes de executar o script!

### Passo 3: Executar a Automação

```powershell
# Ativar ambiente virtual
cd I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT
.\venv\Scripts\Activate.ps1

# Executar automação
python matrix\automation_matrix.py
```

### Passo 4: Escolher Modo de Execução

O script oferece 3 opções:

1. **Processar todas as linhas** (87 linhas) - execução completa
2. **Processar a partir de uma linha** - retomar de onde parou
3. **Testar com uma linha** - validar funcionamento

### ⚠️ Durante a Execução

- **NÃO toque** no mouse ou teclado
- **NÃO minimize** as janelas
- **NÃO abra** outros programas
- Deixe o script trabalhar sozinho

## 📊 Progresso e Logs

- **Log completo:** `matrix/automation_log.txt`
- **Progresso:** `matrix/progress.json`
- **PDFs exportados:** `data/pdf/matrix_export/`

## 🔧 Configurações Avançadas

Edite `matrix/config.py` para ajustar:

```python
# Timeouts
TIMEOUT_JANELA = 10
TIMEOUT_EXPORT = 30
DELAY_ENTRE_LINHAS = 2

# Diretórios
PDF_DIR = DATA_DIR / "pdf" / "matrix_export"
```

## 📝 Linhas Processadas

Total: **87 linhas**

Exemplos:
- 0001, 0004, 0012, 0024, 0027, 0033, 0037, 0039, 0041, 0042
- 0046, 0048, 0051, 0052, 0053, 0056, 0057, 0058, 0068, 0069
- (ver lista completa em `lista_linhas.json`)

## 🐛 Resolução de Problemas

### ❌ "Janela 'Relatório' não encontrada"

**Solução:** Certifique-se de que:
1. O MATRIX está aberto
2. Você está na tela de OSO
3. A janela tem o título "Relatório"

### ❌ Script não clica nos botões corretos

**Solução:** 
- Verifique se a resolução da tela não mudou
- Tente rodar no modo de teste (opção 3) para ajustar

### ❌ Erro ao salvar PDF

**Solução:**
- Verifique permissões da pasta `data/pdf/matrix_export/`
- Certifique-se de que há espaço em disco

## 📁 Estrutura de Saída

```
data/
  pdf/
    matrix_export/
      linha_0001_20260212.pdf
      linha_0004_20260212.pdf
      linha_0012_20260212.pdf
      ...
```

## 🔄 Retomar Execução

Se o script for interrompido, o progresso é salvo automaticamente.

Para retomar:
1. Execute o script novamente
2. Escolha opção 2
3. Informe o número da última linha processada

## 📞 Suporte

Em caso de problemas:
1. Verifique o arquivo `automation_log.txt`
2. Consulte a documentação em `automacao_matrix.md`
3. Execute o modo de teste (opção 3) antes da execução completa

## ⚡ Próximos Passos

Após a extração dos PDFs:
1. Processar PDFs e extrair dados
2. Converter para JSON estruturado
3. Comparar com dados existentes
4. Validar itinerários

---

**Desenvolvido para:** DMTT Maceió  
**Data:** Fevereiro 2026
