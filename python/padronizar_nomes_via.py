"""
Padroniza dados_unificados.json pra ter UMA UNICA grafia de via por codigo
DMTT -- hoje varias linhas escrevem a mesma rua (mesmo codigo) de jeitos
diferentes (com/sem acento, com/sem complemento entre parenteses), o que
gera duplicidade visual em qualquer relatorio que agrupe por bairro/codigo.

itinerario_completo.json (via itinerario_mesclado.json, ja com abreviacoes
expandidas) e a fonte de verdade oficial agora -- a grafia escolhida pra
cada codigo prioriza, nessa ordem:
  1. a grafia que bate (normalizada) com uma via do manual
  2. entre grafias que so diferem por acentuacao/caixa, a mais acentuada
  3. se sobra ambiguidade real (nomes diferentes de fato, nao so acento),
     NAO decide sozinho -- reporta pra revisao manual e deixa como esta

Faz backup do dados_unificados.json antes de escrever.

Uso:
    python python/padronizar_nomes_via.py
"""
import json
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DU_PATH = ROOT / "data" / "json" / "dados_unificados.json"
MESCLADO_PATH = ROOT / "data" / "json" / "intinerario manual" / "itinerario_mesclado.json"


def norm_chave(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def pontuacao_acento(s: str) -> int:
    """conta quantos caracteres acentuados/cedilha tem -- usado pra escolher
    a grafia 'mais correta' quando so muda acentuacao"""
    return sum(1 for c in s if unicodedata.normalize("NFKD", c) != c)


def main():
    du = json.loads(DU_PATH.read_text(encoding="utf-8"))
    mesclado = json.loads(MESCLADO_PATH.read_text(encoding="utf-8"))

    vias_manual_norm = set()
    for dados in mesclado.values():
        for nome in dados.get("ida", []) + dados.get("volta", []):
            vias_manual_norm.add(norm_chave(nome))

    por_codigo: dict[str, set] = defaultdict(set)
    for linha, dados in du.items():
        for sentido in ["ida", "volta"]:
            for r in dados.get(sentido, {}).get("ruas", []):
                if r.get("codigo"):
                    por_codigo[r["codigo"]].add(r["via"])

    canonico: dict[str, str] = {}
    pendentes: list[tuple[str, list[str]]] = []

    for cod, variantes in por_codigo.items():
        if len(variantes) == 1:
            continue
        variantes = sorted(variantes)

        # caso 1: bate com o manual
        candidatos_manual = [v for v in variantes if norm_chave(v) in vias_manual_norm]
        if len(candidatos_manual) == 1:
            canonico[cod] = candidatos_manual[0]
            continue

        # caso 2: so diferem por acentuacao (normalizado e igual pra todas)
        normalizadas = {norm_chave(v) for v in variantes}
        if len(normalizadas) == 1:
            canonico[cod] = max(variantes, key=pontuacao_acento)
            continue

        # caso 3: ambiguidade real -- nao decide
        pendentes.append((cod, variantes))

    # aplica a padronizacao
    alteracoes = 0
    for linha, dados in du.items():
        for sentido in ["ida", "volta"]:
            for r in dados.get(sentido, {}).get("ruas", []):
                cod = r.get("codigo")
                if cod in canonico and r["via"] != canonico[cod]:
                    r["via"] = canonico[cod]
                    alteracoes += 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = DU_PATH.with_suffix(f".{ts}.bak.json")
    shutil.copy(DU_PATH, bak)
    DU_PATH.write_text(json.dumps(du, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Backup: {bak.name}\n")
    print(f"Codigos padronizados: {len(canonico)}")
    print(f"Entradas de rua alteradas: {alteracoes}\n")

    if pendentes:
        print(f"PENDENTES -- ambiguidade real, precisa revisao manual ({len(pendentes)}):")
        for cod, variantes in pendentes:
            print(f"  {cod}:")
            for v in variantes:
                print(f"    - {v}")

    print(f"\nProximo passo: python python/gerar_dados_estaticos.py")


if __name__ == "__main__":
    main()
