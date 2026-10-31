import unittest
from scripts.social_queue import choose

def item(name="a/tool", license="MIT", score=70):
    return {"name": name, "url": "https://github.com/" + name, "license": license,
            "score": score, "description": "Test repo"}

class SocialQueueTests(unittest.TestCase):
    def test_new_permissive_candidate(self):
        self.assertEqual(len(choose({"watchlist": [item()]}, {}, 3)), 1)

    def test_no_duplicates(self):
        self.assertEqual(choose({"high_signal": [item()], "watchlist": [item()]},
                                {"social_seen": ["a/tool"]}), [])

    def test_licence_gate(self):
        self.assertEqual(choose({"watchlist": [item(license="AGPL-3.0")]}, {}), [])

    def test_url_gate(self):
        bad = item()
        bad["url"] = "https://not-github.test/a/tool"
        self.assertEqual(choose({"watchlist": [bad]}, {}), [])

    def test_limit(self):
        data = {"watchlist": [item(str(i) + "/tool") for i in range(6)]}
        self.assertEqual(len(choose(data, {}, 2)), 2)

if __name__ == "__main__":
    unittest.main()
