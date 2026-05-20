import pdfplumber, re
from pathlib import Path

pdf_path = Path(r"I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT\data\listagem-de-pontos-faltantes\0036.pdf")

todos_words = []
y_offset = 0.0
with pdfplumber.open(str(pdf_path)) as pdf:
    for page in pdf.pages:
        for w in (page.extract_words() or []):
            todos_words.append({**w, "top": w["top"] + y_offset})
        y_offset += float(page.height)

def agrupar(words, tolerancia=5):
    grupos = {}
    for w in words:
        chave = round(w["top"] / tolerancia) * tolerancia
        grupos.setdefault(chave, []).append(w)
    return [sorted(v, key=lambda x: x["x0"]) for _, v in sorted(grupos.items())]

linhas = agrupar(todos_words)
# Mostrar todos os blocos Atendimento (cabeçalho) com as 6 linhas seguintes
count = 0
for i, lw in enumerate(linhas):
    texto = " ".join(w["text"] for w in lw)
    if "Atendimento" in texto and "Operacional" not in texto and "Cadastro" not in texto:
        count += 1
        print(f"\n=== BLOCO {count} ===")
        for j in range(min(8, len(linhas) - i)):
            t = " ".join(w["text"] for w in linhas[i+j])
            print(f"  {t[:100]}")
            if "Nome Abrev" in t or ("Nome" in t and "Ordem" in t):
                break
print(f"\nTotal blocos Atendimento: {count}")
