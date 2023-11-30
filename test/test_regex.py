import unittest

from regex import Regex


class TestRegex(unittest.TestCase):
    def test_basic(self):
        r = Regex(r"aa")
        self.assertTrue(r.search("aa"))
        self.assertTrue(r.search("aabyeh"))

    def test_alternation(self):
        r = Regex(r"a|")

        # this regex should match any string
        self.assertTrue(r.search("a"))
        self.assertTrue(r.search(""))
        self.assertTrue(r.search("biujwk"))
    
    def test_kleene_star(self):
        r = Regex(r"a*")

        self.assertTrue(r.search(""))
        self.assertTrue(r.search("aaaa"))

        r = Regex(r"ab*|cd")
        self.assertFalse(r.search("c"))
        self.assertTrue(r.search("cd"))
        self.assertTrue(r.search("ab"))
        self.assertTrue(r.search("a"))

    def test_kleene_plus(self):
        r = Regex(r"a+")

        self.assertFalse(r.search(""))
        self.assertTrue(r.search("a"))

    def test_group(self):
        r = Regex(r"a(b)*")

        self.assertTrue(r.search("a"))
        self.assertTrue(r.search("ab"))

        r = Regex(r"a(b|c)+")

        self.assertTrue(r.search("abc"))
        self.assertTrue(r.search("ac"))
        self.assertFalse(r.search("ad"))

    def test_set(self):
        r = Regex(r"ab[abc]")
        self.assertTrue(r.search("aba"))
        self.assertTrue(r.search("abb"))
        self.assertTrue(r.search("abc"))

        r = Regex(r"[a-z]")
        self.assertTrue(r.search("a"))
        self.assertTrue(r.search("w"))

        r = Regex(r"(a+|b*c)[]-][a-z]")
        self.assertTrue(r.search("a-w"))
        self.assertTrue(r.search("c]a"))
