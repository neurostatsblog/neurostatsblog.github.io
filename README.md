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

1. Go to the repository → **Settings** → **Pages**
2. Under **Source**, select `Deploy from a branch`
3. Choose branch: `main`, folder: `/ (root)`
4. Click **Save**
5. After 1–2 minutes, your site is live at `https://neurostatsblog.github.io`

### 4. (Optional) Local preview

Install Jekyll and preview locally before pushing:

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
