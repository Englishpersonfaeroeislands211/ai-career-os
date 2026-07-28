import re
from html import unescape
from html.parser import HTMLParser

STRIP_TAGS = frozenset({"script", "style", "noscript", "svg", "header", "footer", "nav"})


class _PasteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in STRIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in STRIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)
            self._chunks.append(" ")

    def get_text(self) -> str:
        return unescape("".join(self._chunks))


class JobPasteParseError(ValueError):
    pass


def _looks_like_html(text: str) -> bool:
    return bool(re.search(r"<\s*(html|body|div|main|article|p|h1|ul)\b", text, re.I))


def _collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def html_to_text(html: str) -> str:
    parser = _PasteHTMLParser()
    parser.feed(html)
    parser.close()
    return _collapse_whitespace(parser.get_text())


def prepare_job_post_text(raw: str) -> str:
    """Normalize user-pasted job content (plain text or copied HTML). No network access."""
    text = raw.strip()
    if not text:
        raise JobPasteParseError("Job posting text is empty")

    if _looks_like_html(text):
        text = html_to_text(text)

    text = _collapse_whitespace(text)
    if not text:
        raise JobPasteParseError("No readable text found in pasted content")

    return text
