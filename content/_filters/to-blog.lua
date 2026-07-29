-- content/<name>/source.md  ->  _posts/<date>-<slug>.md
--
-- Resolves the single-source syntax into Jekyll-flavoured markdown. LaTeX
-- cross-referencing has no equivalent on the web, so this filter resolves
-- \ref itself: figures become literal numbers (matching the numbering that
-- _plugins/figure_captions.rb applies), section refs become anchor links.
--
-- Set --metadata img_dir=<path> to point image sources at the asset tree.
--
-- Everything is driven from Pandoc() rather than from top-level element
-- functions, because pandoc would otherwise run those in its own traversal
-- *before* Pandoc() — i.e. before the \ref lookup tables have been built.

local img_dir = "assets/img/posts"
local FIG_EXT = ".png"

local fig_number = {}   -- "fig:wealth" -> "2"
local heading    = {}   -- "sec:game"   -> { id = "sec-game", text = "The betting game" }

-- kramdown generates its own heading ids; we pin explicit ones instead, and
-- avoid colons since they are awkward in CSS selectors.
local function web_id(s) return (s:gsub(":", "-")) end

local function is_figure(el)
  return #el.content == 1 and el.content[1].t == "Image"
end

-- ---------------------------------------------------------------------
-- Conditionals: keep .blog-only, drop .paper-only
-- ---------------------------------------------------------------------
local function do_div(el)
  if el.classes:includes("paper-only") then return {} end
  if el.classes:includes("blog-only") then return el.content end
  -- Authored in source.md but destined for the paper's title block; a post
  -- has no abstract.
  if el.classes:includes("abstract") then return {} end

  -- Theorem-likes reuse the site's existing .callout styling.
  --
  -- The body is rendered to HTML here rather than left as markdown behind a
  -- markdown="1" attribute. kramdown would otherwise re-parse it and mangle
  -- the display math inside: `\mathbb{E}_{X \sim B}` comes back out as
  -- `\mathbb{E}<em>{X \sim B}`. Handing MathJax finished HTML avoids the
  -- whole problem, and matches how these blocks were written by hand.
  for _, kind in ipairs({ "definition", "theorem" }) do
    if el.classes:includes(kind) then
      local name = el.attributes["name"]
      local id = el.identifier ~= "" and (' id="' .. web_id(el.identifier) .. '"') or ""
      local blocks = pandoc.List()
      if name and name ~= "" then
        blocks:insert(pandoc.Para({ pandoc.Strong({ pandoc.Str(name .. ".") }) }))
      end
      blocks:extend(el.content)
      -- Keep the delimiters MathJax expects. Left to itself, pandoc's HTML
      -- writer typesets math into <em>-laden markup that MathJax then skips.
      blocks = pandoc.Blocks(blocks):walk {
        Math = function(m)
          local d = m.mathtype == "DisplayMath" and "$$" or "$"
          return pandoc.RawInline("html", d .. m.text .. d)
        end,
      }
      local inner = pandoc.write(pandoc.Pandoc(blocks), "html")
      return pandoc.RawBlock("html", table.concat({
        '<div class="callout callout-' .. kind .. '"' .. id .. ">",
        inner,
        "</div>",
      }, "\n"))
    end
  end

  if el.classes:includes("appendix") then
    local out = pandoc.List()
    out:insert(pandoc.RawBlock("html", '<div class="supplementary-notes" markdown="1">'))
    out:extend(el.content)
    out:insert(pandoc.RawBlock("html", "</div>"))
    return out
  end

  -- Catch-all, which also covers the #refs wrapper and the per-entry
  -- .csl-entry divs citeproc emits. kramdown has no fenced-div syntax, so
  -- any Div left as-is would surface on the page as literal ":::".
  local attrs = ""
  if el.identifier ~= "" then attrs = attrs .. ' id="' .. web_id(el.identifier) .. '"' end
  if #el.classes > 0 then
    attrs = attrs .. ' class="' .. table.concat(el.classes, " ") .. '"'
  end
  local out = pandoc.List()
  out:insert(pandoc.RawBlock("html", "<div" .. attrs .. ' markdown="1">'))
  out:extend(el.content)
  out:insert(pandoc.RawBlock("html", "</div>"))
  return out
end

-- kramdown's GFM parser does not treat `$...$` as math, so it mangles the
-- LaTeX inside: `_` pairs become emphasis, and any backslash escape it
-- recognises is collapsed, turning `\{` into a bare `{` that MathJax then
-- reads as a group delimiter rather than a brace. Escaping each of those
-- characters makes kramdown hand MathJax back exactly what we wrote.
--
-- Display math is left alone: kramdown does recognise `$$...$$` blocks and
-- passes them through untouched.
local function do_math(el)
  if el.mathtype ~= "InlineMath" then return nil end
  el.text = el.text:gsub("([\\_*])", "\\%1")
  return el
end

local function do_span(el)
  if el.classes:includes("paper-only") then return {} end
  if el.classes:includes("blog-only") then return el.content end
  if el.identifier == "" and #el.classes == 0 then return el.content end

  -- Catch-all, mirroring the one for divs. Without it, spans citeproc adds
  -- (notably .nocase, which suppresses CSL title-casing) reach the page as
  -- a literal "{.nocase}".
  local attrs = ""
  if el.identifier ~= "" then attrs = attrs .. ' id="' .. web_id(el.identifier) .. '"' end
  if #el.classes > 0 then
    attrs = attrs .. ' class="' .. table.concat(el.classes, " ") .. '"'
  end
  local out = pandoc.List()
  out:insert(pandoc.RawInline("html", "<span" .. attrs .. ">"))
  out:extend(el.content)
  out:insert(pandoc.RawInline("html", "</span>"))
  return out
end

local function do_header(el)
  if el.identifier ~= "" then el.identifier = web_id(el.identifier) end
  -- kramdown understands `## Heading {#id}` but not an id combined with a
  -- class, which it prints verbatim. Classes carry no meaning on the web
  -- anyway — .unnumbered is only there to stop LaTeX numbering the section.
  el.classes = pandoc.List()
  el.attributes = pandoc.Attr().attributes
  return el
end

-- Bare names in the source, asset paths on the web. Image attributes are
-- dropped because kramdown renders a trailing {#id} as literal text.
local function do_para(el)
  if not is_figure(el) then return nil end
  local img = el.content[1]
  return pandoc.Para({ pandoc.Image(img.caption, "/" .. img_dir .. "/" .. img.src .. FIG_EXT) })
end

local function do_rawinline(el)
  if el.format ~= "latex" and el.format ~= "tex" then return nil end

  -- MathJax only typesets inside delimiters, so a bare \eqref renders as
  -- literal text. Wrapping it as inline math makes it a real equation link.
  local eq = el.text:match("^\\eqref%{(.+)%}$")
  if eq then return pandoc.Math("InlineMath", "\\eqref{" .. eq .. "}") end

  local ref = el.text:match("^\\ref%{(.+)%}$")
  if ref then
    if fig_number[ref] then return pandoc.Str(fig_number[ref]) end
    local h = heading[ref]
    if h then return pandoc.Link({ pandoc.Str(h.text) }, "#" .. h.id) end
    io.stderr:write("to-blog.lua: unresolved \\ref{" .. ref .. "}\n")
    return pandoc.Str("?")
  end
end

function Pandoc(doc)
  if doc.meta.img_dir then img_dir = pandoc.utils.stringify(doc.meta.img_dir) end

  -- Prune paper-only content up front. Two reasons: figure numbering must
  -- match what a reader of the post actually counts, and pandoc's traversal
  -- is bottom-up — a \ref inside a paper-only span would otherwise be
  -- visited, and reported unresolved, before the span itself is dropped.
  local pruned = doc:walk {
    Div  = function(el) if el.classes:includes("paper-only") then return {} end end,
    Span = function(el) if el.classes:includes("paper-only") then return {} end end,
  }
  local n = 0
  pruned:walk {
    Para = function(el)
      if is_figure(el) and el.content[1].identifier ~= "" then
        n = n + 1
        fig_number[el.content[1].identifier] = tostring(n)
      end
    end,
    Header = function(el)
      if el.identifier ~= "" then
        heading[el.identifier] = {
          id = web_id(el.identifier),
          text = pandoc.utils.stringify(el.content),
        }
      end
    end,
  }

  -- Pass 2, on the pruned copy.
  local out = pruned:walk {
    Div = do_div, Span = do_span, Header = do_header,
    Para = do_para, RawInline = do_rawinline,
  }
  -- Escaping runs last, over what is left. Callout bodies have already been
  -- rendered to raw HTML by now, so their math is no longer a Math element
  -- and correctly escapes nothing — it never passes through kramdown.
  return out:walk { Math = do_math }
end
