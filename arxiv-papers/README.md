# arXiv preprints

Blog posts that have been reworked into citable preprints.

**Nothing here is authored.** The text is single-sourced from `content/<name>/source.md`,
which also generates the Jekyll post; see [`content/README.md`](../content/README.md).
`bin/build-arxiv` takes that source straight to PDF in one pandoc pass. What lives here is
the shared LaTeX machinery and the built preprints.

## Layout

```
arxiv-papers/
  _template/
    arxiv-template.tex          shared pandoc LaTeX template
    unwrap-ams.lua              lua filter for $$\begin{equation}$$ blocks
  YYYY-MM-DD-<slug>/            one directory per paper, dated by the
                                post's front-matter `date:`. All generated.
    <slug>.pdf                  the preprint (committed)
    build/                      gitignored build products
      arxiv-submission.tar.gz     what to upload
      arxiv-submission/           its unpacked contents
      arxiv-source-check.pdf      that package, compiled in isolation
```

Figures are not stored here. They are build products of the analysis code (e.g.
`code/betting/figures/`), and each paper points at its own directory with a `figure_dir:`
key in `meta.paper.yml`. The build reads the filenames straight out of the
`\includegraphics` calls in the generated LaTeX, so adding a figure to the text is all it
takes.

## Current papers

| paper | source post |
| --- | --- |
| `2026-05-27-bits-per-spike-betting` | `_posts/2026-06-01-model-comparison-by-betting.md` |

## Building

```bash
make bits-per-spike-betting     # the usual way in
bin/build-arxiv content/betting # the underlying script; takes a content dir
bin/build-arxiv --all
bin/build-arxiv --pdf content/betting   # preprint only, for faster iteration
```

Everything runs inside the `pdf` service from `docker-compose.yml` (pandoc + TinyTeX);
no local TeX installation is used.

Check `build/arxiv-source-check.pdf` before submitting. It is the document compiled *from
the upload package*, in a container that can see nothing but that package — so if it looks
right, the upload will build on arXiv.

## Adding a paper

Papers are not created here directly — they come from `content/`. See
[`content/README.md`](../content/README.md) for the steps; point that source's
`build.conf` at a new `arxiv-papers/YYYY-MM-DD-<slug>/` directory, named with the post's
front-matter `date:`. The template reads `title`, `subtitle`, `short_title`, `author`,
`affiliation`, `email`, `date`, `keywords`, `abstract` and `figure_dir` from
`meta.paper.yml`.

## Why a source package and not just the PDF

arXiv asks for LaTeX source whenever the PDF was produced from TeX, and will reject a
PDF-only submission it detects as TeX-generated. The build therefore emits `main.tex`
alongside the PDF. Two details make that file self-contained:

- **No `.bib` is shipped.** Pandoc's citeproc formats the reference list and writes it
  into `main.tex` directly, so arXiv never needs to run bibtex.
- **pdflatex, not lualatex.** The template uses `lmodern` + `fontenc` rather than
  `fontspec`, so the source compiles under arXiv's default engine without the submitter
  having to select anything.

Upload `arxiv-submission.tar.gz` as-is. For the betting paper, suggested primary category
`q-bio.NC`, cross-list `stat.ME`.

## Citation

arXiv is the only DOI source the site uses; Zenodo is no longer minted for new work.
Once a preprint is live, put its id in the source post's front matter:

```yaml
arxiv: "2607.12345"
arxiv_class: "q-bio.NC"
arxiv_title: "Full title as submitted, if it differs from the post title"
```

That one key drives the post's BibTeX block (`_includes/citation.html`), the arXiv link
in the post header, the "View as PDF" link, and the Google Scholar `citation_doi` /
`citation_arxiv_id` meta tags. Readers are told to cite the preprint, not the post, so
citations accumulate on a single record.

Keep the two versions non-contradictory rather than identical: the paper is the source of
record for definitions, theorem statements, and reported numbers; the post is exposition.
When a claim changes, revise the paper, post a new arXiv version, then update the post and
note the arXiv version it tracks in its `changelog:`.

## Editing notes

- Section and appendix cross-references go through `\ref{sec:...}` / `\ref{app:...}`, not
  hand-typed numbers. Add an id (`# Heading {#sec:foo}`) when you add a section.
- Theorem-like blocks are raw LaTeX `definition` / `theorem` environments, not the
  `<div class="callout">` markup the blog posts use.
- Display math written as `$$\begin{equation}...\end{equation}$$` is unwrapped by
  `_template/unwrap-ams.lua`. Pandoc lowers `$$...$$` to `\[...\]`, which cannot hold an
  AMS environment; the filter emits those blocks as raw LaTeX instead.
- The citeproc preamble in `_template/arxiv-template.tex` is copied verbatim from
  `pandoc --print-default-template=latex`. If the pinned pandoc version in
  `docker-compose.yml` changes, re-copy that block.
