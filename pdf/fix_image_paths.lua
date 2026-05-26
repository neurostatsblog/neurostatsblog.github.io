-- Two image-related fixes for the PDF build path:
--
-- 1. Jekyll-absolute paths -> in-container paths.
--    Posts use the site-root-relative convention `![](/assets/img/...)`
--    which Jekyll serves from `/`. Pandoc would otherwise read those as
--    filesystem-absolute and fail; we prepend `/data` (the in-container
--    repo mount) to any leading-slash, non-URL src.
--
-- 2. Default width to the full text width.
--    The figures from the analysis script are wide (15in default), so
--    without a width hint LaTeX scales them at native size and they
--    overflow the page. We set width="100%" on any image that doesn't
--    already carry an explicit width attribute. Pandoc translates this
--    to `\includegraphics[width=1.0\linewidth]{...}` in LaTeX. Authors
--    can still override per-image with `![](url){width=50%}`.

function Image(elem)
  -- (1) path rewrite
  if elem.src:sub(1, 1) == "/" and not elem.src:match("^https?://") then
    elem.src = "/data" .. elem.src
  end

  -- (2) default width
  if not elem.attributes.width or elem.attributes.width == "" then
    elem.attributes.width = "100%"
  end

  return elem
end
