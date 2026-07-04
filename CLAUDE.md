# CLAUDE.md — MicroSaaS Linhas DMTT

> Este arquivo é lido automaticamente pelo Claude Code em toda sessão.
> Mantenha-o atualizado após cada sessão de trabalho.
> Última atualização: 04/07/2026 — Sessão 7 (deploy em produção, arquitetura estática)

---

## O que é o projeto

Micro-serviço web para consulta de itinerários de ônibus da **DMTT**
(Diretoria de Mobilidade e Trânsito de Maceió/AL).

**Objetivo principal:** operadores da DMTT recebem reclamações sobre ônibus e precisam
identificar qual linha estava em determinada rua num determinado horário. O sistema permite:
- Selecionar uma linha e ver o traçado no mapa
- Buscar por nome de rua e ver quais linhas passam lá
- Filtrar por horário (±20 min) para identificar o ônibus provável
- Clicar no mapa para descobrir automaticamente qual rua é e quais linhas a atendem

**Fase atual:** em produção em `dmtt.mendesweb.com` (Hostinger, hospedagem compartilhada),
**100% estático** — sem backend rodando em produção. Ver `DEPLOY.md` para o histórico completo
da decisão (por que PHP foi abandonado em favor de estático particionado).

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend (dev local apenas, sem uso em produção) | Python 3.11+ · FastAPI · Uvicorn · Pydantic |
| Frontend | React 18 · Vite · Leaflet 1.9 · react-leaflet 4.2 |
| Dados (fonte de verdade) | Arquivos JSON locais (`data/json/dados_unificados.json`) |
| Dados (produção) | JSONs estáticos gerados em `frontend/public/data/`, servidos direto pelo Apache da Hostinger |
| Dados (futuro) | SQL Server ou banco Hostinger |

**Importante:** o backend Python (`backend/`) continua no repo só para desenvolvimento local /
referência da lógica original. Quem serve os dados em produção é `frontend/src/staticApi.js`,
lendo os JSONs de `public/data/` — não há processo de servidor rodando na Hostinger.

---

## Como rodar localmente

```bash
# Frontend (já roda sozinho contra os JSONs estáticos em public/data/, sem precisar do backend)
cd frontend && npm run dev                    # http://localhost:5173

# Backend Python — opcional, só se for comparar/depurar a lógica original
cd backend && uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

## Como atualizar dados em produção (linhas, trajetos, horários)

```bash
# 1. Editar a fonte de verdade
#    data/json/dados_unificados.json / data/json/horarios/horarios.json

# 2. Regenerar os JSONs estáticos consumidos pelo frontend
python python/gerar_dados_estaticos.py

# 3. Rebuild do frontend
cd frontend && npm run build

# 4. Deploy via SFTP (lê credenciais de .env, nunca imprime a senha)
cd .. && python python/deploy_frontend.py
```

Não precisa reiniciar nada no servidor — é upload de arquivos estáticos. Ver `DEPLOY.md` para
detalhes do acesso SSH/SFTP.

---

## Estrutura de pastas

```
MicroSaaS-Linhas-DMTT/
├── CLAUDE.md
├── start.bat                              ← inicia backend + frontend com duplo-clique
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                        ← FastAPI, todos os endpoints
│       ├── schemas.py                     ← modelos Pydantic
│       └── services/
│           └── data_loader.py             ← DataStore: carrega JSONs, indexa ruas e horários
├── frontend/
│   ├── public/
│   │   ├── .htaccess                      ← rewrite para SPA (Hostinger)
│   │   └── data/                          ← JSONs estáticos consumidos em produção (gerado, não editar à mão)
│   └── src/
│       ├── App.jsx                        ← raiz: estado global, callbacks, Nominatim
│       ├── staticApi.js                   ← lê public/data/*.json e resolve busca/filtro no navegador (substitui o backend em produção)
│       ├── styles.css                     ← tema dark, layout, todos os componentes
│       └── components/
│           ├── MapView.jsx                ← mapa Leaflet + destaque de rua + caixa de contexto
│           ├── RuaSearch.jsx              ← busca por rua com autocomplete e filtro de horário
│           ├── LinhaSelector.jsx          ← dropdown de linha + selector de sentido
│           ├── ItinerarioPanel.jsx        ← lista de ruas IDA/VOLTA com código DMTT
│           ├── HorariosPanel.jsx          ← horários por sentido
│           └── MapStyleSelector.jsx       ← troca de tile (dark/light/etc.)
├── data/
│   ├── json/
│   │   ├── dado-bruto/                    ← IDA.json, VOLTA.json, PONTOS.json (raw)
│   │   ├── dado-tratado/                  ← IDA_amostrado.json, VOLTA_amostrado.json (GPS)
│   │   ├── dado-linhas/                   ← IDA_linhas_ruas.json, VOLTA_linhas_ruas.json
│   │   ├── horarios/
│   │   │   └── horarios.json              ← 85 linhas × dia_util/sabado/domingo × ida/volta
│   │   └── intinerario manual/
│   │       ├── itinerario_completo.json   ← 85 linhas, IDA/VOLTA com nomes de ruas
│   │       └── itinerario_com_codigos.json ← FONTE PRINCIPAL DO BACKEND (código+match)
│   ├── kml/                               ← KMLs gerados por gerar_kml_pontos.py
│   │   ├── pontos_0001.kml ... pontos_0402.kml  ← um por linha
│   │   └── pontos_todas.kml               ← todas as linhas juntas
│   ├── listagem-de-pontos-faltantes/
│   │   ├── 0001.pdf ... 0402.pdf          ← PDFs originais da DMTT (pontos faltantes)
│   │   └── pontos.json                    ← 7 atendimentos, 539 pontos extraídos
│   └── linhas-nomes/
│       └── linhas.json                    ← 99 linhas identificadas nos XLS de passageiros
├── python/
│   ├── extrair_pontos_pdf.py              ← extrai pontos dos PDFs → pontos.json
│   ├── gerar_kml_pontos.py                ← gera KMLs de IDA/VOLTA a partir de pontos.json
│   ├── gerar_dados_unificados.py          ← une GPS + itinerario_com_codigos → dados_unificados.json
│   ├── gerar_dados_estaticos.py           ← dados_unificados.json + horarios.json + terminais.json → frontend/public/data/*.json
│   ├── deploy_frontend.py                 ← sobe frontend/dist/ pra Hostinger via SFTP (lê .env, nunca imprime senha)
│   ├── requirements-deploy.txt            ← deps só do deploy (paramiko, python-dotenv)
│   ├── gerar_relatorios.py                ← gera 3 relatórios de qualidade (data/relatorios/)
│   └── gerar_relatorio_similares.py       ← nomes similares com sugestão de código DMTT
├── resumo-oso/
│   ├── sp_relatorio_resumooso.pdf         ← PDF fonte do OSO (22/05/2026)
│   ├── extrair_resumo_oso.py              ← extrai linhas por tipo de serviço do PDF
│   └── relatorio_tipos_servico.txt        ← resultado: convencional/catraca/madrugadão por empresa
└── matrix/
    └── extrair_linhas_xls.py              ← identifica linhas nos arquivos XLS de passageiros
```

---

## Endpoints da API (backend Python — só dev local, não usado em produção)

> Em produção o frontend não chama esses endpoints — lê os JSONs de `public/data/` via
> `staticApi.js`. Esta tabela documenta a lógica original (equivalente 1:1 ao que roda em JS).

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /health | Status da API |
| GET | /meta | Total de linhas, ruas indexadas, arquivos |
| GET | /linhas | Lista todas as linhas |
| GET | /linhas/{id} | Detalhe: coords GPS + ruas IDA/VOLTA |
| GET | /ruas/suggest?q= | Autocomplete de nomes de rua (mín. 2 chars) |
| GET | /ruas/search?q= | Linhas que passam na rua (+ filtro horario/dia/janela) |
| GET | /ruas/codigo/{codigo} | Linhas que passam pela via com esse código DMTT |
| GET | /geojson/linhas | GeoJSON de todas as linhas |
| GET | /geojson/linhas/{id} | GeoJSON de uma linha específica |
| GET | /horarios/{id} | Horários de uma linha por dia |

**Parâmetros opcionais de `/ruas/search`:**
- `horario=HH:MM` — filtra linhas com partida dentro da janela
- `dia=dia_util|sabado|domingo` (padrão: `dia_util`)
- `janela=20` — minutos de tolerância (5–60, padrão 20)

---

## Dados principais — formato

### `dados_unificados.json` ← FONTE ATUAL DO BACKEND (gerado por gerar_dados_unificados.py)

```json
{
  "0024 - Gruta / Centro / Term. Rotary": {
    "ida":   { "coordenadas": [[lat, lon], ...], "ruas": [{"via": "...", "codigo": "00834", "match": "exato"}] },
    "volta": { "coordenadas": [[lat, lon], ...], "ruas": [...] }
  }
}
```

**Regra:** edite sempre este arquivo. Para regenerar a partir das fontes originais, rode `python python/gerar_dados_unificados.py`.
Após editar o JSON, **reinicie o backend** (uvicorn só recarrega .py, não .json).

---

### `itinerario_com_codigos.json` (fonte original — não mais lida diretamente pelo backend)

```json
{
  "0024 - Gruta / Centro / Term. Rotary": {
    "versao": "pdf_v1",
    "ida": [
      { "via": "AVENIDA ROBERTO SIMONSEN", "codigo": "00834", "match": "exato" }
    ],
    "volta": [ ... ]
  }
}
```

### `horarios.json`

```json
{
  "0024": {
    "dia_util": { "ida": ["05:30","06:00",...], "volta": ["05:45","06:15",...] },
    "sabado":   { ... },
    "domingo":  { ... }
  }
}
```

### `pontos.json` (extraído dos PDFs)

```json
[
  {
    "codigo": "0001",
    "linha": "Terminal x Cruzeiro",
    "nome_ida": "Circular Cruzeiro do Sul",
    "nome_volta": "",
    "pontos": [
      { "nome": "Terminal Eustáquio Gomes", "abreviatura": "T-EGOMES",
        "endereco": "...", "ordem": 1, "vel_limite": 60,
        "latitude": -9.54223, "longitude": -35.78303 }
    ]
  }
]
```

---

## O que já foi feito

### Backend
- [x] FastAPI com 10 endpoints funcionando
- [x] DataStore com `rua_index` (busca por nome de rua normalizado)
- [x] DataStore com `horario_index` (keyed por 4 dígitos da linha)
- [x] `suggest_ruas()` — autocomplete de nomes de rua
- [x] `search_ruas_horario()` — filtra linhas por rua + horário ±janela
- [x] Endpoint `/ruas/suggest` e extensão de `/ruas/search` com filtro de horário
- [x] Schemas `RuaOcorrenciaHorario` e `RuasHorarioResponse`

### Frontend
- [x] Mapa Leaflet com 5 estilos de tile (dark/light/padrão/voyager/satélite)
- [x] Cores padronizadas: IDA = verde `#22c55e`, VOLTA = azul `#1e40af` (mapa + badges + itinerário + horários)
- [x] RuaSearch com autocomplete em tempo real (debounce 250ms, AbortController)
- [x] Filtro de horário + dia no RuaSearch (janela ±20 min)
- [x] Badges IDA/VOLTA clicáveis → carrega só aquele sentido no mapa
- [x] Caixa de contexto no mapa (canto inferior direito) explicando o sentido selecionado
- [x] Botão "Ver os dois sentidos" na caixa de contexto
- [x] Destaque de rua no mapa via Nominatim (halo amarelo espesso + linha sólida)
- [x] Zoom automático na rua destacada (`StreetZoom`)
- [x] Clique no mapa → reverse geocode Nominatim → popula RuaSearch automaticamente
- [x] Cursor crosshair no mapa indicando modo de clique
- [x] Rotas de ônibus sempre visíveis (rua destacada renderiza por cima via halo)
- [x] `start.bat` para iniciar backend + frontend com duplo-clique

### Scripts Python
- [x] `extrair_pontos_pdf.py` — extrai pontos de parada dos PDFs (máquina de estados, filtro Principal=Sim + Ativo=Sim)
- [x] `gerar_kml_pontos.py` — gera KMLs IDA/VOLTA com LineString + Placemarks individuais
- [x] `gerar_dados_unificados.py` — une GPS coords + itinerario_com_codigos → `dados_unificados.json` (85 linhas)
- [x] `gerar_relatorios.py` — gera 3 relatórios de qualidade em `data/relatorios/`
- [x] `gerar_relatorio_similares.py` — relatório de nomes similares com sugestão de código DMTT
- [x] `resumo-oso/extrair_resumo_oso.py` — extrai tipos de serviço do PDF OSO via pdfplumber
- [x] `matrix/extrair_linhas_xls.py` — identifica 99 linhas nos XLS de passageiros

### Dados gerados
- [x] `data/json/dados_unificados.json` — 85 linhas com GPS + ruas + códigos em um único arquivo
- [x] `data/relatorios/ruas_sem_codigo_e_sem_dicionario.txt` — 148 vias sem código e sem dicionário
- [x] `data/relatorios/nomes_similares_possiveis_duplicatas.txt` — 101 pares similares com sugestão de código
- [x] `data/relatorios/atencao_geral.txt` — diagnóstico geral de qualidade dos dados
- [x] `resumo-oso/relatorio_tipos_servico.txt` — 108 linhas: 78 convencional, 2 catraca, 5 madrugadão, 22 integração, 1 cidadã
- [x] `pontos.json` — 7 atendimentos, 539 pontos com lat/lon
- [x] `data/kml/pontos_*.kml` — 7 KMLs individuais + 1 com todas as linhas
- [x] `data/linhas-nomes/linhas.json` — 99 linhas (84 com nome, 15 sem)

---

## Comportamento atual do mapa — fluxo de interação

```
1. Busca por rua (campo de texto):
   - Digitar → autocomplete mostra nomes de rua (via /ruas/suggest)
   - Selecionar rua → Nominatim busca geometria → halo amarelo no mapa + zoom
   - Resultados mostram linhas com badges [→ IDA] [← VOLTA] clicáveis
   - Clicar badge de sentido → mapa carrega só aquele sentido + caixa de contexto aparece
   - Clicar nome da linha → ambos os sentidos

2. Clique no mapa:
   - Clique em qualquer ponto → Nominatim reverse geocode → nome da rua
   - Campo de busca preenchido automaticamente → busca dispara
   - Rua destacada em amarelo no mapa

3. Caixa de contexto (canto inferior direito do mapa):
   - Aparece quando usuário seleciona sentido específico via busca por rua
   - Borda/título na cor do sentido (verde=IDA, azul=VOLTA)
   - Botão "Ver os dois sentidos" reseta e fecha a caixa

4. Seleção por LinhaSelector (dropdown):
   - Comportamento original mantido
   - Deseleciona qualquer contexto de busca por rua
```

---

## Plano — Incorporar Novas Linhas ao Sistema (Sessões 4 e 5)

Este é o plano definitivo para adicionar linhas novas ao MicroSaaS. Seguir sempre esta ordem.

> Última atualização: 02/06/2026 — Sessão 5

### Estado atual (08/06/2026)

**OSO tem 106 linhas (excluindo Catraca de Solo). dados_unificados.json tem 85.**

| Situação | Qtd | Linhas |
|---|---|---|
| No sistema (dados_unificados) | 85 | — |
| ✅ KML feito + coords extraídas + PDFs do Matrix prontos | 12 | 0036, 0065, 0301, 0402, 1020, 1022, 1023, M001–M005 |
| ✅ KML feito + coords extraídas — **aguardando Matrix** | 8 | 0014, 0109, 0209, 0612-A, 0617, 1000-B, 2058, 4000 |
| Não será feita (decisão) | 1 | 0006-M |
| Total pendente no sistema | 20 | — |

**Arquivos intermediários gerados (sessão 6):**
- `data/json/novos_trajetos/coords_novas_linhas.json` — 20 linhas com IDA/VOLTA (KML→JSON)
- `data/json/terminais.json` — 26 terminais com lat/lon
- `data/json/novos_trajetos/itinerario_rascunho.json` — 12 linhas parseadas (aguardando 8)
- `data/json/novos_trajetos/horarios_novos.json` — 12 linhas parseadas (aguardando 8)

**Formato no Matrix para os madrugadões:** `0001-m`, `0002-m` ... `0005-m` (confirmado)
**Formato a confirmar:** `1000-b` e `0612-a` (pode ser diferente no Matrix)

**Observação sobre coordenadas:** Os pontos extraídos do KML (30–300 pts por linha)
são suficientes para exibir o traçado no Leaflet. Não precisa traçar mais fino.

---

### FASE A — Completar o KML ✅ CONCLUÍDA (sessão 6)
- [x] KML corrigido: 1000-B VOLTA movida para pasta VOLTA
- [x] Todas as 8 linhas complementares desenhadas com IDA/VOLTA
- [x] `python/extrair_terminais_kml.py` criado → `data/json/terminais.json` (26 terminais)

---

### FASE B — Extrair coordenadas do KML → JSON ✅ CONCLUÍDA (sessão 6)
**Script:** `python/extrair_coords_kml.py`
- 20 linhas extraídas (12 originais + 8 novas) → `coords_novas_linhas.json`

---

### FASE C — Extrair itinerário e horários do Matrix ⏳ PARCIALMENTE FEITA
**Scripts:** `matrix/automation_novas_itinerario.py` e `matrix/automation_novas_horario.py`

**Status:**
- [x] 12 linhas originais — PDFs já extraídos (sessão 5)
- [ ] 8 linhas complementares — **aguardando Matrix**

Fluxo para as 8 novas:
1. Usuário abre Matrix → OSO → marca só **[x] Itinerário por Via**
2. Roda `cd matrix && python automation_novas_itinerario.py`
3. Usuário troca para só **[x] Quadro Horário**
4. Roda `cd matrix && python automation_novas_horario.py`

**Atenção:** confirmar formato de `1000-b` e `0612-a` no Matrix antes de rodar.

---

### FASE D — Parsear PDFs → JSON rascunho ⏳ PARCIALMENTE FEITA (sessão 6)
**Scripts já criados:**
- `python/parsear_itinerario_pdf.py` → `data/json/novos_trajetos/itinerario_rascunho.json`
- `python/parsear_horarios_pdf.py` → `data/json/novos_trajetos/horarios_novos.json`

**Status:** 12 linhas parseadas. Rodar novamente após Fase C para incluir as 8 restantes.

---

### FASE E — Revisão manual (responsabilidade do usuário)
- [ ] Corrigir vias no `itinerario_rascunho.json`, preencher códigos DMTT
- [ ] Confirmar horários no `horarios_novos.json`
- [ ] Avisar Claude → Fase F

---

### FASE F — Mesclar no sistema ✅ Script criado (sessão 6)
**Script:** `python/mesclar_novos_trajetos.py` (pronto — rodar após Fase E)

- Injeta coords + itinerário em `dados_unificados.json`
- Mescla horários em `horarios/horarios.json`
- Faz backup automático antes de alterar
- Após rodar: reiniciar backend (`cd backend && uvicorn app.main:app --reload`)

---

### Relatórios de controle
- `I:\Micro-SaaS-DMTT\relatorio_pdfs_vs_oso.txt` — status PDFs vs OSO (106 linhas)
- `data/kml/relatorio_mapa_reconstruido_novo.txt` — status KML vs catálogo
- Script para regerar: `python python/gerar_relatorio_pdfs_vs_oso.py`

---

## Backlog (próximas fases)

### Qualidade de dados — pendências identificadas (Sessão 4)

- [ ] 148 vias sem código DMTT e sem correspondência no dicionário → ver `data/relatorios/ruas_sem_codigo_e_sem_dicionario.txt`
- [ ] 22 pares com mesmo código mas grafias diferentes → padronizar no `dados_unificados.json`
- [ ] 4 pares com sugestão automática de código → ver `data/relatorios/nomes_similares_possiveis_duplicatas.txt`
- [ ] 2 linhas com anotações pendentes no nome (`FALTA FAZER`, `PRECISA DE ALTERAÇÃO`) → remover ou corrigir
- [ ] 2 linhas sem coordenadas GPS (IDA e VOLTA) → levantamento em campo

### Fase 3 — Deploy ✅ CONCLUÍDA (04/07/2026) — ver `DEPLOY.md`
- [x] Deploy do frontend em produção (`dmtt.mendesweb.com`, Hostinger)
- [x] Backend abandonado em favor de arquitetura 100% estática (índice de rua + JSON por linha)
- [x] `.env` / `.env.example` para credenciais de deploy (fora do git)
- [ ] Trocar autenticação SSH por chave (em vez de senha)
- [ ] `docker-compose.yml` para rodar backend local com um comando (opcional, dev only)

### Fase 4 — Dados de pontos no sistema
- [ ] Integrar `pontos.json` ao backend (endpoint `/pontos/{codigo}`)
- [ ] Exibir pontos de parada no mapa (markers) quando uma linha é selecionada
- [ ] Completar as 15 linhas que ainda não têm dados de pontos

### Fase 5 — Banco de dados
- [ ] Migrar JSON → SQL Server ou banco Hostinger
- [ ] Manter contratos de endpoint estáveis

---

## Regras de trabalho

- **Produção é 100% estática** — não há backend rodando na Hostinger; o frontend lê `public/data/*.json` via `staticApi.js`
- **JSON como fonte de verdade agora** — não criar banco de dados ainda
- **Fonte de dados** — `dados_unificados.json` é o único arquivo de onde tudo deriva (backend local e geração estática). Edite ele, não o `itinerario_com_codigos.json` diretamente
- **Depois de editar `dados_unificados.json`/`horarios.json`** — rodar `python python/gerar_dados_estaticos.py`, depois `npm run build` e `python python/deploy_frontend.py` (ver seção "Como atualizar dados em produção"). Se estiver usando o backend Python localmente, reiniciar o uvicorn (--reload só observa .py, não .json)
- **Nunca commitar segredos** — credenciais de deploy (SSH host/senha) ficam só em `.env` (git-ignored); `DEPLOY.md`/`CLAUDE.md` não devem conter valores reais
- **Cores:** IDA = `#22c55e` (verde), VOLTA = `#1e40af` (azul) — manter em tudo
- **Nominatim** — chamadas feitas direto do frontend, sem passar pelo backend
- **Sem comentários óbvios** — só comentar o "por quê" quando não for óbvio
- **Sem features não pedidas** — implementar exatamente o que foi definido

---

## Contexto de persistência entre máquinas

```bash
# Ao terminar uma sessão
git add CLAUDE.md
git commit -m "docs: atualiza CLAUDE.md após sessão de trabalho"
git push

# Ao começar em outra máquina
git pull
```
