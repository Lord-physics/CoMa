import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coma.account_setup import detect_provider, valid_email
from coma.classifier import SpamClassifier
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
        authorize.assert_called_once_with("gmail", "client", "common", "", notify, "ana@gmail.com")


if __name__ == "__main__":
    unittest.main()
