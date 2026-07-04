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

## FASE 3 — Reescrever pra PHP — ❌ ABANDONADA (revisão pós-Fase 2)

A decisão original desta fase era reescrever o backend em PHP. Ela foi revista **antes de
começar a implementação** porque a premissa usada para descartar o modelo estático estava errada:
o comparativo abaixo tratava os "dados" como um bloco único de 11,6 MB, mas na prática só uma
fatia pequena disso é necessária para a busca cross-line — o resto (coordenadas GPS) só importa
depois que a linha já foi identificada.

Medição real feita antes de decidir:

| Conteúdo | Tamanho |
|---|---|
| `dados_unificados.json` completo (104 linhas, 126.438 pontos GPS) | 11,6 MB |
| Só o índice de rua (nome da via + linha + sentido + código, sem coordenadas) | 652 KB (**55 KB gzip**) |

Ou seja: o índice de busca cabe inteiro no navegador sem pesar nada, e as coordenadas de cada
linha (em média ~58 KB) só são carregadas quando o usuário já sabe qual linha quer ver — o
padrão exato em que estático funciona bem. Isso elimina a necessidade de qualquer backend.

### Comparativo revisado (estático particionado vs. PHP)

| Critério | Estático (índice + JSON por linha) | PHP no servidor |
|---|---|---|
| Custo extra | Zero | Zero |
| Suporta busca cross-line sem baixar tudo | Sim (índice de 55 KB gzip) | Sim |
| Manutenção de lógica de negócio | Só em JS, um lugar só | Duplicada (Python do pipeline + PHP do backend) |
| Atualizar dados | Rodar script de geração + subir só os JSONs de `data/` (sem rebuild do bundle JS) | Subir o JSON novo |
| Servidor para manter no ar | Nenhum | PHP (mas sem custo extra na Hostinger) |

**Decisão final:** ver FASE 3B abaixo.

---

## FASE 3B — Estático particionado (índice de rua + JSON por linha) — ✅ CONCLUÍDA (04/07/2026)

- [x] `python/gerar_dados_estaticos.py` — gera a partir de `dados_unificados.json` +
      `horarios/horarios.json` + `terminais.json`:
      `frontend/public/data/{linhas.json, rua_index.json, horarios_por_linha.json,
      terminais.json, geojson_todas.json, linhas/{id}.json}`.
- [x] `frontend/src/staticApi.js` — substitui todas as chamadas de API; reimplementa em JS
      `normalize_text`, busca por substring e janela de horário (±min), validado 1:1 contra a
      lógica Python (`backend/app/services/data_loader.py`).
- [x] `App.jsx` e `RuaSearch.jsx` atualizados para usar `staticApi.js` (zero mudança nos demais
      componentes — mesmo formato de dados que o backend retornava).
- [x] Testado local e em produção via Playwright headless: mapa geral, busca por rua ("Fernandes
      Lima" → 48 linhas), filtro de horário (±20 min → 33 linhas), seleção de linha individual,
      painel de itinerário/horários — sem erros de console, resultado idêntico em ambos.
- [x] `python/deploy_frontend.py` — script de deploy via SFTP (paramiko), lê credenciais de
      `.env`, nunca imprime a senha. Sobe `frontend/dist/` inteiro com permissões corretas
      (755 pastas, 644 arquivos).
- [x] Deploy em produção confirmado em `dmtt.mendesweb.com` (04/07/2026).

**Backend Python (`backend/`) continua no repo**, sem uso em produção — mantido para
desenvolvimento local e como referência da lógica original. Nada foi apagado.

### Fluxo de atualização de dados (linhas, trajetos, horários) a partir de agora

```bash
# 1. Editar a fonte de verdade (como já era)
#    data/json/dados_unificados.json / data/json/horarios/horarios.json

# 2. Regenerar os JSONs estáticos
python python/gerar_dados_estaticos.py

# 3. Rebuild do frontend
cd frontend && npm run build

# 4. Deploy
cd .. && python python/deploy_frontend.py
```

Não precisa reiniciar nada no servidor — é upload de arquivos estáticos.

### Próximos passos (backlog, não bloqueiam produção)

- [ ] Trocar autenticação SSH por chave (em vez de senha) — reduz superfície de exposição.
- [ ] Considerar reescrever o histórico do git para remover a senha antiga exposta no commit
      `4a3b8d6` (já rotacionada, então não é urgente).
- [ ] Se o `rua_index.json`/`geojson_todas.json` crescerem muito com novas linhas, reavaliar
      paginação ou compressão adicional — hoje (104 linhas) está bem dentro do confortável.

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
