# Guia de Curadoria e Prompts (By Night) — Teia, Mapa, NPCs e Publicacao

Este arquivo documenta, de forma operacional, como este projeto saiu de um "esqueleto" para um site jogavel (livro + teia + mapa), e quais tipos de pedidos (prompts) foram decisivos para corrigir falhas recorrentes do agente.

A ideia e servir de guia para repetir o processo em outras cidades (ex.: "Rio by Night") com resultados parecidos.

## 1) Principio base: "Cenario", nao "Resumo"

Sinal de falha (do agente):
- texto mecanico, generico, cheio de frases de efeito vagas.
- "ganchos" sem consequencia objetiva (ex.: "alguem observa", "portas mudam de dono").
- termos soltos que parecem nomes de grupos (ex.: "correios", "corredor") sem arquivo/estrutura que explique.

Pedido que corrige (como formular):
- "Reescreva cada trecho para ser objetivamente claro e jogavel. Sem frases de efeito. Se houver gancho, descreva o que acontece em cena e o custo/consequencia."
- "Nao quero um resumo, quero um texto de cenario exploravel: o que se ve, o que se sabe, como se acessa, quem controla, por que importa, o que pode dar errado."

Checklist de qualidade (por arquivo):
- Cada paragrafo responde pelo menos 1: quem, o que, onde, como, custo, risco, sinal, evidencia.
- Cada local/NPC tem pelo menos 1 "cena pronta" (entrada, obstaculo, escolha, consequencia).

## 2) Source of truth: consistencia nao-negociavel

Falhas comuns:
- dominio e residencia em um arquivo, contradizendo outro.
- conexoes descritas na historia, mas ausentes na rede (ou vice-versa).

O que funcionou:
- tratar um arquivo como "fonte oficial" (rede/domnios/boons) e exigir que todo texto derive dele.
- rodar validacao de coerencia apos mudancas.

Como pedir:
- "Antes de reescrever historias, ajuste a fonte de verdade (rede/domnios/boons) e so depois atualize os textos para refletir a fonte."
- "Rode uma checagem que aponte contradicoes (nome, dominio, seita, sire/childe, boons). Se encontrar, corrija na fonte e regenere as saidas."

No projeto:
- Fonte principal operacional usada pelo site: `tools/sp_by_night_source.json`
- Validacao (exemplo): `tools/validate_project_coherence.py`

## 3) Teia (relacoes) — do YAML "pouco visual" para HTML interativo

Problema inicial:
- rede em YAML era correta como dados, mas pouco visual.
- primeiros HTMLs quebravam com erro de sintaxe e/ou tooltip "uma linha com tags".
- filtros sem responsividade (selecionar coterie sem mostrar nada).

Pedido que destravou:
- "Faça do zero um HTML interativo, com filtros, botao 'processar filtros', e descricao em multiplas linhas sem tags (texto plano)."
- "Quero um painel lateral com: foto, ficha, historia, prompt. Sem poluir o grafo com imagens."

Requisitos que devem estar prontos ANTES de gerar a teia:
- IDs/nomes estaveis para entidades (Kindred/Ghouls/Mortais).
- relacoes direcionais claras (ex.: `servant -> master`).
- tagueamento para filtros: `seita`, `cla`, `tipo`, `coterie(s)`.

Como pedir filtros (padrao robusto):
- "Filtros por faccao, cla, tipo (kindred/ghoul/mortal), coteries. Botao: Selecionar todos / Desselecionar todos. Botao: Processar filtros."
- "Se tudo estiver desmarcado e eu marcar um filtro especifico (ex.: uma coterie), mostre aquele subconjunto mesmo assim."
- "Filtro de cla deve mostrar os vampiros do cla e APENAS os ghouls que servem vampiros daquele cla."

Debug rapido para HTML (quando quebra):
- garantir que o HTML abre sem erros no console (SyntaxError).
- se "menu aparece mas grafo nao": checar se o script que inicializa o grafo esta executando e se o container tem tamanho (CSS).
- se tooltip vira "sopa de tags": enviar texto com `\\n` e renderizar com `white-space: pre-wrap`.

## 4) Mapa territorial (Leaflet) — de "circulos concentricos" para limites reais

Falhas comuns (do agente):
- usar circulos por preguiça de poligono, gerando geopolitica sem sentido.
- mapa "vazio" por erro de bounds / tiles infinitos / setView.
- overlays sem clique (baronatos apareciam mas nao eram clicaveis).
- camada macro e camada micro nao conversavam (click no territorio nao leva ao dono).

Pedido que alinhou o objetivo:
- "Use limites reais (distritos/bairros) como delimitadores. Camarilla domina a cidade inteira como base; anarquistas/independentes sao recortes. Areas de risco lupino como overlay de alerta."
- "Checkboxes por faccao/camada no topo; dropdown de dominios (lordes) e dropdown de NPCs. Clique no overlay mostra dono e contagem; clique no dominio seleciona automaticamente o lord no dropdown."

Modelo mental que funcionou (3 niveis):
1. Macro (checkboxes):
   - Camarilla (base/watermark onde nao e de outros; contestados contam como Camarilla ate perder).
   - Anarch (varios baronatos).
   - Independentes/Autarquicos (blocos delimitados por acordo).
   - Risco lupino (alerta por parques/reservas).
   - Contestado (sobreposicao explicita com X vs Y).
2. Micro (dropdown de dominios Camarilla relevantes):
   - um territorio expressivo por lider de cla e por figuras S/A.
   - pins para "lugar de poder" do lord.
3. Pontos de interesse (pins):
   - elisios, rotas, locais de alimentacao, redutos, etc., conectados a donos/aliados.

O que pedir quando "nao aparecem poligonos":
- "Use GeoJSON de distritos como shapes. Cada distrito deve ter 'dominante' e opcionalmente 'disputa'. Renderize como poligono (fill + stroke)."
- "No clique/hover de cada shape, mostre tooltip com multiplas linhas (sem tags) e um painel com detalhes."

Debug de erros tipicos Leaflet:
- `Attempted to load an infinite number of tiles`: tileLayer com bounds errados ou zoom sem limites; fixar `minZoom`, `maxZoom`, `maxBounds`.
- `Set map center and zoom first`: garantir `map.setView()` antes de operar layers.
- `Invalid LatLng (NaN, NaN)`: coordenadas faltando; validar seed/config e fallback.

## 5) Prompts de imagem — diversidade, realismo e "nao repetitivo"

Falhas comuns:
- todos pareciam "homem de terno" / "uniforme".
- repeticao de rosto/cabelo/pose.
- props repetidos (livro em quase todo mundo).
- etnia escolhida aleatoriamente (sem casar com nome/historia).
- "morenho" mal interpretado por IA (precisa ser explicito quando negro/indigena).

Como pedir (formula que funciona):
- "Cada NPC precisa de um prompt altamente individualizado: rosto (formato, marcas), cabelo (tipo/corte), pele/etnia explicita, idade aparente, atratividade (feio/belo/muito belo/horroroso), acessorios (brincos/piercings) se fizer sentido, roupas coerentes com a atuacao mortal, e um unico objeto opcional (so se couber)."
- "Regras negativas obrigatorias: sem texto, sem logotipo, sem marca d'agua, sem rabiscos nas maos, sem dedos extras, sem artefatos estranhos."
- "Nosferatu: nao precisa citar 'deformidade'; use taticas visuais (fantasia) para puxar o uncanny/monstruoso (ex.: goblin/bruxa/orc/caveira com pele), sem virar cartum."
- "Nao use livros por padrao; deixe maos vazias na maioria; props devem ser raros e contextuais."

Como evitar mismatch "nome vs etnia":
- defina a aparencia explicita no proprio NPC (campo/linha fixa).
- quando houver duvida, usar a atuacao/historia como guia (origem familiar, circulos, etc.) e manter consistencia.

## 6) Ghouls e servos — densidade social e utilidade em cena

Falha comum:
- poucos ghouls para muitos vampiros, deixando a cidade "sem cor".

Pedido que resolve:
- "Aumente ghouls para um numero alvo (ex.: 40) e descreva, na ficha de cada vampiro, quantos ghouls ele tem e quais tem ficha."
- "Anarquistas tem mais ghouls e mais uso criminal (gangues, motoboys, seguranças)."

Regras praticas:
- nem todo ghoul precisa de ficha; mas os relevantes (motorista do principe, chefe de gabinete, cobrador, hacker, capanga) devem ter.
- ghouls devem aparecer na teia e no livro, e no filtro por cla via seus mestres.

## 7) Consolidacao (Livro By Night) — quando o projeto vira "produto"

Sinal de falha:
- pagina "consolidada" com links que funcionam, mas conteudo vazio (JSON nao carregando por CORS/file://).

O que funcionou:
- gerar um `index.html` que embute os dados (JSON + SVG) inline, sem `fetch()`.
- incluir modal com ficha/historia/prompt ao clicar no NPC.
- gerar um macro-mapa (SVG) com tooltip e legenda.

Como pedir:
- "Quero um 'livro' com indice clicavel, secoes: faccoes, cls, coteries, NPCs, antagonistas, arquivos do narrador e jogadores. Clique em NPC abre ficha completa e prompt."
- "Sem dependencia de servidor local: tem que abrir em file:// e no GitHub Pages."

## 8) Publicacao no GitHub Pages — sem grilo

Falhas comuns:
- paths absolutos/relativos errados (quebra quando vira subpath do Pages).
- build que tenta apagar `docs/` e falha por lock do OneDrive/navegador.

O que funcionou:
- build para `docs/` com paths corrigidos para `../assets/...`, `../map/...`, `../teia/...`.
- `docs/.nojekyll` para evitar problemas com underscores.
- script de build tolerante a arquivos "em uso" (sincroniza em vez de `rmtree`).

Como pedir:
- "Gere um `docs/` publicavel no GitHub Pages, com `index.html` redirecionando para o livro, e copie assets necessarios."

No projeto:
- Build do livro: `python tools/build_by_night_book.py`
- Empacotamento Pages: `python tools/build_docs_for_github_pages.py`

## 9) Template: prompt para criar uma nova cidade (Rio by Night)

Use este pedido em etapas (nao tudo de uma vez):

1) Fundacao (pastas + regras de consistencia)
- "Crie a arvore de pastas conforme o padrao do projeto. Defina um 'source of truth' para entidades e relacoes (sire/childe/boons/domnios/servos) e valide que os textos nunca contradizem."

2) Lore jogavel (nao-resumo)
- "Escreva background para jogadores e para narrador. Cada area precisa ter: quem controla, como se alimenta, o que e proibido, que tipo de cena acontece la, e 1-2 conflitos ativos."

3) NPCs
- "Crie X NPCs totais, fracionados por faccao. Cada cla jogavel precisa de lideranca local e funcao politica. Todo NPC importante precisa de pelo menos 3 conexoes."

4) Ghouls
- "Adicione ghouls relevantes e conecte-os aos mestres. Na ficha do vampiro, liste quantos ghouls e quais tem ficha."

5) Imagens
- "Para cada NPC/ghoul relevante, gere prompt individualizado (aparencia explicita, etnia consistente, atratividade, detalhes unicos, sem props repetidos)."

6) Teia e mapa
- "Teia: HTML interativo com filtros + botao processar; painel lateral com foto e ficha."
- "Mapa: Leaflet com distritos reais; macro por faccao (checkboxes) + micro dominios Camarilla (dropdown) + pins de interesse; overlays clicaveis com descricao e contagem."

7) Livro e publicacao
- "Gere um livro em HTML com indice clicavel, modal de NPC, macro mapa com tooltip. Empacote em `docs/` para GitHub Pages."

## 10) Onde este projeto ainda exigiu curadoria forte (lições)

Pontos onde o agente tende a errar sem cobranca explicita:
- Prolixidade util (explicar o que acontece) vs frases vagas.
- Poligonos reais vs circulos/placeholder.
- Consistencia de dados vs inventar detalhes em textos sem atualizar a rede.
- Diversidade/individualidade de prompts de imagem (tende a repetir "terno/livro").
- Filtros (principalmente ghouls) exigem regra formal e testes.

Forma de curadoria que deu certo:
- exigir exemplos concretos ("Ucrania x Russia: divisao + disputa") para orientar a semantica do mapa.
- exigir "objetivamente claro" e nao aceitar frases que nao descrevem uma acao/cena.
- congelar partes ja usadas (prompts/imagens) e evoluir o restante sem quebrar.

