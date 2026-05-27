# neurostatsblog

A Jekyll blog for research notes on neuroscience, machine learning theory, and statistical inference. Hosted at [neurostatsblog.github.io](https://neurostatsblog.github.io).

---

## Deployment: One-time setup

### 1. Create the GitHub organization and repository

1. Go to [github.com](https://github.com) and create a **new organization** named `neurostatsblog`
   - Settings → Organizations → New organization → Free plan
2. Inside that org, create a **new repository** named exactly `neurostatsblog.github.io`
   - This name is required for GitHub Pages to serve from the root URL
   - Set it to **Public**, initialize without a README

### 2. Push this site to GitHub

```bash
cd /path/to/neurostatsblog

git init
git add .
git commit -m "Initial commit: Jekyll blog"

git remote add origin https://github.com/neurostatsblog/neurostatsblog.github.io.git
git branch -M main
git push -u origin main
```

### 3. Enable GitHub Pages

The site is built and deployed by GitHub Actions (see `.github/workflows/jekyll.yml`) rather than the built-in "Deploy from a branch" path. We need Actions because the site uses a custom `_plugins/` hook (for display-math blank-line normalization) which GitHub Pages' built-in builder refuses to load — it runs Jekyll in safe mode.

1. Go to the repository → **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions** (NOT "Deploy from a branch")
3. Push to `main`. The `Build and deploy Jekyll site` workflow will run on every push.
4. After 1–2 minutes, your site is live at `https://neurostatsblog.github.io`. You can monitor builds at the repo's **Actions** tab.

You can also manually re-run the deploy from the Actions tab via the **Run workflow** button (the workflow has `workflow_dispatch:` enabled).

### 4. (Optional) Local preview

The repo ships with a `Dockerfile` + `docker-compose.yml` that runs Jekyll 3.10 on Ruby 3.3 — the same versions GitHub Pages uses. No host install of Ruby is needed — just Docker Desktop.

```bash
# Start the preview (first run builds the image, ~2 min; subsequent runs are instant)
docker compose up site

# Open http://localhost:4000
```

Edits to `_posts/`, `_layouts/`, `_includes/`, `assets/`, etc. trigger auto-rebuild via polling, and LiveReload pushes the change to the browser on port 35729.

Run in the background and free up the terminal:

```bash
docker compose up -d site      # start detached
docker compose logs -f site    # tail the Jekyll log
docker compose down            # stop and remove the container
```

If you change the `Gemfile`, refresh the image:

```bash
docker compose build site
```

#### Without Docker

If you'd rather use a host Ruby (3.3 recommended):

```bash
gem install bundler
bundle install
bundle exec jekyll serve --livereload
# Open http://localhost:4000
```

---

## Writing a new post

Create a new file in `_posts/` with this naming convention:

```
_posts/YYYY-MM-DD-slug-here.md
```

Every post needs this front matter at the top:

```yaml
---
layout: post
title: "Your Post Title"
subtitle: "Optional subtitle"     # optional
date: 2026-04-15
tags: [Bayesian inference, neural decoding]
---

Your content here. Markdown is fully supported.
```

### Math

Use `$...$` for inline math and `$$...$$` for display math:

```markdown
The kernel is $k(x, x') = \exp(-\|x - x'\|^2 / 2\ell^2)$.

$$
p(\theta \mid y) \propto p(y \mid \theta)\, p(\theta)
$$
```

MathJax renders this automatically — no extra setup needed.

### Code blocks

Fenced code blocks with syntax highlighting:

````markdown
```python
import jax.numpy as jnp

def rbf_kernel(x, y, lengthscale=1.0, variance=1.0):
    sq_dist = jnp.sum((x - y) ** 2)
    return variance * jnp.exp(-sq_dist / (2 * lengthscale ** 2))
```
````

### Publish

```bash
git add _posts/YYYY-MM-DD-your-post.md
git commit -m "Add post: Your Post Title"
git push
```

GitHub Actions rebuilds the site automatically. Changes are live in ~60 seconds.

---

## Versioning a post

Posts can carry simple version metadata so readers (and future-you) can tell at a glance when a post was last revised and what changed. Three optional YAML fields:

```yaml
---
title: "..."
date: 2026-05-01              # original publication — never change this
version: 2                    # bump when you make a substantive edit
last_updated: 2026-05-27      # most recent edit date (shown if differs from `date`)
changelog:                    # newest first
  - "v2 (2026-05-27): Added Figure 4 showing anticipated wealth growth."
  - "v1 (2026-05-01): Initial publication."
---
```

How it renders:

- If `last_updated` is set and differs from `date`, the post header shows `<original date> · Updated <new date> (v2)` (the `(vN)` suffix is shown when `version` is set).
- If `version > 1` but no `last_updated` is given, the header shows just `(vN)`.
- If `changelog` is provided, a small **Revision history** section appears at the bottom of the post, between the body and the navigation links.
- Posts without these fields display exactly as before — everything is opt-in.

Convention: bump `version` on substantive edits (added/removed content, fixed an error, added a figure). Don't bump on pure typo fixes — leave those silent.

---

## Building a post as a PDF

The repo includes a pandoc-based PDF pipeline (XeLaTeX backend) that runs in Docker — no host install of TeX needed.

```bash
# Build one post
bin/build-pdf _posts/2026-05-13-model-comparison-by-betting.md

# Build everything in _posts/
bin/build-pdf --all
```

Output is written to `pdfs/<slug>.pdf` (gitignored). The first run pulls the `pandoc/extra` image (~1.5 GB); subsequent runs are fast. Math, footnotes, and standard markdown features are all supported. The LaTeX template lives at `pdf/template.tex` — tweak it if you want different typography or a custom title block.

---

## Site structure

```
neurostatsblog/
├── _config.yml          ← Site settings (title, URL, author, plugins)
├── _layouts/
│   ├── default.html     ← Base HTML shell (header, footer, scripts)
│   ├── home.html        ← Post listing page
│   ├── post.html        ← Individual post template
│   └── page.html        ← Static pages (About, etc.)
├── _includes/
│   ├── head.html        ← <head> meta, fonts, MathJax, CSS
│   ├── header.html      ← Nav bar with logo and dark mode toggle
│   └── footer.html      ← Footer with links
├── _posts/              ← Your blog posts (Markdown)
├── assets/
│   ├── css/main.css     ← Full custom theme
│   ├── js/main.js       ← Dark mode toggle + scroll effects
│   └── favicon.svg      ← SVG favicon
├── index.md             ← Home page
├── about.md             ← About page
├── 404.html             ← 404 page
└── Gemfile              ← Ruby dependencies (for local preview)
```

---

## Customizing

- **Change tagline/description:** Edit `_config.yml` → `tagline` and `description`
- **Author info:** Edit `_config.yml` → `author`
- **Colors/fonts:** Edit `assets/css/main.css` — all values are CSS custom properties at the top
- **Add a page:** Create `pagename.md` with `layout: page` in front matter
- **Tags page:** Add `tags.md` with a simple Liquid loop over `site.tags` (no plugin needed)
