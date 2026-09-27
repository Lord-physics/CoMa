import json
import tempfile
import unittest
from pathlib import Path

from coma.i18n import HELP, STRINGS, help_links, language, load_language, set_language, tr


class LanguageTests(unittest.TestCase):
    def tearDown(self):
        load_language(Path(tempfile.gettempdir()) / "coma-no-such-preferences.json")

    def test_language_choice_persists_without_account_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferences.json"
            set_language("en", path)
            self.assertEqual(language(), "en")
            self.assertEqual(tr("add_account"), "Add account")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"language": "en"})
            set_language("es", path)
            self.assertEqual(load_language(path), "es")
            self.assertEqual(tr("add_account"), "Añadir cuenta")

    def test_help_covers_required_fields_in_both_languages(self):
        self.assertEqual(set(STRINGS["es"]), set(STRINGS["en"]))
        for selected in ("es", "en"):
            for provider in ("gmail", "outlook", "educacyl"):
                content = HELP[selected][provider]
                self.assertIn("Mail.ReadWrite" if provider != "gmail" else "gmail.modify", content)
                self.assertIn("client" if selected == "en" else "aplicación", content.lower())

    def test_each_provider_has_six_localized_official_links(self):
        with tempfile.TemporaryDirectory() as directory:
            preference = Path(directory) / "preferences.json"
            for selected in ("es", "en"):
                set_language(selected, preference)
                for provider in ("gmail", "outlook", "educacyl"):
                    links = help_links(provider)
                    self.assertEqual(len(links), 6)
                    self.assertTrue(all(label and url.startswith("https://") for label, url in links))
                    self.assertEqual([label[0] for label, _ in links], list("123456"))


if __name__ == "__main__":
    unittest.main()
