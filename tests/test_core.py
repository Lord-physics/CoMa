import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coma.classifier import SpamClassifier
from coma.models import Account, Message
from coma.http import RemoteError
from coma.providers import Gmail, Microsoft, PartialActionError
from coma.secrets import protect, unprotect
from coma.service import MailService
from coma.storage import AccountStore
from coma.text import plain_text, summarize


class TextTests(unittest.TestCase):
    def test_html_and_quoted_history_are_excluded(self):
        content = "<p>La reunión será el jueves a las diez.</p><script>alert('x')</script><p>Trae el informe.</p><div class='gmail_quote'><p>texto antiguo</p></div>"
        result = plain_text(content, True)
        self.assertIn("reunión", result)
        self.assertIn("informe", result)
        self.assertNotIn("alert", result)
        self.assertNotIn("antiguo", result)
        self.assertNotIn("antiguo", summarize(content, is_html=True))


class StorageTests(unittest.TestCase):
    def test_dpapi_and_account_file_do_not_contain_token(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "accounts.json"
            store = AccountStore(path)
            account = Account("one", "gmail", "a@example.com", "client", "common", "secret", "refresh-secret")
            store.save([account])
            self.assertNotIn("refresh-secret", path.read_text())
            self.assertNotIn('"secret"', path.read_text())
            self.assertEqual(store.list(), [account])
            self.assertEqual(unprotect(protect("áéí")), "áéí")


class ClassifierTests(unittest.TestCase):
    def test_learning_persists_and_correction_excludes_false_positive(self):
        with tempfile.TemporaryDirectory() as directory:
            classifier = SpamClassifier(Path(directory) / "learning.json")
            classifier.learn("spam", "ventas@promo.test", "Oferta premio dinero", "Gana dinero", spam=True)
            classifier.learn("ham", "colega@trabajo.test", "Informe semanal", "Reunión mañana", spam=False)
            self.assertGreater(classifier.probability("ventas@promo.test", "Oferta premio dinero", "Gana dinero"), 0.5)
            message = Message("a", "a@example.com", "gmail", "x", "ventas@promo.test", "Oferta premio dinero", "Gana dinero", None)
            service = MailService(classifier=classifier)
            service.not_spam(message)
            reloaded = SpamClassifier(Path(directory) / "learning.json")
            self.assertEqual(reloaded.examples[message.key]["spam"], False)
            self.assertEqual(MailService(classifier=reloaded).possible_spam([message]), [])
            raw = json.loads((Path(directory) / "learning.json").read_text())
            self.assertNotIn("premio", str(raw))


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.account = Account("a", "gmail", "a@example.com", "id", refresh_token="token")
        self.message = Message("a", "a@example.com", "gmail", "m/1", "s", "t", "u", None)

    @patch("coma.providers.request_json")
    def test_gmail_unread_fetch_does_not_mark_read(self, request):
        request.side_effect = [
            {"messages": [{"id": "one"}]},
            {"id": "one", "threadId": "thread", "labelIds": ["UNREAD", "INBOX"],
             "payload": {"headers": [{"name": "Subject", "value": "Hola"}, {"name": "From", "value": "Ana"}],
                         "mimeType": "text/plain", "body": {"data": "SG9sYSBlc3RvIGVzIHVuIG1lbnNhamUu"}}},
        ]
        rows = Gmail(self.account, "access").unread()
        self.assertEqual(rows[0].subject, "Hola")
        self.assertIn("Hola", rows[0].summary)
        self.assertTrue(all(call.kwargs.get("method", "GET") == "GET" for call in request.call_args_list))

    @patch("coma.providers.request_json")
    def test_microsoft_spam_and_delete_uses_new_message_id(self, request):
        request.side_effect = [{"id": "moved-id"}, {"id": "deleted-id"}]
        Microsoft(self.account, "access").action(self.message, "spam_delete")
        self.assertIn("m%2F1/move", request.call_args_list[0].args[0])
        self.assertIn("moved-id/move", request.call_args_list[1].args[0])
        self.assertEqual(request.call_args_list[0].kwargs["data"], {"destinationId": "junkemail"})
        self.assertEqual(request.call_args_list[1].kwargs["data"], {"destinationId": "deleteditems"})

    @patch("coma.providers.request_json")
    def test_microsoft_unread_is_from_inbox_without_mutation(self, request):
        request.return_value = {"value": [
            {"id": "unread", "isRead": False, "from": {"emailAddress": {"name": "Ana", "address": "ana@test.es"}},
             "subject": "Aviso", "body": {"contentType": "text", "content": "Tienes una reunión mañana."}, "webLink": "https://outlook.test/message"},
            {"id": "read", "isRead": True, "subject": "Leído"},
        ]}
        rows = Microsoft(self.account, "access").unread()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].id, "unread")
        self.assertIn("/mailFolders/inbox/messages?", request.call_args.args[0])
        self.assertEqual(request.call_args.kwargs.get("method", "GET"), "GET")

    @patch("coma.providers.request_json")
    def test_partial_spam_delete_reports_where_message_was_left(self, request):
        request.side_effect = [{"id": "in-junk"}, RemoteError("El servicio devolvió HTTP 503.")]
        with self.assertRaisesRegex(PartialActionError, "Movido a spam, pero no a papelera"):
            Microsoft(self.account, "access").action(self.message, "spam_delete")


class ServiceTests(unittest.TestCase):
    def test_one_failing_account_does_not_hide_other_accounts(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AccountStore(Path(directory) / "accounts.json")
            store.save([Account("bad", "gmail", "bad@example.com", "id", refresh_token="x"),
                        Account("good", "outlook", "good@example.com", "id", refresh_token="y")])
            classifier = SpamClassifier(Path(directory) / "learning.json")
            message = Message("good", "good@example.com", "outlook", "m", "Ana", "Aviso", "Mañana", None)
            with patch.object(MailService, "_access") as access:
                access.side_effect = [RuntimeError("sin acceso"), type("Provider", (), {"unread": lambda self: [message]})()]
                messages, errors = MailService(store, classifier).sync()
            self.assertEqual(messages, [message])
            self.assertEqual(len(errors), 1)
            self.assertIn("bad@example.com", errors[0])

    def test_partial_spam_delete_still_records_explicit_spam_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AccountStore(Path(directory) / "accounts.json")
            store.save([Account("a", "outlook", "a@example.com", "id", refresh_token="token")])
            classifier = SpamClassifier(Path(directory) / "learning.json")
            service = MailService(store, classifier)
            message = Message("a", "a@example.com", "outlook", "m", "Ofertas", "Premio", "Dinero", None)
            provider = type("Provider", (), {"action": lambda self, *_: (_ for _ in ()).throw(PartialActionError("en spam"))})()
            with patch.object(service, "_access", return_value=provider):
                with self.assertRaises(PartialActionError):
                    service.action(message, "spam_delete")
            self.assertTrue(classifier.examples[message.key]["spam"])


if __name__ == "__main__":
    unittest.main()
