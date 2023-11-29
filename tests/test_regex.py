import unittest

from regex import Regex


class TestRegex(unittest.TestCase):
    def test_basic(self):
        r = Regex(r"aa")
        self.assertTrue(r.search("aa"))
        self.assertTrue(r.search("aabyeh"))

    def test_alternation_empty(self):
        r = Regex(r"a|")

        # this regex should match any string
        self.assertTrue(r.search("a"))
        self.assertTrue(r.search(""))
        self.assertTrue(r.search("biujwk"))

