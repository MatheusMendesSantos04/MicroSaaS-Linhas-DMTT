# MELHORIAS.md — O que fazer no MicroSaaS Linhas DMTT

> Criado em 07/10/2026. Lista de melhorias e pendências levantadas numa revisão geral do projeto.
> Complementa o `CLAUDE.md` (que tem o contexto e as regras de trabalho). Marque `[x]` ao concluir.

## Onde o projeto está (07/10/2026)

- Repositório: `D:\portifolio\MicroSaaS-Linhas-DMTT` (movido do OneDrive). Branch `main`, já com o
  layout novo (a branch `redesign` foi mesclada). Último commit: `70fe298`.
- Produção: `https://dmtt.mendesweb.com` (estático, Hostinger), atualizado com tudo acima.
- Em nova máquina: `git pull`, depois `cd frontend && npm install` (o `node_modules` não vai no git),
  e criar o `.env` de deploy a partir do `.env.example` (nunca vai no git).
- Feito nesta sessão: grafias padronizadas (acentos/typos) e vias duplicadas unificadas pela forma
  mais usada, em `itinerario_completo.json`, `itinerario_mesclado.json`, `bairro-manual.json` e
  `dados_unificados.json` (backups em `data/json/_backup_grafias2/`); dois dashboards de eleição
  adicionados.

## Decisões em aberto (precisam de resposta do usuário)

- [ ] **`bairro-codigo.json` desatualizado.** Ainda tem as grafias antigas, e a página de bairros do
      site mostra isso. Regenerar (`python python/gerar_bairro_codigo.py`) **muda os códigos
      sequenciais** (a posição alfabética define o código). Decidir: regenerar agora, ou congelar o
      manual antes. E decidir se o código do Matrix passa a ser o principal.
- [ ] **Dois dashboards de eleição no ar.** "Eleição no ônibus — 2022 e 2026" (`eleicao-onibus`) e
      "Eleição 1º turno — passageiros, viagens e frota" (`eleicao-passageiros-viagens-frota`).
      Remover o antigo?
- [ ] **Vias que saíram de um bairro ao unificar.** `RUA JOSÉ CORRÊA DE MELO` (estava em VERGEL) e
      `RUA DOUTOR PONTES DE MIRANDA` (estava em FERNÃO VELHO) passaram a existir só em CRUZ DAS ALMAS
      e CENTRO. Se também devem aparecer nos bairros antigos, é preciso reavaliar.
- [ ] **Candidatos a duplicata ainda não tratados:** `RUA TRANSVERSAL DENISSON MENEZES 2` (cód. 06691)
      x `RUA DENISSON MENEZES 2` (06692); `RETORNO ...` x via normal (Fernandes Lima, Da Paz,
      Viaduto da PRF); `RUA DO SOL` x `RUA RECANTO DO SOL`; `AVENIDA A - BENEDITO BENTES` x
      `AVENIDA BENEDITO BENTES`; `Q. S1`/`Q W1` (provável typo). Marques/Marquês foi deixado como está.
- [ ] Linha **0006-M** não será feita (decisão já tomada). Linhas **0004** e **1000 A** sumiram da
      OSO e não estão marcadas `(DESATIVADO)`. **0024** e **0614** também precisam ser marcadas.

## Segurança e operação

1. [ ] **Trocar a senha SSH do deploy por chave SSH.** A senha fica no `.env`; chave reduz risco.
2. [ ] **Proteção dos dashboards "interno".** Hoje só o Power BI protege o link, e os HTMLs em
       `public/dashboards/` são acessíveis a quem souber a URL. A senha no site (já descrita no
       CLAUDE.md) ainda não foi implementada.
3. [ ] **Deploy em um só comando, com verificação.** Hoje são 4 passos manuais (pipeline, build,
       upload, commit). Criar um script `publicar` que rode tudo, valide os JSONs e confira o site
       (abre a home, busca uma rua) no final.
4. [ ] **Rollback.** O upload sobrescreve os arquivos. Subir numa pasta versionada e trocar, ou
       guardar o `dist` anterior.

## Dados (a parte mais frágil)

5. [ ] **Pipeline único com validação.** Fontes editadas à mão: `itinerario_completo.json`,
       `Mapa Reconstruido.kml` (em `data/kml/`) e `bairro-manual.json`. Criar um
       `rodar_pipeline.py` que execute `sincronizar_mapa_reconstruido` → `mesclar_itinerarios` →
       `aplicar_itinerarios_mesclado` → `gerar_dados_estaticos` e valide no final. Já houve ~12 dias
       de edições sem propagar.
       **Atenção:** `itinerario_completo.json` e `bairro-manual.json` têm formatação própria (CRLF,
       uma via por linha). Alterar por substituição de texto, nunca reserializar com `json.dump`.
6. [ ] **Checagem automática de nomes no pipeline:** acento inconsistente na mesma palavra, palavra a
       mais ou a menos, e mesmo código com grafias diferentes. Evita que o problema volte a cada
       edição manual.
7. [ ] **2.268 de 6.037 vias sem código DMTT.** Definir qual sistema de código vale (DMTT, Matrix ou
       o sequencial 0001–0715 do `bairro-codigo.json`).
8. [ ] **Linhas incompletas no sistema** (aparecem com mapa ou painel vazio): `0014` (2ª entrada,
       "Cruz das Almas X Centro / J.S. Peixoto"), `0112` (manual tem 2 variantes, sistema 1),
       `0612 A` e `1000 A`. A chave `402 - Circular Bairros II` deveria ser `0402`.
9. [ ] **Códigos de linha duplicados de propósito** (0014, 0109, 0209, 0617: 2 trajetos GPS cada).
       Criar um campo `variante` explícito em vez de depender de `normalizar_codigo()` e de aliases
       hardcoded. Não mexer em `normalizar_codigo()` antes disso (decisão do usuário).
10. [ ] **Itinerários só no sistema** (madrugadões 0001-M a 0005-M, 1000-B, 2058, 4000): vêm do Matrix
        e nunca passaram pelo manual. Colocá-los no `itinerario_completo.json` resolve vias sem
        bairro como `AVENIDA A`, `ALAMEDA B`, `RUA SÃO PEDRO`.
11. [ ] Pendências antigas: linha **0209** com volta 2 pontos GPS desatualizada; ambiguidade da
        **0001** no KML (2 placemarks com nomes diferentes); placemark "Trapiche / Ouro Preto via
        Jacintinho" sem o prefixo `0403 -`.

## Frontend

12. [ ] **Bundle de ~775 kB.** Carregar html2canvas e a geração de PDF sob demanda (`import()`);
        usar `manualChunks` no Vite.
13. [ ] **Exportação em PDF com bug** (backlog da Sessão 8): captura ida e volta no mesmo mapa. Fazer
        duas capturas separadas (IDA e VOLTA), reproduzir o erro "não está imprimindo o PDF certo" e
        incluir o card de quilometragem (`→ IDA 15.9 km · ← VOLTA 15.78 km · Total 31.68 km`).
14. [ ] **Dependência do Nominatim no navegador.** Serviço público com limite de uso; o clique no mapa
        depende dele. Ter fallback ou cache.
15. [ ] **Acessibilidade e mobile.** Sem auditoria até agora (os dashboards são públicos).
16. [ ] **Padronizar o cadastro de dashboards.** Cada novo exige copiar o HTML, gerar a capa à mão e
        editar `frontend/src/dashboardsConfig.js`. Um script que gere a capa (print do HTML), valide e
        registre o card evitaria erros. Como foi feito: HTML em `frontend/public/dashboards/`, capa em
        `frontend/src/assets/dashboards/`; o print saiu via Playwright com ~6 s de espera (o HTML tem
        animação de contagem, e um print antes disso sai com números errados).

## Repositório

17. [ ] **Limpeza.** Há vários `Mapa Reconstruido*.kml` e `.bak.kml` soltos na raiz, scripts de debug
        misturados com os de produção (`python/_debug_*.py`, `tes.py`) e backups grandes de JSON.
        Melhorar o `.gitignore` e criar uma pasta de arquivo morto.
18. [ ] **Backend FastAPI** só serve de referência e pode divergir do `staticApi.js`. Remover, ou usar
        como teste de regressão (comparar respostas com as do JS).
19. [ ] **Testes.** Prioridade: busca por rua e horário (`staticApi.js`) e a geração dos JSONs
        estáticos.
20. [ ] **Enxugar o `CLAUDE.md`.** Separar "regras e comandos" (curto) de um `HISTORICO.md` com as
        sessões e fases antigas.
21. [ ] Feature **Zonas (bairros)** foi para produção junto com o layout novo, apesar de o CLAUDE.md
        dizer para não subir. Confirmar se é isso mesmo que se quer.

## Ordem sugerida

1. Pipeline único com validação (itens 3, 5, 6).
2. Chave SSH no deploy (item 1).
3. Limpeza do repo e do CLAUDE.md (itens 17 e 20).
4. Corrigir o PDF (item 13) e fechar as linhas incompletas (item 8).
5. Resolver as decisões em aberto do topo, que destravam os itens 7 e 10.
