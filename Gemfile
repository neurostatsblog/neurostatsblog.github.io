source "https://rubygems.org"

# Local builds use plain Jekyll (pinned to the version GitHub Pages itself
# runs) rather than the `github-pages` gem. The github-pages gem forcibly
# sets safe: true which disables custom _plugins/ — and we need one for the
# blank-lines-around-display-math hook. Production (GitHub Pages) ignores
# _plugins/ anyway, so this divergence is purely a local-preview concern.
gem "jekyll", "~> 3.10.0"
gem "kramdown-parser-gfm"

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-seo-tag"
  gem "jekyll-sitemap"
  gem "jekyll-archives"   # generates a page per tag (and category, if enabled)
end

# Required for Ruby 3.4+ where these are no longer default gems
gem "csv"
gem "base64"
gem "logger"
gem "webrick"
gem "tzinfo"
gem "tzinfo-data"
gem "wdm"
