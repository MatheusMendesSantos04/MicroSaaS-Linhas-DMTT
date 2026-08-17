"""
Aplica o itinerario_mesclado.json (manual revisado + sistema, abreviacoes
expandidas) em data/json/dados_unificados.json -- SOMENTE para linhas cuja
entrada no sistema esteja com "ruas" vazia em ida E volta (nao sobrescreve
linhas que ja tem itinerario com codigo DMTT por rua).

Cada rua aplicada entra como {"via": <nome>, "codigo": null, "match": "manual"}
-- sem codigo de via (o mesclado so tem o nome da rua), marcada como origem
manual pra distinguir de "exato"/"fuzzy"/"sem_match" do pipeline automatico.

Faz backup do dados_unificados.json antes de escrever.

Uso:
    python python/aplicar_itinerarios_mesclado.py
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sincronizar_mapa_reconstruido import normalizar_codigo

ROOT = Path(__file__).resolve().parents[1]
MESCLADO_PATH = ROOT / "data" / "json" / "intinerario manual" / "itinerario_mesclado.json"
SISTEMA_PATH = ROOT / "data" / "json" / "dados_unificados.json"

sys.stdout.reconfigure(encoding="utf-8")

# codigos com mais de uma entrada no sistema (duplicatas conhecidas) ou que
# exigem decisao estrutural (0112 tem 2 variantes no manual, 1 so no sistema)
# -- ficam de fora da aplicacao automatica.
PULAR_CODIGOS = {"0112"}


def para_ruas(lista_nomes: list[str]) -> list[dict]:
    return [{"via": nome, "codigo": None, "match": "manual"} for nome in lista_nomes]


def main():
    mesclado = json.loads(MESCLADO_PATH.read_text(encoding="utf-8"))
    sistema = json.loads(SISTEMA_PATH.read_text(encoding="utf-8"))

    sistema_por_cod = {}
    for nome in sistema:
        c = normalizar_codigo(nome)
        if c:
            sistema_por_cod.setdefault(c, []).append(nome)

    aplicadas, puladas_ja_cheias, puladas_manual = [], [], []

    for nome_m, dados_m in mesclado.items():
        cod = normalizar_codigo(nome_m)
        if not cod or not dados_m.get("ida") or not dados_m.get("volta"):
            continue
        if cod in PULAR_CODIGOS:
            puladas_manual.append((cod, nome_m))
            continue

        chaves_sistema = sistema_por_cod.get(cod, [])
        chaves_vazias = [
            k for k in chaves_sistema
            if not sistema[k].get("ida", {}).get("ruas") and not sistema[k].get("volta", {}).get("ruas")
        ]
        if not chaves_vazias:
            continue  # ou nao existe no sistema, ou ja tem dado -- nao mexe

        for chave in chaves_vazias:
            sistema[chave]["ida"]["ruas"] = para_ruas(dados_m["ida"])
            sistema[chave]["volta"]["ruas"] = para_ruas(dados_m["volta"])
            aplicadas.append((cod, chave, len(dados_m["ida"]), len(dados_m["volta"])))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = SISTEMA_PATH.with_suffix(f".{ts}.bak.json")
    shutil.copy(SISTEMA_PATH, bak)
    SISTEMA_PATH.write_text(json.dumps(sistema, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Backup: {bak.name}\n")
    print(f"Aplicadas ({len(aplicadas)}):")
    for cod, chave, n_ida, n_volta in aplicadas:
        print(f"  {cod:<8} {chave:<55} ida={n_ida} volta={n_volta}")

    if puladas_manual:
        print(f"\nPuladas (decisao manual necessaria) ({len(puladas_manual)}):")
        for cod, nome in puladas_manual:
            print(f"  {cod:<8} {nome}")

    print(f"\nProximo passo: python python/gerar_dados_estaticos.py")


if __name__ == "__main__":
    main()
