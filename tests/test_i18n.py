import json
import tempfile
import unittest
from pathlib import Path

from coma.i18n import HELP, STRINGS, language, load_language, set_language, tr


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


if __name__ == "__main__":
    unittest.main()
