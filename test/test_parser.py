import unittest

from regex.parser import RegexParser

class TestParser(unittest.TestCase):
    def test_basic(self):
        RegexParser.parse(r"aaaaa") # this shouldn't crash
