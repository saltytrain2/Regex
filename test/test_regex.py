import unittest

from regex import Regex


class TestRegex(unittest.TestCase):
    def test_basic(self):
        r = Regex(r"aa")
        self.assertEqual(r.search("aa").group(0), "aa")
        self.assertEqual(r.search("aabyeh").group(0), "aa")

    def test_alternation(self):
        r = Regex(r"a|")

        # this regex should match any string
        self.assertEqual(r.search("a").group(0), "")
        self.assertEqual(r.search("").group(0), "")
        self.assertEqual(r.search("biujwk").group(0), "")
    
    def test_kleene_star(self):
        r = Regex(r"a*")
        
        self.assertEqual(r.search("").group(0), "")
        self.assertEqual(r.search("aaaa").group(0), "aaaa")

        r = Regex(r"ab*|cd")
        self.assertIsNone(r.search("c"))
        self.assertEqual(r.search("cd").group(0), "cd")
        self.assertEqual(r.search("ab").group(0), "ab")
        self.assertEqual(r.search("a").group(0), "a")

    def test_kleene_plus(self):
        r = Regex(r"a+")

        self.assertIsNone(r.search(""))
        self.assertEqual(r.search("aa").group(0), "aa")

    def test_group(self):
        r = Regex(r"a(b)*")
        
        self.assertEqual(r.search("a").group(0), "a")
        self.assertEqual(r.search("ab").group(0), "ab")

        r = Regex(r"a(b|c)+")
        
        self.assertEqual(r.search("abc").group(0), "abc")
        self.assertEqual(r.search("ac").group(0), "ac")
        self.assertIsNone(r.search("ad"))

    def test_set(self):
        r = Regex(r"ab[abc]")
        self.assertEqual(r.search("aba").group(0), "aba")
        self.assertEqual(r.search("abb").group(0), "abb")
        self.assertEqual(r.search("abc").group(0), "abc")

        r = Regex(r"[a-z]")
        self.assertEqual(r.search("a").group(0), "a")
        self.assertEqual(r.search("w").group(0), "w")

        r = Regex(r"(a+|b*c)[]-][a-z]+")
        self.assertEqual(r.search("a-w").group(0), "a-w")
        self.assertEqual(r.search("c]aby{z").group(0), "c]aby")
