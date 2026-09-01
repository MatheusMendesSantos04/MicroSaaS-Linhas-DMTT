"""
Pra cada linha do sistema, descobre quais bairros (zonas que criamos em
frontend/public/data/zonas.json) o tracado atravessa, e em que porcentagem
-- testando cada ponto GPS (ida+volta) contra os poligonos das zonas
(point-in-polygon, ray casting, sem dependencia externa).

So cobre os bairros que tem zona desenhada (46 dos 53 oficiais -- ver sessao
anterior sobre zonas). Pontos fora de qualquer zona (bairros sem poligono,
ou fora de Maceio mesmo, tipo Rio Largo/Satuba) contam como "FORA DAS ZONAS".

Saida:
    data/relatorios/linhas_por_bairro.txt

Uso:
    python python/linhas_por_bairro.py [codigo_da_linha]
    (sem argumento: todas as linhas)
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]


def chave_ordenacao(nome_linha: str):
    m = re.match(r"^(\d+)", nome_linha.strip())
    return (int(m.group(1)) if m else 999999, nome_linha)

ZONAS_PATH = ROOT / "frontend" / "public" / "data" / "zonas.json"
DU_PATH = ROOT / "data" / "json" / "dados_unificados.json"
SAIDA_PATH = ROOT / "data" / "relatorios" / "linhas_por_bairro.txt"


def ponto_no_poligono(lon: float, lat: float, poligono: list) -> bool:
    """ray casting -- poligono = lista de [lon, lat]"""
    dentro = False
    n = len(poligono)
    x, y = lon, lat
    x1, y1 = poligono[0]
    for i in range(1, n + 1):
        x2, y2 = poligono[i % n]
        if y > min(y1, y2):
            if y <= max(y1, y2):
                if x <= max(x1, x2):
                    if y1 != y2:
                        xinters = (y - y1) * (x2 - x1) / (y2 - y1) + x1
                    if x1 == x2 or x <= xinters:
                        dentro = not dentro
        x1, y1 = x2, y2
    return dentro


def carregar_zonas():
    dados = json.loads(ZONAS_PATH.read_text(encoding="utf-8"))
    zonas = []
    for f in dados["features"]:
        nome = f["properties"]["nome"]
        coords = f["geometry"]["coordinates"][0]  # anel externo
        zonas.append((nome, coords))
    return zonas


def bairro_do_ponto(lat: float, lon: float, zonas: list) -> str:
    for nome, poligono in zonas:
        if ponto_no_poligono(lon, lat, poligono):
            return nome
    return "FORA DAS ZONAS"


def analisar_linha(nome_linha: str, dados: dict, zonas: list):
    pontos = dados.get("ida", {}).get("coordenadas", []) + dados.get("volta", {}).get("coordenadas", [])
    if not pontos:
        return None
    contagem = defaultdict(int)
    for lat, lon in pontos:
        contagem[bairro_do_ponto(lat, lon, zonas)] += 1
    total = len(pontos)
    percentuais = sorted(
        ((bairro, qtd, 100 * qtd / total) for bairro, qtd in contagem.items()),
        key=lambda x: -x[2],
    )
    return percentuais, total


def formatar_linha(nome_linha: str, percentuais, total: int) -> list:
    linhas = [nome_linha, "-" * len(nome_linha)]
    for bairro, qtd, pct in percentuais:
        linhas.append(f"  {pct:5.1f}%  {bairro}  ({qtd}/{total} pontos)")
    linhas.append("")
    return linhas


def main():
    zonas = carregar_zonas()
    du = json.loads(DU_PATH.read_text(encoding="utf-8"))

    filtro = sys.argv[1] if len(sys.argv) > 1 else None

    saida = []
    for nome_linha in sorted(du.keys(), key=chave_ordenacao):
        dados = du[nome_linha]
        if filtro and not nome_linha.startswith(filtro):
            continue
        resultado = analisar_linha(nome_linha, dados, zonas)
        if resultado is None:
            continue
        percentuais, total = resultado
        bloco = formatar_linha(nome_linha, percentuais, total)
        saida.extend(bloco)
        if filtro:
            print("\n".join(bloco))

    if not filtro:
        SAIDA_PATH.parent.mkdir(parents=True, exist_ok=True)
        SAIDA_PATH.write_text("\n".join(saida), encoding="utf-8")
        print(f"[OK] {SAIDA_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
