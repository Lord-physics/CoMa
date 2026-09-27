import tempfile
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

from coma.account_setup import detect_provider, valid_email
from coma.classifier import SpamClassifier
from coma.oauth import _microsoft_browser_authorize
from coma.oauth_clients import OAuthClient, bundled_client
from coma.service import MailService
from coma.storage import AccountStore


class AccountSetupTests(unittest.TestCase):
    def test_detects_known_domains_without_guessing_custom_domains(self):
        self.assertEqual(detect_provider("ana@GMAIL.com"), "gmail")
        self.assertEqual(detect_provider("ana@hotmail.es"), "outlook")
        self.assertEqual(detect_provider("ana@educa.jcyl.es"), "educacyl")
        self.assertIsNone(detect_provider("ana@centro.example"))
        self.assertFalse(valid_email("ana@@gmail.com"))

    @patch("coma.service.provider_for")
    @patch("coma.service.authorize")
    def test_sign_in_hint_goes_to_official_oauth_flow(self, authorize, provider_for):
        authorize.return_value = {"access_token": "access", "refresh_token": "refresh"}
        provider_for.return_value.identity.return_value = "ana@gmail.com"
        def notify(_):
            pass
        with tempfile.TemporaryDirectory() as directory:
            service = MailService(AccountStore(Path(directory) / "accounts.json"),
                                  SpamClassifier(Path(directory) / "learning.json"))
            account = service.add_account("gmail", "client", "common", "", notify,
                                          login_hint="ana@gmail.com")
            self.assertEqual(account.email, "ana@gmail.com")
            self.assertEqual(service.accounts.list(), [account])
        authorize.assert_called_once_with("gmail", "client", "common", "", notify,
                                          "ana@gmail.com", browser_sign_in=False)

    def test_publisher_registration_is_loaded_for_email_only_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oauth-clients.json"
            self.assertIsNone(bundled_client("gmail", path))
            path.write_text(json.dumps({"gmail": {"client_id": "google-id", "client_secret": "public-secret"},
                                        "microsoft": {"client_id": "ms-id", "tenant": "common"}}), encoding="utf-8")
            self.assertEqual(bundled_client("gmail", path), OAuthClient("google-id", "common", "public-secret"))
            self.assertEqual(bundled_client("outlook", path), OAuthClient("ms-id", "common"))
            self.assertEqual(bundled_client("educacyl", path), OAuthClient("ms-id", "organizations"))

    @patch("coma.oauth.post_form")
    @patch("coma.oauth.webbrowser.open")
    def test_microsoft_browser_flow_uses_local_callback_and_pkce(self, open_browser, post_form):
        post_form.return_value = {"access_token": "access", "refresh_token": "refresh"}
        callbacks = []

        def sign_in(url):
            query = parse_qs(urlsplit(url).query)
            self.assertEqual(query["login_hint"], ["ana@outlook.com"])
            self.assertEqual(query["code_challenge_method"], ["S256"])
            callback = query["redirect_uri"][0] + "?" + urlencode({"code": "mock-code", "state": query["state"][0]})
            worker = threading.Thread(target=lambda: urlopen(callback, timeout=5).read(), daemon=True)
            callbacks.append(worker)
            worker.start()
            return True

        open_browser.side_effect = sign_in
        tokens = _microsoft_browser_authorize("ms-id", "common", lambda _: None, "ana@outlook.com")
        callbacks[0].join(timeout=5)
        self.assertEqual(tokens["refresh_token"], "refresh")
        self.assertEqual(post_form.call_args.args[1]["code"], "mock-code")
        self.assertTrue(post_form.call_args.args[1]["code_verifier"])


if __name__ == "__main__":
    unittest.main()
