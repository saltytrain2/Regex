import unittest

from regex import Regex


class TestRegex(unittest.TestCase):
    def test_basic(self):
        r = Regex(r"aa")
        self.assertEqual(r.match("aa").group(0), "aa")
        self.assertEqual(r.match("aabyeh").group(0), "aa")

    def test_alternation(self):
        r = Regex(r"a|")

        # this regex should match any string
        self.assertEqual(r.match("a").group(0), "")
        self.assertEqual(r.match("").group(0), "")
        self.assertEqual(r.match("biujwk").group(0), "")
    
    def test_kleene_star(self):
        r = Regex(r"a*")
        
        self.assertEqual(r.match("").group(0), "")
        self.assertEqual(r.match("aaaa").group(0), "aaaa")

        r = Regex(r"ab*|cd")
        self.assertIsNone(r.match("c"))
        self.assertEqual(r.match("cd").group(0), "cd")
        self.assertEqual(r.match("ab").group(0), "ab")
        self.assertEqual(r.match("a").group(0), "a")

        r = Regex(r"(|a)*")
        self.assertEqual(r.match("aaaab").group(0), "aaaa")

    def test_kleene_plus(self):
        r = Regex(r"a+")

        self.assertIsNone(r.match(""))
        self.assertEqual(r.match("aa").group(0), "aa")

    def test_group(self):
        r = Regex(r"a(b)*")
        
        self.assertEqual(r.match("a").group(0), "a")
        self.assertEqual(r.match("ab").group(0), "ab")

        r = Regex(r"a(b|c)+")
        
        self.assertEqual(r.match("abc").group(0), "abc")
        self.assertEqual(r.match("ac").group(0), "ac")
        self.assertIsNone(r.match("ad"))

    def test_set(self):
        r = Regex(r"ab[abc]")
        self.assertEqual(r.match("aba").group(0), "aba")
        self.assertEqual(r.match("abb").group(0), "abb")
        self.assertEqual(r.match("abc").group(0), "abc")

        r = Regex(r"[a-z]")
        self.assertEqual(r.match("a").group(0), "a")
        self.assertEqual(r.match("w").group(0), "w")

        r = Regex(r"(a+|b*c)[]-][a-z]+")
        self.assertEqual(r.match("a-w").group(0), "a-w")
        self.assertEqual(r.match("c]aby{z").group(0), "c]aby")
