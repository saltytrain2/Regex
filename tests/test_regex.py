import unittest

from regex import Regex


class TestRegex(unittest.TestCase):
    def test_basic(self):
        r = Regex(r"aa")
        self.assertTrue(r.search("aa"))
