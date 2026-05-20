"""
Extrai pontos de linhas dos PDFs em data/listagem-de-pontos-faltantes/.
Filtra apenas secoes onde Principal = Sim E Ativo = Sim.
Salva JSON em data/listagem-de-pontos-faltantes/pontos.json

Uso:
    python extrair_pontos_pdf.py
"""

import json
import re
from pathlib import Path

import pdfplumber

BASE_DIR = Path(__file__).resolve().parents[1]
PDF_DIR  = BASE_DIR / "data" / "listagem-de-pontos-faltantes"
SAIDA    = PDF_DIR / "pontos.json"

# Limites de coluna baseados na inspeção do PDF (posição X)
COL_ABREV_START = 100
COL_END_START   = 220
COL_END_MAX     = 600
COL_ORDEM_MAX   = 650
COL_VEL_MAX     = 710
COL_LAT_MAX     = 770


def agrupar_por_linha(words, tolerancia=5):
    """Agrupa words por posição Y com tolerância."""
    grupos = {}
    for w in words:
        chave = round(w["top"] / tolerancia) * tolerancia
        grupos.setdefault(chave, []).append(w)
    return [sorted(v, key=lambda x: x["x0"]) for _, v in sorted(grupos.items())]


def texto_coluna(words_linha, x_min, x_max):
    return " ".join(
        w["text"] for w in words_linha
        if w["x0"] >= x_min and w["x0"] < x_max
    ).strip()


def coord_para_float(valor: str) -> float:
    return float(valor.replace(",", "."))


def e_linha_ponto(lw) -> bool:
    """Verifica se a linha tem coordenadas no final (padrão de ponto)."""
    texto = " ".join(w["text"] for w in lw)
    return bool(re.search(r"-\d+,\d{4,}\s+-\d+,\d{4,}", texto))


def parsear_ponto(lw) -> dict:
    nome     = texto_coluna(lw, 0,                COL_ABREV_START)
    abrev    = texto_coluna(lw, COL_ABREV_START,  COL_END_START)
    endereco = texto_coluna(lw, COL_END_START,    COL_END_MAX)
    ordem_s  = texto_coluna(lw, COL_END_MAX,      COL_ORDEM_MAX)
    vel_s    = texto_coluna(lw, COL_ORDEM_MAX,    COL_VEL_MAX)
    lat_s    = texto_coluna(lw, COL_VEL_MAX,      COL_LAT_MAX)
    lon_s    = texto_coluna(lw, COL_LAT_MAX,      9999)

    def to_int(s):
        try: return int(float(s))
        except: return 0

    def to_float(s):
        try: return coord_para_float(s)
        except: return None

    return {
        "nome":        nome,
        "abreviatura": abrev,
        "endereco":    endereco,
        "ordem":       to_int(ordem_s),
        "vel_limite":  to_int(vel_s),
        "latitude":    to_float(lat_s),
        "longitude":   to_float(lon_s),
    }


def extrair_pdf(caminho: Path) -> list[dict]:
    codigo = caminho.stem

    todos_words = []
    y_offset = 0.0
    with pdfplumber.open(str(caminho)) as pdf:
        for page in pdf.pages:
            for w in (page.extract_words() or []):
                todos_words.append({**w, "top": w["top"] + y_offset})
            y_offset += float(page.height)

    linhas = agrupar_por_linha(todos_words)

    # ── Máquina de estados ──────────────────────────────────────────────────
    estado = "SEARCHING"
    cabecalho = {}
    header_texto_acumulado = []
    pontos_atual = []
    resultados = []

    def parsear_cabecalho_acumulado():
        # Procura em cada linha acumulada individualmente (mais preciso)
        for linha_txt in header_texto_acumulado:
            # Principal
            m = re.search(r"Atendimento\s+(Sim|N[aã]o)", linha_txt, re.I)
            if m: cabecalho["principal"] = m.group(1)
            m = re.search(r"Principal:\s*(Sim|N[aã]o)", linha_txt, re.I)
            if m: cabecalho["principal"] = m.group(1)
            # Ativo inline
            m = re.search(r"Ativo:\s*(Sim|N[aã]o)", linha_txt, re.I)
            if m: cabecalho["ativo"] = m.group(1)
            # Linha (nome da rota)
            m = re.search(r"Linha:\s*(.+?)(?:Nome Ida|Ativo|$)", linha_txt, re.I)
            if m and m.group(1).strip():
                cabecalho["linha"] = m.group(1).strip()
            # Fallback: nome após "Principal: Sim/Não ..." ou "Atendimento Sim/Não ..."
            if not cabecalho.get("linha"):
                m = re.search(r"(?:Principal:|Atendimento)\s*:?\s*(?:Sim|N[aã]o)\s+(.+)", linha_txt, re.I)
                if m and m.group(1).strip():
                    cabecalho["linha"] = m.group(1).strip()
            # Nome Ida
            m = re.search(r"Nome Ida:\s*(.+?)(?:Ativo|$)", linha_txt, re.I)
            if m: cabecalho["nome_ida"] = m.group(1).strip()
            # Nome Volta
            m = re.search(r"Nome Volta:\s*(.+?)$", linha_txt, re.I)
            if m: cabecalho["nome_volta"] = m.group(1).strip()

        # Ativo pode aparecer em linha isolada: uma linha que é só "Sim" ou "Não"
        # aparecendo DEPOIS de "Nome Ida" e ANTES de "Ativo:"
        if "ativo" not in cabecalho:
            for linha_txt in header_texto_acumulado:
                t = linha_txt.strip()
                if re.fullmatch(r"(Sim|N[aã]o)", t, re.I):
                    cabecalho["ativo"] = t
                    break

    def salvar_secao():
        if (cabecalho.get("principal", "").lower() == "sim"
                and cabecalho.get("ativo", "").lower() == "sim"
                and pontos_atual):
            resultados.append({
                "codigo":     codigo,
                "linha":      cabecalho.get("linha", ""),
                "nome_ida":   cabecalho.get("nome_ida", ""),
                "nome_volta": cabecalho.get("nome_volta", ""),
                "pontos":     list(pontos_atual),
            })

    for lw in linhas:
        texto = " ".join(w["text"] for w in lw)
        eh_rodape = "Operacional" in texto or "Cadastro" in texto

        # ── Início de nova seção ────────────────────────────────────────────
        if "Atendimento" in texto and not eh_rodape:
            salvar_secao()
            pontos_atual = []
            cabecalho = {}
            header_texto_acumulado = [texto]
            estado = "HEADER"
            continue

        if estado == "HEADER":
            if eh_rodape:
                continue
            header_texto_acumulado.append(texto)
            # Cabeçalho da tabela → começa a coletar pontos
            if "Nome Abrev" in texto or ("Nome" in texto and "Ordem" in texto):
                parsear_cabecalho_acumulado()
                estado = "COLLECTING"
            continue

        if estado == "COLLECTING" and not eh_rodape:
            if e_linha_ponto(lw):
                pontos_atual.append(parsear_ponto(lw))

    salvar_secao()
    return resultados


def main():
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print("Nenhum PDF encontrado em", PDF_DIR)
        return

    print(f"[INFO] {len(pdfs)} PDF(s) encontrado(s)")
    todos = []
    for pdf in pdfs:
        print(f"  Processando {pdf.name}...")
        resultado = extrair_pdf(pdf)
        todos.extend(resultado)
        for r in resultado:
            print(f"    -> '{r['linha']}' | {len(r['pontos'])} pontos")

    with SAIDA.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    total_pontos = sum(len(r["pontos"]) for r in todos)
    print(f"\n[OK] {len(todos)} atendimento(s) | {total_pontos} pontos no total")
    print(f"[OK] Salvo em: {SAIDA}")


if __name__ == "__main__":
    main()
