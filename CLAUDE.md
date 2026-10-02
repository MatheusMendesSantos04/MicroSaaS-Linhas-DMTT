# CLAUDE.md — MicroSaaS Linhas DMTT

> Este arquivo é lido automaticamente pelo Claude Code em toda sessão.
> Mantenha-o atualizado após cada sessão de trabalho.
> Última atualização: 02/10/2026 — ver seção **"Sessão 11"** logo abaixo pra contexto da sessão
> mais recente; depois **"Sessão 10"** e **"Sessão 9"** pra contexto mais antigo ainda válido.

## Sessão 11 (02/10/2026) — resumo pra quem chega agora

Sessão longa e variada. Tudo abaixo está **só local** (localhost:5173) — **NADA foi pra produção**
(`dmtt.mendesweb.com` continua com a versão antiga, inclusive o mapa quebrado do CARTO).

### 1. Pipeline de dados FOI RODADO (o aviso de "pipeline desatualizado" da sessão anterior caiu)
Ordem usada: `sincronizar_mapa_reconstruido.py` → `mesclar_itinerarios.py` →
`aplicar_itinerarios_mesclado.py` → `gerar_dados_estaticos.py`. Sistema: **114 linhas**.
- **Linha 1001 (Circular Cruz das Almas) adicionada**: itinerário no `itinerario_completo.json`
  (nomes expandidos, mesmo padrão do manual), traçado IDA/VOLTA no `Mapa Reconstruido.kml` (pastas
  IDA e VOLTA), e os códigos DMTT das vias preenchidos à mão no `dados_unificados.json` a partir do
  PDF oficial (00906, 00221, 00206, 06212, 00703, 00223, 06357, 00580).
- **OSO de 02/10/2026** comparada: `python python/comparar_oso_pdf.py "<pdf>"` (lê o PDF direto,
  sem lista fixa; substitui o uso de `comparar_nova_oso.py` pra OSOs novas). Faltavam só 0004-M e
  0006-M — a **0004-M é a `M004`** do sistema (só o formato do código muda), então só a **0006-M**
  falta, e o usuário disse que **não vai fazer agora**.
- **Ainda pendentes:** variantes da **0112** (pulada no `aplicar`); chave `402 - Circular Bairros II`
  (sem o zero, deveria ser `0402`); marcar **0024 e 0614** como desativadas (não estão na OSO nova;
  0221/0223/0226/0613 já estão marcadas); ambiguidade da **0001** no KML.

### 2. Diagnóstico manual × sistema (relatório: `data/relatorios/diagnostico_manual_x_sistema.txt`)
92 linhas têm itinerário idêntico ao manual. As diferenças reais:
- **Códigos repetidos no sistema (2 entradas, GPS diferente):** 0014, 0109, 0209, 0617, 0612/0612 A,
  1000/1000 A. (0109/0209/0617 são 2 trajetos GPS de propósito.)
- **4 entradas SEM itinerário nenhum** (aparecem no site com mapa e painel vazio): 0014 (a 2ª,
  "Cruz das Almas X Centro / J.S. Peixoto"), 0112, 0612 A, 1000 A.
- **9 entradas só no sistema** (madrugadões 0001–0005-M, 1000-B, 2058, 4000, `402`): **56 vias** só
  existem nelas — vêm de dados antigos do Matrix, nunca passaram pelo manual. É daí que vêm nomes
  sem bairro tipo "RUA E", "AVENIDA A/B", "ALAMEDA B", "RUA SÃO PEDRO", "RUA SETE DE SETEMBRO".
- **2.268 de 6.037 vias do sistema sem código DMTT.**

### 3. Correções de grafia / duplicatas (relatório: `data/relatorios/vias_quase_duplicadas.txt`)
- Busca por "rua e" mostrava uma "RUA E" solta (da 0002-M): renomeada pra
  `RUA E - BENEDITO BENTES` direto no `dados_unificados.json` (backup
  `data/json/dados_unificados.antes_rua_e.bak.json`).
- Pares quase iguais (typos) padronizados nos 3 arquivos (manual, sistema, bairro-manual): Alice
  CAROLINA, Arnon de MELO, Batista ACIOLY, TEOBALDO Barbosa, IND Cícero Toledo, Tabuleiro dos
  MARTINS, Rua A | QUATORZE, + variantes só de acento (Luís Pontes de Miranda, Rotatoria do Viaduto
  da PRF, Presidente Getulio Vargas, João de Azevedo Filho, 1 Rotatoria - Jardim Royal).
- **José AILTON x José HAILTON dos Santos NÃO foram unificados** — estão em bairros diferentes
  (Cidade Universitária / Tabuleiro do Martins) e têm códigos Matrix distintos (provável trechos
  diferentes). Reverter só se o usuário disser que é typo.
- **Não são duplicatas (não mexer):** rotatórias I–IV do Jardim Royal/Novo Jardim, Otacílio x
  Tarcísio de Jesus, "Q G" x "Rua G" do Benedito Bentes.
- Backups pré-troca: `data/json/_backup_grafias/` (apagar quando o usuário confirmar).
- **Vias sem bairro nas linhas fora do manual ainda a corrigir:** `AVENIDA A` (0002-M, só candidato
  "Benedito Bentes"), `ALAMEDA B` (1000-B, só "Terminal Pontal da Barra"); `AVENIDA B`, `RUA SÃO
  PEDRO`, `RUA SETE DE SETEMBRO` são ambíguas (perguntar). A solução definitiva é colocar essas
  linhas no `itinerario_completo.json`.
- **Lição:** `itinerario_completo.json` e `bairro-manual.json` têm formatação própria (editados à
  mão, CRLF, listas com 1 item por linha) — **alterar por substituição de TEXTO (regex sobre os
  literais de string), nunca reserializar com `json.dump`** (reformata o arquivo todo). Rodar antes
  em modo simulação e validar com `json.loads` + `validar_bairro_manual.py`.

### 4. Bairros × códigos (tudo em `data/json/bairros/`)
- `bairro-manual.json` **foi movido** de `data/relatorios/` pra cá (validador
  `validar_bairro_manual.py` já aponta pro novo caminho; hoje 0 problemas).
- **`bairro-codigo.json`** (gerado por `python python/gerar_bairro_codigo.py`): 50 bairros em ordem
  alfabética (ignorando acento), vias de cada bairro em ordem alfabética, **código novo sequencial
  contínuo 0001–0715** (715 vias, sem duplicadas/vazias). ⚠️ **Os códigos dependem da posição
  alfabética: qualquer via/bairro novo desloca todos os seguintes** — congelar o manual antes de usar
  esses códigos no sistema. Eles mudaram 1–2 posições na limpeza de duplicatas desta sessão.
- **`matrix-codigos.json`** (gerado por `python python/extrair_codigos_matrix.py`): os 1.495
  códigos de via do Matrix, extraídos de `data/pdf-intinerarios-por-via-todas-linhas/
  sre_relatorio_via_logradouro-codigo-das-ruas.pdf`. Cada item tem `via` (abreviações expandidas:
  AV.→AVENIDA, R.→RUA, DR.→DOUTOR, CONJ.→CONJUNTO, etc.) e `via_original` (como está no Matrix).
  Iniciais de nome (J., B.) e abreviações de sobrenome ficam como estão (não dá pra expandir sem
  adivinhar).
- **`python python/atualizar_bairro_com_matrix.py`** cruza os dois por nome normalizado e grava
  `codigo_matrix`/`via_matrix` em cada via do `bairro-codigo.json`: **379 de 715 casam**. Gera
  `bairro-matrix-candidatos.txt` (117 casamentos aproximados ≥0.85, **NÃO aplicados** — alguns
  errados, ex. AVENIDA x RUA Getúlio Vargas) e `bairro-sem-matrix.txt`. O código novo sequencial
  **não** é substituído pelo do Matrix (decisão em aberto: usar o do Matrix como principal?).
- **`python python/gerar_pdf_bairro_codigo.py`** → `bairro-codigo.pdf` (20 páginas, bairro →
  vias com código). Fica **desatualizado se o manual mudar** — regerar.
- Ordem pra regerar tudo depois de mexer no `bairro-manual.json`: `gerar_bairro_codigo.py` →
  `atualizar_bairro_com_matrix.py` → `gerar_pdf_bairro_codigo.py` → `gerar_dados_estaticos.py`
  (este copia `bairro-codigo.json` e `matrix-codigos.json` pra `frontend/public/data/`).
- **Página `/bairros`** (`frontend/src/pages/BairrosPage.jsx`) com 2 abas: "Bairros (novos
  códigos)" — cartões por bairro, selo preto com o código novo e selo amarelo "M 00771" com o do
  Matrix, busca por via/bairro/código — e "Códigos do Matrix" (1.495 códigos, busca, mostra no
  máximo 300 por vez, tooltip com o nome original abreviado).

### 5. Dashboards
- Novo card **"EMBARQUES — LINHA 4003"** (ponto da Reserva das Águas, 25–27/09/2026): HTML autônomo
  em `frontend/public/dashboards/embarques-4003.html` (origem: `I:\embarques - linhas futuras\
  PASSAGEIROS 4003\dados\dashboard_4003_25-27set.html`), capa gerada com Edge headless
  (`msedge --headless=new --screenshot`) em `frontend/src/assets/dashboards/embarques-4003.png`.
  O HTML usa só fonte Geist (Google Fonts) e a lib Motion (jsDelivr) por CDN.
- Marcado `tipo: "publico"` — **qualquer pessoa com o link acessa** (tem número de carro e dados
  por viagem). A camada de senha pra dashboards "interno" continua só como ideia (ver Backlog).

### 6. REDESIGN: layout preto + amarelo da logo (aplicado no app, só local)
- **Paleta:** preto `#0A0A0A` + amarelo `#F2C200` (estimado da logo, ~`#F0C000`) + neutros do
  shadcn (canvas `#F5F5F5`, papel `#FFF`, borda `#E5E5E5`). Amarelo **nunca como texto sobre
  branco** (contraste) — só preenchimento com texto preto. **Cores funcionais do mapa intactas:**
  IDA `#16A34A`, VOLTA `#2E64D4`, destaque de rua `#E0A400`.
- **Estrutura:** navbar preta com filete amarelo e navegação em pílulas (ativa = amarela); conteúdo
  claro; painel lateral (sidebar) **preto** com brilho amarelo que segue o mouse; mapa e painel em
  cartões de 24px; controles do Leaflet e legenda/caixa de contexto em "vidro fosco".
- **Página Sobre REMOVIDA** (rota, link e `SobrePage.jsx`).
- **Fonte:** Geist + Geist Mono **hospedadas no site** (`@fontsource-variable/geist`,
  `@fontsource-variable/geist-mono`, importadas no `styles.css`) — não dependem do Google Fonts.
- `frontend/src/styles.css` foi **reescrito inteiro** (mesmos nomes de classe dos componentes).
  Efeitos: entrada escalonada, hover com elevação, contagem animada dos km (`CountUp` em
  `ItinerarioPanel.jsx`), foco amarelo; tudo desligado com `prefers-reduced-motion`.
- **Responsivo:** ≤900px o mapa fica em cima e a página inteira rola; ≤640px a navegação vira barra
  flutuante preta no rodapé. Contêiner de página ocupa a largura toda (barra de rolagem na borda da
  janela), conteúdo centralizado por padding (`--w`).
- **Armadilha de z-index:** `.controls` precisa de `position: relative; z-index: 20`, senão a lista
  do seletor de linhas fica ATRÁS do mapa (animação de entrada cria contexto de empilhamento).
- **Rascunho estático** (aprovado) em `ideias/rascunho-novo-layout.html` (dados fictícios).
- Mapa: padrão agora **"Mapa"** (Esri World_Street_Map); estilos Mapa / Satélite / **Híbrido**
  (satélite + rótulos de transporte e lugares) / Claro / Escuro / OpenStreetMap. Terminais e zonas
  usam o amarelo da marca.
- **Hover de zona/terminal (nome do bairro/terminal):** as rotas são desenhadas em canvas por cima
  de tudo e engolem os eventos do mouse, então tooltips por camada NUNCA funcionaram. Resolvido no
  nível do mapa (`HoverInfo` em `MapView.jsx`): terminal mais próximo (14px) tem prioridade, senão
  point-in-polygon contra `zonas.json`; mostra etiqueta preta com contorno amarelo e realça a zona.
  Não existe hover no celular (não testado em toque).

### 7. Armadilhas de ambiente (Windows) descobertas
- **PowerShell estraga aspas** em `python -c "..."` longos — gravar o script num arquivo (scratchpad)
  e rodar. Heredoc bash com texto longo também falhou uma vez; escrever o arquivo com a ferramenta
  Write é mais seguro. Em regex dentro de string normal, `\b` vira caractere de controle: usar raw.
- **Edge headless** tem largura mínima (~500px: capturas "de celular" saem cortadas) e não termina
  animações com `--virtual-time-budget`; usar `--force-prefers-reduced-motion` pra capturar o estado
  final. Pra testar celular de verdade, usar o painel do navegador com `resize_window` mobile.
- Console do Windows mostra acentos quebrados (cp1252) — os arquivos estão em UTF-8; usar
  `PYTHONIOENCODING=utf-8`.
- Aviso do VSCode ("content is newer" → Overwrite) continua valendo pros arquivos editados à mão.

### 8. O que falta pra publicar (decisões com o usuário)
Nada disso foi deployado. Um deploy leva junto: mapa Esri (corrige "API KEY REQUIRED"), página
Bairros, dashboard 4003, dados atualizados (1001 etc.) e o redesign. **Perguntar antes:** (a) esconder
o toggle "Zonas (bairros)" (o usuário pediu pra não publicar essa feature)? (b) dashboard 4003 público
tudo bem? Passos: `npm run build` → `python python/deploy_frontend.py` (SSH costuma estar bloqueado na
rede do escritório). Rodar `vite build` localmente só atualiza `dist/` (ignorado pelo git).

### 9. Pendências abertas (resumo)
0112; entradas vazias/duplicadas (0014 2ª, 0612 A, 1000 A); chave `402`→`0402`; 0024/0614
desativadas?; 0006-M (adiado); colocar madrugadões/1000-B/2058/4000 no manual (56 vias pra revisar);
`AVENIDA A`/`ALAMEDA B` sem bairro; 2.268 vias sem código; 117 candidatos Matrix; usar código Matrix
como principal?; hover em tela de toque; Zonas (bairros) segue pausado.

---

## Sessão 10 — resumo pra quem chega agora

Sessão focada inteiramente em finalizar e validar `data/relatorios/bairro-manual.json` (o
mapeamento manual bairro→vias mencionado no item 8 da Sessão 9). Pontos essenciais:

1. **`data/relatorios/bairro-manual.json` está FINALIZADO e validado** — 724 vias classificadas
   em 50 bairros, cobrindo **100%** das vias únicas do `itinerario_completo.json` (0 faltando,
   0 duplicadas em mais de um bairro, 0 divergência de grafia). Continua sendo um documento
   **interno/de referência** — não sobe pro sistema nem pra produção (serve pra planejar códigos
   novos pras vias sem código DMTT oficial, conforme já documentado na Sessão 9).
2. **Script novo: `python/validar_bairro_manual.py`** — compara `bairro-manual.json` com
   `itinerario_completo.json` e reporta 3 coisas: (a) vias no bairro-manual sem correspondência
   exata no itinerário (possível erro de digitação ou via que não vem de nenhuma linha de
   ônibus), (b) vias do itinerário ausentes no bairro-manual, (c) vias que aparecem em mais de um
   bairro. Rodar esse script sempre que o usuário disser que mexeu em qualquer um dos dois
   arquivos — ele é rápido (alguns segundos) e pega regressão na hora.
3. **Ciclo de correção usado (repetir se o bairro-manual precisar de nova rodada de limpeza):**
   - Rodar `validar_bairro_manual.py`, olhar os "sem correspondência exata" com score alto
     (≥0.90) ou tag `acento/pontuacao` — esses são candidatos fortes a erro de digitação real.
   - **Nunca aplicar correção só pelo score** — sempre checar se os dois nomes não são pessoas/
     lugares genuinamente diferentes antes de substituir (ex.: "RUA CLÁUDIO MANOEL" ≠ "RUA
     CLAUDIO LIVIO", mesmo com score 0.74 — são pessoas diferentes). Ver lição da sessão anterior
     sobre o incidente Otacílio/Tarcísio (fuzzy match alto não garante que é a mesma via).
   - Pra vias "faltando" (existem no itinerário mas não em nenhum bairro), usar o contexto de
     ruas vizinhas na mesma linha/sentido do `itinerario_completo.json` pra sugerir o bairro mais
     provável — funciona bem pra nomes próprios, mas nomes genéricos tipo "RUA G", "RUA I",
     "RETORNO" tendem a ser ruas **diferentes** repetidas em vários bairros (não dá pra assumir
     um bairro só com segurança nesses casos — sempre perguntar ao usuário).
4. **⚠️ Cuidado com conflito de save do VSCode nesse arquivo.** Durante a sessão, o usuário tinha
   o `bairro-manual.json` aberto no editor desde ANTES de eu aplicar uma correção via script. Ao
   tentar salvar depois, o VSCode mostrou "Failed to save: The content of the file is newer" —
   se o usuário clicar **"Overwrite"** nesse diálogo, ele sobrescreve com a versão antiga do
   buffer do editor e **desfaz qualquer correção aplicada por script entre a abertura do arquivo
   e aquele save**, silenciosamente. Isso aconteceu aqui e precisou de uma segunda rodada pra
   reconciliar. Sempre que for editar esse arquivo (ou qualquer um que o usuário possa ter aberto
   no editor) via script, **avisar o usuário pra recarregar o arquivo no editor antes de editar
   nele de novo**, ou pelo menos checar `mtime` antes/depois de cada round-trip de edição pra
   detectar esse tipo de conflito cedo.
5. **`itinerario_completo.json` também foi editado nesta sessão** (expansão de abreviações tipo
   "CONJ"→"CONJUNTO", "TEN"→"TENENTE", e acentos restaurados em várias vias). Isso significa que
   qualquer correção de grafia aplicada no bairro-manual precisa usar a grafia **atual** do
   itinerário como referência, não uma versão memorizada de sessões anteriores — sempre reler o
   arquivo antes de assumir qual é "a grafia certa".
6. **Pipeline de produção (`mesclar_itinerarios.py` → `aplicar_itinerarios_mesclado.py` →
   `gerar_dados_estaticos.py`) NÃO foi rodado nesta sessão** — o trabalho foi todo no
   bairro-manual.json (documento à parte, não entra no pipeline). Ver aviso no topo do arquivo:
   o sistema está ~1 mês desatualizado em relação ao `itinerario_completo.json` atual.
7. Usuário mencionou que o próximo passo é **"os testes"** — sem detalhes ainda do que isso
   envolve. Perguntar no início da próxima sessão se não houver contexto adicional.

---

## Sessão 9 — resumo pra quem chega agora

Sessão longa (várias conversas seguidas). Pontos essenciais pra continuar sem perder contexto:

1. **`data/json/intinerario manual/itinerario_completo.json` é a fonte de verdade do itinerário
   agora** — o usuário edita esse arquivo diretamente (ida/volta por linha, só nome de rua, sem
   código). Nunca editar `itinerario_mesclado.json` (é gerado, sobrescrito toda vez).
2. **Pipeline pra aplicar edições do manual no sistema**, sempre nessa ordem:
   ```bash
   python python/mesclar_itinerarios.py            # itinerario_completo.json -> itinerario_mesclado.json
   python python/aplicar_itinerarios_mesclado.py    # aplica no dados_unificados.json (backup automático)
   python python/gerar_dados_estaticos.py           # regenera frontend/public/data/*.json
   ```
   Rodar isso **toda vez** que o usuário disser que editou o `itinerario_completo.json`. Checar o
   `mtime` do arquivo antes (`ls -la`) pra confirmar que realmente mudou desde a última rodada.
3. **`data/kml/Mapa Reconstruido.kml` é o KML canônico** (não o da raiz do projeto — esse é
   histórico/versões antigas, tem vários `Mapa Reconstruido*.kml` soltos na raiz, ignorar).
   `python/sincronizar_mapa_reconstruido.py` sincroniza esse KML → `dados_unificados.json`
   (coordenadas GPS). Regra atual: **o KML sempre vence** (sem checagem de "mais pontos que o
   atual" — já foi decidido e implementado, não é mais backlog).
4. **Bug conhecido em `normalizar_codigo()`** (usado em vários scripts): quando o nome da linha
   tem abreviação tipo "C DAS ALMAS" colada sem separador logo após o código, a letra é lida como
   sufixo do código (`0209` vira `0209C`). Isso já causou linhas (0109, 0209, 0617) ficarem "presas"
   sem receber atualização do manual depois que a sincronização do KML renomeou a chave delas nesse
   formato. Corrigido com um dicionário de alias pontual em `aplicar_itinerarios_mesclado.py`
   (`ALIAS_CODIGO_SISTEMA`) — **não mexer na função `normalizar_codigo()` em si**, o usuário já
   confirmou que prefere manter o comportamento atual (evita colisão com duplicatas reais de código
   tipo 0014/0109/0209/0617, que são 2 trajetos GPS diferentes com o mesmo código, de propósito).
5. **Zonas de bairro (polígonos) — feature pausada, NÃO deployar.** Existe um toggle "Zonas
   (bairros)" no `MapStyleSelector` e `frontend/public/data/zonas.json` (50 bairros com polígono,
   de 53 oficiais). O usuário disse explicitamente pra não subir isso em produção ainda ("ainda vou
   fazer atualizações na ideia"). Ver seção própria mais abaixo.
6. **Tiles do mapa: CARTO quebrou** (passou a exigir API key, sem aviso). Trocado pra Esri
   (`server.arcgisonline.com`, grátis, sem key) em `MapView.jsx`. **Isso já está certo no código,
   mas só foi buildado localmente — confirmar se já foi deployado em produção** antes de assumir
   que `dmtt.mendesweb.com` está com o mapa funcionando.
7. **Relatório "Vias por Bairro"** (`data/vias-por-bairro/vias_por_bairro.pdf`) — cruza o PDF
   oficial da DMTT (`data/vias-por-bairro/relatorio_via por bairro.pdf`) com o `dados_unificados.json`.
   Script: `python/gerar_vias_por_bairro.py` (parser tinha um bug de acentuação, já corrigido) +
   `python/gerar_pdf_vias_bairro.py`. Sempre copiar o JSON gerado pra
   `data/vias-por-bairro/vias_por_bairro.json` antes de rodar o PDF (os dois scripts usam caminhos
   diferentes pro mesmo JSON, não foi unificado ainda).
8. **`data/relatorios/bairro-manual.json`** — mapeamento manual bairro→vias (separado do sistema,
   não sobe pra produção), pra criar códigos NOVOS pras vias que não têm código DMTT.
   **FINALIZADO e validado na Sessão 10** (ver seção própria acima) — 724 vias, 50 bairros,
   100% de cobertura contra o itinerario_completo.json. Existe um relatório de apoio com sugestão
   automática de bairro por geocodificação: `data/relatorios/vias_sem_codigo_bairro_sugerido.{json,txt}`
   (gerado por `python/sugerir_bairro_vias_sem_codigo.py` — demora ~15-20min, rate limit do
   Nominatim) — usado como ponto de partida, mas o arquivo final foi todo revisado à mão.
9. **Pendências específicas em aberto:**
   - Linha **0112** — manual tem 2 variantes com o mesmo código, sistema só tem 1 entrada. Precisa
     decisão do usuário de como estruturar antes de aplicar (fica sempre pulada no
     `aplicar_itinerarios_mesclado.py`, ver `PULAR_CODIGOS`).
   - Linha **0209** — uma das 2 entradas duplicadas ficou 2 pontos GPS desatualizada na volta em
     relação à outra (achado, não resolvido).
   - Linhas **0004** ("Rio Largo via Mata do Rolo") e **1000 A** ("Trapiche / Pontal") sumiram da
     OSO mais recente (02/09/2026) mas não estão marcadas `(DESATIVADO)` no sistema — confirmar com
     o usuário se devem ser marcadas.
   - Placemark **"Trapiche / Ouro Preto via Jacintinho"** no KML está sem o prefixo de código
     (deveria ser "0403 - ...").
   - Linha **0001** no KML tem 2 placemarks com nomes muito diferentes pro mesmo código
     ("Terminal X Cruzeiro" vs "Madrugadão Village II") — ambíguo, não aplicado automaticamente.
10. **Script novo pra comparar com OSO**: `python/comparar_nova_oso.py` (lista de linhas hardcoded
    no próprio script — sempre que o usuário mandar uma OSO nova em PDF, ler o PDF, atualizar a
    lista `OSO` no script com os códigos+nomes novos, e rodar).

---

## O que é o projeto

Micro-serviço web para consulta de itinerários de ônibus da **DMTT**
(Diretoria de Mobilidade e Trânsito de Maceió/AL).

**Objetivo principal:** operadores da DMTT recebem reclamações sobre ônibus e precisam
identificar qual linha estava em determinada rua num determinado horário. O sistema permite:
- Selecionar uma linha e ver o traçado no mapa
- Buscar por nome de rua e ver quais linhas passam lá
- Filtrar por horário (±20 min) para identificar o ônibus provável
- Clicar no mapa para descobrir automaticamente qual rua é e quais linhas a atendem

**Fase atual:** em produção em `dmtt.mendesweb.com` (Hostinger, hospedagem compartilhada),
**100% estático** — sem backend rodando em produção. Ver `DEPLOY.md` para o histórico completo
da decisão (por que PHP foi abandonado em favor de estático particionado).

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend (dev local apenas, sem uso em produção) | Python 3.11+ · FastAPI · Uvicorn · Pydantic |
| Frontend | React 18 · Vite · Leaflet 1.9 · react-leaflet 4.2 |
| Dados (fonte de verdade) | Arquivos JSON locais (`data/json/dados_unificados.json`) |
| Dados (produção) | JSONs estáticos gerados em `frontend/public/data/`, servidos direto pelo Apache da Hostinger |
| Dados (futuro) | SQL Server ou banco Hostinger |

**Importante:** o backend Python (`backend/`) continua no repo só para desenvolvimento local /
referência da lógica original. Quem serve os dados em produção é `frontend/src/staticApi.js`,
lendo os JSONs de `public/data/` — não há processo de servidor rodando na Hostinger.

---

## Como rodar localmente

```bash
# Frontend (já roda sozinho contra os JSONs estáticos em public/data/, sem precisar do backend)
cd frontend && npm run dev                    # http://localhost:5173

# Backend Python — opcional, só se for comparar/depurar a lógica original
cd backend && uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

## Como atualizar dados em produção (linhas, trajetos, horários)

```bash
# 1. Editar a fonte de verdade
#    data/json/dados_unificados.json / data/json/horarios/horarios.json

# 2. Regenerar os JSONs estáticos consumidos pelo frontend
python python/gerar_dados_estaticos.py

# 3. Rebuild do frontend
cd frontend && npm run build

# 4. Deploy via SFTP (lê credenciais de .env, nunca imprime a senha)
cd .. && python python/deploy_frontend.py
```

Não precisa reiniciar nada no servidor — é upload de arquivos estáticos. Ver `DEPLOY.md` para
detalhes do acesso SSH/SFTP.

---

## Estrutura de pastas

```
MicroSaaS-Linhas-DMTT/
├── CLAUDE.md
├── start.bat                              ← inicia backend + frontend com duplo-clique
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                        ← FastAPI, todos os endpoints
│       ├── schemas.py                     ← modelos Pydantic
│       └── services/
│           └── data_loader.py             ← DataStore: carrega JSONs, indexa ruas e horários
├── frontend/
│   ├── public/
│   │   ├── .htaccess                      ← rewrite para SPA (Hostinger)
│   │   └── data/                          ← JSONs estáticos consumidos em produção (gerado, não editar à mão)
│   └── src/
│       ├── App.jsx                        ← raiz: estado global, callbacks, Nominatim
│       ├── staticApi.js                   ← lê public/data/*.json e resolve busca/filtro no navegador (substitui o backend em produção)
│       ├── styles.css                     ← tema dark, layout, todos os componentes
│       └── components/
│           ├── MapView.jsx                ← mapa Leaflet + destaque de rua + caixa de contexto
│           ├── RuaSearch.jsx              ← busca por rua com autocomplete e filtro de horário
│           ├── LinhaSelector.jsx          ← dropdown de linha + selector de sentido
│           ├── ItinerarioPanel.jsx        ← lista de ruas IDA/VOLTA com código DMTT
│           ├── HorariosPanel.jsx          ← horários por sentido
│           └── MapStyleSelector.jsx       ← troca de tile (dark/light/etc.)
├── data/
│   ├── json/
│   │   ├── dado-bruto/                    ← IDA.json, VOLTA.json, PONTOS.json (raw)
│   │   ├── dado-tratado/                  ← IDA_amostrado.json, VOLTA_amostrado.json (GPS)
│   │   ├── dado-linhas/                   ← IDA_linhas_ruas.json, VOLTA_linhas_ruas.json
│   │   ├── horarios/
│   │   │   └── horarios.json              ← 85 linhas × dia_util/sabado/domingo × ida/volta
│   │   └── intinerario manual/
│   │       ├── itinerario_completo.json   ← 85 linhas, IDA/VOLTA com nomes de ruas
│   │       └── itinerario_com_codigos.json ← FONTE PRINCIPAL DO BACKEND (código+match)
│   ├── kml/                               ← KMLs gerados por gerar_kml_pontos.py
│   │   ├── pontos_0001.kml ... pontos_0402.kml  ← um por linha
│   │   └── pontos_todas.kml               ← todas as linhas juntas
│   ├── listagem-de-pontos-faltantes/
│   │   ├── 0001.pdf ... 0402.pdf          ← PDFs originais da DMTT (pontos faltantes)
│   │   └── pontos.json                    ← 7 atendimentos, 539 pontos extraídos
│   └── linhas-nomes/
│       └── linhas.json                    ← 99 linhas identificadas nos XLS de passageiros
├── python/
│   ├── extrair_pontos_pdf.py              ← extrai pontos dos PDFs → pontos.json
│   ├── gerar_kml_pontos.py                ← gera KMLs de IDA/VOLTA a partir de pontos.json
│   ├── gerar_dados_unificados.py          ← une GPS + itinerario_com_codigos → dados_unificados.json
│   ├── gerar_dados_estaticos.py           ← dados_unificados.json + horarios.json + terminais.json → frontend/public/data/*.json
│   ├── deploy_frontend.py                 ← sobe frontend/dist/ pra Hostinger via SFTP (lê .env, nunca imprime senha)
│   ├── requirements-deploy.txt            ← deps só do deploy (paramiko, python-dotenv)
│   ├── gerar_relatorios.py                ← gera 3 relatórios de qualidade (data/relatorios/)
│   ├── gerar_relatorio_similares.py       ← nomes similares com sugestão de código DMTT
│   ├── sincronizar_mapa_reconstruido.py   ← KML (data/kml/Mapa Reconstruido.kml) → dados_unificados.json, KML sempre vence
│   ├── mesclar_itinerarios.py             ← itinerario_completo.json (manual) → itinerario_mesclado.json (abreviações expandidas)
│   ├── aplicar_itinerarios_mesclado.py    ← itinerario_mesclado.json → dados_unificados.json (preserva código DMTT quando o nome bate)
│   ├── padronizar_nomes_via.py            ← unifica grafia de rua por código DMTT (quando há 2+ grafias pro mesmo código)
│   ├── padronizar_nomes_via_fuzzy.py      ← idem, mas por similaridade de texto (só acento/pontuação — resto vira relatório de revisão)
│   ├── localizar_duplicatas_no_manual.py  ← acha em qual linha/sentido do itinerario_completo.json cada rua duplicada aparece
│   ├── gerar_vias_por_bairro.py           ← cruza PDF oficial DMTT + dados_unificados.json → data/json/vias_por_bairro.json
│   ├── gerar_pdf_vias_bairro.py           ← vias_por_bairro.json → data/vias-por-bairro/vias_por_bairro.pdf
│   ├── comparar_nova_oso.py               ← compara OSO (PDF, lista hardcoded no script) x dados_unificados.json
│   ├── linhas_por_bairro.py               ← % de cada linha por zona/bairro (point-in-polygon contra zonas.json)
│   ├── buscar_todas_zonas.py              ← busca polígono de bairro no Nominatim (lista oficial de 53 bairros)
│   ├── buscar_zonas_via_overpass.py       ← fallback via Overpass API pra bairros sem polígono direto no Nominatim
│   ├── adicionar_zonas_kml.py             ← injeta pasta "ZONAS" no KML a partir de data/json/zonas/*.geojson
│   ├── gerar_zonas_estaticas.py           ← pasta ZONAS do KML → frontend/public/data/zonas.json
│   ├── ordenar_kml_por_linha.py           ← copia do KML com IDA/VOLTA ordenados por código de linha (pra abrir no Google Earth)
│   ├── colorir_kml.py                     ← aplica cor fixa verde/azul (IDA/VOLTA) num KML, corrige cores quebradas do Google Earth
│   ├── sugerir_bairro_vias_sem_codigo.py  ← geocodifica vias sem código DMTT e sugere bairro (Nominatim + zonas.json)
│   ├── comparar_oso_pdf.py                ← lê PDF do Resumo OSO e lista linhas que faltam no manual e/ou no sistema
│   ├── extrair_codigos_matrix.py          ← PDF do Matrix → data/json/bairros/matrix-codigos.json (nomes expandidos)
│   ├── gerar_bairro_codigo.py             ← bairro-manual.json → bairro-codigo.json (códigos sequenciais 0001…)
│   ├── atualizar_bairro_com_matrix.py     ← cruza bairro-codigo × matrix-codigos (campo codigo_matrix)
│   └── gerar_pdf_bairro_codigo.py         ← bairro-codigo.json → bairro-codigo.pdf
├── resumo-oso/
│   ├── sp_relatorio_resumooso.pdf         ← PDF fonte do OSO (22/05/2026)
│   ├── extrair_resumo_oso.py              ← extrai linhas por tipo de serviço do PDF
│   └── relatorio_tipos_servico.txt        ← resultado: convencional/catraca/madrugadão por empresa
└── matrix/
    └── extrair_linhas_xls.py              ← identifica linhas nos arquivos XLS de passageiros
```

---

## Endpoints da API (backend Python — só dev local, não usado em produção)

> Em produção o frontend não chama esses endpoints — lê os JSONs de `public/data/` via
> `staticApi.js`. Esta tabela documenta a lógica original (equivalente 1:1 ao que roda em JS).

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /health | Status da API |
| GET | /meta | Total de linhas, ruas indexadas, arquivos |
| GET | /linhas | Lista todas as linhas |
| GET | /linhas/{id} | Detalhe: coords GPS + ruas IDA/VOLTA |
| GET | /ruas/suggest?q= | Autocomplete de nomes de rua (mín. 2 chars) |
| GET | /ruas/search?q= | Linhas que passam na rua (+ filtro horario/dia/janela) |
| GET | /ruas/codigo/{codigo} | Linhas que passam pela via com esse código DMTT |
| GET | /geojson/linhas | GeoJSON de todas as linhas |
| GET | /geojson/linhas/{id} | GeoJSON de uma linha específica |
| GET | /horarios/{id} | Horários de uma linha por dia |

**Parâmetros opcionais de `/ruas/search`:**
- `horario=HH:MM` — filtra linhas com partida dentro da janela
- `dia=dia_util|sabado|domingo` (padrão: `dia_util`)
- `janela=20` — minutos de tolerância (5–60, padrão 20)

---

## Dados principais — formato

### `dados_unificados.json` ← FONTE ATUAL DO BACKEND (gerado por gerar_dados_unificados.py)

```json
{
  "0024 - Gruta / Centro / Term. Rotary": {
    "ida":   { "coordenadas": [[lat, lon], ...], "ruas": [{"via": "...", "codigo": "00834", "match": "exato"}] },
    "volta": { "coordenadas": [[lat, lon], ...], "ruas": [...] }
  }
}
```

**Regra:** edite sempre este arquivo. Para regenerar a partir das fontes originais, rode `python python/gerar_dados_unificados.py`.
Após editar o JSON, **reinicie o backend** (uvicorn só recarrega .py, não .json).

---

### `itinerario_com_codigos.json` (fonte original — não mais lida diretamente pelo backend)

```json
{
  "0024 - Gruta / Centro / Term. Rotary": {
    "versao": "pdf_v1",
    "ida": [
      { "via": "AVENIDA ROBERTO SIMONSEN", "codigo": "00834", "match": "exato" }
    ],
    "volta": [ ... ]
  }
}
```

### `horarios.json`

```json
{
  "0024": {
    "dia_util": { "ida": ["05:30","06:00",...], "volta": ["05:45","06:15",...] },
    "sabado":   { ... },
    "domingo":  { ... }
  }
}
```

### `pontos.json` (extraído dos PDFs)

```json
[
  {
    "codigo": "0001",
    "linha": "Terminal x Cruzeiro",
    "nome_ida": "Circular Cruzeiro do Sul",
    "nome_volta": "",
    "pontos": [
      { "nome": "Terminal Eustáquio Gomes", "abreviatura": "T-EGOMES",
        "endereco": "...", "ordem": 1, "vel_limite": 60,
        "latitude": -9.54223, "longitude": -35.78303 }
    ]
  }
]
```

---

## O que já foi feito

### Backend
- [x] FastAPI com 10 endpoints funcionando
- [x] DataStore com `rua_index` (busca por nome de rua normalizado)
- [x] DataStore com `horario_index` (keyed por 4 dígitos da linha)
- [x] `suggest_ruas()` — autocomplete de nomes de rua
- [x] `search_ruas_horario()` — filtra linhas por rua + horário ±janela
- [x] Endpoint `/ruas/suggest` e extensão de `/ruas/search` com filtro de horário
- [x] Schemas `RuaOcorrenciaHorario` e `RuasHorarioResponse`

### Frontend
- [x] Mapa Leaflet com 5 estilos de tile (dark/light/padrão/voyager/satélite)
- [x] Cores padronizadas: IDA = verde `#22c55e`, VOLTA = azul `#1e40af` (mapa + badges + itinerário + horários)
- [x] RuaSearch com autocomplete em tempo real (debounce 250ms, AbortController)
- [x] Filtro de horário + dia no RuaSearch (janela ±20 min)
- [x] Badges IDA/VOLTA clicáveis → carrega só aquele sentido no mapa
- [x] Caixa de contexto no mapa (canto inferior direito) explicando o sentido selecionado
- [x] Botão "Ver os dois sentidos" na caixa de contexto
- [x] Destaque de rua no mapa via Nominatim (halo amarelo espesso + linha sólida)
- [x] Zoom automático na rua destacada (`StreetZoom`)
- [x] Clique no mapa → reverse geocode Nominatim → popula RuaSearch automaticamente
- [x] Cursor crosshair no mapa indicando modo de clique
- [x] Rotas de ônibus sempre visíveis (rua destacada renderiza por cima via halo)
- [x] `start.bat` para iniciar backend + frontend com duplo-clique

### Scripts Python
- [x] `extrair_pontos_pdf.py` — extrai pontos de parada dos PDFs (máquina de estados, filtro Principal=Sim + Ativo=Sim)
- [x] `gerar_kml_pontos.py` — gera KMLs IDA/VOLTA com LineString + Placemarks individuais
- [x] `gerar_dados_unificados.py` — une GPS coords + itinerario_com_codigos → `dados_unificados.json` (85 linhas)
- [x] `gerar_relatorios.py` — gera 3 relatórios de qualidade em `data/relatorios/`
- [x] `gerar_relatorio_similares.py` — relatório de nomes similares com sugestão de código DMTT
- [x] `resumo-oso/extrair_resumo_oso.py` — extrai tipos de serviço do PDF OSO via pdfplumber
- [x] `matrix/extrair_linhas_xls.py` — identifica 99 linhas nos XLS de passageiros

### Dados gerados
- [x] `data/json/dados_unificados.json` — 85 linhas com GPS + ruas + códigos em um único arquivo
- [x] `data/relatorios/ruas_sem_codigo_e_sem_dicionario.txt` — 148 vias sem código e sem dicionário
- [x] `data/relatorios/nomes_similares_possiveis_duplicatas.txt` — 101 pares similares com sugestão de código
- [x] `data/relatorios/atencao_geral.txt` — diagnóstico geral de qualidade dos dados
- [x] `resumo-oso/relatorio_tipos_servico.txt` — 108 linhas: 78 convencional, 2 catraca, 5 madrugadão, 22 integração, 1 cidadã
- [x] `pontos.json` — 7 atendimentos, 539 pontos com lat/lon
- [x] `data/kml/pontos_*.kml` — 7 KMLs individuais + 1 com todas as linhas
- [x] `data/linhas-nomes/linhas.json` — 99 linhas (84 com nome, 15 sem)

---

## Comportamento atual do mapa — fluxo de interação

```
1. Busca por rua (campo de texto):
   - Digitar → autocomplete mostra nomes de rua (via /ruas/suggest)
   - Selecionar rua → Nominatim busca geometria → halo amarelo no mapa + zoom
   - Resultados mostram linhas com badges [→ IDA] [← VOLTA] clicáveis
   - Clicar badge de sentido → mapa carrega só aquele sentido + caixa de contexto aparece
   - Clicar nome da linha → ambos os sentidos

2. Clique no mapa:
   - Clique em qualquer ponto → Nominatim reverse geocode → nome da rua
   - Campo de busca preenchido automaticamente → busca dispara
   - Rua destacada em amarelo no mapa

3. Caixa de contexto (canto inferior direito do mapa):
   - Aparece quando usuário seleciona sentido específico via busca por rua
   - Borda/título na cor do sentido (verde=IDA, azul=VOLTA)
   - Botão "Ver os dois sentidos" reseta e fecha a caixa

4. Seleção por LinhaSelector (dropdown):
   - Comportamento original mantido
   - Deseleciona qualquer contexto de busca por rua
```

---

## Plano — Incorporar Novas Linhas ao Sistema (Sessões 4 e 5)

Este é o plano definitivo para adicionar linhas novas ao MicroSaaS. Seguir sempre esta ordem.

> Última atualização: 02/06/2026 — Sessão 5

### Estado atual (08/06/2026)

**OSO tem 106 linhas (excluindo Catraca de Solo). dados_unificados.json tem 85.**

| Situação | Qtd | Linhas |
|---|---|---|
| No sistema (dados_unificados) | 85 | — |
| ✅ KML feito + coords extraídas + PDFs do Matrix prontos | 12 | 0036, 0065, 0301, 0402, 1020, 1022, 1023, M001–M005 |
| ✅ KML feito + coords extraídas — **aguardando Matrix** | 8 | 0014, 0109, 0209, 0612-A, 0617, 1000-B, 2058, 4000 |
| Não será feita (decisão) | 1 | 0006-M |
| Total pendente no sistema | 20 | — |

**Arquivos intermediários gerados (sessão 6):**
- `data/json/novos_trajetos/coords_novas_linhas.json` — 20 linhas com IDA/VOLTA (KML→JSON)
- `data/json/terminais.json` — 26 terminais com lat/lon
- `data/json/novos_trajetos/itinerario_rascunho.json` — 12 linhas parseadas (aguardando 8)
- `data/json/novos_trajetos/horarios_novos.json` — 12 linhas parseadas (aguardando 8)

**Formato no Matrix para os madrugadões:** `0001-m`, `0002-m` ... `0005-m` (confirmado)
**Formato a confirmar:** `1000-b` e `0612-a` (pode ser diferente no Matrix)

**Observação sobre coordenadas:** Os pontos extraídos do KML (30–300 pts por linha)
são suficientes para exibir o traçado no Leaflet. Não precisa traçar mais fino.

---

### FASE A — Completar o KML ✅ CONCLUÍDA (sessão 6)
- [x] KML corrigido: 1000-B VOLTA movida para pasta VOLTA
- [x] Todas as 8 linhas complementares desenhadas com IDA/VOLTA
- [x] `python/extrair_terminais_kml.py` criado → `data/json/terminais.json` (26 terminais)

---

### FASE B — Extrair coordenadas do KML → JSON ✅ CONCLUÍDA (sessão 6)
**Script:** `python/extrair_coords_kml.py`
- 20 linhas extraídas (12 originais + 8 novas) → `coords_novas_linhas.json`

---

### FASE C — Extrair itinerário e horários do Matrix ⏳ PARCIALMENTE FEITA
**Scripts:** `matrix/automation_novas_itinerario.py` e `matrix/automation_novas_horario.py`

**Status:**
- [x] 12 linhas originais — PDFs já extraídos (sessão 5)
- [ ] 8 linhas complementares — **aguardando Matrix**

Fluxo para as 8 novas:
1. Usuário abre Matrix → OSO → marca só **[x] Itinerário por Via**
2. Roda `cd matrix && python automation_novas_itinerario.py`
3. Usuário troca para só **[x] Quadro Horário**
4. Roda `cd matrix && python automation_novas_horario.py`

**Atenção:** confirmar formato de `1000-b` e `0612-a` no Matrix antes de rodar.

---

### FASE D — Parsear PDFs → JSON rascunho ⏳ PARCIALMENTE FEITA (sessão 6)
**Scripts já criados:**
- `python/parsear_itinerario_pdf.py` → `data/json/novos_trajetos/itinerario_rascunho.json`
- `python/parsear_horarios_pdf.py` → `data/json/novos_trajetos/horarios_novos.json`

**Status:** 12 linhas parseadas. Rodar novamente após Fase C para incluir as 8 restantes.

---

### FASE E — Revisão manual (responsabilidade do usuário)
- [ ] Corrigir vias no `itinerario_rascunho.json`, preencher códigos DMTT
- [ ] Confirmar horários no `horarios_novos.json`
- [ ] Avisar Claude → Fase F

---

### FASE F — Mesclar no sistema ✅ Script criado (sessão 6)
**Script:** `python/mesclar_novos_trajetos.py` (pronto — rodar após Fase E)

- Injeta coords + itinerário em `dados_unificados.json`
- Mescla horários em `horarios/horarios.json`
- Faz backup automático antes de alterar
- Após rodar: reiniciar backend (`cd backend && uvicorn app.main:app --reload`)

---

### Relatórios de controle
- `I:\Micro-SaaS-DMTT\relatorio_pdfs_vs_oso.txt` — status PDFs vs OSO (106 linhas)
- `data/kml/relatorio_mapa_reconstruido_novo.txt` — status KML vs catálogo
- Script para regerar: `python python/gerar_relatorio_pdfs_vs_oso.py`

---

## Backlog (próximas fases)

### Dashboards (GEPOT) — autenticação para dashboards "interno" (futuro, NÃO implementar ainda)

`frontend/src/pages/DashboardsPage.jsx` + `frontend/src/dashboardsConfig.js` listam os dashboards do
Power BI em cards (`/dashboards`). Cada entrada tem um campo `tipo`: `"publico"` (link de "Publicar na
Web" do Power BI, sem login — qualquer um que abrir o link acessa) ou `"interno"` (compartilhamento
autenticado do Power BI, só quem tem conta na organização acessa).

Hoje os dois tipos se comportam igual no site: o card só abre o link em nova aba (`target="_blank"`),
sem nenhuma barreira própria do MicroSaaS — a proteção de um dashboard `"interno"` depende inteiramente
do próprio Power BI pedir login.

**Ideia futura (decidida, mas ainda NÃO deve ser implementada):** quando um dashboard for `tipo:
"interno"`, o usuário deve digitar uma senha *no próprio site* antes de conseguir abrir o link — uma
camada de senha simples do lado do MicroSaaS, adicional ao login do Power BI. Ainda não foi definido
como/onde essa senha seria armazenada nem o fluxo de UI. Só documentar por enquanto; não construir nada
disso até receber instrução explícita pra retomar.

### Zonas (bairros) no mapa — feature pausada, NÃO deployar (Sessão 9)

Toggle "Zonas (bairros)" no `MapStyleSelector` mostra polígonos de bairro sobre o mapa
(`frontend/public/data/zonas.json`, gerado a partir da pasta "ZONAS" do
`data/kml/Mapa Reconstruido.kml`). 50 dos 53 bairros oficiais têm polígono (Alto da Alegria, Chã
de Bebedouro, Gama Lins, Santo Amaro e Village Campestre não têm — sem dado geográfico disponível
no OpenStreetMap nem via Overpass). O usuário pediu explicitamente pra **não subir isso em
produção ainda** ("ainda vou fazer atualizações na ideia") — é só uma feature local/experimental
por enquanto. Não incluir no próximo deploy sem confirmar com o usuário.

Scripts: `buscar_todas_zonas.py` (Nominatim), `buscar_zonas_via_overpass.py` (fallback pros
bairros sem polígono direto), `adicionar_zonas_kml.py` (injeta no KML), `gerar_zonas_estaticas.py`
(KML → `zonas.json`). `linhas_por_bairro.py` usa esses polígonos pra calcular quanto % do trajeto
de cada linha passa por cada bairro (point-in-polygon nos pontos GPS).

### Tiles do mapa — CARTO quebrou, trocado por Esri (Sessão 9)

O CARTO (`basemaps.cartocdn.com`, usado nos estilos Escuro/Claro/Voyager) passou a exigir API key
sem aviso — testado direto na CDN deles, fora do app, mesmo resultado. Trocado em `MapView.jsx`
pra tiles do Esri (`server.arcgisonline.com`, grátis, sem key, mesmo domínio que o estilo
"Satélite" já usava). Detalhes:
- Estilos Escuro/Claro usam `Canvas/World_Dark_Gray_Base` + `Canvas/World_Dark_Gray_Reference`
  (camada de base + camada de rótulos separada — o Esri divide os dois, tem que carregar as duas
  ou fica sem nome de rua/bairro no mapa).
- `maxNativeZoom` configurado por estilo (16 pros Canvas Escuro/Claro, 19 pro Ruas/Street Map) —
  esses tiles do Esri têm zoom nativo mais baixo que o CARTO tinha, o Leaflet estica além disso.
- "Voyager" renomeado pra "Ruas" (usa `World_Street_Map` do Esri, visual diferente).
- **Confirmar se isso já foi deployado em produção** — foi corrigido e testado localmente, mas o
  deploy pra `dmtt.mendesweb.com` ficou pendente (SSH costuma estar bloqueado na rede do escritório
  do usuário).

### Sessão 8 (pendente) — PDF do itinerário + sincronização total do KML

**1. Exportação em PDF — refazer a captura do mapa**

Estado atual: `frontend/src/pdfExport.js` tira um único screenshot do mapa (`html2canvas` em cima do
`.leaflet-container`) exatamente como ele está na tela no momento do clique — se o usuário está vendo
"Ida e Volta" juntos, o PDF sai com as duas rotas sobrepostas no mesmo mapa. O usuário reportou que "não
está imprimindo o PDF correto" (a reproduzir/detalhar quando retomar — pode ser esse problema de captura
combinada, ou outro bug ainda não identificado).

O que fazer:
- [ ] Trocar a captura única por **duas capturas separadas**: uma do trajeto de IDA sozinho, outra do
      trajeto de VOLTA sozinho — provavelmente setando `selectedSentido` temporariamente pra cada
      sentido (ou renderizando o `MapView` isolado por sentido) antes de cada `html2canvas`, e montando
      o PDF com as duas imagens (uma por sentido, cada uma com seu próprio título "→ IDA" / "← VOLTA").
- [ ] Reproduzir e corrigir o erro relatado ("não está imprimindo o pdf correto") — pedir pro usuário
      mandar um exemplo do PDF errado ou descrever o que aparece de errado, já que na sessão anterior o
      teste automatizado (Playwright) não pegou esse problema.
- [ ] Adicionar um **card visual de quilometragem** no PDF (hoje é só uma linha de texto simples), no
      formato: `→ IDA 15.9 km · ← VOLTA 15.78 km · Total 31.68 km` — com uma caixa/borda, não só texto
      corrido, pra ficar consistente com o `.linha-distancia` que já existe na tela.

**2. Sincronização do `Mapa Reconstruido.kml` ✅ CONCLUÍDA (Sessão 8/9)**

`python/sincronizar_mapa_reconstruido.py` agora **sempre substitui** a coordenada pela do KML
(regra "KML sempre vence" implementada, sem checagem de contagem de pontos) — confirmado como
comportamento padrão pelo usuário. Continuam valendo as proteções contra colisão de código e a
checagem de nomes que perdem detalhe (`deve_renomear`). Arquivo canônico:
`data/kml/Mapa Reconstruido.kml` (não o da raiz do projeto).

---

### Qualidade de dados — pendências identificadas (Sessão 4)

- [ ] 148 vias sem código DMTT e sem correspondência no dicionário → ver `data/relatorios/ruas_sem_codigo_e_sem_dicionario.txt`
- [ ] 22 pares com mesmo código mas grafias diferentes → padronizar no `dados_unificados.json`
- [ ] 4 pares com sugestão automática de código → ver `data/relatorios/nomes_similares_possiveis_duplicatas.txt`
- [ ] 2 linhas com anotações pendentes no nome (`FALTA FAZER`, `PRECISA DE ALTERAÇÃO`) → remover ou corrigir
- [ ] 2 linhas sem coordenadas GPS (IDA e VOLTA) → levantamento em campo

### Fase 3 — Deploy ✅ CONCLUÍDA (04/07/2026) — ver `DEPLOY.md`
- [x] Deploy do frontend em produção (`dmtt.mendesweb.com`, Hostinger)
- [x] Backend abandonado em favor de arquitetura 100% estática (índice de rua + JSON por linha)
- [x] `.env` / `.env.example` para credenciais de deploy (fora do git)
- [ ] Trocar autenticação SSH por chave (em vez de senha)
- [ ] `docker-compose.yml` para rodar backend local com um comando (opcional, dev only)

### Fase 4 — Dados de pontos no sistema
- [ ] Integrar `pontos.json` ao backend (endpoint `/pontos/{codigo}`)
- [ ] Exibir pontos de parada no mapa (markers) quando uma linha é selecionada
- [ ] Completar as 15 linhas que ainda não têm dados de pontos

### Fase 5 — Banco de dados
- [ ] Migrar JSON → SQL Server ou banco Hostinger
- [ ] Manter contratos de endpoint estáveis

---

## Regras de trabalho

- **Produção é 100% estática** — não há backend rodando na Hostinger; o frontend lê `public/data/*.json` via `staticApi.js`
- **JSON como fonte de verdade agora** — não criar banco de dados ainda
- **Fonte de dados** — `dados_unificados.json` é o arquivo de onde tudo deriva (backend local e geração estática), mas ele por sua vez é **gerado a partir de 2 fontes editadas à mão**: `data/json/intinerario manual/itinerario_completo.json` (texto do itinerário, ida/volta por linha) e `data/kml/Mapa Reconstruido.kml` (trajeto GPS). Editar essas duas, nunca editar `dados_unificados.json` nem `itinerario_com_codigos.json`/`itinerario_mesclado.json` diretamente — rodar o pipeline (ver "Sessão 9 — resumo" no topo do arquivo) depois de qualquer edição num dos dois
- **Depois de editar `dados_unificados.json`/`horarios.json`** — rodar `python python/gerar_dados_estaticos.py`, depois `npm run build` e `python python/deploy_frontend.py` (ver seção "Como atualizar dados em produção"). Se estiver usando o backend Python localmente, reiniciar o uvicorn (--reload só observa .py, não .json)
- **Nunca commitar segredos** — credenciais de deploy (SSH host/senha) ficam só em `.env` (git-ignored); `DEPLOY.md`/`CLAUDE.md` não devem conter valores reais
- **Cores:** IDA = `#22c55e` (verde), VOLTA = `#1e40af` (azul) — manter em tudo
- **Nominatim** — chamadas feitas direto do frontend, sem passar pelo backend
- **Sem comentários óbvios** — só comentar o "por quê" quando não for óbvio
- **Sem features não pedidas** — implementar exatamente o que foi definido

---

## Contexto de persistência entre máquinas

```bash
# Ao terminar uma sessão
git add CLAUDE.md
git commit -m "docs: atualiza CLAUDE.md após sessão de trabalho"
git push

# Ao começar em outra máquina
git pull
```
