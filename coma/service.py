"""Coordinación de cuentas, sincronización y aprendizaje."""

import uuid
from dataclasses import replace

from .classifier import SpamClassifier
from .i18n import tr
from .models import Account, Message
from .oauth import authorize, refresh
from .providers import PartialActionError, provider_for
from .storage import AccountStore


class MailService:
    def __init__(self, accounts: AccountStore | None = None, classifier: SpamClassifier | None = None):
        self.accounts = accounts or AccountStore()
        self.classifier = classifier or SpamClassifier()

    def add_account(self, provider: str, client_id: str, tenant: str, client_secret: str, notify) -> Account:
        credentials = authorize(provider, client_id, tenant, client_secret, notify)
        refresh_token = credentials.get("refresh_token")
        if not refresh_token:
            raise ValueError(tr("refresh_missing"))
        temporary = Account(str(uuid.uuid4()), provider, "", client_id, tenant, client_secret, refresh_token)
        email = provider_for(temporary, credentials["access_token"]).identity()
        account = replace(temporary, email=email)
        self.accounts.upsert(account)
        return account

    def _access(self, account: Account):
        credentials = refresh(account)
        rotated = credentials.get("refresh_token")
        if rotated and rotated != account.refresh_token:
            account = replace(account, refresh_token=rotated)
            self.accounts.upsert(account)
        return provider_for(account, credentials["access_token"])

    def sync(self) -> tuple[list[Message], list[str]]:
        messages, errors = [], []
        for account in self.accounts.list():
            try:
                messages.extend(self._access(account).unread())
            except (OSError, ValueError, KeyError, RuntimeError) as exc:
                errors.append(f"{account.email}: {exc}")
        messages.sort(key=lambda message: message.received_at, reverse=True)
        return messages, errors

    def action(self, message: Message, action: str) -> None:
        account = next((row for row in self.accounts.list() if row.id == message.account_id), None)
        if account is None:
            raise ValueError(tr("account_missing"))
        try:
            self._access(account).action(message, action)
        except PartialActionError:
            self.classifier.learn(message.key, message.sender, message.subject, message.summary, spam=True)
            raise
        if action in {"spam", "spam_delete"}:
            try:
                self.classifier.learn(message.key, message.sender, message.subject, message.summary, spam=True)
            except OSError:
                raise RuntimeError(tr("learning_failed")) from None

    def not_spam(self, message: Message) -> None:
        self.classifier.learn(message.key, message.sender, message.subject, message.summary, spam=False)

    def possible_spam(self, messages: list[Message]) -> list[Message]:
        return [message for message in messages if self.classifier.is_possible_spam(message.sender, message.subject, message.summary)
                and not self.classifier.examples.get(message.key, {}).get("spam") is False]
