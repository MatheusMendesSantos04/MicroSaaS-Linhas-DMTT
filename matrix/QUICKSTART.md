# 🚀 INÍCIO RÁPIDO - Automação MATRIX

## ⚡ Execução Rápida (3 Passos)

### 1️⃣ Preparar o MATRIX
```
✅ Abra o MATRIX
✅ Faça login
✅ Navegue: STC-MACEIO → Relatório → Cadastro → OSO → OSO
✅ Configure:
   - Tipo de Pesquisa: "Nº da Linha"
   - Data: "12/02/2026"
   - Marque: ☑ Itinerário por Via
```

### 2️⃣ Testar Conexão (PRIMEIRO!)
```powershell
cd I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT
python matrix\test_connection.py
```

**Se o teste passar → prossiga para passo 3**  
**Se o teste falhar → revise a configuração do MATRIX**

### 3️⃣ Executar Automação
```powershell
python matrix\automation_matrix.py
```

Escolha:
- **Opção 1:** Todas as 87 linhas (automação completa)
- **Opção 2:** A partir de uma linha específica
- **Opção 3:** Testar com 1 linha (recomendado primeiro!)

## 📊 Acompanhar Progresso

Durante a execução, veja:
- **Terminal:** Progresso em tempo real
- **Log:** `matrix\automation_log.txt`
- **PDFs:** `data\pdf\matrix_export\`

## ⚠️ LEMBRE-SE

❌ **NÃO toque** no mouse/teclado durante execução  
❌ **NÃO minimize** janelas  
❌ **NÃO abra** outros programas  

## 🐛 Se Algo Der Errado

1. Pressione `Ctrl+C` para parar
2. Verifique `automation_log.txt`
3. Execute novamente (progresso é salvo)
4. Escolha opção 2 para retomar

## 📁 Resultado Final

```
data/pdf/matrix_export/
  ├── linha_0001_20260212.pdf
  ├── linha_0004_20260212.pdf
  ├── linha_0012_20260212.pdf
  └── ... (87 arquivos)
```

---

**Tempo estimado:** ~15-30 minutos para 87 linhas  
**Requisitos:** Windows, MATRIX aberto e configurado

**Dúvidas?** Veja `README.md` completo
