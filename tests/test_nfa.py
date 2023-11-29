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

        self.assertTrue(nfa.search("a"))
        self.assertTrue(nfa.search("aa"))

        nfa.add_transition(s2, s2, fa.CharacterMatcher("b"))
        
        self.assertTrue(nfa.search("ab"))
        self.assertTrue(nfa.search("aa"))
