"""Render Ansible semantic markup in the generated collection pages.

The mkdocs-ansible-collection plugin renders the raw ``doc`` and ``return``
values from ``ansible-doc``. Ansible markup such as ``M(module.name)`` or
``C(value)`` is therefore left as plain text in the generated Markdown. This
hook converts those macros to inline HTML for the collection pages only; hand
written docs and role READMEs are untouched.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from antsibull_docs_parser import dom
from antsibull_docs_parser.format import LinkProvider
from antsibull_docs_parser.html import to_html
from antsibull_docs_parser.parser import Context, parse

COLLECTION = "ak1ra_lab.general"
BUILTIN_DOCS = "https://docs.ansible.com/ansible/latest/collections/ansible/builtin"
KNOWN_MACROS = frozenset({"B", "C", "E", "I", "L", "M", "O", "R", "RV", "U", "V"})
FENCED_CODE = re.compile(
    r"^(?P<fence>`{3,}|~{3,}).*?^(?P=fence)\s*$",
    re.MULTILINE | re.DOTALL,
)
INLINE_CODE = re.compile(r"(`+)")


class CollectionLinkProvider(LinkProvider):
    """Resolve module references to the local site or docs.ansible.com."""

    def plugin_link(self, plugin: dom.PluginIdentifier) -> str | None:
        """Return a link for module and plugin references, when known."""
        fqcn = plugin.fqcn
        if fqcn.startswith("ansible.builtin."):
            name = fqcn.removeprefix("ansible.builtin.")
            return f"{BUILTIN_DOCS}/{name}_module.html"
        if fqcn.startswith(f"{COLLECTION}."):
            name = fqcn.removeprefix(f"{COLLECTION}.")
            return f"{name}.html"
        return None


LINK_PROVIDER = CollectionLinkProvider()


def _macro_spans(text: str) -> Iterator[tuple[int, int]]:
    """Yield ``(start, end)`` spans for known Ansible markup macros."""
    index = 0
    while index < len(text):
        if not text[index].isupper() or (index and (text[index - 1].isalnum() or text[index - 1] == "_")):
            index += 1
            continue

        name_end = index + 1
        while name_end < len(text) and (text[name_end].isupper() or text[name_end].isdigit() or text[name_end] == "_"):
            name_end += 1

        name = text[index:name_end]
        if name not in KNOWN_MACROS or name_end >= len(text) or text[name_end] != "(":
            index += 1
            continue

        depth = 1
        cursor = name_end + 1
        while cursor < len(text) and depth:
            if text[cursor] == "\\":
                cursor += 2
                continue
            if text[cursor] == "(":
                depth += 1
            elif text[cursor] == ")":
                depth -= 1
            cursor += 1

        if depth:
            index += 1
            continue

        yield index, cursor
        index = cursor


def _render_macro(macro: str) -> str:
    """Render one macro as inline HTML, falling back to the raw text."""
    try:
        paragraphs = parse(macro, Context(), strict=False)
        return to_html(paragraphs, link_provider=LINK_PROVIDER, par_start="", par_end="")
    except Exception:  # noqa: BLE001 - never break the docs build for one macro
        return macro


def _replace_macros_in_text(text: str) -> str:
    """Replace macros in one text chunk."""
    result: list[str] = []
    last = 0
    for start, end in _macro_spans(text):
        result.append(text[last:start])
        result.append(_render_macro(text[start:end]))
        last = end
    result.append(text[last:])
    return "".join(result)


def _replace_macros(text: str) -> str:
    """Replace macros in text that is not inside inline code."""
    chunks: list[str] = []
    in_code = False
    for chunk in INLINE_CODE.split(text):
        if not chunk:
            continue
        if set(chunk) == {"`"}:
            in_code = not in_code
            chunks.append(chunk)
        elif in_code:
            chunks.append(chunk)
        else:
            chunks.append(_replace_macros_in_text(chunk))
    return "".join(chunks)


def _render_markdown(text: str) -> str:
    """Render macros outside fenced code blocks."""
    result: list[str] = []
    last = 0
    for match in FENCED_CODE.finditer(text):
        result.append(_replace_macros(text[last : match.start()]))
        result.append(match.group(0))
        last = match.end()
    result.append(_replace_macros(text[last:]))
    return "".join(result)


def on_page_markdown(markdown, page, config, files):
    """Transform generated collection pages only."""
    if page.file.src_uri.startswith(f"{COLLECTION}/"):
        return _render_markdown(markdown)
    return markdown
