"""
Extrai o indice global de vias do Matrix (codigo -> nome da via) do PDF
data/pdf-intinerarios-por-via-todas-linhas/sre_relatorio_via_logradouro-codigo-das-ruas.pdf
e grava data/json/bairros/matrix-codigos.json.

`via` = nome com abreviacoes expandidas; `via_original` = como esta no Matrix.
Iniciais de nome (J., B., M....) e abreviacoes de sobrenome (SAMP., OLIV....) ficam como
estao: nao da pra expandir sem adivinhar.

Uso:
    python python/extrair_codigos_matrix.py
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "pdf-intinerarios-por-via-todas-linhas" / "sre_relatorio_via_logradouro-codigo-das-ruas.pdf"
OUT = ROOT / "data" / "json" / "bairros" / "matrix-codigos.json"

# abreviacao (sem ponto) -> forma por extenso. So vale quando a palavra termina em ponto
# (ou, para o 1o termo do nome, as marcadas em INICIO_SEM_PONTO).
ABREV = {
    "AV": "AVENIDA", "R": "RUA", "TRAV": "TRAVESSA", "PÇA": "PRAÇA", "PCA": "PRAÇA", "LAD": "LADEIRA",
    "ESTR": "ESTRADA", "EST": "ESTRADA", "AL": "ALAMEDA", "TERM": "TERMINAL", "CONJ": "CONJUNTO",
    "CJ": "CONJUNTO", "LOT": "LOTEAMENTO", "QD": "QUADRA", "COND": "CONDOMÍNIO", "HOSP": "HOSPITAL",
    "JD": "JARDIM", "RES": "RESIDENCIAL", "INDL": "INDUSTRIAL", "STO": "SANTO", "STA": "SANTA",
    "STº": "SANTO", "DRA": "DOUTORA", "DR": "DOUTOR", "PROF": "PROFESSOR", "GOV": "GOVERNADOR",
    "DEP": "DEPUTADO", "CEL": "CORONEL", "VER": "VEREADOR", "ENG": "ENGENHEIRO", "JORN": "JORNALISTA",
    "MAJ": "MAJOR", "SEN": "SENADOR", "COM": "COMENDADOR", "DESEMB": "DESEMBARGADOR",
    "DES": "DESEMBARGADOR", "PREF": "PREFEITO", "GEN": "GENERAL", "GAL": "GENERAL", "EMP": "EMPRESÁRIO",
    "TEN": "TENENTE", "PRES": "PRESIDENTE", "SARG": "SARGENTO", "CONS": "CONSELHEIRO", "ESC": "ESCRITOR",
    "MAL": "MARECHAL", "PRESID": "PRESIDENTE", "ALAM": "ALAMEDA", "JARD": "JARDIM", "CID": "CIDADE",
    "DEL": "DELEGADO",
}
INICIO_SEM_PONTO = {"AV", "R", "TRAV", "LAD", "TERM", "CONJ", "AL"}

RE_PALAVRA_PONTO = re.compile(r"(?<![\wÀ-Ú])([A-ZÀ-Ú]{1,6}º?)\.(?=\s|[A-ZÀ-Ú]|$)")
RE_TI = re.compile(r"(?<![\wÀ-Ú])T\.I\.?(?=\s|[A-ZÀ-Ú]|$)")
RE_INICIO = re.compile(r"^([A-ZÀ-Ú]{1,6})\s+")


def expandir(nome: str) -> str:
    n = re.sub(r"\s+", " ", nome).strip()
    n = RE_TI.sub("TERMINAL INTEGRADO ", n)

    def troca(m):
        forma = ABREV.get(m.group(1))
        return forma + " " if forma else m.group(0)

    n = RE_PALAVRA_PONTO.sub(troca, n)
    m = RE_INICIO.match(n)
    if m and m.group(1) in INICIO_SEM_PONTO:
        n = ABREV[m.group(1)] + " " + n[m.end():]
    return re.sub(r"\s+", " ", n).strip()


RE_LINHA = re.compile(r"^(\d{5})\s+(.+?)\s+\d{4}\s+\d{2,4}$")
RE_TOTAL = re.compile(r"TOTAL:\s*([\d.]+)")


def main():
    vias, total_pdf = [], None
    with pdfplumber.open(PDF) as pdf:
        for pg in pdf.pages:
            for l in (pg.extract_text() or "").split("\n"):
                m = RE_LINHA.match(l.strip())
                if m:
                    orig = m.group(2).strip()
                    vias.append({"codigo": m.group(1), "via": expandir(orig), "via_original": orig})
                t = RE_TOTAL.search(l)
                if t:
                    total_pdf = int(t.group(1).replace(".", ""))
    cods = [v["codigo"] for v in vias]
    print(f"{len(vias)} codigos extraidos (TOTAL no PDF: {total_pdf}), {len(set(cods))} unicos")
    OUT.write_text(json.dumps({"fonte": PDF.name, "total": len(vias), "total_pdf": total_pdf, "vias": vias},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
