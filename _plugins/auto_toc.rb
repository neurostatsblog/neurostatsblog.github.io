#
# When a post or page has `toc: true` in its YAML front matter, prepend
# a kramdown table-of-contents marker to the content. Kramdown then
# replaces the marker with a nested <ul id="markdown-toc"> of headings.
#
# Authors don't need to write the `{:toc}` marker manually; setting
# `toc: true` in the YAML is enough. Set it back to `false` (or omit it)
# to opt out.
#

module NeurostatsBlog
  module AutoTOC
    module_function

    MARKER = <<~MARKDOWN
      ## Contents
      {:.no_toc}

      * temporary placeholder, replaced by kramdown's {:toc} directive
      {:toc}

    MARKDOWN

    def prepend(content)
      return content if content.nil?
      MARKER + content
    end
  end
end

Jekyll::Hooks.register [:posts, :pages], :pre_render do |doc|
  next unless doc.extname =~ /\.(md|markdown)$/i
  next unless doc.data["toc"]
  doc.content = NeurostatsBlog::AutoTOC.prepend(doc.content)
end
