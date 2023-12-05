import unittest

from regex import Regex


class TestRegex(unittest.TestCase):
    def test_basic(self):
        r = Regex(r"aa")
        self.assertEqual(r.match("aa").group(), "aa")
        self.assertEqual(r.match("aabyeh").group(), "aa")

    def test_alternation(self):
        r = Regex(r"a|")
        self.assertEqual(r.match("a").group(), "")
        self.assertEqual(r.match("").group(), "")
        self.assertEqual(r.match("biujwk").group(), "")

        r = Regex(r"abcd|efgh")
        self.assertEqual(r.match("abcd").group(), "abcd")
        self.assertListEqual(r.findall("abcdefgh"), ["abcd", "efgh"])

    def test_kleene_star(self):
        r = Regex(r"a*")
        self.assertEqual(r.match("b").group(), "")
        self.assertEqual(r.search("bcdaaaa").group(), "")
        self.assertEqual(len(list(r.finditer("bcdaaaa"))), 5)

        r = Regex(r"ab*|cd")
        self.assertIsNone(r.match("c"))
        self.assertEqual(r.match("cd").group(), "cd")
        self.assertEqual(r.match("ab").group(), "ab")
        self.assertEqual(r.match("a").group(), "a")

        r = Regex(r"(|a)*")
        self.assertEqual(r.match("aaaab").group(), "aaaa")

    def test_kleene_plus(self):
        r = Regex(r"a+")
        self.assertIsNone(r.match(""))
        self.assertEqual(r.match("aa").group(), "aa")

    def test_group(self):
        r = Regex(r"a(b)*")
        self.assertEqual(r.match("a").group(), "a")
        self.assertEqual(r.match("ab").group(), "ab")

        r = Regex(r"a(b|c)+\1")
        self.assertEqual(r.match("abb").group(), "abb")
        self.assertEqual(r.match("abcc").group(), "abcc")
        self.assertIsNone(r.match("abcb"))
        self.assertIsNone(r.match("ad"))

        r = Regex(r"(([A-Za-z_]+)[0-9]+) \2\1")
        self.assertEqual(r.search("123abc123 abcabc123").group(), "abc123 abcabc123")
        self.assertTupleEqual(r.search("123abc123 abcabc123").span(), (3, 19))

    def test_set(self):
        r = Regex(r"ab[abc]")
        self.assertEqual(r.match("aba").group(), "aba")
        self.assertEqual(r.match("abb").group(), "abb")
        self.assertEqual(r.match("abc").group(), "abc")

        r = Regex(r"[a-z]")
        self.assertEqual(r.match("a").group(), "a")
        self.assertEqual(r.match("w").group(), "w")

        r = Regex(r"(a+|b*c)[]-][a-z]+")
        self.assertEqual(r.match("a-w").group(), "a-w")
        self.assertEqual(r.match("c]aby{z").group(), "c]aby")
