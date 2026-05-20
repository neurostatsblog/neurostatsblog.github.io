source "https://rubygems.org"

# The site is built by GitHub Actions (see .github/workflows/jekyll.yml),
# not by GitHub Pages' built-in builder, so we use modern Jekyll directly
# instead of the version-pinned `github-pages` gem.
gem "jekyll", "~> 4.3"

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-seo-tag"
  gem "jekyll-sitemap"
  gem "jekyll-archives"   # generates a page per tag (and category, if enabled)
end

# Platform-specific gems needed for local builds.
gem "webrick", "~> 1.8"             # required on Ruby >= 3.0 for `jekyll serve`
gem "tzinfo", ">= 1", "< 3"
gem "tzinfo-data", platforms: [:mingw, :x64_mingw, :mswin, :jruby]
gem "wdm", "~> 0.1.1", platforms: [:mingw, :x64_mingw, :mswin]
