"""Summarize an HTML file to see the structure we care about."""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class HtmlSummarizer(HTMLParser):
    """Summarize an HTML file by keeping only the parts we are interested in.

    We only want the content of <div role="main">. We want to omit certain
    tags like <span> that are used for styling but don't affect the structure.
    We want to ignore some tags and their contents.

    For links, we add a "self-link" class if the link points to an id that is
    currently "in scope", that is, clicking it would keep you in the same
    section of the page the link is in.

    """

    def __init__(self) -> None:
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

        # Stack of tags we're currently inside.
        self.tags = []
        # The ids for each element in our current stack. Some ids are moved
        # up to parent elements. <dl><dt id="foo"> should be treated as if it
        # were <dl id="foo"><dt>.
        self.element_ids = []
        # The set of all ids we're inside.
        self.current_ids = set()

        self.output = []

    def print(self, s: str, open: bool = False, close: bool = False) -> None:
        if close:
            self.print_indent -= 2
        self.output.append(" " * self.print_indent)
        self.output.append(s)
        self.output.append("\n")
        if open:
            self.print_indent += 2

    def summary(self) -> str:
        return "".join(self.output)

    def has_class(self, dattrs: dict[str, str | None], class_name: str) -> bool:
        return class_name in (dattrs.get("class") or "").split()

    def should_ignore(self, tag: str, dattrs: dict[str, str | None]) -> bool:
        """Return true if we should ignore this tag and all its contents."""
        if tag == "a" and self.has_class(dattrs, "headerlink"):
            return True
        return False

    def should_omit(self, tag: str, dattrs: dict[str, str | None]) -> bool:
        """Return true if we should omit this tag but still attend to its contents."""
        if tag == "span":
            return True
        return False

    # Map of tags to the parent tag that should get their ids.
    ID_PARENTS = {
        "dt": "dl",
    }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        dattrs = dict(attrs)
        if self.main and not self.ignoring:
            if self.should_ignore(tag, dattrs):
                self.ignoring = True
                self.ignoring_start_level = self.indent
            elif self.should_omit(tag, dattrs):
                self.omit_levels.add(self.indent)
            else:
                tattrs = "".join(f' {k}="{v}"' for k, v in attrs if k in {"id", "href"})
                href = dattrs.get("href")
                if href and href.startswith("#"):
                    if href[1:] in self.current_ids:
                        tattrs += ' class="self-link"'
                self.print(f"<{tag}{tattrs}>", open=True)
                id = dattrs.get("id")
                ids = []
                if id:
                    assert id not in self.current_ids, f"Duplicate id: {id}"
                    self.current_ids.add(id)
                    parent_to_id = self.ID_PARENTS.get(tag)
                    if parent_to_id and self.tags and self.tags[-1] == parent_to_id:
                        self.element_ids[-1].append(id)
                        ids = []
                self.element_ids.append(ids)
                self.tags.append(tag)
            self.indent += 1
        if dattrs.get("role") == "main":
            self.main = True

    def handle_endtag(self, tag: str) -> None:
        if self.main:
            self.indent -= 1
            if self.indent in self.omit_levels:
                self.omit_levels.remove(self.indent)
            elif not self.ignoring:
                self.print(f"</{tag}>", close=True)
                self.tags.pop()
                ids = self.element_ids.pop()
                for id in ids:
                    self.current_ids.remove(id)
            else:
                if self.indent == self.ignoring_start_level:
                    self.ignoring = False
            if self.indent == 0:
                self.main = False

    def handle_data(self, data: str) -> None:
        if self.main and not self.ignoring:
            data = re.sub(r"\s+", " ", data.strip())
            if data:
                self.print(data)


def summarize_html_file(filename: str) -> str:
    parser = HtmlSummarizer()
    parser.feed(Path(filename).read_text())
    return parser.summary()


if __name__ == "__main__":
    sys.stdout.write(summarize_html_file(sys.argv[1]))
