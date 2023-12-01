from abc import ABC, abstractmethod
from regex import finite_automata as fa

from more_itertools import peekable
from copy import deepcopy


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


class Literal(AST):
    """Matches a character literal
    """

    def __init__(self, c):
        self.c = c

    def item(self):
        return self.c

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

    def __init__(self, regex, name=None):
        super().__init__(regex)
        self.group_name = None

    def item(self):
        return "()"

    def get_group_name(self):
        return self.group_name

    def accept(self, visitor):
        return visitor.visit_group(self)


class Range(AST):
    """Matches a range of character literals, by ascii value
    """

    def __init__(self, c1, c2):
        self.c1 = c1
        self.c2 = c2

    def item(self):
        return self.c1 + "-" + self.c2
    
    def get_left(self):
        return self.c1

    def get_right(self):
        return self.c2

    def accept(self, visitor):
        return visitor.visit_range(self)


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
    def visit_literal(self, node: Literal):
        pass

    @abstractmethod
    def visit_sequence(self, node: Sequence):
        pass

    @abstractmethod
    def visit_epsilon(self, node: Epsilon):
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

    @abstractmethod
    def visit_range(self, node: Range):
        pass


class NFABuilder(Visitor):
    def __init__(self):
        self.nfa = fa.NFA()
        self.start = None
        self.end = None
        self.cur_group = 1

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
        if node.get_group_name() is not None:
            group = node.get_group_name()
        else:
            group = self.cur_group
            self.cur_group += 1

        l1, l2 = node.get_child().accept(self)

        self.nfa.add_transition(s1, l1, fa.EpsilonMatcher(), start_group=group)
        self.nfa.add_transition(l2, s2, fa.EpsilonMatcher(), end_group=group)

        self.start = s1
        self.end = s2
        return (s1, s2)
    
    def visit_range(self, node):
        s1 = self.nfa.add_state()
        s2 = self.nfa.add_state()
        self.nfa.add_transition(s1, s2, fa.RangeMatcher(node.get_left(), node.get_right()))
        self.start = s1
        self.end = s2
        return (s1, s2)


class ParserError(RuntimeError):
    pass


GLOBAL_METACHARS = set(r"\^$[.|()?*+{")
SET_METACHARS = set(r"\^-[]")
SPECIALCHARS = set("sSdDwW")
QUANTIFIERS = set("*+?")
ANCHORS = set("^$")
SPECIALANCHORS = set("bB")
INVALID_START_CHAR = set(")|")
IT = None


def _lex(regex):
    # for now, each character in the symbol represents their own lexeme
    return list(regex)


def parse(regex):
    global IT
    IT = peekable(_lex(regex))
    ast = _parse_expr()
    assert _eof()  # must match entire regex
    return ast


def _advance():
    global IT
    return next(IT)


def _peek():
    return IT.peek("")


def _peek_ahead(i):
    try:
        return "".join(IT[:i])
    except IndexError:
        return ""


def _eof():
    return _peek() == ""


def _expect(*args):
    if _peek() not in set(args):
        raise ParserError(f"Expected one of {''.join(list(args))}, received {_peek()}")


def _consume(c):
    _expect(c)
    return _advance()


def _parse_expr():
    lhs = _parse_term()

    if _peek() == "|":
        _advance()
        return Or(lhs, _parse_expr())

    return lhs


def _parse_term():
    lhs = _parse_atom()

    if _eof() or _peek() in INVALID_START_CHAR:
        return lhs

    return Sequence(lhs, _parse_term())


def _parse_atom():
    c = _peek()

    if c == "(":
        atom = _parse_group()
    elif c == ".":
        _advance()
        atom = Dot()
    elif c == "[":
        atom = _parse_set()
    elif c in ANCHORS:
        return _parse_anchor()
    elif c == "|":
        return Epsilon()
    else:
        atom = _parse_literal(GLOBAL_METACHARS)

    return _parse_quantifier(atom)


def _parse_anchor():
    c = _advance()

    if c == "$":
        return EndAnchor()
    elif c == "^":
        return StartAnchor()


def _parse_set():
    _consume("[")
    regex_set = _parse_set_items()
    _consume("]")
    return regex_set


def _parse_set_literal():
    return _parse_literal(SET_METACHARS)


def _parse_regex_literal():
    return _parse_literal(GLOBAL_METACHARS)


def _parse_literal(metachars: set):
    if _peek() == "":
        return Epsilon()

    if _peek() == "\\":
        _advance()

        # still need to do octal numbers
        if _peek() not in metachars:
            raise ParserError(f"Meaningless escaped char {_peek()}")

    return Literal(_advance())


def _parse_set_items():
    lhs = _parse_set_literal()

    if _peek() == "-" and _peek_ahead(2) != "-]":
        try:
            global IT
            tmp = deepcopy(IT)
            _advance()
            lhs = Range(lhs.item(), _parse_set_literal().item())
        except ParserError:
            IT = tmp

    if _peek() == "]":
        return lhs
    else:
        return Or(lhs, _parse_set_items())


def _parse_group():
    _consume("(")
    group = Group(_parse_expr())
    _consume(")")
    return group


def _parse_quantifier(atom):
    if _peek() not in QUANTIFIERS:
        return atom

    meta = _advance()
    if meta == "*":
        return KleeneStar(atom)
    elif meta == "+":
        return KleenePlus(atom)
