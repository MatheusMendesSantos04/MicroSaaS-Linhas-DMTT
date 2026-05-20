"""
Extrai todos os codigos de linha de um arquivo XLS de passageiros (DDMMYYYY.xls),
cruza com horarios.json e itinerario_com_codigos.json para obter os nomes,
e salva o resultado em data/linhas-nomes/linhas.json.

Uso:
    python extrair_linhas_xls.py
    python extrair_linhas_xls.py 31122025.xls   # arquivo especifico
"""

import json
import re
import sys
from pathlib import Path

import xlrd

# ── Caminhos ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[1]
PASTA_XLS = Path(r"I:\cumprimento\passageiros\Passageiros\passageiros")
HORARIOS_JSON = BASE_DIR / "data" / "json" / "horarios" / "horarios.json"
ITINERARIO_JSON = BASE_DIR / "data" / "json" / "intinerario-com-codigo-rua" / "itinerario_com_codigos.json"
SAIDA = BASE_DIR / "data" / "linhas-nomes" / "linhas.json"

# Palavras que indicam que a célula NÃO é um código de linha
IGNORAR = {"linha", "total", "empresa", "impresso", "pagina", "normal",
           "integration", "abt", "cidadao", "correios", "empresarial",
           "emv", "escolar", "especial", "funcional", "orgao", "rod",
           "senior", "vale", "gratuito", "diario", "cc", "ac"}


def e_codigo_linha(valor: str) -> bool:
    """Retorna True se o valor parece um codigo de linha (0001, M006, 4003...)."""
    v = valor.strip()
    if not v or len(v) > 6:
        return False
    # Codigos numericos de 4 digitos ou com prefixo M
    if re.match(r"^[M]?\d{3,4}$", v):
        return True
    return False


def extrair_codigos_xls(caminho: Path) -> list[str]:
    """Le o XLS e retorna lista ordenada de codigos de linha unicos."""
    wb = xlrd.open_workbook(str(caminho))
    codigos = set()
    for sheet in wb.sheets():
        for row in range(sheet.nrows):
            val = str(sheet.cell_value(row, 1)).strip()
            if e_codigo_linha(val):
                # Normaliza: garante 4 digitos com zero a esquerda para numericos
                if re.match(r"^\d+$", val):
                    val = val.zfill(4)
                codigos.add(val)
    return sorted(codigos)


def carregar_nomes_horarios(path: Path) -> dict[str, str]:
    """Carrega {codigo_4dig: nome} do horarios.json."""
    if not path.exists():
        print(f"  [AVISO] horarios.json nao encontrado: {path}")
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {cod: info.get("nome", "") for cod, info in data.items()}


def carregar_nomes_itinerario(path: Path) -> dict[str, str]:
    """Carrega {codigo_4dig: nome_chave} do itinerario_com_codigos.json."""
    if not path.exists():
        print(f"  [AVISO] itinerario_com_codigos.json nao encontrado: {path}")
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    resultado = {}
    for nome_chave in data:
        m = re.match(r"^(\d{4})", nome_chave.strip())
        if m:
            resultado[m.group(1)] = nome_chave.strip()
    return resultado


def main():
    # Escolhe o arquivo XLS
    if len(sys.argv) > 1:
        arquivo = PASTA_XLS / sys.argv[1]
    else:
        # Usa o mais recente no padrao DDMMYYYY.xls
        candidatos = sorted(PASTA_XLS.glob("[0-9]" * 8 + ".xls"), reverse=True)
        if not candidatos:
            print("ERRO: Nenhum arquivo DDMMYYYY.xls encontrado em", PASTA_XLS)
            sys.exit(1)
        arquivo = candidatos[0]

    print(f"[INFO] Lendo arquivo: {arquivo.name}")

    # Extrai codigos
    codigos = extrair_codigos_xls(arquivo)
    print(f"[INFO] {len(codigos)} codigos de linha encontrados")

    # Carrega fontes de nomes
    nomes_horarios = carregar_nomes_horarios(HORARIOS_JSON)
    nomes_itinerario = carregar_nomes_itinerario(ITINERARIO_JSON)

    # Monta resultado
    linhas = []
    sem_nome = []
    for cod in codigos:
        nome = nomes_horarios.get(cod) or nomes_itinerario.get(cod) or ""
        linhas.append({"codigo": cod, "nome": nome})
        if not nome:
            sem_nome.append(cod)

    # Salva JSON
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)

    print(f"[OK] Salvo em: {SAIDA}")
    print(f"[INFO] {len(linhas) - len(sem_nome)} linhas com nome | {len(sem_nome)} sem nome: {sem_nome}")


if __name__ == "__main__":
    main()
