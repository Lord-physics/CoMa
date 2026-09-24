from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    id: str
    provider: str
    email: str
    client_id: str
    tenant: str = "common"
    client_secret: str = ""
    refresh_token: str = ""


@dataclass(frozen=True)
class Message:
    account_id: str
    account_email: str
    provider: str
    id: str
    sender: str
    subject: str
    summary: str
    web_link: str | None
    received_at: str = ""

    @property
    def key(self) -> str:
        return f"{self.account_id}:{self.id}"
