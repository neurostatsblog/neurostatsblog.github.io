# Build the blog post and the arXiv preprint from single-source content.
#
# Everything is driven from content/<name>/source.md. The point of driving
# the scripts from make rather than calling them directly is incrementality:
# each Docker/pandoc/pdflatex run takes tens of seconds, and a target is only
# rebuilt when its text, metadata, bibliography, figures, the shared LaTeX
# template, or a lua filter actually changed.
#
#   make                       regenerate anything out of date, end to end
#   make content               only regenerate the Jekyll posts
#   make list                  show content and the targets it exposes
#   make bits-per-spike-betting        one paper, PDF + upload package
#   make bits-per-spike-betting-pdf    one paper, PDF only (faster loop)
#   make quick                 every paper, PDF only
#   make check-refs            verify every DOI against the DOI registry
#   make clean                 drop build/ dirs; keeps the committed PDFs
#   make -B <target>           force a rebuild even if nothing changed
#
# Written for GNU Make 3.81, the version macOS ships.

SHELL := /bin/bash

CONTENT_DIRS := $(patsubst %/source.md,%,$(wildcard content/*/source.md))

GENERATOR := bin/build-content
BUILDER   := bin/build-arxiv
TEMPLATE  := arxiv-papers/_template/arxiv-template.tex
AMS       := arxiv-papers/_template/unwrap-ams.lua
BLOG_LUA  := content/_filters/to-blog.lua
PAPER_LUA := content/_filters/to-paper.lua

# Output locations are declared per source in build.conf; read them without
# sourcing the file so make stays independent of shell state.
conf     = $(shell sed -n 's/^$(2)=//p' $(1)/build.conf)
paperdir = $(call conf,$(1),PAPER_DIR)

# <PAPER_DIR> is YYYY-MM-DD-<slug>; the PDF is <slug>.pdf, and <slug> is
# also the phony target name.
slug = $(shell echo '$(notdir $(call paperdir,$(1)))' | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//')

# Figures live with the analysis code, so a rerun of the analysis correctly
# invalidates the preprint.
figdir = $(shell awk -F': *' '/^figure_dir:/{gsub(/"/,"",$$2); print $$2; exit}' '$(1)/meta.paper.yml')

# Everything an output depends on inside the content directory.
srcdeps = $(1)/source.md $(wildcard $(1)/meta.*.yml) $(1)/references.bib $(1)/build.conf

ALL_POSTS    := $(foreach d,$(CONTENT_DIRS),$(call conf,$(d),BLOG_OUT))
ALL_PDFS     := $(foreach d,$(CONTENT_DIRS),$(call paperdir,$(d))/$(call slug,$(d)).pdf)
ALL_PACKAGES := $(foreach d,$(CONTENT_DIRS),$(call paperdir,$(d))/build/arxiv-submission.tar.gz)

.PHONY: all papers quick content list check-refs clean help
.DEFAULT_GOAL := all

all: $(ALL_POSTS) $(ALL_PACKAGES)

papers: $(ALL_PACKAGES)

quick: $(ALL_PDFS)

# Only the Jekyll posts — no LaTeX, so this is the fast check.
content: $(ALL_POSTS)

define CONTENT_RULES

$(call conf,$(1),BLOG_OUT): $(call srcdeps,$(1)) $(BLOG_LUA) $(GENERATOR)
	$(GENERATOR) $(1)

$(call paperdir,$(1))/$(call slug,$(1)).pdf: $(call srcdeps,$(1)) $(PAPER_LUA) $(AMS) $(TEMPLATE) $(BUILDER) $(wildcard $(call figdir,$(1))/*.pdf)
	$(BUILDER) --pdf $(1)

# The full build also refreshes the PDF, so no separate ordering is needed.
$(call paperdir,$(1))/build/arxiv-submission.tar.gz: $(call srcdeps,$(1)) $(PAPER_LUA) $(AMS) $(TEMPLATE) $(BUILDER) $(wildcard $(call figdir,$(1))/*.pdf)
	$(BUILDER) $(1)

.PHONY: $(call slug,$(1)) $(call slug,$(1))-pdf

$(call slug,$(1)): $(call paperdir,$(1))/build/arxiv-submission.tar.gz

$(call slug,$(1))-pdf: $(call paperdir,$(1))/$(call slug,$(1)).pdf

endef

$(foreach d,$(CONTENT_DIRS),$(eval $(call CONTENT_RULES,$(d))))

list:
	@echo "single-source content:"
	@for d in $(CONTENT_DIRS); do \
	  p=$$(sed -n 's/^PAPER_DIR=//p' $$d/build.conf); \
	  s=$$(echo "$$(basename $$p)" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//'); \
	  printf '  %-22s make %s | make %s-pdf\n' "$$d" "$$s" "$$s"; \
	done

# Deliberately not a prerequisite of the build: it hits the network, so it
# is a pre-submission check rather than a cost every rebuild pays. Catches
# corrupted or invented reference metadata, which is the failure mode an
# LLM-assisted bibliography is most prone to.
check-refs:
	@bin/check-refs

clean:
	rm -rf arxiv-papers/*/build content/*/.build

help:
	@sed -n '3,20p' $(MAKEFILE_LIST) | sed 's/^# \{0,1\}//'
