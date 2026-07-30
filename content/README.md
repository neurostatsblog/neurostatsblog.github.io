# Single-source content

Writing that exists both as a blog post and as an arXiv preprint lives here **once**.
`source.md` is the file you edit; `bin/build-content` generates both outputs:

```
content/betting/source.md
        │
        ├── bin/build-content (to-blog.lua)
        │     ──▶ _posts/2026-06-01-model-comparison-by-betting.md   (committed)
        │
        └── bin/build-arxiv (to-paper.lua + unwrap-ams.lua + citeproc + template)
              ──▶ arxiv-papers/2026-05-27-.../bits-per-spike-betting.pdf
              ──▶ .../build/arxiv-submission.tar.gz
```

The generated post is **committed**, because the GitHub Pages workflow builds the site
with plain Jekyll and has no pandoc. Treat it as a build product: edit `source.md`, run
`make`, commit the result. The preprint needs no committed intermediate — `source.md` goes
straight to PDF in a single pandoc pass.

The house style is that `source.md` reads as the blog post, and the extra material a
preprint needs — methods detail, limitations, code availability, references — is added in
`.paper-only` blocks. That keeps the post's voice intact and the diff between the two
outputs small and reviewable.

## Files

| file | purpose |
| --- | --- |
| `source.md` | the text — the file you edit most of the time |
| `meta.common.yml` | front matter shared by both outputs (title, subtitle) |
| `meta.blog.yml` | Jekyll-only front matter (layout, tags, changelog, …) |
| `meta.paper.yml` | pandoc-only front matter (keywords, affiliation, date, …) |
| `references.bib` | bibliography, read directly by both builds |
| `build.conf` | where the outputs land, and where the blog's PNGs live |

Front matter is assembled by *concatenating* the YAML fragments, so `meta.common.yml` and
`meta.blog.yml` must not define the same key. No YAML library is involved and comments
survive.

### Derived, not authored

Two things you might expect to type are computed instead, so a new piece of content gets
them for free and they cannot drift:

- **The blog backlink in the PDF** — "This material is also published as a blog post,
  *Title*, on <url>". `bin/build-arxiv` builds the URL from `url:` and `permalink:` in
  `_config.yml`, the `date:` in `meta.blog.yml`, and the slug in `BLOG_OUT`. Change the
  site's permalink scheme and the backlink follows. The title is the shared one from
  `meta.common.yml`, so it always matches the paper's own title.
- **Figure filenames for the arXiv package** — read out of the generated LaTeX rather than
  listed anywhere.

## Syntax

Ordinary pandoc markdown, plus the following.

**Conditional content.** Blocks and inline spans:

```markdown
::: {.blog-only}
I have struggled to answer these questions satisfactorily.
:::

This [post]{.blog-only}[note]{.paper-only} takes up that problem.
```

**Theorem-likes.** `.theorem` and `.definition`:

```markdown
::: {.theorem name="Ville's inequality" #thm:ville}
Let $(M_t)_{t \geq 0}$ be ...
:::
```

Paper gets a real `amsthm` environment (numbered, referenceable); post gets the site's
`.callout` styling.

**Figures.** Bare name, no extension or directory:

```markdown
![Caption text.](wealth_trajectory){#fig:wealth}
```

Paper resolves to `<figure_dir>/wealth_trajectory.pdf` inside a float; post resolves to
`<IMG_DIR>/wealth_trajectory.png`. Both auto-number.

**Appendices.** Wrap the trailing sections in `::: {.appendix}`. Paper emits `\appendix`;
post emits the `.supplementary-notes` div.

**Abstract.** Wrap it in `::: {.abstract}` at the top of `source.md`. `to-paper.lua`
hoists it into `meta.abstract` so the template can place it inside `\begin{abstract}`;
the post drops it. It lives here rather than in `meta.paper.yml` because it is prose, and
a 300-word YAML block scalar truncates silently if a line loses its indentation.

**Cross-references.** Write LaTeX and let the filters translate:

| in `source.md` | paper | post |
| --- | --- | --- |
| `\ref{fig:wealth}` | `2` (via LaTeX) | `2` (counted by the filter) |
| `\ref{sec:game}` | `4` (via LaTeX) | link to `#sec-game` titled by the heading |
| `\eqref{eq:wealth}` | equation number | `$\eqref{...}$` so MathJax renders it |

A `\ref` the post cannot express — `Theorem \ref{thm:ville}`, where the post's callouts
are unnumbered — should be written as a conditional span instead. Unresolved refs are
reported on stderr and rendered as `?`.

**Citations.** Two routes, and the betting source uses the second:

- Standard `[@key]`. Both builds run citeproc: the post gets a rendered reference list at
  generation time, the paper resolves them against the LaTeX template.
- `nocite: "@*"` in `meta.paper.yml` plus a `.paper-only` `# References` section holding an
  empty `::: {#refs}`. Every entry in `references.bib` prints in the paper, with no `[@key]`
  markers anywhere in the body — which is what lets the post keep its inline hyperlinks
  ("[Pillow et al. 2008](https://doi.org/...)") completely unchanged.

## Things that bite

- **kramdown and inline math.** kramdown's GFM parser does not recognise `$...$`, so a
  pair of underscores inside inline math is read as emphasis. `to-blog.lua` escapes them;
  kramdown unescapes before MathJax sees the text. Display `$$...$$` is recognised and is
  left alone.
- **Raw LaTeX swallows markdown.** Pandoc's raw-LaTeX reader consumes everything between
  `\begin{env}` and `\end{env}`. `to-paper.lua` therefore renders theorem bodies to LaTeX
  itself rather than emitting the body as markdown between two raw blocks — otherwise
  `*emphasis*` reaches the PDF as literal asterisks.
- **Fenced divs have no kramdown equivalent.** Any `Div` left unconverted would appear on
  the page as literal `:::`. `to-blog.lua` has a catch-all that turns every remaining div
  into raw HTML with `markdown="1"`. Spans get the same treatment — citeproc's `.nocase`
  would otherwise print verbatim.
- **kramdown heading attributes.** kramdown accepts `## Heading {#id}` but prints
  `{#id .class}` literally, so `to-blog.lua` strips classes from headings. `.unnumbered`
  only exists to stop LaTeX numbering a section; it means nothing on the web.
- **Callout bodies are rendered to HTML, not left as markdown.** Behind a `markdown="1"`
  div, kramdown re-parses the body and mangles display math — `\mathbb{E}_{X \sim B}`
  comes back as `\mathbb{E}<em>{X \sim B}`. `to-blog.lua` renders those bodies itself and
  passes `$...$` / `$$...$$` through untouched for MathJax.
- **AMS math appears mid-paragraph.** The callouts mix `$$\begin{align}...$$` into running
  text, not just standalone blocks, so `to-paper.lua` unwraps display math at both the
  paragraph *and* the inline level. Miss the inline case and pdflatex fails outright with
  a bad math environment delimiter.

## Adding a piece

1. `mkdir content/<name>`, then write `source.md` and the four metadata/config files —
   copy them from `content/betting/` and edit.
2. `make content` to generate, or plain `make` to go all the way to the preprint PDF.
3. Commit `source.md`, the metadata, **and** both generated files.
