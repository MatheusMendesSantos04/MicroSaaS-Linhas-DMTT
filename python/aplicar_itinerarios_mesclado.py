"""
Aplica o itinerario_mesclado.json (manual revisado + sistema, abreviacoes
expandidas) em data/json/dados_unificados.json -- para TODAS as linhas com
correspondencia de codigo, nao so as vazias.

Pra cada rua do manual, tenta preservar o codigo DMTT + match ("exato"/
"fuzzy"/"sem_match") que a rua ja tinha no sistema: compara nomes
normalizados (maiusculo, sem acento, sem pontuacao) contra as ruas
atualmente cadastradas naquela linha/sentido. Se bater, reusa codigo+match;
se nao bater (rua nova ou reescrita), entra como
{"via": <nome>, "codigo": null, "match": "manual"}.

Faz backup do dados_unificados.json antes de escrever.

Uso:
    python python/aplicar_itinerarios_mesclado.py
"""
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sincronizar_mapa_reconstruido import normalizar_codigo

ROOT = Path(__file__).resolve().parents[1]
MESCLADO_PATH = ROOT / "data" / "json" / "intinerario manual" / "itinerario_mesclado.json"
SISTEMA_PATH = ROOT / "data" / "json" / "dados_unificados.json"

sys.stdout.reconfigure(encoding="utf-8")

# codigos com mais de uma entrada no manual mas so uma no sistema (ou outro
# descompasso estrutural) -- exigem decisao humana, ficam de fora.
PULAR_CODIGOS = {"0112"}

# normalizar_codigo() tem uma ambiguidade conhecida (nao mexer nela -- outras
# partes do projeto dependem do comportamento atual pra resolver colisao de
# placemark do KML): quando o nome da linha tem uma abreviacao tipo "C DAS
# ALMAS" logo apos o codigo, sem separador, a letra "C" e lida como se fosse
# sufixo do codigo ("0209C" em vez de "0209"). Isso faz essas linhas ficarem
# invisiveis pro merge com o manual desde que a sincronizacao do KML renomeou
# a chave delas nesse formato abreviado. Correcao pontual so pra essas 3 --
# confirmado que NAO sao variantes reais tipo "0612-A" (essas continuam sem
# alias, ja que podem ser linhas de fato diferentes).
ALIAS_CODIGO_SISTEMA = {
    "0109C": "0109",
    "0209C": "0209",
    "0617C": "0617",
}


def norm_chave(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def montar_ruas(nomes_manual: list[str], ruas_sistema_atuais: list[dict]) -> list[dict]:
    """Pra cada nome do manual, reusa codigo/match da rua do sistema com o
    mesmo nome normalizado (se existir); senao entra como manual/sem codigo."""
    indice_sistema = {}
    for r in ruas_sistema_atuais:
        chave = norm_chave(r.get("via", ""))
        if chave and chave not in indice_sistema:
            indice_sistema[chave] = r

    ruas = []
    reaproveitadas = 0
    for nome in nomes_manual:
        existente = indice_sistema.get(norm_chave(nome))
        if existente:
            ruas.append({"via": nome, "codigo": existente.get("codigo"), "match": existente.get("match")})
            reaproveitadas += 1
        else:
            ruas.append({"via": nome, "codigo": None, "match": "manual"})
    return ruas, reaproveitadas


def main():
    mesclado = json.loads(MESCLADO_PATH.read_text(encoding="utf-8"))
    sistema = json.loads(SISTEMA_PATH.read_text(encoding="utf-8"))

    sistema_por_cod = {}
    for nome in sistema:
        c = normalizar_codigo(nome)
        c = ALIAS_CODIGO_SISTEMA.get(c, c)
        if c:
            sistema_por_cod.setdefault(c, []).append(nome)

    aplicadas, sem_mudanca, puladas_manual, sem_correspondencia = [], [], [], []

    for nome_m, dados_m in mesclado.items():
        cod = normalizar_codigo(nome_m)
        if not cod or not dados_m.get("ida") or not dados_m.get("volta"):
            continue
        if cod in PULAR_CODIGOS:
            puladas_manual.append((cod, nome_m))
            continue

        chaves_sistema = sistema_por_cod.get(cod, [])
        if not chaves_sistema:
            sem_correspondencia.append((cod, nome_m))
            continue

        for chave in chaves_sistema:
            ruas_ida_atuais = sistema[chave].get("ida", {}).get("ruas", [])
            ruas_volta_atuais = sistema[chave].get("volta", {}).get("ruas", [])

            ida_novas, reap_ida = montar_ruas(dados_m["ida"], ruas_ida_atuais)
            volta_novas, reap_volta = montar_ruas(dados_m["volta"], ruas_volta_atuais)

            nomes_ida_atuais = [r["via"] for r in ruas_ida_atuais]
            nomes_volta_atuais = [r["via"] for r in ruas_volta_atuais]
            if nomes_ida_atuais == dados_m["ida"] and nomes_volta_atuais == dados_m["volta"]:
                sem_mudanca.append((cod, chave))
                continue

            sistema[chave]["ida"]["ruas"] = ida_novas
            sistema[chave]["volta"]["ruas"] = volta_novas
            aplicadas.append((cod, chave, len(ida_novas), reap_ida, len(volta_novas), reap_volta))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = SISTEMA_PATH.with_suffix(f".{ts}.bak.json")
    shutil.copy(SISTEMA_PATH, bak)
    SISTEMA_PATH.write_text(json.dumps(sistema, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Backup: {bak.name}\n")
    print(f"Aplicadas / atualizadas ({len(aplicadas)}):")
    for cod, chave, n_ida, reap_ida, n_volta, reap_volta in aplicadas:
        print(f"  {cod:<8} {chave:<60} ida={n_ida} (codigo reaproveitado em {reap_ida})  volta={n_volta} (codigo reaproveitado em {reap_volta})")

    print(f"\nJa identicas, sem mudanca ({len(sem_mudanca)}):")
    for cod, chave in sem_mudanca:
        print(f"  {cod:<8} {chave}")

    if puladas_manual:
        print(f"\nPuladas (decisao manual necessaria) ({len(puladas_manual)}):")
        for cod, nome in puladas_manual:
            print(f"  {cod:<8} {nome}")

    if sem_correspondencia:
        print(f"\nSem correspondencia de codigo no sistema ({len(sem_correspondencia)}):")
        for cod, nome in sem_correspondencia:
            print(f"  {cod:<8} {nome}")

    print(f"\nProximo passo: python python/gerar_dados_estaticos.py")


if __name__ == "__main__":
    main()
