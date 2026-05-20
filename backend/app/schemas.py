from typing import Dict, List, Optional

from pydantic import BaseModel


class RuaItem(BaseModel):
    via: str
    codigo: Optional[str]
    match: str


class SentidoData(BaseModel):
    coordenadas: List[List[float]]
    ruas: List[RuaItem]


class LinhaSummary(BaseModel):
    id: str
    nome: str
    tem_ida: bool
    tem_volta: bool
    tem_itinerario_manual: bool


class LinhaDetalhe(BaseModel):
    id: str
    nome: str
    ida: SentidoData
    volta: SentidoData


class RuaOcorrencia(BaseModel):
    linha_id: str
    linha_nome: str
    sentido: str
    rua: str
    codigo: Optional[str]


class RuasSearchResponse(BaseModel):
    query: str
    total: int
    resultados: List[RuaOcorrencia]


class RuasPorCodigoResponse(BaseModel):
    codigo: str
    total: int
    resultados: List[RuaOcorrencia]


class RuaOcorrenciaHorario(RuaOcorrencia):
    horarios_proximos: List[str]


class RuasHorarioResponse(BaseModel):
    query: str
    horario: str
    dia: str
    janela: int
    total: int
    resultados: List[RuaOcorrenciaHorario]


class MetaResponse(BaseModel):
    total_linhas: int
    total_ruas_indexadas: int
    arquivos_origem: Dict[str, str]


class HealthResponse(BaseModel):
    status: str


class LinhasResponse(BaseModel):
    total: int
    itens: List[LinhaSummary]


class HorarioSentido(BaseModel):
    ida: List[str]
    volta: List[str]


class HorariosLinha(BaseModel):
    linha_id: str
    nome: str
    dia_util: HorarioSentido
    sabado: HorarioSentido
    domingo: HorarioSentido
