-- content/<name>/source.md  ->  the arXiv preprint
--
-- Resolves the single-source syntax into LaTeX. Runs as the first filter in
-- bin/build-arxiv's pandoc chain, ahead of unwrap-ams.lua and citeproc.
-- See content/README.md for the syntax itself.

local FIG_EXT = ".pdf"

-- AMS environments cannot live inside the \[ ... \] that pandoc's LaTeX
-- writer wraps display math in. unwrap-ams.lua handles the document body
-- later in the chain, but any body we render to LaTeX ourselves — theorem
-- environments — has to be unwrapped here first.
local AMS = {
  ["equation"] = true, ["equation*"] = true, ["align"]    = true, ["align*"]    = true,
  ["gather"]   = true, ["gather*"]   = true, ["multline"] = true, ["multline*"] = true,
  ["alignat"]  = true, ["alignat*"]  = true, ["flalign"]  = true, ["flalign*"]  = true,
  ["eqnarray"] = true, ["eqnarray*"] = true,
}

local function ams_env(text)
  local env = text:match("^%s*\\begin{([%w%*]+)}")
  if env and AMS[env] then
    return (text:gsub("^%s+", ""):gsub("%s+$", ""))
  end
end

-- Render blocks to a LaTeX string. Emitting the body as markdown between
-- two raw \begin/\end blocks does not work: pandoc's raw-LaTeX reader
-- swallows everything up to the matching \end, so the markdown never gets
-- parsed and *emphasis* reaches the PDF as literal asterisks.
local function to_latex(blocks)
  -- Display math in a paragraph of its own becomes a raw block...
  local unwrapped = pandoc.Blocks(blocks):walk {
    Para = function(el)
      if #el.content == 1 and el.content[1].t == "Math"
         and el.content[1].mathtype == "DisplayMath" then
        local raw = ams_env(el.content[1].text)
        if raw then return pandoc.RawBlock("latex", raw) end
      end
    end,
  }
  -- ...and display math sitting inside running text becomes a raw inline.
  -- The callouts mix the two, so both cases have to be covered or pandoc
  -- emits \[\begin{align}...\end{align}\] and LaTeX rejects it.
  unwrapped = unwrapped:walk {
    Math = function(m)
      if m.mathtype == "DisplayMath" then
        local raw = ams_env(m.text)
        if raw then return pandoc.RawInline("latex", raw) end
      end
    end,
  }
  return pandoc.write(pandoc.Pandoc(unwrapped), "latex")
end

-- ---------------------------------------------------------------------
-- Conditionals: keep .paper-only, drop .blog-only
-- ---------------------------------------------------------------------
function Div(el)
  if el.classes:includes("blog-only") then return {} end
  if el.classes:includes("paper-only") then return el.content end

  -- Theorem-likes become real amsthm environments, so LaTeX numbers them.
  for _, kind in ipairs({ "definition", "theorem" }) do
    if el.classes:includes(kind) then
      local name = el.attributes["name"] or ""
      local open = "\\begin{" .. kind .. "}[" .. name .. "]"
      if el.identifier and el.identifier ~= "" then
        open = open .. "\n\\label{" .. el.identifier .. "}"
      end
      return pandoc.RawBlock("latex", table.concat({
        open, to_latex(el.content), "\\end{" .. kind .. "}",
      }, "\n"))
    end
  end

  -- Everything after this div is an appendix.
  if el.classes:includes("appendix") then
    local out = pandoc.List()
    out:insert(pandoc.RawBlock("latex", "\\appendix"))
    out:extend(el.content)
    return out
  end
end

function Span(el)
  if el.classes:includes("blog-only") then return {} end
  if el.classes:includes("paper-only") then return el.content end
end

-- Wikipedia is a fine pointer in a blog post and reads as an unsourced
-- claim in a preprint. Keep the wording, drop the hyperlink. Done here
-- rather than with a conditional span at each site: there are ten of them,
-- they all want the same treatment, and future ones get it for free.
function Link(el)
  if el.target:match("^https?://[%w%.%-]*wikipedia%.org/") then
    return el.content
  end
end

-- ---------------------------------------------------------------------
-- The abstract is prose, so it is authored in source.md like everything
-- else rather than as a YAML block scalar. Hoisting it into metadata here
-- is what lets the template place it inside \begin{abstract} — pandoc has
-- no other route from body content to a template variable.
--
-- Runs after the element filters above, so anything inside the abstract
-- (conditional spans, citations) has already been resolved.
-- ---------------------------------------------------------------------
function Pandoc(doc)
  local kept = pandoc.List()
  for _, blk in ipairs(doc.blocks) do
    if blk.t == "Div" and blk.classes:includes("abstract") then
      doc.meta.abstract = pandoc.MetaBlocks(blk.content)
    else
      kept:insert(blk)
    end
  end
  doc.blocks = kept
  return doc
end

-- ---------------------------------------------------------------------
-- Figures: a lone image becomes a float carrying its own \label, so that
-- \ref{fig:...} resolves through LaTeX rather than a hand-typed number.
-- ---------------------------------------------------------------------
function Para(el)
  if #el.content ~= 1 or el.content[1].t ~= "Image" then return nil end
  local img = el.content[1]
  local caption = pandoc.write(pandoc.Pandoc({ pandoc.Plain(img.caption) }), "latex")
  caption = caption:gsub("%s+$", "")
  local label = ""
  if img.identifier and img.identifier ~= "" then
    label = "\n\\label{" .. img.identifier .. "}"
  end
  return pandoc.RawBlock("latex", table.concat({
    "\\begin{figure}[t]",
    "\\centering",
    "\\includegraphics[width=\\textwidth]{" .. img.src .. FIG_EXT .. "}",
    "\\caption{" .. caption .. "}" .. label,
    "\\end{figure}",
  }, "\n"))
end
