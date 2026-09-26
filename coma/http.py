"""Cliente JSON pequeño; los errores nunca incluyen tokens ni cuerpos remotos."""

import json
import urllib.error
import urllib.parse
import urllib.request

from .i18n import tr


class RemoteError(RuntimeError):
    pass


def request_json(url: str, *, token: str | None = None, method: str = "GET", data: dict | None = None, headers: dict | None = None) -> dict:
    request_headers = {"Accept": "application/json", **(headers or {})}
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=payload, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise RemoteError(tr("http_service", code=exc.code)) from None
    except urllib.error.URLError:
        raise RemoteError(tr("http_mail_connect")) from None


def post_form(url: str, fields: dict) -> dict:
    payload = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Un error de OAuth se traduce a un código breve sin registrar la respuesta.
        raise RemoteError(tr("http_auth", code=exc.code)) from None
    except urllib.error.URLError:
        raise RemoteError(tr("http_auth_connect")) from None
