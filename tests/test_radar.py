import unittest
from datetime import datetime, timedelta, timezone
from scripts.radar import evaluate

NOW = datetime(2026, 10, 31, tzinfo=timezone.utc)


def repo(**overrides):
    r = {
        "name": "task-automation", "full_name": "someone/task-automation",
        "html_url": "https://github.com/someone/task-automation",
        "description": "Workflow automation and webhook integration for teams",
        "topics": ["automation"], "fork": False, "archived": False,
        "disabled": False, "stargazers_count": 500,
        "created_at": (NOW - timedelta(days=5)).isoformat(),
        "updated_at": NOW.isoformat(), "language": "TypeScript",
        "license": {"spdx_id": "MIT"}
    }
    r.update(overrides)
    return r


class RadarTests(unittest.TestCase):
    def test_genuine_candidate(self):
        c = evaluate(repo(), {}, NOW)
        self.assertEqual(c["category"], "Automation")
        self.assertIsNone(c["delta"])
        self.assertEqual(c["license"], "MIT")

    def test_star_delta_is_from_stored_snapshot(self):
        c = evaluate(repo(), {"someone/task-automation": 425}, NOW)
        self.assertEqual(c["delta"], 75)

    def test_fork_and_archived_rejected(self):
        self.assertIsNone(evaluate(repo(fork=True), {}, NOW))
        self.assertIsNone(evaluate(repo(archived=True), {}, NOW))

    def test_bad_urls_rejected(self):
        self.assertIsNone(evaluate(repo(html_url="https://evil.test/hack"), {}, NOW))

    def test_suspicious_repo_rejected(self):
        self.assertIsNone(evaluate(repo(description="Phishing kit credential stealer"), {}, NOW))

    def test_no_license_not_marked_ready(self):
        c = evaluate(repo(license=None), {}, NOW)
        self.assertEqual(c["action"], "CHECK_LICENSE")
        self.assertEqual(c["license"], "UNKNOWN")

    def test_old_repo_not_confused_with_new_hot(self):
        self.assertIsNone(evaluate(repo(created_at=(NOW - timedelta(days=100)).isoformat()), {}, NOW))


if __name__ == "__main__":
    unittest.main()
