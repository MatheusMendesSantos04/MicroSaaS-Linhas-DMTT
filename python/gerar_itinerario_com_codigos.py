"""
Gera itinerario_com_codigos.json e relatorio_codigos.txt

Fontes:
  - itinerario_completo.json (nomes de ruas por linha/sentido)
  - sre_relatorio_via_logradouro-codigo-das-ruas.pdf (índice global código→via)
  - data/pdf-intinerarios-por-via-todas-linhas/linha_XXXX.pdf (por linha, por sentido)

Saída:
  - itinerario-com-codigo-rua/itinerario_com_codigos.json
  - itinerario-com-codigo-rua/relatorio_codigos.txt
"""

import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "pdf-intinerarios-por-via-todas-linhas"
MASTER_PDF = PDF_DIR / "sre_relatorio_via_logradouro-codigo-das-ruas.pdf"
ITINERARIO_JSON = ROOT / "python" / "dado principal" / "intinerario manual" / "itinerario_completo.json"
OUTPUT_DIR = ROOT / "python" / "dado principal" / "intinerario-com-codigo-rua"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Normalização
# ---------------------------------------------------------------------------

ABBREV_MAP = {
    r"\bAV\.?\b": "AVENIDA",
    r"\bR\.?\b": "RUA",
    r"\bTRAV\.?\b": "TRAVESSA",
    r"\bTRA\.?\b": "TRAVESSA",
    r"\bLAD\.?\b": "LADEIRA",
    r"\bPCA\.?\b": "PRACA",
    r"\bP\.?\b": "PRACA",
    r"\bEST\.?\b": "ESTRADA",
    r"\bROD\.?\b": "RODOVIA",
    r"\bALM\.?\b": "ALMIRANTE",
    r"\bCOM\.?\b": "COMENDADOR",
    r"\bDEP\.?\b": "DEPUTADO",
    r"\bSEN\.?\b": "SENADOR",
    r"\bDR\.?\b": "DOUTOR",
    r"\bGEN\.?\b": "GENERAL",
    r"\bCEL\.?\b": "CORONEL",
    r"\bSGT\.?\b": "SARGENTO",
    r"\bCAP\.?\b": "CAPITAO",
    r"\bTEN\.?\b": "TENENTE",
    r"\bPROF\.?\b": "PROFESSOR",
    r"\bJORN\.?\b": "JORNALISTA",
    r"\bARQ\.?\b": "ARQUITETO",
    r"\bENG\.?\b": "ENGENHEIRO",
    r"\bPRES\.?\b": "PRESIDENTE",
    r"\bGOV\.?\b": "GOVERNADOR",
    r"\bPREF\.?\b": "PREFEITO",
}


def normalize(text: str) -> str:
    # Remove acentos
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.upper().strip()
    # Remove caracteres especiais de PDF corrompidos
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_pdf_artifacts(text: str) -> str:
    """Remove artefatos específicos de extração de PDF antes de normalizar."""
    # "A V." / "A V " → "AV." (espaço no meio da palavra AVENIDA)
    text = re.sub(r"\bA\s+V\s*\.?\s*", "AV. ", text)
    # "TRA V." → "TRAV."
    text = re.sub(r"\bTRA\s+V\s*\.?\s*", "TRAV. ", text)
    # "A VENIDA" → "AVENIDA"
    text = re.sub(r"\bA\s+VENIDA\b", "AVENIDA", text)
    # Padrões específicos conhecidos de artefato neste PDF
    text = re.sub(r"\bGUSTA\s+VO\b", "GUSTAVO", text)
    text = re.sub(r"\bPAIV\s+A\b", "PAIVA", text)
    text = re.sub(r"\bLOURIV\s+AL\b", "LOURIVAL", text)
    text = re.sub(r"\bSILV\s+A\b", "SILVA", text)
    text = re.sub(r"\bOLIV\s+A\b", "OLIVA", text)
    text = re.sub(r"\bCALV\s+A\b", "CALVA", text)
    text = re.sub(r"\bSALV\s+A\b", "SALVA", text)
    # "PAIV" sem seguir A (caso já corrigido acima, mas garante)
    text = re.sub(r"([A-Z]{4,})\s+([AEIOU])\b(?!\s+[A-Z])", lambda m: m.group(1) + m.group(2), text)
    return text


def normalize_strip_complement(text: str) -> str:
    """Normaliza removendo complementos entre parênteses antes."""
    text = re.sub(r"\(.*?\)", "", text)
    return normalize(text)


def expand_abbrevs(text: str) -> str:
    for pattern, replacement in ABBREV_MAP.items():
        text = re.sub(pattern, replacement, text)
    return re.sub(r"\s+", " ", text).strip()


def full_normalize(text: str) -> str:
    return expand_abbrevs(normalize(text))


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------------------
# Extração do PDF master (código global)
# ---------------------------------------------------------------------------

def extract_master_codes(pdf_path: Path) -> dict[str, str]:
    """Retorna {codigo: via_original} e constrói índice normalizado."""
    reader = PdfReader(str(pdf_path))
    code_to_via: dict[str, str] = {}
    # Padrão: 5 dígitos seguidos de nome de via
    pattern = re.compile(r"(\d{5})\s+(.+?)(?=\d{5}|\Z)", re.DOTALL)

    for page in reader.pages:
        raw = page.extract_text() or ""
        raw = clean_pdf_artifacts(raw)
        raw = re.sub(r"P\s*C\s*A\s*\.\s*", "PCA. ", raw)
        for match in pattern.finditer(raw):
            code = match.group(1)
            via = match.group(2).strip()
            # Remove sufixos numéricos como "0000 0001"
            via = re.sub(r"\s+\d{4}\s+\d{4}.*", "", via).strip()
            via = re.sub(r"\s+", " ", via)
            if len(via) > 2 and code not in code_to_via:
                code_to_via[code] = via
    return code_to_via


# ---------------------------------------------------------------------------
# Extração dos PDFs por linha
# ---------------------------------------------------------------------------

def extract_linha_pdf(pdf_path: Path) -> dict[str, list[dict]]:
    """
    Retorna {sentido: [{seq, code, via}]} para a linha.
    sentido: 'ida' ou 'volta'
    """
    reader = PdfReader(str(pdf_path))
    result: dict[str, list[dict]] = {"ida": [], "volta": []}
    current_sentido = None

    entry_pattern = re.compile(
        r"(\d{3})\s+(\d{5})(IDA|VOLTA)?\s+(.+?)(?=\d{3}\s+\d{5}|Sub-Total|\Z)",
        re.DOTALL,
    )

    full_text = ""
    for page in reader.pages:
        raw = page.extract_text() or ""
        raw = clean_pdf_artifacts(raw)
        raw = re.sub(r"P\s*C\s*A\s*\.\s*", "PCA. ", raw)
        full_text += "\n" + raw

    for match in entry_pattern.finditer(full_text):
        seq = match.group(1)
        code = match.group(2)
        sentido_marker = match.group(3)
        via = match.group(4).strip()
        via = re.sub(r"\s+", " ", via)
        # Descarta linhas de cabeçalho/rodapé
        if any(skip in via for skip in ["Sub-Total", "TOTAL:", "Sentido", "Sequ", "IntinerarioPorVia", "P gina", "ITINER"]):
            continue
        if sentido_marker:
            current_sentido = sentido_marker.lower()
        if current_sentido and len(via) > 1:
            result[current_sentido].append({"seq": seq, "code": code, "via": via})

    return result


# ---------------------------------------------------------------------------
# Índice de busca
# ---------------------------------------------------------------------------

class CodeIndex:
    def __init__(self, master_codes: dict[str, str]):
        # code → via original
        self.code_to_via = master_codes
        # normalized_full → (code, via_original)
        self.norm_to_code: dict[str, tuple[str, str]] = {}
        # normalized_sem_complemento → (code, via_original)
        self.norm_nocomp_to_code: dict[str, tuple[str, str]] = {}
        for code, via in master_codes.items():
            key = full_normalize(via)
            if key not in self.norm_to_code:
                self.norm_to_code[key] = (code, via)
            key_nc = full_normalize(normalize_strip_complement(via))
            if key_nc not in self.norm_nocomp_to_code:
                self.norm_nocomp_to_code[key_nc] = (code, via)

        # Também index por linha: line_num → sentido → [norm_via → (code, via)]
        self.per_line: dict[str, dict[str, dict[str, tuple[str, str]]]] = defaultdict(
            lambda: {"ida": {}, "volta": {}}
        )

    def add_line_data(self, line_num: str, data: dict[str, list[dict]]):
        for sentido, entries in data.items():
            for entry in entries:
                key = full_normalize(entry["via"])
                self.per_line[line_num][sentido][key] = (entry["code"], entry["via"])

    def lookup(
        self,
        via: str,
        line_num: str | None = None,
        sentido: str | None = None,
        fuzzy_threshold: float = 0.82,
    ) -> tuple[str | None, str | None, str]:
        """
        Retorna (code, via_pdf, match_type).
        match_type: 'exato', 'exato_global', 'exato_sem_complemento',
                    'contem', 'fuzzy', 'fuzzy_global', 'nao_encontrado'
        """
        norm = full_normalize(via)
        norm_nc = full_normalize(normalize_strip_complement(via))

        # 1) Busca exata na linha/sentido
        if line_num and sentido:
            line_data = self.per_line.get(line_num, {}).get(sentido, {})
            if norm in line_data:
                code, via_pdf = line_data[norm]
                return code, via_pdf, "exato"

        # 2) Busca exata na linha (qualquer sentido)
        if line_num:
            for s in ("ida", "volta"):
                line_data = self.per_line.get(line_num, {}).get(s, {})
                if norm in line_data:
                    code, via_pdf = line_data[norm]
                    return code, via_pdf, "exato"

        # 3) Busca exata global
        if norm in self.norm_to_code:
            code, via_pdf = self.norm_to_code[norm]
            return code, via_pdf, "exato_global"

        # 4) Busca exata global sem complemento (ex: query "MENINO MARCELO" vs "MENINO MARCELO SERRARIA")
        if norm_nc in self.norm_nocomp_to_code:
            code, via_pdf = self.norm_nocomp_to_code[norm_nc]
            return code, via_pdf, "exato_sem_complemento"

        # 5) Busca por contenção: query está contida no candidato ou vice-versa
        #    Útil para "PARQUE RODOLFO LINS" → "PARQUE RODOLFO LINS PCA DO PIRULITO"
        if len(norm) >= 8:
            # Busca por linha primeiro
            candidates = {}
            if line_num:
                for s in ("ida", "volta"):
                    candidates.update(self.per_line.get(line_num, {}).get(s, {}))
            if not candidates:
                candidates = self.norm_to_code
            for candidate_norm, (code, via_pdf) in candidates.items():
                if norm in candidate_norm or candidate_norm in norm:
                    shorter = min(len(norm), len(candidate_norm))
                    longer = max(len(norm), len(candidate_norm))
                    # Só aceita se a parte comum for pelo menos 70% do total
                    if shorter / longer >= 0.70:
                        return code, via_pdf, "contem"

        # 6) Busca fuzzy na linha/sentido
        best_score = 0.0
        best_code = None
        best_via_pdf = None

        if line_num:
            for s in ("ida", "volta"):
                line_data = self.per_line.get(line_num, {}).get(s, {})
                for candidate_norm, (code, via_pdf) in line_data.items():
                    score = similarity(norm, candidate_norm)
                    if score > best_score:
                        best_score = score
                        best_code = code
                        best_via_pdf = via_pdf

        if best_score >= fuzzy_threshold:
            return best_code, best_via_pdf, "fuzzy"

        # 7) Busca fuzzy global
        best_score = 0.0
        best_code = None
        best_via_pdf = None
        for candidate_norm, (code, via_pdf) in self.norm_to_code.items():
            score = similarity(norm, candidate_norm)
            if score > best_score:
                best_score = score
                best_code = code
                best_via_pdf = via_pdf

        if best_score >= fuzzy_threshold:
            return best_code, best_via_pdf, "fuzzy_global"

        return None, None, "nao_encontrado"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def extract_line_num(key: str) -> str:
    m = re.match(r"^(\d{4})", key.strip())
    return m.group(1) if m else ""


def main():
    print("Lendo itinerario_completo.json...")
    with ITINERARIO_JSON.open(encoding="utf-8") as f:
        itinerario = json.load(f)

    print("Extraindo índice master de códigos...")
    master_codes = extract_master_codes(MASTER_PDF)
    print(f"  {len(master_codes)} códigos encontrados no master")

    index = CodeIndex(master_codes)

    print("Extraindo PDFs por linha...")
    pdf_files = sorted(PDF_DIR.glob("linha_*.pdf"))
    for pdf_path in pdf_files:
        line_num = re.search(r"linha_(\d{4})", pdf_path.name)
        if not line_num:
            continue
        num = line_num.group(1)
        try:
            data = extract_linha_pdf(pdf_path)
            index.add_line_data(num, data)
        except Exception as e:
            print(f"  AVISO: erro ao ler {pdf_path.name}: {e}")

    print("Fazendo matching e gerando JSON...")

    output: dict = {}
    # Estatísticas para relatório
    stats = {
        "total_ruas": 0,
        "exato": 0,
        "exato_global": 0,
        "exato_sem_complemento": 0,
        "contem": 0,
        "fuzzy": 0,
        "fuzzy_global": 0,
        "nao_encontrado": 0,
    }
    report_lines_nao_encontrado: list[str] = []
    report_lines_fuzzy: list[str] = []
    report_lines_exato: list[str] = []

    for linha_key, sentidos in itinerario.items():
        line_num = extract_line_num(linha_key)
        output[linha_key] = {
            "versao": sentidos.get("versao", ""),
        }

        for sentido in ("ida", "volta"):
            ruas = sentidos.get(sentido, [])
            output[linha_key][sentido] = []

            for via in ruas:
                stats["total_ruas"] += 1
                code, via_pdf, match_type = index.lookup(via, line_num=line_num, sentido=sentido)
                stats[match_type] += 1

                entry = {
                    "via": via,
                    "codigo": code,
                    "via_pdf": via_pdf,
                    "match": match_type,
                }
                output[linha_key][sentido].append(entry)

                tag = f"[{linha_key}] [{sentido.upper()}] \"{via}\""
                if match_type == "nao_encontrado":
                    report_lines_nao_encontrado.append(tag)
                elif match_type in ("fuzzy", "fuzzy_global"):
                    report_lines_fuzzy.append(
                        f"{tag}\n    → [{match_type}] código {code} | PDF: \"{via_pdf}\""
                    )
                else:
                    report_lines_exato.append(
                        f"{tag}\n    → [{match_type}] código {code} | PDF: \"{via_pdf}\""
                    )

    # Salva JSON
    output_json = OUTPUT_DIR / "itinerario_com_codigos.json"
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"JSON salvo: {output_json}")

    # Salva relatório
    output_report = OUTPUT_DIR / "relatorio_codigos.txt"
    total = stats["total_ruas"]
    matched = stats["exato"] + stats["exato_global"] + stats["exato_sem_complemento"] + stats["contem"] + stats["fuzzy"] + stats["fuzzy_global"]
    nao = stats["nao_encontrado"]

    with output_report.open("w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO DE MATCHING: ITINERÁRIOS × CÓDIGOS DE RUAS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total de ocorrências de ruas nos itinerários : {total}\n")
        f.write(f"Encontradas (match exato ou fuzzy)           : {matched} ({matched/total*100:.1f}%)\n")
        f.write(f"  → Exato por linha/sentido                  : {stats['exato']}\n")
        f.write(f"  → Exato no índice global                   : {stats['exato_global']}\n")
        f.write(f"  → Exato sem complemento (ignora parênteses): {stats['exato_sem_complemento']}\n")
        f.write(f"  → Contenção (nome é parte do nome PDF)     : {stats['contem']}\n")
        f.write(f"  → Fuzzy por linha/sentido                  : {stats['fuzzy']}\n")
        f.write(f"  → Fuzzy no índice global                   : {stats['fuzzy_global']}\n")
        f.write(f"Não encontradas                              : {nao} ({nao/total*100:.1f}%)\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write(f"RUAS NÃO ENCONTRADAS ({len(report_lines_nao_encontrado)})\n")
        f.write("Possíveis causas: nome abreviado diferente, rua exclusiva do itinerário manual,\n")
        f.write("nome completo no itinerário vs. abreviado no PDF, ou erro de OCR.\n")
        f.write("=" * 80 + "\n\n")
        for line in report_lines_nao_encontrado:
            f.write(line + "\n")

        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write(f"RUAS ENCONTRADAS POR SIMILARIDADE (FUZZY) ({len(report_lines_fuzzy)})\n")
        f.write("Revisar: nomes podem diferir (abreviação, acento, complemento).\n")
        f.write("=" * 80 + "\n\n")
        for line in report_lines_fuzzy:
            f.write(line + "\n\n")

        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write(f"RUAS ENCONTRADAS COM MATCH EXATO ({len(report_lines_exato)})\n")
        f.write("=" * 80 + "\n\n")
        for line in report_lines_exato:
            f.write(line + "\n\n")

    print(f"Relatório salvo: {output_report}")
    print("\n--- RESUMO ---")
    print(f"Total ruas    : {total}")
    print(f"Encontradas   : {matched} ({matched/total*100:.1f}%)")
    print(f"Não encontradas: {nao} ({nao/total*100:.1f}%)")


if __name__ == "__main__":
    main()
