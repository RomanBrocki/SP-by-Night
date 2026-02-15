# Sao Paulo by Night (V5) - Site + GitHub Pages

Este repositorio contem um cenario "Sao Paulo by Night" (Vampire: The Masquerade 5a edicao) com:

- Livro consolidado (indice, NPCs, coteries, faccoes, antagonistas)
- Mapa interativo de dominios em Sao Paulo
- Teia (grafo) de conexoes entre NPCs

O site pronto para publicacao fica em `docs/` (formato esperado pelo GitHub Pages).

## Gerar/atualizar o site (docs/)

No PowerShell, na raiz do projeto:

```powershell
python tools/build_by_night_book.py
python tools/build_docs_for_github_pages.py
```

Entrada do GitHub Pages: `docs/index.html` (redireciona para `docs/book/index.html`).

## Publicar no GitHub Pages

1. Crie um repositorio no GitHub (vazio).
2. No seu PC, na raiz do projeto:

```powershell
git init
git add -A
git commit -m "Publicar Sao Paulo by Night"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

3. No GitHub: `Settings` -> `Pages`
4. Em `Build and deployment`:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main`
   - `Folder`: `/docs`
5. Aguarde o deploy e abra a URL do Pages.

## Observacoes

- Se o `build_docs_for_github_pages.py` falhar no Windows por arquivo "em uso", feche abas do navegador abertas em `docs/` (mapa/teia/livro) e rode novamente.
- Retratos usados pelo site: `05_ASSETS/portraits/*.png` (publicados em `docs/assets/portraits/`).

