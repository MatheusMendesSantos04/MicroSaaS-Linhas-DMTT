"""
Gera arquivos KML a partir de data/listagem-de-pontos-faltantes/pontos.json.
- IDA:   pontos em ordem crescente (ordem 1, 2, 3...)
- VOLTA: pontos em ordem decrescente (invertido)

Saída:
  data/kml/pontos_<codigo>.kml  — um arquivo por linha
  data/kml/pontos_todas.kml     — todos juntos

Uso:
    python gerar_kml_pontos.py
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

BASE_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = BASE_DIR / "data" / "listagem-de-pontos-faltantes" / "pontos.json"
KML_DIR   = BASE_DIR / "data" / "kml"

# Cores no formato KML: aabbggrr (alpha, blue, green, red)
COR_IDA   = "ff4dc322"   # verde
COR_VOLTA = "ffaf401e"   # azul escuro
COR_PONTO_IDA   = "ff4dc322"
COR_PONTO_VOLTA = "ffaf401e"


def coords_kml(pontos: list[dict]) -> str:
    """Converte lista de pontos em string de coordenadas KML (lon,lat,alt)."""
    return " ".join(
        f"{p['longitude']},{p['latitude']},0"
        for p in pontos
        if p.get("latitude") is not None and p.get("longitude") is not None
    )


def estilo_linha(doc_el, style_id: str, cor: str, largura: int = 4):
    style = ET.SubElement(doc_el, "Style", id=style_id)
    line  = ET.SubElement(style, "LineStyle")
    ET.SubElement(line, "color").text = cor
    ET.SubElement(line, "width").text = str(largura)


def estilo_ponto(doc_el, style_id: str, cor: str):
    style  = ET.SubElement(doc_el, "Style", id=style_id)
    icon   = ET.SubElement(style, "IconStyle")
    ET.SubElement(icon, "color").text = cor
    ET.SubElement(icon, "scale").text = "0.7"
    icn    = ET.SubElement(icon, "Icon")
    ET.SubElement(icn, "href").text = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"


def placemark_linha(parent, name: str, descricao: str, coords: str, style_id: str):
    pm   = ET.SubElement(parent, "Placemark")
    ET.SubElement(pm, "name").text = name
    ET.SubElement(pm, "description").text = descricao
    ET.SubElement(pm, "styleUrl").text = f"#{style_id}"
    ls   = ET.SubElement(pm, "LineString")
    ET.SubElement(ls, "tessellate").text = "1"
    ET.SubElement(ls, "coordinates").text = coords


def placemark_ponto(parent, ponto: dict, style_id: str):
    pm = ET.SubElement(parent, "Placemark")
    ET.SubElement(pm, "name").text = ponto.get("nome", "")
    desc = (
        f"Abrev: {ponto.get('abreviatura','')}\n"
        f"Endereço: {ponto.get('endereco','')}\n"
        f"Ordem: {ponto.get('ordem','')}\n"
        f"Vel. Limite: {ponto.get('vel_limite','')} km/h"
    )
    ET.SubElement(pm, "description").text = desc
    ET.SubElement(pm, "styleUrl").text = f"#{style_id}"
    pt = ET.SubElement(pm, "Point")
    ET.SubElement(pt, "coordinates").text = (
        f"{ponto['longitude']},{ponto['latitude']},0"
    )


def construir_documento(linhas: list[dict]) -> ET.Element:
    kml  = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc  = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = "Linhas DMTT — Pontos Faltantes"

    # Estilos globais
    estilo_linha(doc,  "tracado_ida",   COR_IDA,   largura=4)
    estilo_linha(doc,  "tracado_volta", COR_VOLTA, largura=4)
    estilo_ponto(doc,  "ponto_ida",     COR_PONTO_IDA)
    estilo_ponto(doc,  "ponto_volta",   COR_PONTO_VOLTA)

    for linha in linhas:
        codigo    = linha["codigo"]
        nome_rota = linha["linha"]
        nome_ida  = linha.get("nome_ida")  or "IDA"
        nome_volta= linha.get("nome_volta") or "VOLTA"
        pontos    = sorted(linha["pontos"], key=lambda p: p.get("ordem", 0))

        pontos_validos = [p for p in pontos if p.get("latitude") and p.get("longitude")]
        if not pontos_validos:
            print(f"  [AVISO] {codigo}: nenhum ponto com coordenadas válidas")
            continue

        pontos_volta = list(reversed(pontos_validos))

        # Pasta da linha
        pasta = ET.SubElement(doc, "Folder")
        ET.SubElement(pasta, "name").text = f"{codigo} — {nome_rota}"

        # ── Subpasta IDA ──────────────────────────────────────────────────
        pasta_ida = ET.SubElement(pasta, "Folder")
        ET.SubElement(pasta_ida, "name").text = f"→ IDA — {nome_ida}"

        coords_ida = coords_kml(pontos_validos)
        placemark_linha(
            pasta_ida,
            name="Traçado IDA",
            descricao=f"Linha {codigo} — {nome_ida}\n{len(pontos_validos)} paradas",
            coords=coords_ida,
            style_id="tracado_ida",
        )
        for p in pontos_validos:
            placemark_ponto(pasta_ida, p, "ponto_ida")

        # ── Subpasta VOLTA ────────────────────────────────────────────────
        pasta_volta = ET.SubElement(pasta, "Folder")
        ET.SubElement(pasta_volta, "name").text = f"← VOLTA — {nome_volta}"

        coords_volta = coords_kml(pontos_volta)
        placemark_linha(
            pasta_volta,
            name="Traçado VOLTA",
            descricao=f"Linha {codigo} — {nome_volta}\n{len(pontos_volta)} paradas",
            coords=coords_volta,
            style_id="tracado_volta",
        )
        for p in pontos_volta:
            placemark_ponto(pasta_volta, p, "ponto_volta")

    return kml


def salvar_kml(element: ET.Element, path: Path):
    xml_str = ET.tostring(element, encoding="unicode")
    pretty  = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="UTF-8")
    path.write_bytes(pretty)
    print(f"  [OK] {path.name}")


def main():
    with JSON_PATH.open("r", encoding="utf-8") as f:
        linhas = json.load(f)

    KML_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] {len(linhas)} linha(s) encontrada(s)")

    # KML individual por linha
    for linha in linhas:
        kml = construir_documento([linha])
        salvar_kml(kml, KML_DIR / f"pontos_{linha['codigo']}.kml")

    # KML com todas as linhas
    kml_todas = construir_documento(linhas)
    salvar_kml(kml_todas, KML_DIR / "pontos_todas.kml")

    print(f"\n[OK] Arquivos salvos em: {KML_DIR}")


if __name__ == "__main__":
    main()
