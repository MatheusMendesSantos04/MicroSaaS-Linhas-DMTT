# CLAUDE.md — MicroSaaS Linhas DMTT

> Este arquivo é lido automaticamente pelo Claude Code em toda sessão.
> Mantenha-o atualizado após cada sessão de trabalho.
> Última atualização: 20/05/2026 — Sessão 3 concluída

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

**Fase atual:** MVP local com dados em JSON. Sem banco de dados ainda.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ · FastAPI · Uvicorn · Pydantic |
| Frontend | React 18 · Vite · Leaflet 1.9 · react-leaflet 4.2 |
| Dados (agora) | Arquivos JSON locais |
| Dados (futuro) | SQL Server ou banco Hostinger |

---

## Como rodar localmente

```bash
# Opção 1: duplo-clique em start.bat (abre backend + frontend + browser)
MicroSaaS-Linhas-DMTT/start.bat

# Opção 2: manual
cd backend && uvicorn app.main:app --reload   # http://127.0.0.1:8000
cd frontend && npm run dev                    # http://localhost:5173
```

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
│   └── src/
│       ├── App.jsx                        ← raiz: estado global, callbacks, Nominatim
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
│   └── gerar_kml_pontos.py                ← gera KMLs de IDA/VOLTA a partir de pontos.json
└── matrix/
    └── extrair_linhas_xls.py              ← identifica linhas nos arquivos XLS de passageiros
```

---

## Endpoints da API (atuais)

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

### `itinerario_com_codigos.json` (fonte principal do backend)

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
- [x] `matrix/extrair_linhas_xls.py` — identifica 99 linhas nos XLS de passageiros

### Dados gerados
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

## Backlog (próximas fases)

### Fase 3 — Qualidade e deploy
- [ ] CORS configurável via variável de ambiente
- [ ] Criar `.env.example` para backend e frontend
- [ ] `docker-compose.yml` para rodar tudo com um comando
- [ ] Atualizar `.gitignore` (venvs, node_modules, .env)

### Fase 4 — Dados de pontos no sistema
- [ ] Integrar `pontos.json` ao backend (endpoint `/pontos/{codigo}`)
- [ ] Exibir pontos de parada no mapa (markers) quando uma linha é selecionada
- [ ] Completar as 15 linhas que ainda não têm dados de pontos

### Fase 5 — Banco de dados
- [ ] Migrar JSON → SQL Server ou banco Hostinger
- [ ] Manter contratos de endpoint estáveis

---

## Regras de trabalho

- **Não quebrar endpoints existentes** — frontend já consome a API
- **JSON como fonte de verdade agora** — não criar banco de dados ainda
- **Itinerário com código** — sempre usar `itinerario_com_codigos.json`, nunca o antigo
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
