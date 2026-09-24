"""Naive Bayes ligero. Aprende solo con decisiones explícitas."""

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from threading import RLock

from .storage import _write_json, data_dir


def tokens(sender: str, subject: str, summary: str) -> set[str]:
    text = f"{sender} {subject} {summary}".lower()
    words = set(re.findall(r"[\wáéíóúüñ]{3,}", text))
    return {hashlib.sha256(word.encode("utf-8")).hexdigest()[:20] for word in words}


class SpamClassifier:
    def __init__(self, path: Path | None = None):
        self.path = path or data_dir() / "learning.json"
        self.lock = RLock()
        self.examples: dict[str, dict] = {}
        if self.path.exists():
            self.examples = json.loads(self.path.read_text(encoding="utf-8"))

    def learn(self, key: str, sender: str, subject: str, summary: str, *, spam: bool) -> None:
        with self.lock:
            self.examples[key] = {"spam": spam, "tokens": sorted(tokens(sender, subject, summary))}
            _write_json(self.path, self.examples)

    def probability(self, sender: str, subject: str, summary: str) -> float:
        with self.lock:
            spam_examples = [row for row in self.examples.values() if row["spam"]]
            ham_examples = [row for row in self.examples.values() if not row["spam"]]
            if not spam_examples or not ham_examples:
                return 0.0
            spam_counts = Counter(word for row in spam_examples for word in row["tokens"])
            ham_counts = Counter(word for row in ham_examples for word in row["tokens"])
            log_odds = math.log((len(spam_examples) + 1) / (len(ham_examples) + 1))
            for word in tokens(sender, subject, summary):
                if word not in spam_counts and word not in ham_counts:
                    continue
                p_spam = (spam_counts[word] + 1) / (len(spam_examples) + 2)
                p_ham = (ham_counts[word] + 1) / (len(ham_examples) + 2)
                log_odds += math.log(p_spam / p_ham)
            return 1 / (1 + math.exp(-max(-40, min(40, log_odds))))

    def is_possible_spam(self, sender: str, subject: str, summary: str) -> bool:
        return self.probability(sender, subject, summary) >= 0.8
