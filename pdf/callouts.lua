-- Convert <div class="callout callout-VARIANT">…</div> blocks (which Pandoc
-- parses as Div elements with classes) into tcolorbox environments defined
-- in pdf/template.tex. Variants without a dedicated environment fall back
-- to "theorem".

local variant_to_env = {
  theorem    = "nsbcallouttheorem",
  lemma      = "nsbcalloutlemma",
  definition = "nsbcalloutdefinition",
  proof      = "nsbcalloutproof",
}

function Div(elem)
  if not elem.classes:includes("callout") then return nil end

  local env = "nsbcallouttheorem"
  for _, class in ipairs(elem.classes) do
    local variant = class:match("^callout%-(.+)$")
    if variant and variant_to_env[variant] then
      env = variant_to_env[variant]
      break
    end
  end

  local out = pandoc.List()
  out:insert(pandoc.RawBlock("latex", "\\begin{" .. env .. "}"))
  for _, block in ipairs(elem.content) do
    out:insert(block)
  end
  out:insert(pandoc.RawBlock("latex", "\\end{" .. env .. "}"))
  return out
end
