"""
Fase F do pipeline — mescla novas linhas no dados_unificados.json e horarios.json.

Fontes:
  data/json/novos_trajetos/coords_novas_linhas.json   — coordenadas GPS do KML
  data/json/novos_trajetos/itinerario_rascunho.json   — ruas parseadas do PDF (revisado pelo usuário)
  data/json/novos_trajetos/horarios_novos.json        — horários parseados do PDF
  data/json/dados_unificados.json                     — destino principal (backend)
  data/json/horarios/horarios.json                    — destino de horários

Antes de rodar:
  1. O usuário deve ter revisado itinerario_rascunho.json
  2. Ter confirmado horarios_novos.json
  3. Backend offline (ou será necessário reiniciar após)

Uso:
    python python/mesclar_novos_trajetos.py
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR   = Path(__file__).resolve().parents[1]
COORDS_F   = BASE_DIR / "data" / "json" / "novos_trajetos" / "coords_novas_linhas.json"
ITIN_F     = BASE_DIR / "data" / "json" / "novos_trajetos" / "itinerario_rascunho.json"
HOR_F      = BASE_DIR / "data" / "json" / "novos_trajetos" / "horarios_novos.json"
DU_F       = BASE_DIR / "data" / "json" / "dados_unificados.json"
HORAS_F    = BASE_DIR / "data" / "json" / "horarios" / "horarios.json"


def extrair_cod(texto: str) -> str:
    m = re.match(r"^([A-Z]?\d{3,4})(?:\s+([A-Z])(?=[\s\-/]|$))?", texto.strip())
    if not m:
        return ""
    base   = m.group(1)
    suffix = m.group(2) or ""
    v = base + suffix
    return v.zfill(4) if v.isdigit() else v


def backup(path: Path):
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix(f".{ts}.bak.json")
    shutil.copy(path, bak)
    print(f"  Backup: {bak.name}")


# --- carrega fontes ---
coords   = json.loads(COORDS_F.read_text(encoding="utf-8"))
itin     = json.loads(ITIN_F.read_text(encoding="utf-8"))
hor_nov  = json.loads(HOR_F.read_text(encoding="utf-8"))
du       = json.loads(DU_F.read_text(encoding="utf-8"))
horarios = json.loads(HORAS_F.read_text(encoding="utf-8"))

# --- índice por código ---
itin_por_cod  = {extrair_cod(k): v for k, v in itin.items()}
du_por_cod    = {extrair_cod(k): k for k in du}

novos = 0
atualizados = 0

print("=" * 60)
print("MESCLANDO NOVAS LINHAS")
print("=" * 60)

for nome_kml, sentidos in coords.items():
    cod = extrair_cod(nome_kml)
    if not cod:
        print(f"  [IGNORADO] nao extraiu codigo de: {nome_kml}")
        continue

    # ruas do itinerário (se existir)
    itin_data = itin_por_cod.get(cod, {})
    ruas_ida   = [{"via": r["via"], "codigo": r["codigo"], "match": "matrix"}
                  for r in itin_data.get("ida", [])]
    ruas_volta = [{"via": r["via"], "codigo": r["codigo"], "match": "matrix"}
                  for r in itin_data.get("volta", [])]

    coords_ida   = sentidos.get("ida",   [])
    coords_volta = sentidos.get("volta", [])

    # nome para o dados_unificados (usa nome do itinerário PDF se disponível)
    if itin_data:
        nome_du = next((k for k in itin.keys() if extrair_cod(k) == cod), nome_kml)
    else:
        nome_du = nome_kml

    # se já existe no du, atualiza; caso contrário, cria
    chave_existente = du_por_cod.get(cod)

    if chave_existente:
        entrada = du[chave_existente]
        entrada["ida"]["coordenadas"]  = coords_ida
        entrada["volta"]["coordenadas"] = coords_volta
        if ruas_ida:
            entrada["ida"]["ruas"] = ruas_ida
        if ruas_volta:
            entrada["volta"]["ruas"] = ruas_volta
        print(f"  [ATUALIZADO] {chave_existente}")
        atualizados += 1
    else:
        du[nome_du] = {
            "ida":   {"coordenadas": coords_ida,   "ruas": ruas_ida},
            "volta": {"coordenadas": coords_volta, "ruas": ruas_volta},
        }
        print(f"  [NOVO] {nome_du}")
        novos += 1

# --- mescla horários ---
print()
print("Mesclando horários...")
for cod_h, dados_h in hor_nov.items():
    # normaliza chave para 4 dígitos ou formato m
    cod_norm = cod_h.upper()
    if cod_norm not in horarios:
        horarios[cod_norm] = dados_h
        print(f"  [NOVO horario] {cod_norm}")
    else:
        horarios[cod_norm] = dados_h
        print(f"  [ATUALIZADO horario] {cod_norm}")

# --- salva com backup ---
print()
backup(DU_F)
DU_F.write_text(json.dumps(du, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] {DU_F.name} — total: {len(du)} linhas")

backup(HORAS_F)
HORAS_F.write_text(json.dumps(horarios, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] {HORAS_F.name} — total: {len(horarios)} entradas")

print()
print(f"Novas: {novos}  |  Atualizadas: {atualizados}")
print()
print("Reinicie o backend para carregar os dados atualizados:")
print("  cd backend && uvicorn app.main:app --reload")
