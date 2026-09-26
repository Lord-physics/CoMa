"""Adaptadores de Gmail y Microsoft Graph."""

import base64
import email.header
import urllib.parse

from .http import RemoteError, request_json
from .i18n import tr
from .models import Account, Message
from .text import summarize


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _decode_header(value: str) -> str:
    fragments = []
    for part, encoding in email.header.decode_header(value):
        fragments.append(part.decode(encoding or "utf-8", errors="replace") if isinstance(part, bytes) else part)
    return "".join(fragments)


def _gmail_body(payload: dict) -> tuple[str, bool]:
    plain = []
    html = []

    def visit(part):
        if part.get("filename") or part.get("body", {}).get("attachmentId"):
            return
        mime = part.get("mimeType", "")
        encoded = part.get("body", {}).get("data", "")
        if encoded and mime in {"text/plain", "text/html"}:
            try:
                content = base64.urlsafe_b64decode(encoded + "===").decode("utf-8", errors="replace")
            except (ValueError, UnicodeError):
                content = ""
            if mime == "text/plain":
                plain.append(content)
            else:
                html.append(content)
        for child in part.get("parts", []):
            visit(child)

    visit(payload)
    return ("\n".join(plain), False) if plain else ("\n".join(html), True)


class PartialActionError(RemoteError):
    """El mensaje ya se marcó como spam, pero no llegó a la papelera."""


class Gmail:
    base = "https://gmail.googleapis.com/gmail/v1/users/me"

    def __init__(self, account: Account, token: str):
        self.account, self.token = account, token

    def identity(self) -> str:
        return request_json(self.base + "/profile", token=self.token)["emailAddress"]

    def unread(self) -> list[Message]:
        result = []
        page = None
        while True:
            params = {"q": "in:inbox is:unread -in:spam -in:trash", "maxResults": "100"}
            if page:
                params["pageToken"] = page
            listing = request_json(self.base + "/messages?" + urllib.parse.urlencode(params), token=self.token)
            for item in listing.get("messages", []):
                raw = request_json(self.base + "/messages/" + _q(item["id"]) + "?format=full", token=self.token)
                labels = set(raw.get("labelIds", []))
                if "UNREAD" not in labels or labels & {"SPAM", "TRASH"}:
                    continue
                headers = {row["name"].lower(): row["value"] for row in raw.get("payload", {}).get("headers", [])}
                content, is_html = _gmail_body(raw.get("payload", {}))
                summary = summarize(content or raw.get("snippet", ""), is_html=is_html if content else False)
                thread = raw.get("threadId", "")
                link = f"https://mail.google.com/mail/u/{_q(self.account.email)}/#all/{thread}" if thread else None
                result.append(Message(self.account.id, self.account.email, "gmail", raw["id"],
                                      _decode_header(headers.get("from", tr("sender_unknown"))),
                                      _decode_header(headers.get("subject", tr("subject_missing"))), summary, link,
                                      raw.get("internalDate", "")))
            page = listing.get("nextPageToken")
            if not page:
                return result

    def action(self, message: Message, action: str) -> None:
        base = self.base + "/messages/" + _q(message.id)
        if action == "archive":
            request_json(base + "/modify", token=self.token, method="POST", data={"removeLabelIds": ["INBOX"]})
        elif action == "delete":
            request_json(base + "/trash", token=self.token, method="POST", data={})
        elif action == "spam":
            request_json(base + "/modify", token=self.token, method="POST", data={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]})
        elif action == "spam_delete":
            self.action(message, "spam")
            try:
                self.action(message, "delete")
            except RemoteError as exc:
                raise PartialActionError(tr("gmail_partial", error=exc)) from None
        else:
            raise ValueError(action)


class Microsoft:
    base = "https://graph.microsoft.com/v1.0"

    def __init__(self, account: Account, token: str):
        self.account, self.token = account, token

    def _get(self, path: str) -> dict:
        return request_json(path if path.startswith("https://") else self.base + path, token=self.token,
                            headers={"Prefer": 'outlook.body-content-type="text"'})

    def identity(self) -> str:
        profile = self._get("/me?$select=mail,userPrincipalName")
        return profile.get("mail") or profile["userPrincipalName"]

    def unread(self) -> list[Message]:
        fields = "id,from,subject,body,bodyPreview,isRead,parentFolderId,webLink,receivedDateTime"
        params = urllib.parse.urlencode({"$select": fields, "$filter": "isRead eq false", "$top": "100"})
        url = self.base + "/me/mailFolders/inbox/messages?" + params
        result = []
        while url:
            page = self._get(url)
            for row in page.get("value", []):
                if row.get("isRead"):
                    continue
                sender = (row.get("from") or {}).get("emailAddress") or {}
                body = row.get("body") or {}
                summary = summarize(body.get("content") or row.get("bodyPreview", ""),
                                    is_html=body.get("contentType", "").lower() == "html")
                result.append(Message(self.account.id, self.account.email, self.account.provider, row["id"],
                                      f"{sender.get('name', '')} <{sender.get('address', '')}>".strip(),
                                      row.get("subject") or tr("subject_missing"), summary, row.get("webLink"),
                                      row.get("receivedDateTime", "")))
            url = page.get("@odata.nextLink")
            if url and not url.startswith(self.base + "/"):
                raise ValueError(tr("graph_pagination"))
        return result

    def action(self, message: Message, action: str) -> None:
        if action == "spam_delete":
            moved = self._move(message.id, "junkemail")
            try:
                self._move(moved["id"], "deleteditems")
            except RemoteError as exc:
                raise PartialActionError(tr("microsoft_partial", error=exc)) from None
            return
        destination = {"archive": "archive", "delete": "deleteditems", "spam": "junkemail"}.get(action)
        if not destination:
            raise ValueError(action)
        self._move(message.id, destination)

    def _move(self, message_id: str, folder: str) -> dict:
        return request_json(self.base + "/me/messages/" + _q(message_id) + "/move", token=self.token,
                            method="POST", data={"destinationId": folder})


def provider_for(account: Account, token: str):
    return Gmail(account, token) if account.provider == "gmail" else Microsoft(account, token)
