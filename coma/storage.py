"""Estado local sin contenido de mensajes; tokens cifrados por DPAPI."""

import json
import os
from dataclasses import asdict
from pathlib import Path
from threading import RLock

from .models import Account
from .secrets import protect, unprotect


def data_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "CoMa"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


class AccountStore:
    def __init__(self, path: Path | None = None):
        self.path = path or data_dir() / "accounts.json"
        self.lock = RLock()

    def list(self) -> list[Account]:
        with self.lock:
            if not self.path.exists():
                return []
            rows = json.loads(self.path.read_text(encoding="utf-8"))
            return [Account(**{**row, "refresh_token": unprotect(row["refresh_token"]), "client_secret": unprotect(row["client_secret"]) if row.get("client_secret") else ""}) for row in rows]

    def save(self, accounts: list[Account]) -> None:
        with self.lock:
            rows = [{**asdict(account), "refresh_token": protect(account.refresh_token), "client_secret": protect(account.client_secret) if account.client_secret else ""} for account in accounts]
            _write_json(self.path, rows)

    def upsert(self, account: Account) -> None:
        with self.lock:
            self.save([row for row in self.list() if row.id != account.id] + [account])

    def remove(self, account_id: str) -> None:
        with self.lock:
            self.save([row for row in self.list() if row.id != account_id])
