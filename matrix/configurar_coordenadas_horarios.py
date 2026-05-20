"""
Configurador de Coordenadas — Quadro Horário
============================================
Captura as coordenadas do mouse para cada elemento da tela do MATRIX
na tela de OSO configurada para "Quadro Horário".

As coordenadas são idênticas às do script de itinerário (mesma tela),
exceto pelo campo "checkbox_quadro_horario" que é novo.

INSTRUÇÕES:
1. Abra o MATRIX e navegue até a tela de OSO
2. Execute este script: python matrix/configurar_coordenadas_horarios.py
3. Posicione o mouse em cada elemento quando solicitado e pressione Enter
4. As coordenadas serão salvas em coordenadas_horarios.json
"""

import json
import time
import pyautogui
from pathlib import Path

COORD_FILE = Path(__file__).parent / "coordenadas_horarios.json"

ELEMENTOS = [
    ("campo_numero",          "campo 'Número' na tela de OSO (onde você digita o número da linha)"),
    ("botao_imprimir",        "botão 'Imprimir' na barra superior da tela de OSO"),
    ("icone_exportar",        "ícone de seta vermelha para baixo (exportar) na janela de visualização"),
    ("botao_ok_1",            "botão OK no 1º diálogo (seleção de formato PDF)"),
    ("botao_ok_2",            "botão OK no 2º diálogo (confirmar 'Todas' as páginas)"),
    ("campo_arquivo",         "campo de nome do arquivo na janela 'Salvar Como'"),
    ("botao_salvar",          "botão 'Salvar' na janela 'Salvar Como'"),
    ("botao_fechar",          "botão X vermelho para fechar a janela de visualização"),
    ("checkbox_quadro_horario","checkbox 'Quadro Horário' na tela de OSO (para verificação futura)"),
]

# campo_pasta é opcional — só adicione se quiser navegar para pasta automaticamente
ELEMENTOS_OPCIONAIS = [
    ("campo_pasta", "campo de endereço/pasta na janela 'Salvar Como' (opcional — pressione Enter para pular)"),
]


def capturar(nome: str, descricao: str, opcional: bool = False) -> tuple[int, int] | None:
    print(f"\n  [{nome}]")
    print(f"  Posicione o mouse em: {descricao}")
    if opcional:
        print("  (Opcional — pressione Enter SEM mover o mouse para pular)")
    input("  Pressione Enter quando o mouse estiver na posição... ")

    x, y = pyautogui.position()

    if opcional and (x, y) == pyautogui.position():
        resposta = input(f"  Coordenada capturada: ({x}, {y})  —  Usar? (S/N): ").strip().upper()
        if resposta != "S":
            print("  Elemento ignorado.")
            return None

    print(f"  ✅ Coordenada: ({x}, {y})")
    return x, y


def main():
    print("=" * 60)
    print("  CONFIGURADOR DE COORDENADAS — QUADRO HORÁRIO")
    print("=" * 60)
    print("""
  Este script captura as posições dos elementos na tela do MATRIX.
  Você tem 3 segundos após pressionar Enter para mover o mouse
  para a posição correta.

  Dica: os elementos obrigatórios são idênticos ao script de itinerário.
  Se as coordenadas do itinerário ainda funcionam, você pode copiá-las.
""")

    # Opção: copiar do arquivo existente
    coord_original = Path(__file__).parent / "coordenadas.json"
    if coord_original.exists():
        usar_original = input("  Encontrei coordenadas.json existente. Copiar como base? (S/N): ").strip().upper()
        if usar_original == "S":
            with open(coord_original, "r") as f:
                coords = json.load(f)
            print("  ✅ Coordenadas copiadas. Você pode adicionar/sobrescrever elementos individuais.")
        else:
            coords = {}
    else:
        coords = {}

    confirma = input("\n  Iniciar captura interativa? (S/N): ").strip().upper()
    if confirma == "N":
        if coords:
            with open(COORD_FILE, "w") as f:
                json.dump(coords, f, indent=2)
            print(f"\n  ✅ Coordenadas salvas em: {COORD_FILE}")
        return

    print("\n  Iniciando captura em 3 segundos...")
    time.sleep(3)

    # Capturar elementos obrigatórios
    for nome, descricao in ELEMENTOS:
        if nome in coords:
            manter = input(f"\n  '{nome}' já existe: {coords[nome]}. Manter? (S/N): ").strip().upper()
            if manter == "S":
                continue

        resultado = capturar(nome, descricao)
        if resultado:
            coords[nome] = list(resultado)

    # Capturar elementos opcionais
    print("\n  ── Elementos opcionais ──")
    for nome, descricao in ELEMENTOS_OPCIONAIS:
        resultado = capturar(nome, descricao, opcional=True)
        if resultado:
            coords[nome] = list(resultado)

    # Salvar
    with open(COORD_FILE, "w") as f:
        json.dump(coords, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  ✅ Coordenadas salvas em: {COORD_FILE}")
    print(f"\n  Resumo:")
    for nome, xy in coords.items():
        print(f"    {nome:30} → {xy}")
    print(f"{'='*60}")
    print("\n  Agora execute: python matrix/automation_horarios.py")


if __name__ == "__main__":
    main()
