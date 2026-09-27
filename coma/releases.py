"""Descarga manual y verificada de la última versión de Windows."""

import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from .i18n import tr


LATEST_RELEASE = "https://api.github.com/repos/Lord-physics/CoMa/releases/latest"
ASSET_NAME = "CoMa-Windows.zip"
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "CoMa-Desktop"}


class ReleaseError(RuntimeError):
    """Error de descarga que se puede mostrar sin exponer respuestas remotas."""


def _latest_asset() -> tuple[str, str, str]:
    try:
        request = urllib.request.Request(LATEST_RELEASE, headers=HEADERS)
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise ReleaseError(tr("release_connection_failed")) from exc

    if not isinstance(release, dict):
        raise ReleaseError(tr("release_missing"))
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ReleaseError(tr("release_missing"))
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("name") != ASSET_NAME or asset.get("state") != "uploaded":
            continue
        url = asset.get("browser_download_url", "")
        digest = asset.get("digest", "")
        if not isinstance(url, str) or not isinstance(digest, str):
            raise ReleaseError(tr("release_invalid"))
        try:
            parsed = urlsplit(url)
            valid_url = (parsed.scheme == "https" and parsed.hostname == "github.com"
                         and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment
                         and parsed.path.startswith("/Lord-physics/CoMa/releases/download/")
                         and parsed.path.endswith("/" + ASSET_NAME))
        except ValueError:
            valid_url = False
        if (not valid_url
                or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest)):
            raise ReleaseError(tr("release_invalid"))
        return str(release.get("tag_name", "")), url, digest[7:].lower()
    raise ReleaseError(tr("release_missing"))


def download_latest(destination: Path) -> str:
    """Guarda el ZIP completo y verificado; devuelve la etiqueta publicada."""
    destination = Path(destination)
    if destination.suffix.lower() != ".zip" or not destination.parent.is_dir():
        raise ReleaseError(tr("release_bad_destination"))
    tag, url, expected = _latest_asset()
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".coma-download-", suffix=".part", dir=destination.parent)
        with os.fdopen(fd, "wb") as output:
            request = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
            with urllib.request.urlopen(request, timeout=60) as response:
                digest = hashlib.sha256()
                size = 0
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_DOWNLOAD_BYTES:
                        raise ReleaseError(tr("release_too_large"))
                    output.write(chunk)
                    digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ReleaseError(tr("release_hash_failed"))
        os.replace(temporary, destination)
        temporary = None
        return tag
    except (OSError, urllib.error.URLError) as exc:
        raise ReleaseError(tr("release_download_failed")) from exc
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
