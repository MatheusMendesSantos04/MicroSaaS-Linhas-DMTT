# CLAUDE.md — MicroSaaS Linhas DMTT

> Este arquivo é lido automaticamente pelo Claude Code em toda sessão.
> Mantenha-o atualizado após cada sessão de trabalho.
> Última atualização: 18/05/2026 — Fase 1 e 2 concluídas

---

## O que é o projeto

Micro-serviço web para consulta de itinerários de ônibus da **DMTT**
(Diretoria de Mobilidade e Trânsito de Maceió/AL).

**Objetivo:** usuário seleciona uma linha → vê o traçado no mapa → vê o itinerário completo
(lista de ruas percorridas) → pode buscar por rua e saber quais linhas passam lá.

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
# Backend (na raiz do projeto)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API em: http://127.0.0.1:8000

# Frontend
cd frontend
npm install
npm run dev
# UI em: http://localhost:5173
```

---

## Estrutura de pastas

```
MicroSaaS-Linhas-DMTT/
├── CLAUDE.md                          ← este arquivo
├── backend/
│   ├── requirements.txt               ← fastapi, uvicorn, pydantic
│   └── app/
│       ├── main.py                    ← FastAPI, todos os endpoints
│       ├── schemas.py                 ← modelos Pydantic
│       └── services/
│           └── data_loader.py         ← DataStore: carrega JSONs, indexa ruas
├── frontend/
│   └── src/
│       ├── App.jsx                    ← componente raiz
│       ├── components/                ← componentes individuais (a criar)
│       ├── main.jsx
│       └── styles.css
├── data/
│   ├── json/
│   │   ├── dado-bruto/                ← IDA.json, VOLTA.json, PONTOS.json (raw)
│   │   ├── dado-tratado/              ← IDA_amostrado.json, VOLTA_amostrado.json (GPS)
│   │   └── dado-linhas/               ← IDA_linhas_ruas.json, VOLTA_linhas_ruas.json
│   ├── kml/                           ← arquivos KML dos mapas
│   └── pdf-intinerarios-por-via-todas-linhas/  ← 86 PDFs (itinerários por linha)
│       └── sre_relatorio_via_logradouro-codigo-das-ruas.pdf  ← master de códigos
└── python/
    ├── gerar_itinerario_com_codigos.py  ← script: adiciona códigos DMTT ao itinerário
    └── dado principal/
        ├── intinerario manual/
        │   └── itinerario_completo.json   ← 85 linhas, IDA e VOLTA com nomes de ruas
        └── intinerario-com-codigo-rua/
            ├── itinerario_com_codigos.json  ← FONTE PRINCIPAL DO BACKEND (código+match)
            └── relatorio_codigos.txt        ← relatório de matching (88,6% encontradas)
            ATENÇÃO: esses dois diretórios ficam em data/json/ (não em python/)
```

---

## Endpoints da API (atuais)

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /health | Status da API |
| GET | /meta | Total de linhas, ruas indexadas, arquivos |
| GET | /linhas | Lista todas as linhas |
| GET | /linhas/{id} | Detalhe: coords GPS + ruas IDA/VOLTA |
| GET | /ruas/search?q= | Busca por nome de rua |
| GET | /ruas/codigo/{codigo} | Linhas que passam pela via com esse código DMTT |
| GET | /geojson/linhas | GeoJSON de todas as linhas |
| GET | /geojson/linhas/{id} | GeoJSON de uma linha específica |

---

## Dados principais — formato

### `itinerario_com_codigos.json` (fonte principal do backend)

```json
{
  "0024 - Gruta / Centro / Term. Rotary": {
    "versao": "pdf_v1",
    "ida": [
      {
        "via": "AVENIDA ROBERTO SIMONSEN",
        "codigo": "00834",
        "via_pdf": "AV. ROBERTO SIMONSEN",
        "match": "exato"
      }
    ],
    "volta": [ ... ]
  }
}
```

Campos de `match`: `exato`, `exato_global`, `exato_sem_complemento`, `contem`,
`fuzzy`, `fuzzy_global`, `nao_encontrado`.

### `IDA_amostrado.json` / `VOLTA_amostrado.json` (coordenadas GPS)

```json
[
  {
    "linha": "0024 - GRUTA/CENTRO-VIA C. ALMAS(TERM. ROTARY)",
    "coordenadas": [[-9.623, -35.741], ...]
  }
]
```

---

## O que já foi feito

- [x] Backend FastAPI com 8 endpoints funcionando
- [x] Frontend React + Leaflet básico (seletor de linha, mapa, busca por rua)
- [x] Extração de itinerários de 85 linhas a partir dos PDFs da DMTT
- [x] Script de matching: adicionou códigos DMTT a 88,6% das vias
- [x] Arquivo `itinerario_com_codigos.json` gerado (fonte principal)
- [x] DataStore atualizado para carregar `itinerario_com_codigos.json`
- [x] `schemas.py` atualizado com `RuaItem` (via + codigo + match)
- [x] Endpoint `GET /ruas/codigo/{codigo}` adicionado
- [x] Frontend refatorado em componentes
- [x] Mapa com cores por sentido, popups, zoom automático
- [x] Itinerário exibindo código da via
- [x] Busca com resultados clicáveis

---

## Backlog (próximas fases)

### Fase 3 — Qualidade e deploy
- [ ] CORS configurável via variável de ambiente
- [ ] Criar `.env.example` para backend e frontend
- [ ] `docker-compose.yml` para rodar tudo com um comando
- [ ] Atualizar `.gitignore` (venvs, node_modules, .env)

### Fase 4 — Horários (quando o dado estiver disponível)
- [ ] Estrutura JSON: `{linha_id, dia_tipo, horarios: [{partida, terminal}]}`
- [ ] `GET /horarios/{linha_id}?dia=util`
- [ ] `GET /ruas/search?q=...&horario=07:30&dia=util`

### Fase 5 — Banco de dados
- [ ] Migrar JSON → SQL Server ou banco Hostinger
- [ ] Manter contratos de endpoint estáveis
- [ ] Trocar `JsonRepository` por `SqlRepository` no DataStore

---

## Regras de trabalho

- **Não quebrar endpoints existentes** — frontend já consome a API
- **JSON como fonte de verdade agora** — não criar banco de dados ainda
- **Itinerário com código** — sempre usar `itinerario_com_codigos.json`, nunca o antigo
- **Sem comentários óbvios no código** — só comentar o "por quê" quando não for óbvio
- **Sem features não pedidas** — implementar exatamente o que foi definido no backlog
- **Atualizar este CLAUDE.md** após cada sessão que adicionar/concluir algo

---

## Contexto de persistência entre máquinas

Este arquivo viaja pelo Git. Para sincronizar:

```bash
# Ao terminar uma sessão
git add CLAUDE.md
git commit -m "docs: atualiza CLAUDE.md após sessão de trabalho"
git push

# Ao começar em outra máquina
git pull
```

O Claude Code lê este arquivo automaticamente ao abrir o projeto.
