# Backend - MicroSaaS Linhas DMTT

API local em FastAPI que unifica dados de:

- `data/json/dado-tratado/IDA_amostrado.json`
- `data/json/dado-tratado/VOLTA_amostrado.json`
- `python/dado principal/intinerario manual/itinerario_completo_rua_principal_somente_ruas_v1.json`

## Executar localmente

No diretório raiz do projeto:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /meta`
- `GET /linhas`
- `GET /linhas/{linha_id}`
- `GET /ruas/search?q=FERNANDES`
- `GET /geojson/linhas`
- `GET /geojson/linhas?sentido=ida`
- `GET /geojson/linhas/{linha_id}`
- `GET /geojson/linhas/{linha_id}?sentido=volta`

## Observações

- O merge IDA/VOLTA é feito em memória no startup da API.
- O itinerário manual entra junto no payload da linha (`ida.ruas` e `volta.ruas`).
- Endpoints GeoJSON já retornam coordenadas no formato `[lon, lat]` para uso direto no Leaflet.