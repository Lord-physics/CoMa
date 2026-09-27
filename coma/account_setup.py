"""Detección conservadora del proveedor a partir del correo indicado."""

import re


OUTLOOK_DOMAINS = {
    "outlook.com", "outlook.es", "hotmail.com", "hotmail.es",
    "live.com", "live.es", "msn.com",
}


def valid_email(address: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address))


def detect_provider(address: str) -> str | None:
    if not valid_email(address):
        return None
    domain = address.rsplit("@", 1)[1].lower()
    if domain in {"gmail.com", "googlemail.com"}:
        return "gmail"
    if domain in OUTLOOK_DOMAINS:
        return "outlook"
    if domain == "educa.jcyl.es":
        return "educacyl"
    return None
