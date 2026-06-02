"""
Etapa 1 do pipeline de novas linhas.

Extrai as coordenadas GPS das linhas novas do Mapa Reconstruido.kml
e salva em data/json/novos_trajetos/coords_novas_linhas.json.

A separação IDA/VOLTA é feita pelas pastas do KML (<Folder><name>IDA</name>).
Coordenadas convertidas de lon,lat (KML) para [lat, lon] (sistema).

Uso:
    python python/extrair_coords_kml.py
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
KML_PATH = BASE_DIR / "data" / "kml" / "Mapa Reconstruido.kml"
SAIDA    = BASE_DIR / "data" / "json" / "novos_trajetos" / "coords_novas_linhas.json"

NS = {"k": "http://www.opengis.net/kml/2.2"}

# Linhas novas a extrair (códigos conforme aparecem no KML)
LINHAS_NOVAS = {
    "0036", "0065", "0301", "0402",
    "1020", "1022", "1023",
    "M001", "M002", "M003", "M004", "M005",
}


def extrair_codigo(texto: str) -> str:
    if not texto:
        return ""
    m = re.match(r"^([A-Z]?\d{3,4})", texto.strip())
    if not m:
        return ""
    v = m.group(1)
    return v.zfill(4) if v.isdigit() else v


def parse_coords(coords_text: str) -> list[list[float]]:
    """Converte 'lon,lat,alt lon,lat,alt ...' → [[lat, lon], ...]"""
    pontos = []
    for token in coords_text.strip().split():
        partes = token.split(",")
        if len(partes) < 2:
            continue
        try:
            lon = float(partes[0])
            lat = float(partes[1])
            pontos.append([lat, lon])
        except ValueError:
            continue
    return pontos


def extrair_nome_limpo(texto: str) -> str:
    """Retorna o nome do placemark sem encoding quebrado, strip."""
    return texto.strip() if texto else ""


# ---------------------------------------------------------------------------
# leitura do KML
# ---------------------------------------------------------------------------

tree = ET.parse(KML_PATH)
root = tree.getroot()

# resultado: nome_canônico → {ida: [...], volta: [...]}
resultado: dict[str, dict] = {}

# mapa código → nome canônico (primeiro encontrado na pasta IDA)
cod_to_nome: dict[str, str] = {}

for folder in root.findall(".//k:Folder", NS):
    fname_el = folder.find("k:name", NS)
    fname = fname_el.text.strip().upper() if fname_el is not None and fname_el.text else ""
    if fname not in ("IDA", "VOLTA"):
        continue
    sentido = fname.lower()  # "ida" ou "volta"

    for pm in folder.findall("k:Placemark", NS):
        n_el = pm.find("k:name", NS)
        nome = extrair_nome_limpo(n_el.text if n_el is not None else "")
        cod  = extrair_codigo(nome)
        if cod not in LINHAS_NOVAS:
            continue

        coords_el = pm.find(".//k:coordinates", NS)
        if coords_el is None or not coords_el.text:
            continue
        pontos = parse_coords(coords_el.text)
        if not pontos:
            continue

        # registra nome canônico pelo código (usa o nome da pasta IDA)
        if sentido == "ida" and cod not in cod_to_nome:
            cod_to_nome[cod] = nome

        chave = cod_to_nome.get(cod, nome)
        if chave not in resultado:
            resultado[chave] = {"ida": [], "volta": []}

        # se já tem coordenadas nesse sentido, concatena (caso de múltiplos segmentos)
        resultado[chave][sentido] = pontos

# ---------------------------------------------------------------------------
# reorganiza por código ordenado
# ---------------------------------------------------------------------------

resultado_ordenado = dict(
    sorted(resultado.items(), key=lambda x: extrair_codigo(x[0]))
)

# ---------------------------------------------------------------------------
# salva
# ---------------------------------------------------------------------------

SAIDA.parent.mkdir(parents=True, exist_ok=True)
with SAIDA.open("w", encoding="utf-8") as f:
    json.dump(resultado_ordenado, f, ensure_ascii=False, indent=2)

print(f"[OK] {SAIDA}")
print()
for nome, sentidos in resultado_ordenado.items():
    n_ida   = len(sentidos.get("ida", []))
    n_volta = len(sentidos.get("volta", []))
    aviso   = "  ** SEM VOLTA **" if n_volta == 0 else ""
    print(f"  {extrair_codigo(nome):<6} {nome[:50]:<52}  IDA={n_ida:>3}pts  VOLTA={n_volta:>3}pts{aviso}")
