# DEPLOY.md — MicroSaaS Linhas DMTT

> Registro da sessão de deploy em produção (Hostinger).
> Criado em 04/07/2026.

---

## Objetivo da sessão

Colocar o MicroSaaS Linhas DMTT no ar, usando a hospedagem Hostinger que o usuário já paga
(sem custo mensal adicional), seguindo os princípios de deploy React+Vite fornecidos pelo usuário
(build → scp → chmod, `.htaccess` para SPA, variáveis `VITE_*`).

---

## Acesso ao servidor

| Item | Valor |
|---|---|
| Domínio | ver `.env` (`DOMINIO`) |
| Subdomínio do projeto | ver `.env` (`SUBDOMINIO`) |
| Pasta do subdomínio | ver `.env` (`PASTA_SUBDOMINIO`) |
| SSH host/porta/usuário/senha | ver `.env` (`SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PASSWORD`) |
| Tipo de hospedagem | Compartilhada (CloudLinux + CageFS), **não é VPS** |

> Credenciais reais ficam só em `.env` (fora do git). Este arquivo não deve conter segredos.

---

## FASE 1 — Deploy do frontend (React + Vite) — ✅ CONCLUÍDA

Passos executados:

1. `frontend/vite.config.js` → adicionado `base: "/"` explícito.
2. Criado `frontend/public/.htaccess`:
   ```
   Options -MultiViews
   RewriteEngine On
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteRule ^ index.html [QSA,L]
   ```
3. Apagado `default.php` que a Hostinger cria por padrão dentro da pasta do subdomínio (causava 403).
4. `npm install` + `npm run build` no `frontend/`.
5. Upload do `dist/` via SFTP (usando script Python com `paramiko`, já que o ambiente de execução
   não suporta `scp` interativo pedindo senha).
6. Permissões corrigidas: `755` em pastas, `644` em arquivos (scp/sftp do Windows sobe com `600`,
   que o Apache não consegue servir).

**Resultado:** frontend funcionando em `dmtt.mendesweb.com`. Confirmado pelo usuário.

---

## FASE 2 — Tentativa de deploy do backend (Python/FastAPI) — ❌ DESCARTADA

### O que foi tentado, em ordem

1. **Rodar `uvicorn` direto via SSH.**
   Descartado: o processo morre quando a sessão SSH fecha (sem `systemd`/`supervisor`, sem root
   pra instalar um).

2. **"Configurar Aplicativo Python" no hPanel** (CloudLinux Passenger).
   Investigado via SSH: o servidor tem estrutura CloudLinux (`.cl.selector`, `/opt/alt/python311`),
   mas o comando que provisiona isso (`cloudlinux-selector`) roda com privilégio root e só é
   acionado pela interface do hPanel — inacessível via SSH comum.
   Ao inspecionar `.cl.selector`, só havia configuração de **PHP** (`alt_php83.cfg`), nenhuma de
   Python — sinal de que esse recurso provavelmente **não está habilitado** para esse plano
   específico (confirmado depois pela própria IA de suporte da Hostinger: Python só é suportado
   em planos VPS, não em hospedagem compartilhada).

3. **Proxy reverso via `.htaccess`** (`RewriteRule ... [P]` apontando para um processo Python
   local em `127.0.0.1`).
   Testado ao vivo (com autorização explícita do usuário, em pasta isolada `/dmtt/proxytest/`):
   - Subiu um servidor de teste em `127.0.0.1:8099` — funcionou localmente (`curl` local OK).
   - Criada regra de proxy reverso isolada.
   - Testado externamente via HTTPS → **503 Service Unavailable**.
   - Causa: a Hostinger usa uma camada de CDN própria (`hcdn`) na frente do Apache, que bloqueia
     esse tipo de proxy para processos locais. **Sem contorno possível.**
   - Processo de teste e arquivos removidos após o teste (sem resíduos no servidor).

### Conclusão da Fase 2

Hospedagem compartilhada da Hostinger **não suporta** rodar um processo Python persistente
(FastAPI/Uvicorn) de forma confiável e gratuita. As únicas alternativas seriam:
- Contratar uma VPS (custo mensal adicional — **descartado pelo usuário por orçamento**).
- Usar serviço externo com camada gratuita (Render/Railway/Fly.io) — descartado por não ser
  confiável a longo prazo (cold start, sono por inatividade, expiração de plano free).

---

## FASE 3 — Decisão: reescrever o backend em PHP — ✅ DECIDIDO, ⏳ NÃO INICIADO

### Por que PHP, e não "tudo estático no frontend"

Foi cogitada a ideia de eliminar o backend por completo e portar toda a lógica de busca para
JavaScript no navegador, servindo os JSONs como arquivos estáticos (custo zero, mesma hospedagem
do frontend). Essa ideia foi **descartada** depois de medir os dados reais:

| Arquivo | Tamanho |
|---|---|
| `data/json/dados_unificados.json` | **11,6 MB** (104 linhas, 126.438 pontos de GPS) |
| `data/json/horarios/horarios.json` | 132 KB |
| `data/json/terminais.json` | 2,5 KB |

**Motivo da rejeição do modelo estático:** o recurso central do sistema (buscar por **nome de
rua** e retornar todas as linhas que passam ali) é uma busca *cross-line* — precisa varrer o
índice de ruas de todas as 104 linhas. Não dá pra "carregar só a linha selecionada", porque o
usuário ainda não sabe qual linha é até buscar. Isso obrigaria a mandar o índice de ruas inteiro
pro navegador de qualquer forma, ou perder a funcionalidade principal do app. Estático funciona
bem quando o padrão é "ver o item que eu já sei qual é" — aqui o padrão é "descobrir o item a
partir de dado parcial", que é trabalho de índice/busca no servidor.

### Comparativo final (estático vs. PHP)

| Critério | Estático (JS no navegador) | PHP no servidor |
|---|---|---|
| Custo extra | Zero | Zero |
| Suporta busca cross-line sem baixar tudo | Não | Sim |
| Carregamento inicial | Pesado (vários MB no 1º acesso) | Leve (payload por requisição) |
| Esforço de port | Reescrever lógica + redesenhar fluxo de dados | Tradução 1:1 da lógica atual |
| Caminho pra banco de dados futuro (Fase 5 do CLAUDE.md) | Exige reintroduzir servidor do zero | Natural (PHP+MySQL é o padrão da hospedagem) |
| Atualizar dados | Rebuild + reupload do frontend inteiro | Só sobe o JSON novo |

**Decisão:** reescrever `backend/app/services/data_loader.py` e `backend/app/main.py` em PHP,
mantendo os mesmos endpoints e contratos de resposta. PHP já roda nativamente nessa hospedagem
(confirmado: `.cl.selector` tem config de PHP ativa), sem precisar de proxy, VPS ou recurso
especial nenhum.

---

## Próximos passos (não iniciados)

- [ ] Portar `normalize_text`, `rua_index`, `codigo_index`, `horario_index` de Python pra PHP.
- [ ] Portar os endpoints de `main.py` (`/linhas`, `/ruas/search`, `/ruas/codigo/{codigo}`,
      `/horarios/{id}`, `/geojson/linhas`, `/terminais`) pra scripts PHP equivalentes.
- [ ] Restringir CORS só para `https://dmtt.mendesweb.com` (nunca `*` em produção).
- [ ] Decidir estrutura de pastas do backend PHP no servidor (fora de `public_html` ou dentro,
      dependendo de como a hospedagem expõe scripts PHP).
- [ ] Atualizar frontend para consumir os novos endpoints PHP (`VITE_API_BASE_URL` ou relativo).
- [ ] Rebuild + redeploy do frontend apontando pro backend novo.
- [ ] Testar todos os fluxos (busca por rua, filtro de horário, clique no mapa, seleção de linha).
- [ ] Trocar a senha SSH usada durante os testes.

---

## Notas de segurança da sessão

- A senha SSH usada durante os testes foi commitada em texto puro neste arquivo por engano no
  commit `4a3b8d6` (04/07/2026) e ficou exposta no histórico do GitHub. **Já foi trocada** na
  Hostinger. Credenciais agora vivem só em `.env` (ignorado pelo git) — nunca escrever segredos
  neste arquivo.
- Considerar reescrever o histórico do git (`git filter-repo` ou BFG) para remover a senha antiga
  do commit `4a3b8d6`, já que ela permanece visível no histórico mesmo após a rotação.
- Considerar migrar para autenticação por chave SSH.
- Scripts Python temporários com a senha embutida (usados via `paramiko` para contornar a falta de
  `scp`/`sshpass` interativo no ambiente) foram sempre apagados do disco logo após o uso.
- Teste de proxy reverso foi feito em pasta isolada (`/dmtt/proxytest/`) e totalmente removido
  (processo + arquivos) após validação, sem deixar exposição residual.
