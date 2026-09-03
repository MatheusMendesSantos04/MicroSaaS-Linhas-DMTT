"""
Pra cada via SEM CODIGO (data/json/vias_por_bairro.json), tenta descobrir o
bairro automaticamente: busca o nome da rua no Nominatim (OpenStreetMap) e
testa o ponto retornado contra os 46 poligonos de zona que ja temos
(frontend/public/data/zonas.json).

NAO cria codigo nenhum nem mexe no sistema -- so gera um documento de
referencia (JSON + TXT) com a sugestao de bairro por via, organizado em
ordem alfabetica de bairro e depois de via, numerado sequencialmente (pro
usuario revisar e decidir os codigos novos por fora do sistema).

Uso:
    python python/sugerir_bairro_vias_sem_codigo.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from linhas_por_bairro import carregar_zonas, bairro_do_ponto

ROOT = Path(__file__).resolve().parents[1]
VIAS_PATH = ROOT / "data" / "json" / "vias_por_bairro.json"
SAIDA_JSON = ROOT / "data" / "relatorios" / "vias_sem_codigo_bairro_sugerido.json"
SAIDA_TXT = ROOT / "data" / "relatorios" / "vias_sem_codigo_bairro_sugerido.txt"

NOMINATIM = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "MicroSaaS-Linhas-DMTT/1.0 (uso interno DMTT Maceio)"}


def buscar_ponto_da_rua(nome_via: str):
    params = {
        "q": f"{nome_via}, Maceió, AL, Brasil",
        "format": "geojson",
        "limit": 5,
        "countrycodes": "br",
    }
    url = f"{NOMINATIM}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None, None

    for f in data.get("features", []):
        geom = f["geometry"]
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            return lat, lon, f["properties"].get("addresstype")
        if geom["type"] == "LineString":
            coords = geom["coordinates"]
            meio = coords[len(coords) // 2]
            lon, lat = meio
            return lat, lon, f["properties"].get("addresstype")
        if geom["type"] == "MultiLineString":
            primeiro = geom["coordinates"][0]
            meio = primeiro[len(primeiro) // 2]
            lon, lat = meio
            return lat, lon, f["properties"].get("addresstype")
    return None, None, None


def main():
    dados = json.loads(VIAS_PATH.read_text(encoding="utf-8"))
    sem_codigo = sorted(v["via"] for v in dados.get("SEM CODIGO", []))
    zonas = carregar_zonas()

    resultados = []
    for i, via in enumerate(sem_codigo, 1):
        r = buscar_ponto_da_rua(via)
        if r is None or r[0] is None:
            resultados.append({"via": via, "bairro_sugerido": None, "confianca": "SEM_RESULTADO"})
            print(f"[{i}/{len(sem_codigo)}] {via} -> sem resultado no Nominatim")
        else:
            lat, lon, addresstype = r
            bairro = bairro_do_ponto(lat, lon, zonas)
            confianca = "OK" if bairro != "FORA DAS ZONAS" else "FORA_DAS_ZONAS"
            resultados.append({"via": via, "bairro_sugerido": bairro, "confianca": confianca, "addresstype": addresstype})
            print(f"[{i}/{len(sem_codigo)}] {via} -> {bairro} ({confianca})")
        time.sleep(1.1)

    # organiza: bairro (alfabetico) -> vias (alfabetico), numeracao sequencial
    com_bairro = [r for r in resultados if r["confianca"] == "OK"]
    sem_bairro = [r for r in resultados if r["confianca"] != "OK"]

    por_bairro = {}
    for r in com_bairro:
        por_bairro.setdefault(r["bairro_sugerido"], []).append(r["via"])

    saida = {"bairros": {}, "precisa_revisar": sorted(r["via"] for r in sem_bairro)}
    contador = 1
    for bairro in sorted(por_bairro.keys()):
        vias_ordenadas = sorted(por_bairro[bairro])
        entradas = []
        for via in vias_ordenadas:
            entradas.append({"codigo_proposto": f"{contador:04d}", "via": via})
            contador += 1
        saida["bairros"][bairro] = entradas

    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_JSON.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    linhas_txt = [
        "Sugestao automatica de bairro para vias sem codigo DMTT",
        "=" * 78,
        "",
        "Bairro sugerido via geocodificacao (Nominatim/OSM) + zonas -- CONFERIR",
        "antes de aceitar, especialmente nomes de rua genericos (ex.: 'Rua A').",
        "",
    ]
    for bairro, entradas in saida["bairros"].items():
        linhas_txt.append(f"--- {bairro} ({len(entradas)}) ---")
        for e in entradas:
            linhas_txt.append(f"  {e['codigo_proposto']}  {e['via']}")
        linhas_txt.append("")

    linhas_txt.append("=" * 78)
    linhas_txt.append(f"PRECISA REVISAR MANUALMENTE -- sem resultado ou fora de qualquer zona ({len(saida['precisa_revisar'])})")
    linhas_txt.append("=" * 78)
    for via in saida["precisa_revisar"]:
        linhas_txt.append(f"  - {via}")

    SAIDA_TXT.write_text("\n".join(linhas_txt), encoding="utf-8")

    print()
    print(f"[OK] {SAIDA_JSON.relative_to(ROOT)}")
    print(f"[OK] {SAIDA_TXT.relative_to(ROOT)}")
    print(f"Com bairro sugerido: {len(com_bairro)} | Precisa revisar: {len(sem_bairro)}")


if __name__ == "__main__":
    main()
