from abc import ABC, abstractmethod
from regex import finite_automata as fa

import itertools
from more_itertools import peekable


class AST(ABC):
    """ABC for Regex AST Nodes
    """

    @abstractmethod
    def item(self):
        return ""

    @abstractmethod
    def accept(self, visitor: "Visitor"):
        return ""


class BinaryOperator(AST):
    """ABC for nodes with 2 operands
    """

    def __init__(self, r1: AST, r2: AST):
        self.left = r1
        self.right = r2

    def get_left(self):
        return self.left

    def get_right(self):
        return self.right


class UnaryOperator(AST):
    """ABC for nodes with one operand
    """

    def __init__(self, regex: AST):
        self.child = regex

    def get_child(self):
        return self.child


class ManyOperator(AST):
    """ABC for nodes with an arbitrary number of operands
    """

    def __init__(self, *args):
        self.regexes = list(args)


class Epsilon(AST):
    """Matches the empty string
    """

    def item(self):
        return "e"

    def accept(self, visitor: "Visitor"):
        return visitor.visit_epsilon(self)


class Literal(UnaryOperator):
    """Matches a character literal
    """

    def __init__(self, c):
        super().__init__(c)

    def item(self):
        return self.child

    def accept(self, visitor: "Visitor"):
        return visitor.visit_literal(self)


class MetaChar(UnaryOperator):
    """Matches a character with a special meaning
    """
    pass


class Sequence(BinaryOperator):
    """Matches a sequence of regex expressions


    Because every regex is a sequence of regexes,
    this is always the root node of any regex
    """

    def __init__(self, r1, r2, capture=False):
        super().__init__(r1, r2)
        self.capture = capture

    def item(self):
        return "->"

    def accept(self, visitor):
        return visitor.visit_sequence(self)


class Or(BinaryOperator):
    """Matches either of the two children regexes
    """

    def __init__(self, r1, r2):
        super().__init__(r1, r2)

    def item(self):
        return "|"

    def accept(self, visitor):
        return visitor.visit_or(self)


class KleeneStar(UnaryOperator):
    """Matches a Kleene Star Regex
    """

    def __init__(self, regex):
        super().__init__(regex)

    def item(self):
        return "*"

    def accept(self, visitor):
        return visitor.visit_kleene_star(self)


class KleenePlus(UnaryOperator):
    """Matches a Kleene Plus regex
    """

    def __init__(self, regex):
        super().__init__(regex)

    def item(self):
        return "+"

    def accept(self, visitor):
        return visitor.visit_kleene_plus(self)

class Group(UnaryOperator):
    """Matches a singular expression that may or may not be captured
    """

    def __init__(self, regex):
        super().__init__(regex)

    def item(self):
        return "()"

    def accept(self, visitor):
        return visitor.visit_group(self)


class Range(BinaryOperator):
    """Matches a range of character literals, by ascii value
    """

    def __init__(self, r1, r2):
        super().__init__(r1, r2)


class Dot(AST):
    """Matches anything except a newline
    """

    def __init__(self, flags=""):
        self.flags = ""

    def item(self):
        return "."

    def accept(self, visitor):
        return visitor.visit_dot(self)


class StartAnchor(AST):
    """Matches the start of the string
    """

    def item(self):
        return "^"

    def accept(self, visitor):
        return visitor.visit_start_anchor(self)


class EndAnchor(AST):
    """Matches the end of the string
    """

    def item(self):
        return "$"

    def accept(self, visitor):
        return visitor.visit_end_anchor(self)


class Visitor(ABC):
    @abstractmethod
    def visit_literal(self, node):
        pass

    @abstractmethod
    def visit_sequence(self, node):
        pass

    @abstractmethod
    def visit_epsilon(self, node):
        pass

    @abstractmethod
    def visit_or(self, node: Or):
        pass

    @abstractmethod
    def visit_kleene_star(self, node: KleeneStar):
        pass

    @abstractmethod
    def visit_kleene_plus(self, node: KleenePlus):
        pass

    @abstractmethod
    def visit_group(self, node: Group):
        pass


class NFABuilder(Visitor):
    def __init__(self):
        self.nfa = fa.NFA()
        self.start = None
        self.end = None

    def get_nfa(self):
        self.nfa.set_start_state(self.start)
        self.nfa.add_end_state(self.end)
        return self.nfa

    def visit_literal(self, node: Literal):
        s1 = self.nfa.add_state()
        s2 = self.nfa.add_state()
        self.nfa.add_transition(s1, s2, fa.CharacterMatcher(node.item()))

        self.start = s1
        self.end = s2
        return (s1, s2)

    def visit_sequence(self, node: Sequence):
        l1, l2 = node.get_left().accept(self)
        r1, r2 = node.get_right().accept(self)

        self.nfa.add_transition(l2, r1, fa.EpsilonMatcher())

        self.start = l1
        self.end = r2
        return (l1, r2)

    def visit_epsilon(self, node: Epsilon):
        s1 = self.nfa.add_state()

        self.start = s1
        self.end = s1
        return (s1, s1)

    def visit_or(self, node):
        s1 = self.nfa.add_state()
        s2 = self.nfa.add_state()

        l1, l2 = node.get_left().accept(self)
        r1, r2 = node.get_right().accept(self)

        self.nfa.add_transition(s1, l1, fa.EpsilonMatcher())
        self.nfa.add_transition(s1, r1, fa.EpsilonMatcher())
        self.nfa.add_transition(l2, s2, fa.EpsilonMatcher())
        self.nfa.add_transition(r2, s2, fa.EpsilonMatcher())

        self.start = s1
        self.end = s2
        return (s1, s2)

    def visit_kleene_star(self, node):
        s1 = self.nfa.add_state()
        s2 = self.nfa.add_state()

        l1, l2 = node.get_child().accept(self)

        # this is currently a non-greedy match
        self.nfa.add_transition(s1, s2, fa.EpsilonMatcher())
        self.nfa.add_transition(s1, l1, fa.EpsilonMatcher())
        self.nfa.add_transition(l2, l1, fa.EpsilonMatcher())
        self.nfa.add_transition(l2, s2, fa.EpsilonMatcher())

        self.start = s1
        self.end = s2
        return (s1, s2)

    def visit_kleene_plus(self, node):
        s1 = self.nfa.add_state()
        s2 = self.nfa.add_state()

        l1, l2 = node.get_child().accept(self)

        self.nfa.add_transition(s1, l1, fa.EpsilonMatcher())
        self.nfa.add_transition(l2, l1, fa.EpsilonMatcher())
        self.nfa.add_transition(l2, s2, fa.EpsilonMatcher())

        self.start = s1
        self.end = s2
        return (s1, s2)

    def visit_group(self, node):
        s1 = self.nfa.add_state()
        s2 = self.nfa.add_state()

        # TODO: add memory interface for NFA

        l1, l2 = node.get_child().accept(self)

        self.nfa.add_transition(s1, l1, fa.EpsilonMatcher())
        self.nfa.add_transition(l2, s2, fa.EpsilonMatcher())

        self.start = s1
        self.end = s2
        return (s1, s2)


class ParserError(RuntimeError):
    pass


class RegexParser:
    METACHARS = set("[()^$")
    SPECIALCHARS = set("sSdDwW")
    QUANTIFIERS = set("*+?")
    ANCHORS = set("^$")
    SPECIALANCHORS = set("bB")
    INVALID_START_CHAR = set(")|")

    @staticmethod
    def _lex(regex):
        # for now, each character in the symbol represents their own lexeme
        return list(regex)

    @staticmethod
    def parse(regex):
        it = peekable(RegexParser._lex(regex))
        ast = RegexParser._parse_expr(it)
        assert RegexParser._eof(it)  # must match entire regex
        return ast

    @staticmethod
    def _advance(it):
        return next(it)

    @staticmethod
    def _peek(it):
        return it.peek("")

    @staticmethod
    def _peek_ahead(it, i):
        try:
            return it[:i]
        except IndexError:
            return ""

    @staticmethod
    def _eof(it):
        return RegexParser._peek(it) == ""

    @staticmethod
    def _expect(it, *args):
        if RegexParser._peek(it) not in set(args):
            raise ParserError(f"Expected one of {''.join(list(args))}, received {RegexParser._peek(it)}")

    @staticmethod
    def _consume(it, c):
        RegexParser._expect(it, c)
        return RegexParser._advance(it)

    @staticmethod
    def _parse_expr(it):
        lhs = RegexParser._parse_term(it)

        if RegexParser._peek(it) == "|":
            RegexParser._advance(it)
            return Or(lhs, RegexParser._parse_expr(it))

        return lhs

    @staticmethod
    def _parse_term(it):
        lhs = RegexParser._parse_atom(it)

        if RegexParser._eof(it) or RegexParser._peek(it) in RegexParser.INVALID_START_CHAR:
            return lhs

        return Sequence(lhs, RegexParser._parse_term(it))

    @staticmethod
    def _parse_atom(it):
        c = RegexParser._peek(it)

        if c == "(":
            atom = RegexParser._parse_group(it)
        elif c == ".":
            RegexParser._advance(it)
            atom = Dot()
        elif c == "[":
            atom = RegexParser._parse_set(it)
        elif c in RegexParser.ANCHORS:
            return RegexParser._parse_anchor(it)
        elif c == "" or c == "|":
            return Epsilon()
        else:
            atom = Literal(RegexParser._advance(it))

        return RegexParser._parse_quantifier(it, atom)
    
    @staticmethod
    def _parse_anchor(it):
        c = RegexParser._advance(it)

        if c == "$":
            return EndAnchor()
        elif c == "^":
            return StartAnchor()

    @staticmethod
    def _parse_set(it):
        RegexParser._consume(it, "[")
        RegexParser._consume(it, "]")

    @staticmethod
    def _parse_group(it):
        RegexParser._consume(it, "(")
        group = Group(RegexParser._parse_expr(it))
        RegexParser._consume(it, ")")
        return group

    @staticmethod
    def _parse_quantifier(it, atom):
        if RegexParser._peek(it) not in RegexParser.QUANTIFIERS:
            return atom

        meta = RegexParser._advance(it)
        if meta == "*":
            return KleeneStar(atom)
        elif meta == "+":
            return KleenePlus(atom)
