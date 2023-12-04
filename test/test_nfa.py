import unittest

from regex import finite_automata as fa


class TestNFA(unittest.TestCase):
    def test_basic(self):
        nfa = fa.NFA()
        s1 = nfa.add_state()
        s2 = nfa.add_state()
        nfa.set_start_state(s1)
        nfa.add_end_state(s2)
        nfa.add_transition(s1, s2, fa.CharacterMatcher("a"))

        self.assertIsNotNone(nfa.match("a"))
        self.assertIsNotNone(nfa.match("aa"))

        nfa.add_transition(s2, s2, fa.CharacterMatcher("b"))
        
        self.assertIsNotNone(nfa.match("ab"))
        self.assertIsNotNone(nfa.match("aa"))
