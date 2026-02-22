# Sao Paulo by Night (V5) - teste de criacao de cenario (site + GitHub Pages)

Este repositorio contem o projeto de cenario `Sao Paulo by Night` para `Vampiro: A Mascara 5a edicao`, com integracao entre lore, faccoes, dominios, NPCs, conexoes, mapa e material de mesa.

## Metodologia do projeto

Este teste foi conduzido em camadas:

- O **esqueleto inicial** do projeto foi gerado com agente no VS Code (Codex/Cortex, GPT 5-2), incluindo estrutura de pastas, base de lore e primeira versao de mapa/teia/site.
- Em seguida, foi produzido um **livro em PDF** sobre esse esqueleto, com refinamento narrativo e consolidacao de canon.
- Esse livro foi **destilado com apoio do ChatGPT**, com curadoria iterativa.
- Houve **criacao e edicao de conteudo por sua parte** ate o estado atual, com ajustes de coerencia, territorio, relacoes, tom narrativo e consolidacao final.

Resultado: o estado atual do repo representa uma composicao entre geracao assistida por IA + curadoria humana forte + edicao autoral.
Hoje o projeto esta mais consistente e o livro esta em um nivel mais profissional do que nas iteracoes iniciais.

## O que o cenario inclui

- Livro consolidado (faccoes, coteries, NPCs, antagonistas e material de apoio).
- Mapa interativo de dominios e marcadores.
- Teia interativa de conexoes entre membros da cidade.
- Estrutura de faccoes/seitas e conexoes cruzadas entre textos, teia e mapa.
- Galeria de imagens e retratos vinculados aos personagens.

## Publicacao (GitHub Pages)

- Repositorio: `https://github.com/RomanBrocki/SP-by-Night`
- Site publicado: `https://romanbrocki.github.io/SP-by-Night/book/index.html`
- Entrada do Pages: `docs/index.html` (redireciona para `docs/book/index.html`).

## Build local (gerar/atualizar `docs/`)

No PowerShell, na raiz do projeto:

```powershell
python tools/build_by_night_book.py
python tools/build_docs_for_github_pages.py
```

## Publicar no GitHub Pages (resumo)

1. Commit e push para `main`.
2. No GitHub: `Settings` -> `Pages`.
3. Em `Build and deployment`:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main`
   - `Folder`: `/docs`
4. Aguardar deploy e abrir a URL do Pages.

## Observacoes

- Se `build_docs_for_github_pages.py` falhar no Windows por arquivo em uso, feche abas abertas em `docs/` e rode novamente.
- Retratos usados pelo site publicado: `docs/assets/portraits/` (formato atual `.jpg`).
- `05_ASSETS/portraits/` pode ser usado como cache/local, enquanto o conteudo versionado para publicacao fica em `docs/assets/portraits/`.
