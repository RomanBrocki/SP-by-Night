# São Paulo by Night (Vampire: The Masquerade 5e) — Project Instructions

## 0) Objetivo
Construir um cenário completo “São Paulo by Night” para VTM 5ª edição, com:
- sociedade cainita local (seitas, política, feudos, domínio, Tradições),
- todos os clãs jogáveis + presença relevante de antagonistas V5,
- NPCs (Cainitas e servos importantes) com conexões coerentes,
- material separado: “o que jogadores sabem” vs “segredos do narrador”,
- prontuário de antagonistas/ameaças típicas V5.
- Se passa em 2035

## 1) Regras de lore e consistência
- Respeitar o lore de VTM 5e (metaplot e conceitos centrais).
- Quando precisar inventar algo por falta de fonte clara: marcar como **[CANON-ADJACENT / HOME BREW]**.
- Não criar “poderes novos”; usar Disciplinas, Vantagens, Méritos, Defeitos e regras V5.
- Toda relação (Sire/Childe/aliança/rivalidade/boon) deve existir em um único “source of truth” (arquivo de rede) e ser referenciada de lá.

## 2) Segurança e realismo (São Paulo real)
- Evitar usar pessoas reais contemporâneas como NPCs centrais.
- Evitar atribuir crimes reais específicos a grupos reais. Mas pode usar organizações reais, publicas ou criminosas como background.
- Locais reais podem ser usados (bairros, vias, pontos turísticos).

## 3) Estrutura de pastas (obrigatória)
Criar exatamente esta árvore:

/00_BACKGROUND_JOGADORES/
  overview_sao_paulo.md
  seitas_e_politica.md
  mascarade_e_ameacas.md
  bairros_e_dominios.md
  rumores.md

/01_BACKGROUND_NARRADOR/
  segredos_e_verdades.md
  cronologia.md
  tramas_em_andamento.md
  teia_de_conexoes.md
  index_personagens.md
  data/
    rede_cainita.yml
    dominios.yml
    boon_e_dividas.yml

/02_NPCS/
  /Banu_Haqim/
  /Brujah/
  /Caitiff/
  /Gangrel/
  /Hecata/
  /Lasombra/
  /Malkavian/
  /Ministry/
  /Nosferatu/
  /Ravnos/
  /Salubri/
  /Toreador/
  /Tremere/
  /Tzimisce/
  /Ventrue/
  /Thin_Blood/

/03_SERVOS_E_CONTATOS/
  /ghouls/
  /mortais_influentes/
  /cainicais_outros/

/04_ANTAGONISTAS_V5/
  hunters.md
  second_inquisition.md
  sabbat.md
  werewolves.md
  ghosts_and_occult.md
  cults.md
  creatures_index.md

/05_ASSETS/
  /portraits/
  /portrait_prompts/

## 4) Convenções de arquivos por NPC
Para cada NPC (Cainita):
- Criar 2 arquivos:
  1) `NOME_DO_NPC_ficha_resumida.txt`
  2) `NOME_DO_NPC_historia.txt`
- Para NPCs “tier S” (Príncipe, Senescal, Xerife, Primógenos, Barões, líderes de seita, anciões etc.):
  - criar também `NOME_DO_NPC_ficha_completa.md` com ficha V5 completa (atributos, habilidades, disciplinas, vantagens, defeitos, humanidade, fome, compulsões, etc).

Retrato:
- Criar `05_ASSETS/portrait_prompts/NOME_DO_NPC.txt` com um prompt de imagem.
- Reservar o caminho final da imagem em `05_ASSETS/portraits/NOME_DO_NPC.png` (pode ser placeholder vazio se necessário).

## 5) Source of truth de relações (obrigatório)
- O arquivo `01_BACKGROUND_NARRADOR/data/rede_cainita.yml` é a fonte oficial de:
  - sire -> childe
  - alianças, rivalidades
  - boons (quem deve a quem e por quê)
  - vínculos com servos/contatos
- Antes de escrever história de um NPC, consultar/atualizar a rede.
- Nunca contradizer: se algo mudar, ajustar primeiro o YAML e depois os textos.

## 6) Conteúdo mínimo por NPC (ficha resumida)
Cada `*_ficha_resumida.txt` deve conter:
- Nome / Alcunha
- Clã (ou Thin-blood/Caitiff), Geração aproximada/Idade aparente
- Seita (Camarilla/Anarch/Autárquico/etc.)
- Função na cidade (se houver)
- Domínio/área principal
- Disciplinas (top 3) e “assinatura” de estilo
- 2 Touchstones/convicções ou nota de Humanidade (resumo)
- 3 ganchos de cena (como o NPC entra em jogo)

Cada `*_historia.txt` deve conter:
- Abraço (quando/por quem/por quê) e linhagem (sire + 1 nível acima se relevante)
- Ambição, Medo, Segredo
- Conexões principais (referenciar nomes exatamente como no YAML)
- 1 rumor falso e 1 verdade perigosa

## 7) Fluxo de execução (ordem de geração)
1) Criar a árvore de pastas e arquivos base.
2) Escrever BACKGROUND_JOGADORES (visão pública).
3) Escrever BACKGROUND_NARRADOR (verdade/segredos/tramas).
4) Criar `rede_cainita.yml`, `dominios.yml`, `boon_e_dividas.yml` (mesmo que inicial).
5) Criar NPCs por clã, mantendo consistência com o YAML.
6) Criar servos/contatos vinculados.
7) Criar antagonistas V5 e índice final.
8) Rodar checagem final: nomes, vínculos, domínios e boons sem contradição.

## 8) Qualidade / Definition of Done
- Todos os clãs listados acima possuem NPCs suficientes para “política jogável”.
- Existe um núcleo de poder (Camarilla/Anarch/Autárquicos) + tensão com SI e outras ameaças.
- Nenhum NPC importante está “solto”: todo mundo tem pelo menos 3 conexões registradas no YAML.
- Cada NPC tem prompt de retrato e caminho de imagem padronizado.