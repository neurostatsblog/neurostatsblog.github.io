# Generates one page per author at /authors/<slug>/.
# "Author" = any name listed in a post's `authors:` front-matter array.
#
# The layout (author-archive.html) receives:
#   page.title  — the author's name
#   page.author — same
#   page.posts  — array of posts authored by them, newest first
module Jekyll
  class AuthorPage < Page
    def initialize(site, base, dir, author, posts)
      @site = site
      @base = base
      @dir  = dir
      @name = "index.html"

      process(@name)

      self.data = {
        "layout" => "author-archive",
        "title"  => author,
        "author" => author,
        "posts"  => posts,
      }
    end
  end

  class AuthorPageGenerator < Generator
    safe true
    priority :low

    def generate(site)
      buckets = Hash.new { |h, k| h[k] = [] }

      site.posts.docs.each do |post|
        Array(post.data["authors"]).each do |author|
          name = author.is_a?(Hash) ? author["name"] : author
          next if name.nil? || name.to_s.empty?
          buckets[name] << post
        end
      end

      buckets.each do |author, posts|
        sorted = posts.sort_by(&:date).reverse
        slug = Jekyll::Utils.slugify(author)
        site.pages << AuthorPage.new(site, site.source, File.join("authors", slug), author, sorted)
      end
    end
  end
end
