"""
Sincroniza dados_unificados.json a partir de TODAS as linhas presentes em
data/kml/Mapa Reconstruido.kml — sem lista fixa de códigos (diferente de
extrair_coords_kml.py, que só olha uma whitelist).

Regras:
- Linha nova (código não existe no sistema) -> cria a entrada (sem
  itinerário de rua — isso continua vindo do Matrix, nunca do KML).
- Nome mudou pro mesmo código -> renomeia a chave, preserva as "ruas" já
  cadastradas.
- Trajeto mudou -> só atualiza coordenadas se o KML tiver MAIS pontos que o
  já existente (nunca reduz a densidade/precisão de um traçado já bom).
- Quando há Placemarks duplicados pro mesmo código+sentido no KML (nomes
  variantes / typos), usa o de mais pontos; se algum tiver "(DESATIVADO)"
  no nome, esse tem prioridade sobre a contagem de pontos.

⚠️ Este script edita dados_unificados.json diretamente (mesmo padrão do
mesclar_novos_trajetos.py). Se alguém rodar gerar_dados_unificados.py depois
(que reconstrói tudo do zero a partir de IDA_amostrado/VOLTA_amostrado +
itinerario_com_codigos.json), essas mudanças de trajeto/nome são perdidas —
esses dois scripts não conversam entre si.

Uso:
    python python/sincronizar_mapa_reconstruido.py
"""
import json
import re
import shutil
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
KML_PATH = BASE_DIR / "data" / "kml" / "Mapa Reconstruido.kml"
DU_PATH = BASE_DIR / "data" / "json" / "dados_unificados.json"

NS = {"k": "http://www.opengis.net/kml/2.2"}


_CODIGO_RE = re.compile(r"^([A-Z]{0,2}\d{1,4})(?:\s*-{0,2}\s*([A-Z]))?(?=[\s\-/]|$)")


def normalizar_codigo(nome: str):
    """'0027 - ...' -> '0027' | 'M001 - ...' -> '0001M' | '0001-M - ...' -> '0001M'
    '0612 A - ...' -> '0612A'. Retorna None se não achar um código no início."""
    nome = nome.strip().upper()
    m = _CODIGO_RE.match(nome)
    if not m:
        return None
    base, suf = m.groups()
    m2 = re.match(r"^([A-Z]*)(\d+)$", base)
    if not m2:
        return None
    pre, digits = m2.groups()
    letra = pre or suf or ""
    return digits.zfill(4) + letra


def _normalizar_texto(t: str) -> str:
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.upper()
    t = re.sub(r"[^A-Z0-9]+", " ", t)
    return t.strip()


def _descricao_sem_codigo(nome: str) -> str:
    """Remove só o código do início (usando a mesma regex de normalizar_codigo),
    não um split ingênuo em ' - ' — nomes tipo '0033 Jose Tenorio / Centro - VIA
    ROTARY' não têm hífen logo após o código, e um split cru cortaria errado."""
    nome_upper = nome.strip().upper()
    m = _CODIGO_RE.match(nome_upper)
    resto = nome_upper[m.end():] if m else nome_upper
    resto = resto.lstrip(" -/")
    resto = re.sub(r"\(DESATIVADO\)", "", resto, flags=re.IGNORECASE)
    return _normalizar_texto(resto)


def _palavras_relevantes(nome: str) -> set:
    return {w for w in _descricao_sem_codigo(nome).split() if len(w) >= 3}


def deve_renomear(nome_atual: str, nome_novo: str) -> bool:
    """Só renomeia se o nome novo (do KML) tiver tag (DESATIVADO) nova, ou se
    tiver descrição igual/mais detalhada que a atual — nunca troca um nome
    completo por um mais pobre (ex.: '0402 - CIRCULAR / BAIRROS 2' -> '0402'
    seria uma perda de informação, não uma atualização)."""
    desativado_novo = "(DESATIVADO)" in nome_novo.upper()
    desativado_atual = "(DESATIVADO)" in nome_atual.upper()
    if desativado_novo and not desativado_atual:
        return True
    palavras_atual = _palavras_relevantes(nome_atual)
    palavras_novo = _palavras_relevantes(nome_novo)
    return len(palavras_novo) >= len(palavras_atual)


def similaridade(nome_a: str, nome_b: str) -> float:
    """Jaccard entre as palavras (>=3 letras) da descrição de cada nome —
    usado pra distinguir 'mesma linha com nome variante' de 'linhas
    diferentes que colidiram no mesmo código por coincidência/erro no KML'."""
    ta = {w for w in _descricao_sem_codigo(nome_a).split() if len(w) >= 3}
    tb = {w for w in _descricao_sem_codigo(nome_b).split() if len(w) >= 3}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


LIMIAR_SIMILARIDADE = 0.25


def parse_coords(texto: str):
    pontos = []
    for token in texto.strip().split():
        partes = token.split(",")
        if len(partes) < 2:
            continue
        try:
            lon, lat = float(partes[0]), float(partes[1])
            pontos.append([lat, lon])
        except ValueError:
            continue
    return pontos


def parse_kml(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()

    candidatos = defaultdict(list)  # (codigo, sentido) -> [(nome, pontos), ...]

    for folder in root.findall(".//k:Folder", NS):
        fname_el = folder.find("k:name", NS)
        fname = fname_el.text.strip().upper() if fname_el is not None and fname_el.text else ""
        if fname not in ("IDA", "VOLTA"):
            continue
        sentido = fname.lower()

        for pm in folder.findall("k:Placemark", NS):
            n_el = pm.find("k:name", NS)
            nome = (n_el.text or "").strip() if n_el is not None else ""
            if not nome:
                continue
            cod = normalizar_codigo(nome)
            if not cod:
                continue
            coords_el = pm.find(".//k:coordinates", NS)
            if coords_el is None or not coords_el.text:
                continue
            pontos = parse_coords(coords_el.text)
            if not pontos:
                continue
            candidatos[(cod, sentido)].append((nome, pontos))

    # resolve duplicatas: prioriza "(DESATIVADO)", depois mais pontos —
    # MAS só quando os nomes parecem ser a mesma linha. Se dois candidatos
    # com o mesmo código tiverem descrições sem nada em comum, é provável
    # que sejam LINHAS DIFERENTES que colidiram por coincidência/erro no
    # KML (ex.: "0001 Terminal X Cruzeiro" vs "0001 Madrugadão Village II"
    # — a segunda deveria ser "M001"). Nesse caso não resolve sozinho.
    resolvidos = {}
    duplicatas_aviso = []
    ambiguos_aviso = []
    for chave, lista in candidatos.items():
        if len(lista) > 1:
            nomes = [n for n, _ in lista]
            pares_sim = [
                similaridade(nomes[i], nomes[j])
                for i in range(len(nomes))
                for j in range(i + 1, len(nomes))
            ]
            if min(pares_sim) < LIMIAR_SIMILARIDADE:
                ambiguos_aviso.append((chave, [(n, len(p)) for n, p in lista]))
                continue
            lista_ordenada = sorted(
                lista,
                key=lambda x: ("(DESATIVADO)" in x[0].upper(), len(x[1])),
                reverse=True,
            )
            duplicatas_aviso.append((chave, [(n, len(p)) for n, p in lista_ordenada]))
            resolvidos[chave] = lista_ordenada[0]
        else:
            resolvidos[chave] = lista[0]

    # agrupa por código só: nome preferido + coordenadas por sentido
    linhas = {}
    for (cod, sentido), (nome, pontos) in resolvidos.items():
        entry = linhas.setdefault(cod, {"nome": None, "ida": [], "volta": []})
        atual = entry["nome"]
        desativado_novo = "(DESATIVADO)" in nome.upper()
        desativado_atual = atual is not None and "(DESATIVADO)" in atual.upper()
        if atual is None or (desativado_novo and not desativado_atual) or (sentido == "ida" and not desativado_atual):
            entry["nome"] = nome
        entry[sentido] = pontos

    return linhas, duplicatas_aviso, ambiguos_aviso


def main():
    kml_linhas, duplicatas, ambiguos = parse_kml(KML_PATH)
    du = json.loads(DU_PATH.read_text(encoding="utf-8"))

    du_por_codigo = {}
    for chave in du:
        cod = normalizar_codigo(chave)
        if cod:
            du_por_codigo[cod] = chave

    novas, renomeadas, nomes_mantidos, trajeto_atualizado, ignoradas = [], [], [], [], []

    for cod, info in sorted(kml_linhas.items()):
        nome_kml = info["nome"]
        chave_existente = du_por_codigo.get(cod)

        if chave_existente is None:
            du[nome_kml] = {
                "ida": {"coordenadas": info["ida"], "ruas": []},
                "volta": {"coordenadas": info["volta"], "ruas": []},
            }
            novas.append((cod, nome_kml))
            continue

        entrada = du[chave_existente]

        if chave_existente != nome_kml and deve_renomear(chave_existente, nome_kml):
            du[nome_kml] = du.pop(chave_existente)
            entrada = du[nome_kml]
            renomeadas.append((cod, chave_existente, nome_kml))
        elif chave_existente != nome_kml:
            nomes_mantidos.append((cod, chave_existente, nome_kml))

        for sentido in ("ida", "volta"):
            novos_pontos = info[sentido]
            existentes = entrada[sentido]["coordenadas"]
            if novos_pontos and len(novos_pontos) > len(existentes):
                entrada[sentido]["coordenadas"] = novos_pontos
                trajeto_atualizado.append((cod, nome_kml, sentido, len(existentes), len(novos_pontos)))
            elif novos_pontos:
                ignoradas.append((cod, nome_kml, sentido, len(existentes), len(novos_pontos)))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = DU_PATH.with_suffix(f".{ts}.bak.json")
    shutil.copy(DU_PATH, bak)
    DU_PATH.write_text(json.dumps(du, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 70)
    print("SINCRONIZAÇÃO COM Mapa Reconstruido.kml")
    print("=" * 70)
    print(f"Backup salvo em: {bak.name}")

    print(f"\nLinhas novas criadas ({len(novas)}):")
    for cod, nome in novas:
        print(f"  [NOVA]      {cod:<7} {nome}  (sem itinerário de rua — pendente Matrix)")

    print(f"\nLinhas renomeadas ({len(renomeadas)}):")
    for cod, antigo, novo in renomeadas:
        print(f"  [RENOMEADA] {cod:<7} '{antigo}' -> '{novo}'")

    print(f"\nNomes diferentes no KML mas mantido o nome atual (KML tinha menos detalhe) ({len(nomes_mantidos)}):")
    for cod, atual, kml in nomes_mantidos:
        print(f"  [mantido nome] {cod:<7} atual: '{atual}'  |  KML: '{kml}'")

    print(f"\nTrajetos atualizados ({len(trajeto_atualizado)}):")
    for cod, nome, sentido, antes, depois in trajeto_atualizado:
        print(f"  [TRAJETO+]  {cod:<7} {nome[:48]:<48} {sentido.upper():<5} {antes}pts -> {depois}pts")

    print(f"\nTrajetos mantidos (KML tinha igual ou menos pontos) ({len(ignoradas)}):")
    for cod, nome, sentido, antes, depois in ignoradas:
        print(f"  [mantido]   {cod:<7} {nome[:48]:<48} {sentido.upper():<5} {antes}pts (KML tinha {depois}pts)")

    if duplicatas:
        print(f"\n⚠ Placemarks duplicados no KML — resolvidos automaticamente ({len(duplicatas)}):")
        for (cod, sentido), variantes in duplicatas:
            print(f"  {cod} ({sentido}):")
            for nome, npts in variantes:
                print(f"      \"{nome}\" -> {npts}pts")

    if ambiguos:
        print(f"\n🛑 AMBÍGUOS — NÃO aplicados, nomes muito diferentes pro mesmo código ({len(ambiguos)}):")
        print("   (provável colisão/erro de digitação no KML — revisar manualmente)")
        for (cod, sentido), variantes in ambiguos:
            print(f"  {cod} ({sentido}):")
            for nome, npts in variantes:
                print(f"      \"{nome}\" -> {npts}pts")

    print(f"\nTotal de linhas no sistema agora: {len(du)}")
    print("\nPróximo passo: python python/gerar_dados_estaticos.py")


if __name__ == "__main__":
    main()
