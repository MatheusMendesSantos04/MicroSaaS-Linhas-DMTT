"""
Para cada uma das 180 vias sem match, busca as candidatas mais parecidas
no itinerario_completo.json e exibe lado a lado.

Usa dois critérios combinados:
  - SequenceMatcher (semelhança de caracteres)
  - Jaccard de tokens (palavras em comum)

Saída: data/json/novos_trajetos/relatorio_variantes_vias.txt

Uso:
    python python/gerar_relatorio_variantes_vias.py
"""

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
NOVOS_F  = BASE_DIR / "data" / "json" / "novos_trajetos" / "intinerario-vias-novos.json"
REF_F    = BASE_DIR / "data" / "json" / "intinerario manual" / "itinerario_completo.json"
SAIDA    = BASE_DIR / "data" / "json" / "novos_trajetos" / "relatorio_variantes_vias.txt"

ABREVIACOES = [
    (r"\bAV\.\s+",      "AVENIDA "),
    (r"\bR\.\s+",       "RUA "),
    (r"\bLAD\.\s+",     "LADEIRA "),
    (r"\bP[CÇ]A?\.\s+", "PRACA "),
    (r"\bTV\.\s+",      "TRAVESSA "),
    (r"\bTRAV\.\s+",    "TRAVESSA "),
    (r"\bDR\.\s+",      "DOUTOR "),
    (r"\bPROF\.\s+",    "PROFESSOR "),
    (r"\bDEP\.\s+",     "DEPUTADO "),
    (r"\bENG\.\s+",     "ENGENHEIRO "),
    (r"\bJORN\.\s+",    "JORNALISTA "),
    (r"\bGOV\.\s+",     "GOVERNADOR "),
    (r"\bGAL\.\s+",     "GENERAL "),
    (r"\bGEN\.\s+",     "GENERAL "),
    (r"\bCEL\.\s+",     "CORONEL "),
    (r"\bCAP\.\s+",     "CAPITAO "),
    (r"\bTERM\.\s+",    "TERMINAL "),
    (r"\bDESEMB\.\s+",  "DESEMBARGADOR "),
    (r"\bDES\.\s+",     "DESEMBARGADOR "),
    (r"\bVER\.\s+",     "VEREADOR "),
    (r"\bSEN\.\s+",     "SENADOR "),
    (r"\bSTA\.\s+",     "SANTA "),
    (r"\bSTO\.\s+",     "SANTO "),
    (r"\bCJ\.\s+",      "CONJUNTO "),
    (r"\bCONJ\.\s+",    "CONJUNTO "),
]

STOPWORDS = {"DE", "DA", "DO", "DAS", "DOS", "E", "A", "O", "AS", "OS"}


def normalizar(txt: str) -> str:
    txt = txt.upper().strip()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"[^A-Z0-9 ]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def expandir(txt: str) -> str:
    for padrao, sub in ABREVIACOES:
        txt = re.sub(padrao, sub, txt, flags=re.IGNORECASE)
    return normalizar(txt)


def tokens(txt: str) -> set[str]:
    return {w for w in txt.split() if w not in STOPWORDS and len(w) > 2}


def score(a: str, b: str) -> float:
    seq = SequenceMatcher(None, a, b).ratio()
    ta, tb = tokens(a), tokens(b)
    union = ta | tb
    jac = len(ta & tb) / len(union) if union else 0.0
    return 0.5 * seq + 0.5 * jac


# --- carrega arquivos ---
novos    = json.loads(NOVOS_F.read_text(encoding="utf-8"))
completo = json.loads(REF_F.read_text(encoding="utf-8"))

# conjunto de referência (normalizado → original)
ref_norm: dict[str, str] = {}
for linha, dados in completo.items():
    for sentido in ["ida", "volta"]:
        for via in dados.get(sentido, []):
            if isinstance(via, str):
                ref_norm[normalizar(via)] = via

ref_keys = list(ref_norm.keys())

# vias do novo com contexto
via_contextos: dict[str, list[str]] = {}
for linha, dados in novos.items():
    cod = linha.split(" - ")[0].strip() if " - " in linha else linha
    for sentido in ["ida", "volta"]:
        for via in dados.get(sentido, []):
            if isinstance(via, str):
                v = via.strip()
                via_contextos.setdefault(v, []).append(f"{cod}/{sentido.upper()}")

# identifica as 180 "novas" (sem match exato nem expansão simples)
sem_match: list[str] = []
for via_orig in via_contextos:
    norm = normalizar(via_orig)
    if norm in ref_norm:
        continue
    exp = expandir(via_orig)
    if normalizar(exp) in ref_norm:
        continue
    sem_match.append(via_orig)

sem_match.sort()

# --- calcula candidatas para cada via sem match ---
LIMITE_SCORE  = 0.50   # só mostra se score >= 50 %
MAX_CANDIDATAS = 3

resultados: list[dict] = []

for via_orig in sem_match:
    norm_orig = normalizar(expandir(via_orig))
    candidatas = []
    for rk in ref_keys:
        s = score(norm_orig, rk)
        if s >= LIMITE_SCORE:
            candidatas.append((s, ref_norm[rk], rk))
    candidatas.sort(reverse=True)
    candidatas = candidatas[:MAX_CANDIDATAS]
    resultados.append({
        "via":        via_orig,
        "contextos":  via_contextos[via_orig],
        "candidatas": candidatas,
    })

com_candidatas    = [r for r in resultados if r["candidatas"]]
sem_candidatas    = [r for r in resultados if not r["candidatas"]]

# --- relatório ---
with SAIDA.open("w", encoding="utf-8") as f:

    def w(linha=""):
        f.write(linha + "\n")

    w("=" * 90)
    w("RELATÓRIO — VARIANTES DE NOME (180 vias sem match direto)")
    w("=" * 90)
    w()
    w(f"  Vias sem match : {len(sem_match)}")
    w(f"  Com candidata  : {len(com_candidatas)}  (score >= {int(LIMITE_SCORE*100)}%)")
    w(f"  Sem candidata  : {len(sem_candidatas)}  (provavelmente vias genuinamente novas)")
    w()

    # --- COM CANDIDATAS ---
    w("=" * 90)
    w(f"[ A. POSSÍVEIS VARIANTES ]  {len(com_candidatas)} vias")
    w("  Verifique se o nome do arquivo novo é o mesmo que a referência.")
    w("  Score = 100% → muito provável que seja a mesma rua.")
    w("-" * 90)
    w()

    for r in com_candidatas:
        ctx = ", ".join(r["contextos"][:4]) + ("..." if len(r["contextos"]) > 4 else "")
        w(f"  NOVO: {r['via']}")
        w(f"  [{ctx}]")
        for s, nome_ref, _ in r["candidatas"]:
            w(f"    {int(s*100):>3}%  REF: {nome_ref}")
        w()

    # --- SEM CANDIDATAS ---
    w("=" * 90)
    w(f"[ B. VIAS NOVAS (sem candidata na referência) ]  {len(sem_candidatas)} vias")
    w("  Estas são provavelmente ruas de fato novas no sistema.")
    w("-" * 90)
    w()
    for r in sem_candidatas:
        ctx = ", ".join(r["contextos"][:4]) + ("..." if len(r["contextos"]) > 4 else "")
        w(f"  {r['via']}")
        w(f"    [{ctx}]")
    w()

    w("-" * 90)
    w("Gerado por python/gerar_relatorio_variantes_vias.py")

print(f"[OK] {SAIDA}")
print(f"  Com candidata : {len(com_candidatas)}")
print(f"  Sem candidata : {len(sem_candidatas)}")
