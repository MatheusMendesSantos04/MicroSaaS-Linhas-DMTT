"""
Configurações para automação do sistema MATRIX
"""
from pathlib import Path
import json

# Diretórios
BASE_DIR = Path(__file__).parent.parent
MATRIX_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf" / "matrix_export"
LISTA_LINHAS_JSON = MATRIX_DIR / "lista_linhas.json"

# Criar diretórios se não existirem
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Configurações do MATRIX
MATRIX_EXE = r"D:\Prefeitura_Digital\Modulo\Fonte\Matrix\Maceio\MATRIX\matrix.exe"
MATRIX_TITULO = "Relatório"  # Título da janela principal

# Credenciais
USUARIO = "matheus mendes"
SENHA = "dmtt2025"

# Data de referência padrão
DATA_REFERENCIA = "12/02/2026"

# Timeouts (em segundos)
TIMEOUT_JANELA = 10
TIMEOUT_DIALOGO = 5
TIMEOUT_EXPORT = 30
DELAY_ENTRE_ACOES = 0.5
DELAY_ENTRE_LINHAS = 2

# Carregar lista de linhas
def carregar_linhas():
    """Carrega lista de linhas do arquivo JSON"""
    with open(LISTA_LINHAS_JSON, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    return dados['numeros'], dados['detalhes']

# Configurações de log
LOG_FILE = MATRIX_DIR / "automation_log.txt"
PROGRESS_FILE = MATRIX_DIR / "progress.json"
