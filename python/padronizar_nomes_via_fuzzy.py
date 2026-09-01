"""
Segunda passada de padronizacao de dados_unificados.json.

TIER 1 (aplica automaticamente, risco zero): vias cuja unica diferenca e
acento/caixa/pontuacao -- normalizadas ficam identicas. Ex.: "RUA DO CEARA"
e "RUA DO CEARÁ" sao garantidamente a mesma rua.

TIER 2 (so relatorio, NAO aplica): vias parecidas mas com diferenca real de
caracteres (typo, complemento de nome) -- comparar por similaridade de texto
aqui e perigoso, porque nomes proprios curtos e diferentes (ex.: "OTACÍLIO
DE JESUS" x "TARCÍSIO DE JESUS") tem pontuacao de similaridade tao alta
quanto erros de digitacao genuinos. Gera lista de candidatos ordenada por
confianca pra revisao manual -- NAO junta nada sozinho.

Faz backup antes de escrever (so por causa do TIER 1).

Uso:
    python python/padronizar_nomes_via_fuzzy.py
"""
import json
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DU_PATH = ROOT / "data" / "json" / "dados_unificados.json"
RELATORIO_PATH = ROOT / "data" / "relatorios" / "vias_candidatas_duplicata.txt"

LIMIAR_RELATORIO = 0.82

NUM_POR_EXTENSO = {
    "UM", "DOIS", "TRES", "TRÊS", "QUATRO", "CINCO", "SEIS", "SETE", "OITO", "NOVE", "DEZ",
    "ONZE", "DOZE", "TREZE", "QUATORZE", "CATORZE", "QUINZE", "DEZESSEIS", "DEZESSETE",
    "DEZOITO", "DEZENOVE", "VINTE",
}
ROMANOS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}
LETRAS_ISOLADAS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def norm_chave(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens_distintivos(norm: str) -> set:
    palavras = norm.split()
    out = set()
    for p in palavras:
        if p.isdigit():
            out.add(("num", p))
        elif p in NUM_POR_EXTENSO:
            out.add(("extenso", p))
        elif p in ROMANOS:
            out.add(("romano", p))
        elif len(p) == 1 and p in LETRAS_ISOLADAS:
            out.add(("letra", p))
    return out


def pontuacao_qualidade(s: str) -> tuple:
    acentos = sum(1 for c in s if unicodedata.normalize("NFKD", c) != c)
    return (acentos, len(s))


def main():
    du = json.loads(DU_PATH.read_text(encoding="utf-8"))

    ocorrencias: dict[str, int] = defaultdict(int)
    for linha, dados in du.items():
        for sentido in ["ida", "volta"]:
            for r in dados.get(sentido, {}).get("ruas", []):
                via = r.get("via", "")
                if via:
                    ocorrencias[via] += 1

    todas_vias = list(ocorrencias.keys())

    # TIER 1: agrupa por norm_chave identica (so acento/caixa/pontuacao mudam)
    por_norm: dict[str, list[str]] = defaultdict(list)
    for v in todas_vias:
        por_norm[norm_chave(v)].append(v)

    canonico: dict[str, str] = {}
    tier1_grupos = []
    for norm, variantes in por_norm.items():
        if len(variantes) > 1:
            melhor = max(variantes, key=pontuacao_qualidade)
            tier1_grupos.append((melhor, [v for v in variantes if v != melhor]))
            for v in variantes:
                if v != melhor:
                    canonico[v] = melhor

    alteracoes = 0
    if canonico:
        for linha, dados in du.items():
            for sentido in ["ida", "volta"]:
                for r in dados.get(sentido, {}).get("ruas", []):
                    via = r.get("via", "")
                    if via in canonico:
                        r["via"] = canonico[via]
                        alteracoes += 1

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = DU_PATH.with_suffix(f".{ts}.bak.json")
        shutil.copy(DU_PATH, bak)
        DU_PATH.write_text(json.dumps(du, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Backup: {bak.name}\n")

    print(f"TIER 1 -- grafias so-acento unificadas automaticamente ({len(tier1_grupos)} grupos, {alteracoes} entradas alteradas):")
    for melhor, variantes in tier1_grupos:
        print(f"  -> {melhor!r}")
        for v in variantes:
            print(f"       era: {v!r}")

    # TIER 2: candidatos por similaridade -- so relatorio
    restantes = sorted({canonico.get(v, v) for v in todas_vias})
    pares_candidatos = []
    n = len(restantes)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = restantes[i], restantes[j]
            na, nb = norm_chave(a), norm_chave(b)
            if tokens_distintivos(na) != tokens_distintivos(nb):
                continue
            score = SequenceMatcher(None, na, nb).ratio()
            if score >= LIMIAR_RELATORIO:
                pares_candidatos.append((score, a, b))

    pares_candidatos.sort(key=lambda x: -x[0])

    linhas_relatorio = [
        "Candidatos a duplicata em dados_unificados.json (pra revisao manual)",
        "=" * 78,
        "",
        "Estas vias tem texto parecido mas NAO foram unificadas automaticamente",
        "-- podem ser a mesma rua com erro de digitacao, ou ruas DIFERENTES com",
        "nomes parecidos (cuidado especial com nomes proprios curtos).",
        "",
        "Se confirmar que sao a mesma rua, edite manualmente em",
        "data/json/intinerario manual/itinerario_completo.json pra usar sempre",
        "a mesma grafia, e rode de novo:",
        "  python python/mesclar_itinerarios.py",
        "  python python/aplicar_itinerarios_mesclado.py",
        "",
    ]
    for score, a, b in pares_candidatos:
        linhas_relatorio.append(f"[{score:.2f}]")
        linhas_relatorio.append(f"  {a}")
        linhas_relatorio.append(f"  {b}")
        linhas_relatorio.append("")

    RELATORIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_PATH.write_text("\n".join(linhas_relatorio), encoding="utf-8")

    print(f"\n[OK] {RELATORIO_PATH.relative_to(ROOT)} -- {len(pares_candidatos)} pares candidatos pra revisao manual")
    print(f"\nProximo passo: python python/gerar_dados_estaticos.py")


if __name__ == "__main__":
    main()
