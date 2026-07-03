import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    HealthResponse,
    HorarioSentido,
    HorariosLinha,
    LinhaDetalhe,
    LinhasResponse,
    LinhaSummary,
    MetaResponse,
    RuaItem,
    RuaOcorrencia,
    RuaOcorrenciaHorario,
    RuasPorCodigoResponse,
    RuasHorarioResponse,
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


@app.get("/ruas/suggest", response_model=list[str])
def sugerir_rua(
    q: str = Query(..., min_length=2, description="Prefixo do nome da rua"),
    limit: int = Query(10, ge=1, le=50),
) -> list[str]:
    return data_store.suggest_ruas(q, limit=limit)


@app.get("/ruas/search")
def buscar_rua(
    q: str = Query(..., min_length=1, description="Nome da rua para busca"),
    limit: int = Query(100, ge=1, le=500),
    horario: str | None = Query(None, description="Filtrar por horário HH:MM"),
    dia: str = Query("dia_util", description="dia_util | sabado | domingo"),
    janela: int = Query(20, ge=5, le=60, description="Janela em minutos"),
):
    if horario:
        matches = data_store.search_ruas_horario(q, horario=horario, dia=dia, janela=janela, limit=limit)
        results = [
            RuaOcorrenciaHorario(
                linha_id=line_id,
                linha_nome=line_name,
                sentido=sentido,
                rua=rua_norm,
                codigo=codigo,
                horarios_proximos=horarios_proximos,
            )
            for line_id, line_name, sentido, rua_norm, codigo, horarios_proximos in matches
        ]
        return RuasHorarioResponse(query=q, horario=horario, dia=dia, janela=janela, total=len(results), resultados=results)

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


@app.get("/horarios/{linha_id}", response_model=HorariosLinha)
def horarios_linha(linha_id: str) -> HorariosLinha:
    line = data_store.get_line(linha_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Linha não encontrada")
    horarios = data_store.get_horarios(linha_id)
    if horarios is None:
        raise HTTPException(status_code=404, detail="Horários não disponíveis para esta linha")
    return HorariosLinha(
        linha_id=linha_id,
        nome=horarios.get("nome", line.nome),
        dia_util=HorarioSentido(**horarios.get("dia_util", {"ida": [], "volta": []})),
        sabado=HorarioSentido(**horarios.get("sabado", {"ida": [], "volta": []})),
        domingo=HorarioSentido(**horarios.get("domingo", {"ida": [], "volta": []})),
    )


@app.get("/terminais")
def listar_terminais() -> list[dict]:
    terminais_path = PROJECT_ROOT / "data" / "json" / "terminais.json"
    return json.loads(terminais_path.read_text(encoding="utf-8"))


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
