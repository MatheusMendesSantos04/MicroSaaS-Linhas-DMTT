# MicroSaaS Linhas DMTT

Micro-serviço web para consulta de itinerários de ônibus da DMTT, com foco em visualização no mapa e busca por ruas.

## Objetivo (MVP local)

Nesta fase, o sistema roda localmente e utiliza arquivos JSON como fonte de dados (sem banco de dados).

Funcionalidades do MVP:

- Visualizar no mapa o traçado de todas as linhas.
- Selecionar uma linha específica para visualização.
- Visualizar o itinerário completo da linha.
- Alternar entre os sentidos IDA e VOLTA.
- Pesquisar por nome de rua e retornar todas as linhas que atendem a rua.

## Stack definida

### Backend

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- Dados em JSON (arquivos locais)
- Unidecode + RapidFuzz (busca tolerante por nome de rua)

### Frontend

- React + Vite
- Leaflet
- OpenStreetMap (tiles)

### Qualidade

- pytest
- ruff
- black

## Fonte de dados atual

Os dados estão organizados principalmente em:

- `data/json/dado-bruto`
- `data/json/dado-tratado`
- `data/vias-normalizadas`
- `data/vias-por-bairro`

## Escopo da fase atual

- Sem PostgreSQL nesta etapa.
- Persistência 100% em JSON.
- Foco em validar funcionalidades e experiência de uso local.

## Próxima evolução (planejada)

Quando houver acesso ao servidor, migrar camada de dados para PostgreSQL/PostGIS mantendo a API.

Estratégia sugerida:

1. Manter contratos de endpoint estáveis.
2. Isolar acesso a dados em repositórios (ex.: `JsonRepository` -> `PostgresRepository`).
3. Migrar gradualmente sem quebrar o frontend.

## Status

Documento criado para registrar decisões de arquitetura e escopo do MVP local em 04/03/2026.
