-- Pandoc lowers $$ ... $$ to \[ ... \] in LaTeX, but \[ \] cannot contain
-- AMS environments like \begin{equation} or \begin{align} — LaTeX raises
-- "Bad math environment delimiter". This filter spots display-math blocks
-- whose payload IS an AMS environment and emits them as raw LaTeX instead.

local ams_envs = {
  ["equation"]  = true, ["equation*"]  = true,
  ["align"]     = true, ["align*"]     = true,
  ["gather"]    = true, ["gather*"]    = true,
  ["multline"]  = true, ["multline*"]  = true,
  ["eqnarray"]  = true, ["eqnarray*"]  = true,
  ["alignat"]   = true, ["alignat*"]   = true,
  ["flalign"]   = true, ["flalign*"]   = true,
}

local function unwrap(text)
  local env = text:match("^%s*\\begin{([%w%*]+)}")
  if env and ams_envs[env] then
    return (text:gsub("^%s+", ""):gsub("%s+$", ""))
  end
  return nil
end

function Para(elem)
  if #elem.content == 1
     and elem.content[1].t == "Math"
     and elem.content[1].mathtype == "DisplayMath" then
    local raw = unwrap(elem.content[1].text)
    if raw then return pandoc.RawBlock("latex", raw) end
  end
  return nil
end

function Math(elem)
  if elem.mathtype == "DisplayMath" then
    local raw = unwrap(elem.text)
    if raw then return pandoc.RawInline("latex", raw) end
  end
  return nil
end
