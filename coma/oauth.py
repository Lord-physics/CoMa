"""Autenticación OAuth para aplicaciones públicas de escritorio."""

import base64
import hashlib
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from .http import RemoteError, post_form
from .i18n import tr
from .models import Account


GOOGLE_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
MS_SCOPE = "offline_access User.Read Mail.ReadWrite"


def _google_authorize(client_id: str, client_secret: str, notify) -> dict:
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            if query.get("state", [""])[0] == state:
                received["code"] = query.get("code", [""])[0]
                received["error"] = query.get("error", [""])[0]
            body = "<html><body>" + tr("browser_callback") + "</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    server.timeout = 1
    redirect = f"http://127.0.0.1:{server.server_port}/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    notify(tr("google_browser"))
    webbrowser.open(url)
    deadline = time.monotonic() + 180
    try:
        while time.monotonic() < deadline and not received:
            server.handle_request()
    finally:
        server.server_close()
    if not received.get("code"):
        raise RemoteError(tr("google_auth_failed"))
    fields = {"client_id": client_id, "code": received["code"], "code_verifier": verifier,
              "grant_type": "authorization_code", "redirect_uri": redirect}
    if client_secret:
        fields["client_secret"] = client_secret
    return post_form("https://oauth2.googleapis.com/token", fields)


def _microsoft_authorize(client_id: str, tenant: str, notify) -> dict:
    base = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0"
    # El código de dispositivo se muestra en la interfaz, nunca en un registro.
    request = urllib.request.Request(base + "/devicecode", data=urllib.parse.urlencode({"client_id": client_id, "scope": MS_SCOPE}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            import json
            device = json.load(response)
    except Exception:
        raise RemoteError(tr("microsoft_start_failed")) from None
    notify(tr("microsoft_device", url=device["verification_uri"], code=device["user_code"]))
    webbrowser.open(device["verification_uri"])
    deadline = time.monotonic() + int(device.get("expires_in", 900))
    interval = max(5, int(device.get("interval", 5)))
    while time.monotonic() < deadline:
        time.sleep(interval)
        fields = {"grant_type": "urn:ietf:params:oauth:grant-type:device_code", "client_id": client_id, "device_code": device["device_code"]}
        try:
            with urllib.request.urlopen(urllib.request.Request(base + "/token", data=urllib.parse.urlencode(fields).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=30) as response:
                import json
                return json.load(response)
        except urllib.error.HTTPError as exc:
            import json
            error = json.loads(exc.read()).get("error", "")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            raise RemoteError(tr("microsoft_rejected", error=error or exc.code)) from None
    raise RemoteError(tr("microsoft_expired"))


def authorize(provider: str, client_id: str, tenant: str, client_secret: str, notify) -> dict:
    if provider == "gmail":
        return _google_authorize(client_id, client_secret, notify)
    return _microsoft_authorize(client_id, tenant, notify)


def refresh(account: Account) -> dict:
    if account.provider == "gmail":
        fields = {"client_id": account.client_id, "refresh_token": account.refresh_token, "grant_type": "refresh_token"}
        if account.client_secret:
            fields["client_secret"] = account.client_secret
        return post_form("https://oauth2.googleapis.com/token", fields)
    base = f"https://login.microsoftonline.com/{account.tenant}/oauth2/v2.0/token"
    return post_form(base, {"client_id": account.client_id, "refresh_token": account.refresh_token,
                            "grant_type": "refresh_token", "scope": MS_SCOPE})
