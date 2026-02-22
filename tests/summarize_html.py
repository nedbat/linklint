import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class HtmlSummarizer(HTMLParser):
    """Summarize an HTML file by printing only the parts we are interested in.

    We only want the content of <div role="main">. We want to omit certain
    tags like <span> that are used for styling but don't affect the structure.
    We want to ignore some tags and their contents.
    """

    def __init__(self):
        super().__init__()
        # The tag indentation level of the original HTML.
        self.indent = 0
        # The printing indentation level.
        self.print_indent = 0
        # Have we found role="main" yet?
        self.main = False
        # Are we ignoring all tags until we get back to the same indent level?
        self.ignoring = False
        self.ignoring_start_level = 0
        # Indent levels of tags we'll omit, while still attending to their children.
        self.omit_levels = set()

        self.output = []

    def print(self, s):
        if s[:2] == "</":
            self.print_indent -= 2
        self.output.append(" " * self.print_indent)
        self.output.append(s)
        self.output.append("\n")
        if s[0] == "<" and s[1] != "/":
            self.print_indent += 2

    def summary(self):
        return "".join(self.output)

    def should_ignore(self, tag, dattrs):
        if tag == "a" and "headerlink" in dattrs.get("class", "").split():
            return True
        return False

    def should_omit(self, tag, dattrs):
        if tag == "span":
            return True
        return False

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if self.main and not self.ignoring:
            if self.should_ignore(tag, dattrs):
                self.ignoring = True
                self.ignoring_start_level = self.indent
            elif self.should_omit(tag, dattrs):
                self.omit_levels.add(self.indent)
            else:
                tattrs = "".join(f' {k}="{v}"' for k, v in attrs if k in {"id", "href"})
                self.print(f"<{tag}{tattrs}>")
            self.indent += 1
        if dattrs.get("role") == "main":
            self.main = True

    def handle_endtag(self, tag):
        if self.main:
            self.indent -= 1
            if self.indent in self.omit_levels:
                self.omit_levels.remove(self.indent)
            elif not self.ignoring:
                self.print(f"</{tag}>")
            else:
                if self.indent == self.ignoring_start_level:
                    self.ignoring = False
            if self.indent == 0:
                self.main = False

    def handle_data(self, data):
        if self.main and not self.ignoring:
            data = re.sub(r"\s+", " ", data.strip())
            if data:
                assert data[0] != "<"
                self.print(data)


def summarize_html_file(filename):
    parser = HtmlSummarizer()
    parser.feed(Path(filename).read_text())
    return parser.summary()


if __name__ == "__main__":
    sys.stdout.write(summarize_html_file(sys.argv[1]))
