"""
Busca no Overpass API (dados brutos do OSM) o contorno administrativo de
bairros que o Nominatim NAO retorna via /search nem /lookup (aparecem so
como Point la, mas existem como relation boundary=administrative no OSM).

Reconstroi o poligono manualmente encadeando os "ways" (role=outer) da
relation pelas extremidades, ja que o Overpass nao devolve o anel fechado
pronto.

Uso:
    python python/buscar_zonas_via_overpass.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ZONAS_DIR = ROOT / "data" / "json" / "zonas"

HEADERS = {"User-Agent": "MicroSaaS-Linhas-DMTT/1.0 (uso interno DMTT Maceio)"}
OVERPASS = "https://overpass-api.de/api/interpreter"

# nome oficial DMTT -> osm relation id (achado via Overpass, boundary=administrative)
RELACOES = {
    "Centro": 400298,
    "Farol": 400297,
    "Jaraguá": 400193,
    "Poço": 400191,
}


def overpass_query(ql: str):
    req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": ql}).encode(), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def stitch_rings(ways_coords):
    """ways_coords: lista de listas de (lon,lat). Encadeia pelas extremidades
    ate formar anel(is) fechado(s). Retorna lista de aneis (cada um lista de pontos)."""
    pendentes = [list(w) for w in ways_coords]
    aneis = []
    while pendentes:
        anel = pendentes.pop(0)
        mudou = True
        while mudou and anel[0] != anel[-1]:
            mudou = False
            for i, w in enumerate(pendentes):
                if w[0] == anel[-1]:
                    anel = anel + w[1:]
                    pendentes.pop(i)
                    mudou = True
                    break
                if w[-1] == anel[-1]:
                    anel = anel + list(reversed(w))[1:]
                    pendentes.pop(i)
                    mudou = True
                    break
                if w[0] == anel[0]:
                    anel = list(reversed(w))[:-1] + anel
                    pendentes.pop(i)
                    mudou = True
                    break
                if w[-1] == anel[0]:
                    anel = w[:-1] + anel
                    pendentes.pop(i)
                    mudou = True
                    break
        aneis.append(anel)
    return aneis


def area_aprox(anel):
    """Area (shoelace) aproximada, so pra comparar tamanho de aneis."""
    s = 0.0
    for i in range(len(anel) - 1):
        x1, y1 = anel[i]
        x2, y2 = anel[i + 1]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def slug(nome: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return s.lower().replace(" ", "-")


def main():
    sucesso, falhas = [], []
    for nome, rel_id in RELACOES.items():
        ql = f"[out:json][timeout:30];relation({rel_id});out geom;way(r);out geom;"
        data = overpass_query(ql)

        outer_way_ids = None
        ways_geom = {}
        for el in data["elements"]:
            if el["type"] == "relation":
                outer_way_ids = [m["ref"] for m in el["members"] if m["type"] == "way" and m.get("role") == "outer"]
            elif el["type"] == "way":
                ways_geom[el["id"]] = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]

        if not outer_way_ids:
            print(f"[FALHA] {nome}: relation {rel_id} sem members outer")
            falhas.append(nome)
            time.sleep(1)
            continue

        ways_coords = [ways_geom[wid] for wid in outer_way_ids if wid in ways_geom]
        aneis = stitch_rings(ways_coords)
        aneis_fechados = [a for a in aneis if a[0] == a[-1] and len(a) >= 4]

        if not aneis_fechados:
            print(f"[FALHA] {nome}: nao foi possivel fechar um anel ({len(aneis)} fragmento(s), fechados: 0)")
            falhas.append(nome)
            time.sleep(1)
            continue

        maior = max(aneis_fechados, key=area_aprox)

        feature = {
            "type": "Feature",
            "properties": {
                "name": nome,
                "addresstype": "administrative_boundary_overpass",
                "osm_type": "relation",
                "osm_id": rel_id,
            },
            "geometry": {"type": "Polygon", "coordinates": [maior]},
        }
        saida = {"type": "FeatureCollection", "features": [feature]}
        caminho = ZONAS_DIR / f"{slug(nome)}.geojson"
        caminho.write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] {nome} -> {caminho.name} ({len(maior)} pontos, {len(aneis_fechados)} anel(is) fechado(s) de {len(aneis)} total)")
        sucesso.append(nome)

        time.sleep(1)

    print(f"\nTotal: {len(sucesso)} ok, {len(falhas)} falha(s)")
    if falhas:
        print("Falharam:", falhas)


if __name__ == "__main__":
    main()
