from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    HealthResponse,
    LinhaDetalhe,
    LinhasResponse,
    LinhaSummary,
    MetaResponse,
    RuaItem,
    RuaOcorrencia,
    RuasPorCodigoResponse,
    RuasSearchResponse,
    SentidoData,
)
from .services.data_loader import DataStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
data_store = DataStore(PROJECT_ROOT)

app = FastAPI(
    title="MicroSaaS Linhas DMTT API",
    version="0.2.0",
    description="API para visualização de linhas, itinerários IDA/VOLTA e busca por ruas.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    return MetaResponse(**data_store.get_metadata())


@app.get("/linhas", response_model=LinhasResponse)
def listar_linhas() -> LinhasResponse:
    items = []
    for line in data_store.list_lines():
        items.append(
            LinhaSummary(
                id=line.id,
                nome=line.nome,
                tem_ida=bool(line.ida_coordenadas),
                tem_volta=bool(line.volta_coordenadas),
                tem_itinerario_manual=bool(line.ida_ruas or line.volta_ruas),
            )
        )
    return LinhasResponse(total=len(items), itens=items)


@app.get("/linhas/{linha_id}", response_model=LinhaDetalhe)
def detalhar_linha(linha_id: str) -> LinhaDetalhe:
    line = data_store.get_line(linha_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Linha não encontrada")

    return LinhaDetalhe(
        id=line.id,
        nome=line.nome,
        ida=SentidoData(
            coordenadas=line.ida_coordenadas,
            ruas=[RuaItem(via=r.via, codigo=r.codigo, match=r.match) for r in line.ida_ruas],
        ),
        volta=SentidoData(
            coordenadas=line.volta_coordenadas,
            ruas=[RuaItem(via=r.via, codigo=r.codigo, match=r.match) for r in line.volta_ruas],
        ),
    )


@app.get("/ruas/search", response_model=RuasSearchResponse)
def buscar_rua(
    q: str = Query(..., min_length=1, description="Nome da rua para busca"),
    limit: int = Query(100, ge=1, le=500),
) -> RuasSearchResponse:
    matches = data_store.search_ruas(q, limit=limit)
    results = [
        RuaOcorrencia(
            linha_id=line_id,
            linha_nome=line_name,
            sentido=sentido,
            rua=rua_norm,
            codigo=codigo,
        )
        for line_id, line_name, sentido, rua_norm, codigo in matches
    ]
    return RuasSearchResponse(query=q, total=len(results), resultados=results)


@app.get("/ruas/codigo/{codigo}", response_model=RuasPorCodigoResponse)
def buscar_por_codigo(codigo: str) -> RuasPorCodigoResponse:
    matches = data_store.search_by_codigo(codigo)
    results = [
        RuaOcorrencia(
            linha_id=line_id,
            linha_nome=line_name,
            sentido=sentido,
            rua=via,
            codigo=codigo,
        )
        for line_id, line_name, sentido, via in matches
    ]
    return RuasPorCodigoResponse(codigo=codigo, total=len(results), resultados=results)


@app.get("/geojson/linhas")
def geojson_todas_linhas(
    sentido: str | None = Query(None, description="Filtrar sentido: ida, volta ou ambos"),
) -> dict[str, Any]:
    try:
        return data_store.get_geojson_feature_collection(sentido=sentido)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/geojson/linhas/{linha_id}")
def geojson_linha(
    linha_id: str,
    sentido: str | None = Query(None, description="Filtrar sentido: ida, volta ou ambos"),
) -> dict[str, Any]:
    try:
        payload = data_store.get_linha_geojson(linha_id=linha_id, sentido=sentido)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if payload is None:
        raise HTTPException(status_code=404, detail="Linha não encontrada")

    return payload
