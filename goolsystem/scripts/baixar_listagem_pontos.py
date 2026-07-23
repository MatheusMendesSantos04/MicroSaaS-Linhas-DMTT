"""
Baixa, do GoolSystem (Cittati), um PDF de "Listagem de Pontos" POR LINHA
(nao mais um PDF gigante por empresa) -- muito mais simples de processar
depois, e o cabecalho de cada PDF ja traz "Linha: <codigo> - <nome>" com o
codigo DMTT correto, sem precisar de fuzzy-match contra o OSO.

Fluxo (confirmado por reconhecimento manual em 17/07/2026):
  1. Login em gool.cittati.com.br (modulo Urbano)
  2. Navega pra https://.../Negocio/Atendimento/ListarAtendimento.aspx
  3. Seleciona Empresa (dropdown ddlEmpresa) -> recarrega Linha (postback)
  4. Para cada opcao do dropdown ddlLinhaEmpresa (pula "Selecione um item"):
     - seleciona a linha
     - clica "Gerar Listagem" (btnImprimirListagem) -> PDF baixa direto
       (sem passo intermediario de export/print)
     - salva em pdfs_por_linha/<EMPRESA>/<codigo>_<nome>.pdf

E' resumivel: se o arquivo de destino ja existe, pula (nao baixa de novo).

Uso:
    cd goolsystem/scripts
    python baixar_listagem_pontos.py [--empresas CIMA,REAL,SFRA] [--limite N]
"""
import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE_DIR = Path(__file__).resolve().parents[1]  # goolsystem/
OUT_DIR = BASE_DIR / "pdfs_por_linha"

LOGIN_URL = "https://gool.cittati.com.br/Login.aspx?ReturnUrl=%2fHome%2fInicio.aspx"
LISTAGEM_URL = "https://gool.cittati.com.br/Negocio/Atendimento/ListarAtendimento.aspx"
USUARIO = "smtt.maceio"
SENHA = "Ccint@2022"

EMPRESAS = {
    "SFRA": "Empresa São Francisco",
    "REAL": "Real Transportes Urbanos Ltda.",
    "CIMA": "Viação Cidade de Maceió",
}

SEL_EMPRESA = "#ContentPlaceHolder1_contentFiltroPesquisa_ddlEmpresa"
SEL_LINHA = "#ContentPlaceHolder1_contentFiltroPesquisa_ddlLinhaEmpresa"
BTN_GERAR = "#ContentPlaceHolder1_contentFiltroPesquisa_btnImprimirListagem span.bordaEsquerda"


def normalizar_nome_arquivo(nome: str) -> str:
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = re.sub(r'[\\/*?:"<>|]', "-", nome).strip()
    return nome[:80]


def extrair_codigo_e_nome(texto_opcao: str) -> tuple[str, str]:
    """'0012 - Jose da Silva Peixoto / Centro' -> ('0012', 'Jose da Silva Peixoto / Centro')
    'M004 - MADRUGÃO - OURO PRETO/PONTA VERDE' -> ('M004', 'MADRUGÃO - OURO PRETO/PONTA VERDE')"""
    m = re.match(r"^([\dM]{3,5})\s*-\s*(.+)$", texto_opcao.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return "SEMCODIGO", texto_opcao.strip()


def login(page):
    page.goto(LOGIN_URL, wait_until="networkidle")
    page.click("#ucTrocarModulo_moduloUrbano")
    page.wait_for_timeout(800)
    page.fill("#ucLogarUsuario_txtLogin", USUARIO)
    page.fill("#ucLogarUsuario_txtSenha", SENHA)
    page.click("#ucLogarUsuario_btnLogar")
    page.wait_for_timeout(2500)
    if "Login.aspx" in page.url:
        raise RuntimeError("Login falhou -- ainda na tela de Login apos submeter.")


def listar_opcoes_linha(page) -> list[tuple[str, str]]:
    opcoes = page.eval_on_selector_all(
        f"{SEL_LINHA} option",
        "els => els.map(e => [e.value, e.textContent.trim()])",
    )
    return [(v, t) for v, t in opcoes if v and v != "0"]


def baixar_linha(page, pasta_empresa: Path, valor: str, texto_opcao: str, log) -> str:
    codigo, nome = extrair_codigo_e_nome(texto_opcao)
    nome_arquivo = f"{codigo}_{normalizar_nome_arquivo(nome)}.pdf"
    destino = pasta_empresa / nome_arquivo

    if destino.exists():
        return "pulado (ja existe)"

    page.select_option(SEL_LINHA, value=valor)
    page.wait_for_timeout(400)

    try:
        with page.expect_download(timeout=20000) as download_info:
            page.click(BTN_GERAR)
        download = download_info.value
        download.save_as(str(destino))
        return "OK"
    except PWTimeout:
        return "ERRO: timeout esperando download"
    except Exception as e:
        return f"ERRO: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--empresas", default="CIMA,REAL,SFRA")
    parser.add_argument("--limite", type=int, default=None, help="limita quantas linhas por empresa (teste)")
    parser.add_argument("--headless", action="store_true", default=True)
    args = parser.parse_args()

    empresas_alvo = [e.strip().upper() for e in args.empresas.split(",")]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = BASE_DIR / "scripts" / "log_baixar_listagem_pontos.txt"

    with sync_playwright() as p, open(log_path, "a", encoding="utf-8") as log:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("Fazendo login...")
        login(page)
        print("Login OK.\n")

        for empresa in empresas_alvo:
            if empresa not in EMPRESAS:
                print(f"[AVISO] empresa desconhecida: {empresa}")
                continue

            label = EMPRESAS[empresa]
            pasta_empresa = OUT_DIR / empresa
            pasta_empresa.mkdir(parents=True, exist_ok=True)

            print(f"=== {empresa} ({label}) ===")
            page.goto(LISTAGEM_URL, wait_until="networkidle")
            page.select_option(SEL_EMPRESA, label=label)
            page.wait_for_timeout(1200)

            opcoes = listar_opcoes_linha(page)
            if args.limite:
                opcoes = opcoes[: args.limite]
            print(f"  {len(opcoes)} linhas encontradas no dropdown.")

            ok = pulado = erro = 0
            for i, (valor, texto) in enumerate(opcoes, 1):
                resultado = baixar_linha(page, pasta_empresa, valor, texto, log)
                marcador = "OK" if resultado == "OK" else ("pulado" if "pulado" in resultado else "ERRO")
                print(f"  [{i}/{len(opcoes)}] {texto[:55]:<55} -> {resultado}")
                log.write(f"{empresa}\t{valor}\t{texto}\t{resultado}\n")
                log.flush()
                if resultado == "OK":
                    ok += 1
                elif "pulado" in resultado:
                    pulado += 1
                else:
                    erro += 1
                time.sleep(0.5)

            print(f"  Resumo {empresa}: {ok} OK, {pulado} pulados, {erro} erros\n")

        browser.close()

    print(f"Log completo em: {log_path}")


if __name__ == "__main__":
    main()
