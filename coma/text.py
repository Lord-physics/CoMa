"""Extracción y resumen local; nunca interpreta HTML como contenido activo."""

import html
import re
from collections import Counter
from html.parser import HTMLParser


STOPWORDS = frozenset("de la el los las un una unos unas y o que en por para con del al a es se su sus como no si lo le ya the and to of in is for on with this that you your from it".split())
QUOTE_MARKERS = re.compile(r"^(?:>|El .+ escribió:|On .+ wrote:|De:\s|From:\s|_{8,}|-{8,})", re.I)
SIGNATURE_MARKERS = re.compile(r"^(?:--\s*$|Enviado desde mi |Sent from my |Un saludo[,!.]*$|Saludos[,!.]*$|Atentamente[,!.]*$)", re.I)
WORDS = re.compile(r"[\wáéíóúüñ]{3,}", re.I)
SENTENCES = re.compile(r"(?<=[.!?])\s+|\n+")


class _TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.hidden = 0
        self.tags: list[tuple[str, bool]] = []

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").lower()
        suppress = tag in {"script", "style", "head", "svg", "iframe", "blockquote"} or any(
            marker in classes for marker in ("gmail_quote", "yahoo_quoted", "gmail_signature"))
        if tag not in {"br", "hr", "img", "input", "meta", "link"}:
            self.tags.append((tag, suppress))
        self.hidden += suppress
        if not self.hidden and tag in {"p", "div", "br", "li", "tr"}:
            self.chunks.append("\n")

    def handle_endtag(self, tag):
        matching = next((index for index in range(len(self.tags) - 1, -1, -1) if self.tags[index][0] == tag), None)
        if matching is not None:
            for _, suppressed in self.tags[matching:]:
                self.hidden -= suppressed
            del self.tags[matching:]
        if not self.hidden and tag in {"p", "div", "li", "tr"}:
            self.chunks.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.chunks.append(data)


def plain_text(content: str, is_html: bool = False) -> str:
    if is_html:
        parser = _TextOnly()
        parser.feed(content)
        content = "".join(parser.chunks)
    content = html.unescape(content).replace("\r", "")
    lines = []
    for line in content.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if QUOTE_MARKERS.match(line) or SIGNATURE_MARKERS.match(line):
            break
        if line:
            lines.append(line)
    return "\n".join(lines)


def summarize(content: str, *, is_html: bool = False, max_chars: int = 280) -> str:
    clean = plain_text(content, is_html)
    if not clean:
        return "Sin texto para resumir."
    sentences = [s.strip() for s in SENTENCES.split(clean) if s.strip()]
    unique = list(dict.fromkeys(sentences))
    if len(unique) <= 2:
        return " ".join(unique)[:max_chars].rstrip()
    counts = Counter(word.lower() for word in WORDS.findall(clean) if word.lower() not in STOPWORDS)
    scored = []
    for index, sentence in enumerate(unique):
        words = [w.lower() for w in WORDS.findall(sentence) if w.lower() not in STOPWORDS]
        score = sum(counts[w] for w in set(words)) / max(len(words), 1)
        score += 0.3 if index == 0 else 0
        scored.append((score, index, sentence))
    chosen = sorted(sorted(scored, reverse=True)[:2], key=lambda row: row[1])
    return " ".join(row[2] for row in chosen)[:max_chars].rstrip()
