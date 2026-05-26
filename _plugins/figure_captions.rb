#
# Wrap inline images in <figure> with auto-numbered <figcaption>.
#
# Authors write standard markdown:
#
#     ![Caption text here.](/path/to/image.png)
#
# Kramdown renders this as `<p><img alt="Caption text here." src="..." /></p>`.
# This post-render hook rewrites those single-image paragraphs into:
#
#     <figure>
#       <img alt="..." src="..." />
#       <figcaption><strong>Figure 1.</strong> Caption text here.</figcaption>
#     </figure>
#
# Numbering resets per page/post. The existing .post-body figure CSS in
# main.css then styles the result (rounded border, italic centered caption).
# Images without alt text are still wrapped in <figure> but get no caption.
#

require 'cgi'

module NeurostatsBlog
  module FigureCaptions
    module_function

    # Match a paragraph that contains exactly one image and nothing else.
    SINGLE_IMG_PARA = %r{
      <p>                                  # opening paragraph
      \s*
      (?<img><img\b[^>]*\/?>)              # the image tag
      \s*
      </p>                                 # closing paragraph
    }mx.freeze

    def process(html)
      return html if html.nil?
      fig_num = 0
      html.gsub(SINGLE_IMG_PARA) do
        img_tag = Regexp.last_match[:img]
        fig_num += 1
        alt_match = img_tag.match(/\balt="([^"]*)"/)
        if alt_match && !alt_match[1].strip.empty?
          # alt was HTML-escaped by kramdown when it became an attribute;
          # decode and re-encode just enough for inline text context
          # (the math `$...$` and other content should pass through fine).
          alt_text = CGI.unescapeHTML(alt_match[1])
          %(<figure>#{img_tag}<figcaption><strong>Figure #{fig_num}.</strong> #{alt_text}</figcaption></figure>)
        else
          %(<figure>#{img_tag}</figure>)
        end
      end
    end
  end
end

Jekyll::Hooks.register [:posts, :pages], :post_render do |doc|
  next unless doc.extname =~ /\.(md|markdown)$/i
  next if doc.output.nil?
  doc.output = NeurostatsBlog::FigureCaptions.process(doc.output)
end
