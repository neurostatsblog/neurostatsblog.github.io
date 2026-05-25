#
# Inserts blank lines around standalone `$$` display-math delimiters so
# kramdown treats them as a block-level math construct (rendered as
# centered display) rather than as inline math (`\(...\)`).
#
# Authors can keep their markdown compact (no surrounding blank lines)
# so that pandoc/LaTeX downstream gets a tight input, and this hook
# transparently inserts the blank lines kramdown needs.
#
# Blank lines are only inserted OUTSIDE a $$...$$ block, never between
# the opening and closing markers.
#

module NeurostatsBlog
  module BlankLinesAroundMath
    module_function

    def process(content)
      return content if content.nil?

      lines = content.split("\n", -1)
      out = []
      in_math = false

      lines.each_with_index do |line, i|
        is_marker = (line.strip == "$$")

        if is_marker && !in_math
          # Opening $$ — ensure a blank line precedes it
          out << "" if !out.empty? && !out.last.strip.empty?
          out << line
          in_math = true
        elsif is_marker && in_math
          # Closing $$ — ensure a blank line follows it
          out << line
          in_math = false
          nxt = lines[i + 1]
          out << "" if nxt && !nxt.strip.empty?
        else
          out << line
        end
      end

      out.join("\n")
    end
  end
end

Jekyll::Hooks.register [:posts, :pages], :pre_render do |doc|
  next unless doc.extname =~ /\.(md|markdown)$/i

  doc.content = NeurostatsBlog::BlankLinesAroundMath.process(doc.content)
end
