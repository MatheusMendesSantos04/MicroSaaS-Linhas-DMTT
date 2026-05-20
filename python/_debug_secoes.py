import pdfplumber, re
from pathlib import Path

pdf_path = Path(r"I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT\data\listagem-de-pontos-faltantes\0001.pdf")

todos_words = []
y_offset = 0
with pdfplumber.open(str(pdf_path)) as pdf:
    for page in pdf.pages:
        for w in (page.extract_words() or []):
            todos_words.append({**w, "top": w["top"] + y_offset})
        y_offset += page.height

def agrupar_por_linha(words, tolerancia=4):
    linhas = {}
    for w in words:
        y = round(w["top"] / tolerancia) * tolerancia
        linhas.setdefault(y, []).append(w)
    return [sorted(v, key=lambda w: w["x0"]) for _, v in sorted(linhas.items())]

linhas = agrupar_por_linha(todos_words)
for lw in linhas:
    texto = " ".join(w["text"] for w in lw)
    y = lw[0]["top"]
    if any(k in texto for k in ["Atendimento", "Principal", "Ativo", "Nome Ida", "Nome Volta", "Nome Nome"]):
        print(f"  y={y:.0f}: {texto[:120]}")
