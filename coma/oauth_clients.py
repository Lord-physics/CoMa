"""OAuth registrations supplied once by the CoMa distributor, never by mail users."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OAuthClient:
    client_id: str
    tenant: str = "common"
    client_secret: str = ""


def configuration_path() -> Path:
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    return base / "oauth-clients.json"


def bundled_client(provider: str, path: Path | None = None) -> OAuthClient | None:
    """Return a publisher registration for the selected provider, if configured."""
    source = path or configuration_path()
    if not source.is_file():
        return None
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        row = data["microsoft" if provider in {"outlook", "educacyl"} else provider]
        client_id = row["client_id"].strip()
        tenant = ("organizations" if provider == "educacyl" else row.get("tenant", "common")).strip()
        secret = row.get("client_secret", "").strip()
        if not client_id or not tenant or "/" in tenant:
            return None
        return OAuthClient(client_id, tenant, secret if provider == "gmail" else "")
    except (OSError, ValueError, KeyError, AttributeError, TypeError):
        return None
