"""
Compara a nova OSO (02/09/2026) com dados_unificados.json -- linhas que
sumiram do sistema e linhas novas que a OSO tem mas o sistema nao.

Uso:
    python python/comparar_nova_oso.py
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sincronizar_mapa_reconstruido import normalizar_codigo

ROOT = Path(__file__).resolve().parents[1]
DU_PATH = ROOT / "data" / "json" / "dados_unificados.json"

OSO = [
    ("0012", "CONJ. JOSÉ S. PEIXOTO/CENTRO"), ("0014", "C DAS ALMAS/CENTRO(PEIXOTO-RODOV-MERCAD)"),
    ("0027", "VILA SAEM/CENTRO(PINHEIRO-PITANGUINHA)"), ("0033", "JOSÉ TENÓRIO/CENTRO (ROTARY-GRUTA)"),
    ("0036", "DUBEAUX LEÃO/CENTRO"), ("0041", "FEITOSA / CENTRO / PIABAS / C. DAS ALMAS"),
    ("0109", "C DAS ALMAS/TRAPICHE-VERGEL(P. VDE/POÇO)"), ("0112", "IPIOCA/TRAPICH-VERGEL(P VDE-POÇO-J. LEÃO"),
    ("0114", "C DAS ALMAS/TRAPICHE(JACINTINHO-J. LEÃO)"), ("0116", "JOSÉ TENÓRIO/TRAPICHE(VIA CRUZ DAS ALMAS"),
    ("0209", "C DAS ALMAS/VERGEL(STº EDUARDO-J LEÃO)"), ("0403", "TRAPICHE/OURO PRETO(JACINTINHO-FAROL)"),
    ("0404", "TRAPICHE/NOVO MUNDO(FAROL-JACINTINHO)"), ("0501", "VERGEL/SÃO JORGE(MERCADO-JACINTINHO)"),
    ("0502", "VERGEL/SÃO JORGE(MERCADO-FAROL)"), ("0504", "TRAPICHE/SÃO JORGE(PTA VERDE-JACARECICA)"),
    ("0603", "VERGEL/MIRANTE(VIA POÇO - PÇA BOMFIM)"), ("0604", "EUST. GOMES/C. DAS ALMAS(VIA UFAL-ROTARY"),
    ("0606", "JOSÉ TENÓRIO/MANGABEIRAS(ROTARY-GRUTA)"), ("0610", "CRUZ DAS ALMAS/OURO PRETO (VIA GRUTA)"),
    ("0617", "C DAS ALMAS/IPIOCA(SAÚDE-SAUAÇUHY)"), ("0700", "GRUTA/PONTA VERDE-VIA JACINT.(T. ROTARY)"),
    ("0708", "CRUZ DAS ALMAS / PTA VERDE/TER. ROD. JAC"), ("0900", "CRUZ DAS ALMAS/UFAL (VIA JOSÉ TENÓRIO)"),
    ("1000-B", "TRAPICHE/PONTAL(VILA DOS PESCADORES)"), ("1001", "CIRCULAR CRUZ DAS ALMAS"),
    ("1018", "A. DO CRUZEIRO/AL 101 NORTE(ANDRAÚJO)"), ("1019", "T. SAUAÇUHY/ALTO DE IPIOCA(ALTO DO BOI)"),
    ("1020", "C. DAS ALMAS/SÃO JORGE(JOSEPHA DE MELO)"), ("1022", "C.DAS ALMAS/ALTO DE GUAXUMA(JACARECICA)"),
    ("1023", "C. DAS ALMAS/J. TENÓRIO(L. ÓLEO-MURILÓP)"), ("1024", "TERMINAL ROTARY/TERMINAL CRUZ DAS ALMAS"),
    ("0004-M", "OURO PRETO/PONTA VERDE (FEITOSA)"), ("0005-M", "IPIOCA/PONTAL (PONTA VERDE)"),
    ("0800", "CATRACA DE SOLO T.I. BENEDITO BENTES"), ("0902", "CATRACA DE SOLO T.I. EUSTÁQUIO GOMES"),
    ("0037", "SALVADOR LIRA/CENTRO"), ("0039", "CLETO MARQUES LUZ/CENTRO"),
    ("0042", "BEN. BENTES / CENTRO / SALVADOR LIRA"), ("0046", "VILLAGE CAMPESTRE II / CENTRO"),
    ("0048", "BEN. BENTES/CENTRO(VIA JOSEPHA DE MELO)"), ("0052", "T.I. EUST GOMES/CENTRO(CAMBUCÍ/S. LÚCIA)"),
    ("0053", "GRACILIANO RAMOS/CENTRO(FAROL)"), ("0104", "BENEDITO BENTES/TRAPICHE(VIA JACINTINHO)"),
    ("0105", "JARD PETROPÓLIS/TRAPICHE/TERM SALV. LYRA"), ("0110", "GRACILIANO RAMOS/TRAPICHE(T. ROD.)"),
    ("0113", "T.I. EUST. GOMES/TRAPICHE(CENTRO-VERGEL)"), ("0117", "VILLAGE II/TRAPICHE(CAMBUCÍ-RODOVIÁRIA)"),
    ("0214", "HENRIQUE EQUELMAN/VERGEL-TER. A. ALEGRIA"), ("0217", "BENEDITO BENTES/MERCADO/FEITOSA"),
    ("0601", "BEN. BENTES/JATIÚCA(VIA ROTA DO MAR)"), ("0602", "S. LIRA/IGUAT./VIA D.LEÃO/CLETO/P.VERDE"),
    ("0607", "T.I. EUST. GOMES/MANGABEIRAS(MCZ SHOP)"), ("0612", "E GOMES/JATIÚCA (VIA CENTRO-PONTA VERDE)"),
    ("0615", "E. GOMES/MANGABEIRAS(M. MARCELO/J. MELO)"), ("0703", "BENEDITO BENTES/PONTA VERDE"),
    ("0704", "BENEDITO BENTES/PONTA VERDE/FAROL"), ("0706", "T.I. EUST. GOMES/PT VERDE(J. MELO-JACINT"),
    ("0707", "GRAC. RAMOS/P. VERDE(JACINT. - J DE MEL)"), ("0720", "DENISSON MENEZES/PONTA VERDE(FAROL)"),
    ("0727", "EUSTÁQUIO GOMES/PTA VERDE(VILLAGE II)"), ("0901", "T.I. B. BENTES/T.I. E. GOMES(H. METROP)"),
    ("0903", "T.I. B.BENTES/T.I EUST. GOMES(G. VIL II)"),
    ("0804", "CONJ. CIDADE SORRISO I/TER. B. BENTES"), ("0805", "GUAXUMA/TERMINAL DO BENEDITO BENTES"),
    ("0807", "JOSÉ APRÍGIO VILLELA / T.I. B. BENTES"), ("0809", "SELMA BANDEIRA/TERMINAL BENEDITO BENTES"),
    ("0812", "PQE DAS AMERICAS/C.CARMINHA/T.B.BENTES"), ("1000", "TRAPICHE/PONTAL(V. DOS PESCADORES)"),
    ("4000", "CIRCULAR UFAL (INTEGRAÇÃO)"), ("4003", "T.I. EUST. GOMES/GRAN JARDIM(MACEIÓ 1)"),
    ("4006", "TERMINAL MOCAMBO/T.I. BENEDITO BENTES"), ("4011", "TERM. SAL. LYRA / TERM. INTEG. VIA REC."),
    ("4013", "T.I. EUSTÁQUIO GOMES/FORENE(J SAÚDE)"), ("4014", "T.I. EUSTÁQUIO GOMES/N JARDIM-JD ROYAL"),
    ("4015", "T.I. EUST. GOMES/JD. AMARILIS(FLAMBOYANT"),
    ("0001-M", "VILLAGE II/PONTA VERDE(GRACILIANO RAMOS)"), ("0002-M", "BENEDITO BENTES/PONTA VERDE (TRAPICHE)"),
    ("0003-M", "EUSTÁQUIO GOMES/PONTA VERDE (TRAPICHE)"),
    ("0051", "SANTOS DUMONT/CENTRO(VIA POÇO)"), ("0056", "JOÃO SAMPAIO I / CENTRO / FAROL"),
    ("0057", "RIO NOVO / CENTRO / VIA COLINA"), ("0058", "FERNÃO VELHO / CENTRO / B. GONZAGA"),
    ("0065", "ROSANE COLLOR / CENTRO (FAROL)"), ("0068", "COLINA/CENTRO(SANTA AMÉLIA - FAROL)"),
    ("0069", "CLIMA BOM / CENTRO / FAROL"), ("0101", "CHÃ DA JAQUEIRA/TRAPICHE(J.S.-B. PARTO)"),
    ("0102", "JOÃO SAMPAIO/TRAPICHE(ROTARY-JACINTINHO)"), ("0108", "CLIMA BOM / TRAPICHE / BEBEDOURO"),
    ("0115", "CHÃ DA JAQUEIRA/TRAPICHE(CENTRO-PRADO)"), ("0301", "VILLAGE II/C. DA JAQUEIRA(UFAL-COLINA)"),
    ("0401", "CIRCULAR / BAIRROS 1"), ("0402", "CIRCULAR / BAIRROS 2"),
    ("0612-A", "E GOMES/JATIÚCA(VIA CENTRO-PONTA VERDE)"), ("0709", "CHÃ DA JAQUEIRA / PONTA VERDE / MUTIRÃO"),
    ("0710", "CHÃ DA JAQUEIRA/PONTA VERDE/BOA VISTA"), ("0712", "SANTO DUMONT/ PONTA VERDE/ IGUATEMI"),
    ("0714", "RIO NOVO/PONTA VERDE(FAROL-JACINTINHO)"), ("0716", "CLIMA BOM/PTA.VERDE/IGUATEMI/V.FAROL"),
    ("0719", "CHÃ NOVA/PONTA VERDE(VIA J. SAMPAIO)"), ("0723", "ROSANE COLLOR/PONTA VERDE(B PARTO-JACINT"),
    ("0802", "T.I. COLINA/T.I. B. BENTES(C BOM-CORREI)"),
    ("0006-M", "CLIMA BOM/PONTA VERDE (FERNÃO VELHO)"), ("2058", "FERNÃO VELHO/COLINA-VIA FEIRINHA-M. NETO"),
    ("0999", "JOÃO SAMPAIO/FLEXAIS-VIA CHÃ DA JAQUEIRA"),
]


def norm_oso(c: str) -> str:
    c = c.upper().strip()
    m = re.match(r"^(\d+)-?(M|A|B)?$", c)
    if m:
        num, suf = m.groups()
        return num + (suf or "")
    return c.replace("-", "")


def main():
    print("total linhas na nova OSO:", len(OSO))

    oso_norm = {}
    for cod, nome in OSO:
        oso_norm[norm_oso(cod)] = (cod, nome)

    # mesmo bug/correcao do aplicar_itinerarios_mesclado.py: "C DAS ALMAS"
    # colado no codigo sem separador confunde normalizar_codigo()
    ALIAS = {"0014C": "0014", "0109C": "0109", "0209C": "0209", "0617C": "0617"}

    du = json.loads(DU_PATH.read_text(encoding="utf-8"))
    sis_norm = {}
    for nome in du:
        c = normalizar_codigo(nome)
        c = ALIAS.get(c, c)
        if c:
            sis_norm.setdefault(c, []).append(nome)

    novas = sorted(set(oso_norm) - set(sis_norm))
    sumidas = sorted(set(sis_norm) - set(oso_norm))

    print()
    print(f"=== Linhas da nova OSO que NAO estao no sistema (novas p/ nos) -- {len(novas)} ===")
    for c in novas:
        cod_orig, nome = oso_norm[c]
        print(f"  {cod_orig:<8} {nome}")

    print()
    print(f"=== Linhas do sistema que NAO aparecem na nova OSO -- {len(sumidas)} ===")
    for c in sumidas:
        for nome in sis_norm[c]:
            print(f"  {c:<8} {nome}")


if __name__ == "__main__":
    main()
