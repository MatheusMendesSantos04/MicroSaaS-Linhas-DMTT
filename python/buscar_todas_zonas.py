"""
Busca no Nominatim o poligono de cada bairro oficial da DMTT (lista extraida do
relatorio "VIAS POR BAIRRO") e salva um .geojson por bairro em data/json/zonas/,
no mesmo formato ja usado pelas 4 zonas existentes (Ponta Verde, Jatiuca,
Pajucara, Mangabeiras).

Regra de escolha do resultado (evita pegar entidade errada com o mesmo nome,
como ja aconteceu com Pajucara vs. um estadio): busca com limit=8 e filtra
por addresstype == "suburb"; se nao achar suburb, tenta "neighbourhood" e por
ultimo "quarter". So aceita geometria Polygon/MultiPolygon.

Uso:
    python python/buscar_todas_zonas.py
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
ZONAS_DIR.mkdir(parents=True, exist_ok=True)

NOMINATIM = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "MicroSaaS-Linhas-DMTT/1.0 (uso interno DMTT Maceio)"}

BAIRROS = [
    "Alto da Alegria", "Antares", "Barro Duro", "Bebedouro", "Benedito Bentes",
    "Bom Parto", "Canaã", "Centro", "Chã da Jaqueira", "Chã de Bebedouro",
    "Cidade Universitária", "Clima Bom", "Cruz das Almas", "Farol", "Feitosa",
    "Fernão Velho", "Gama Lins", "Garça Torta", "Gruta de Lourdes", "Guaxuma",
    "Ipioca", "Jacarecica", "Jacintinho", "Jaraguá", "Jardim Petrópolis I",
    "Jardim Petrópolis II", "Jatiúca", "Levada", "Mangabeiras", "Mutange",
    "Ouro Preto", "Pajuçara", "Pescaria", "Pinheiro", "Pitanguinha", "Poço",
    "Ponta da Terra", "Ponta Grossa", "Ponta Verde", "Pontal da Barra", "Prado",
    "Riacho Doce", "Rio Novo", "Santa Amélia", "Santa Lúcia", "Santo Amaro",
    "Santos Dumont", "São Jorge", "Serraria", "Tabuleiro dos Martins",
    "Trapiche da Barra", "Vergel do Lago", "Village Campestre",
]

# nomes que o Nominatim nao reconhece com o sufixo I/II/etc -- tenta sem o sufixo
ALIAS_BUSCA = {
    "Jardim Petrópolis I": "Jardim Petrópolis",
    "Jardim Petrópolis II": "Jardim Petrópolis",
}

TIPOS_ACEITOS = ("suburb", "neighbourhood", "quarter")


def slug(nome: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return s.lower().replace(" ", "-")


def buscar(nome_query: str):
    params = {
        "q": f"{nome_query}, Maceió, AL, Brasil",
        "format": "geojson",
        "polygon_geojson": 1,
        "limit": 8,
        "countrycodes": "br",
    }
    url = f"{NOMINATIM}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("features", [])


def escolher_melhor(features):
    for tipo in TIPOS_ACEITOS:
        for f in features:
            if f["properties"].get("addresstype") == tipo and f["geometry"]["type"] in ("Polygon", "MultiPolygon"):
                return f
    return None


def main():
    sucesso, falhas = [], []
    for i, bairro in enumerate(BAIRROS):
        query = ALIAS_BUSCA.get(bairro, bairro)
        try:
            features = buscar(query)
            escolhido = escolher_melhor(features)
            if escolhido is None:
                tipos = [f["properties"].get("addresstype") for f in features]
                print(f"[FALHA] {bairro}: nenhum polygon suburb/neighbourhood/quarter (tipos vistos: {tipos})")
                falhas.append(bairro)
            else:
                escolhido["properties"]["name"] = bairro  # mantem o nome oficial da DMTT
                saida = {"type": "FeatureCollection", "features": [escolhido]}
                caminho = ZONAS_DIR / f"{slug(bairro)}.geojson"
                caminho.write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
                print(f"[OK] {bairro} -> {caminho.name} ({escolhido['properties'].get('addresstype')})")
                sucesso.append(bairro)
        except Exception as e:
            print(f"[ERRO] {bairro}: {e}")
            falhas.append(bairro)

        if i < len(BAIRROS) - 1:
            time.sleep(1.1)

    print(f"\nTotal: {len(sucesso)} ok, {len(falhas)} falha(s)")
    if falhas:
        print("Falharam:", falhas)


if __name__ == "__main__":
    main()
