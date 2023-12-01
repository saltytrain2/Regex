import unittest

from regex.parser import parse

class TestParser(unittest.TestCase):
    def test_basic(self):
        parse(r"aaaaa") # this shouldn't crash
