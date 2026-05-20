import pdfplumber

with pdfplumber.open(r'I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT\data\listagem-de-pontos-faltantes\0001.pdf') as pdf:
    page = pdf.pages[1]
    words = page.extract_words()
    for w in words[:60]:
        print(f"  x={w['x0']:.0f}  y={w['top']:.0f}  [{w['text']}]")
