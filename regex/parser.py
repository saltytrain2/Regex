from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Union

from . import finite_automata as fa

import graphviz as gviz
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

    def accept(self, visitor: Visitor):
        return visitor.visit_epsilon(self)


class Literal(AST):
    """Matches a character literal
    """

    def __init__(self, c):
        self.c = c

    def item(self):
        return f"'{self.c}'"

    def accept(self, visitor: "Visitor"):
        return visitor.visit_literal(self)


class BackReference(AST):
    """Matches a Backreference
    """
    def __init__(self, reference: Union[int, str]):
        self.reference = reference

    def item(self):
        if isinstance(self.reference, int):
            return "\\\\" + str(self.reference)
        else:
            return self.reference
    
    def get_reference(self):
        return self.reference

    def accept(self, visitor: Visitor):
        return visitor.visit_backreference(self)


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

    def __init__(self, regex, num: Optional[int] = None, name: Optional[str] = None):
        super().__init__(regex)
        self.num = num
        self.group_name = name

    def item(self):
        group_ref = ""
        if self.num is not None:
            group_ref += str(self.num)

        if self.group_name is not None:
            group_ref += ", " + self.group_name

        return f"({group_ref})"
    
    def get_group_num(self):
        return self.num

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

    @abstractmethod
    def visit_backreference(self, node: BackReference):
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

        # this is currently a greedy match
        self.nfa.add_transition(s1, l1, fa.EpsilonMatcher())
        self.nfa.add_transition(s1, s2, fa.EpsilonMatcher())
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

        self.nfa.add_transition(s1, l1, fa.EpsilonMatcher(), start_group=node.get_group_num())
        self.nfa.add_transition(l2, s2, fa.EpsilonMatcher(), end_group=node.get_group_num())

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

    def visit_backreference(self, node):
        s1 = self.nfa.add_state()
        s2 = self.nfa.add_state()
        self.nfa.add_transition(s1, s2, fa.BackReferenceMatcher(node.get_reference()))
        self.start = s1
        self.end = s2
        return (s1, s2)
        pass


class ASTPrinter(Visitor):
    def __init__(self, **kwargs):
        self.graph = gviz.Digraph(**kwargs)
        self.node = 0

    def new_node(self, node: AST):
        tmp = str(self.node)
        self.node += 1
        self.graph.node(tmp, label=node.item())
        return tmp
    
    def link(self, parent: str, child: str):
        self.graph.edge(parent, child)

    def unary_node(self, node: UnaryOperator):
        new_node = self.new_node(node)
        self.link(new_node, node.get_child().accept(self))
        return new_node

    def binary_node(self, node: BinaryOperator):
        new_node = self.new_node(node)
        self.link(new_node, node.get_left().accept(self))
        self.link(new_node, node.get_right().accept(self))
        return new_node

    def visit_literal(self, node):
        return self.new_node(node)

    def visit_or(self, node):
        return self.binary_node(node)
    
    def visit_sequence(self, node):
        return self.binary_node(node)

    def visit_kleene_plus(self, node):
        return self.unary_node(node)

    def visit_kleene_star(self, node):
        return self.unary_node(node)

    def visit_range(self, node):
        return self.new_node(node)

    def visit_epsilon(self, node):
        return self.new_node(node)

    def visit_backreference(self, node):
        return self.new_node(node)

    def visit_group(self, node):
        return self.unary_node(node)
    
    def dump(self, filename="ast", dir=".", format="pdf"):
        return self.graph.render(filename=filename, directory=dir, format=format, engine="dot")


class ParserError(RuntimeError):
    pass


class GroupManager:
    def __init__(self):
        self.next_group = 1
        self.finished_groups = set()

    def get_next_group(self):
        groupno = self.next_group
        self.next_group += 1
        return groupno

    def finish_group(self, group):
        self.finished_groups.add(group)

    def is_finished(self, groupno: int):
        return groupno in self.finished_groups


class RegexParser:
    GLOBAL_METACHARS = set(r"\^$[.|()?*+{")
    SET_METACHARS = set(r"\^-[]")
    SPECIALCHARS = set("sSdDwW")
    QUANTIFIERS = set("*+?")
    ANCHORS = set("^$")
    SPECIALANCHORS = set("bB")
    INVALID_START_CHAR = set(")|")

    CHAR_ESCAPE_SEQS = {
        "a": "\x07",
        "e": "\x1e",
        "f": "\x0c",
        "n": "\x0a",
        "r": "\x0d",
        "t": "\x09",
    }

    ESCAPE_GROUPS = {
        "w": Or(Range("a", "z"),
                Or(Range("A", "Z"),
                   Or(Range("0", "9"),
                      Literal("_"),
                      )
                   )
                ),
        "d": Range("0", "9"),
        "v": Or(Literal("\n"),
                Or(Literal("\v"),
                   Or(Literal("\f"),
                      Or(Literal("\r"),
                         Literal("\x85"),
                         )
                      )
                   )
                ),
        "h": Or(Literal("\t"),
                Or(Literal(" "),
                   Literal("\xa0"),
                   )
                ),
        "s": Or(Or(Literal("\n"),
                   Or(Literal("\v"),
                      Or(Literal("\f"),
                         Or(Literal("\r"),
                            Literal("\x85"),
                            )
                         )
                      )
                   ),
                Or(Literal("\t"),
                   Or(Literal(" "),
                      Literal("\xa0"),
                      )
                   )
                ),
    }

    def __init__(self, regex):
        self.it = peekable(self._lex(regex))
        self.group_manager = GroupManager()

    def _lex(self, regex):
        # for now, each character in the symbol represents their own lexeme
        return regex

    def _start_group(self):
        return self.group_manager.get_next_group()

    def _finish_group(self, groupno):
        self.group_manager.finish_group(groupno)

    def parse(self):
        ast = self._parse_expr()

        if not self._eof():
            if self._peek() == ")":
                raise ParserError("Unmatched parentheses")
            else:
                raise ParserError("Unknown error in consuming entire input")

        return Group(ast, 0)

    def _advance(self):
        return next(self.it)

    def _peek(self):
        return self.it.peek("")

    def _peek_ahead(self, i):
        try:
            return "".join(self.it[:i])
        except IndexError:
            return ""

    def _eof(self):
        return self._peek() == ""

    def _expect(self, *args):
        if self._peek() not in set(args):
            raise ParserError(f"Expected one of {''.join(list(args))}, received {self._peek()}")

    def _consume(self, c):
        self._expect(c)
        return self._advance()

    def _parse_expr(self):
        lhs = self._parse_term()

        if self._peek() == "|":
            self._advance()
            return Or(lhs, self._parse_expr())

        return lhs

    def _parse_term(self):
        lhs = self._parse_atom()

        if self._eof() or self._peek() in self.INVALID_START_CHAR:
            return lhs

        return Sequence(lhs, self._parse_term())

    def _parse_atom(self):
        c = self._peek()

        if c == "(":
            atom = self._parse_group()
        elif c == ".":
            self._advance()
            atom = Dot()
        elif c == "[":
            atom = self._parse_set()
        elif c in self.ANCHORS:
            return self._parse_anchor()
        elif c in "|)":
            return Epsilon()
        elif c == "\\":
            atom = self._parse_escape()
        else:
            atom = self._parse_literal(self.GLOBAL_METACHARS)

        return self._parse_quantifier(atom)

    def _parse_anchor(self):
        c = self._advance()

        if c == "$":
            return EndAnchor()
        elif c == "^":
            return StartAnchor()

    def _parse_set(self):
        self._consume("[")
        regex_set = self._parse_set_items()
        self._consume("]")
        return regex_set

    def _parse_set_literal(self):
        return self._parse_literal(self.SET_METACHARS)

    def _parse_regex_literal(self):
        return self._parse_literal(self.GLOBAL_METACHARS)

    def _parse_literal(self, metachars: set):
        if self._peek() == "":
            return Epsilon()

        if self._peek() == "\\":
            self._advance()

            # still need to do octal numbers
            if self._peek() not in metachars:
                raise ParserError(f"Meaningless escaped char {self._peek()}")

        return Literal(self._advance())

    def _parse_set_items(self):
        lhs = self._parse_set_literal()

        if self._peek() == "-" and self._peek_ahead(2) != "-]":
            self._advance()
            lhs = Range(lhs.item(), self._parse_set_literal().item())

        if self._peek() == "]":
            return lhs
        else:
            return Or(lhs, self._parse_set_items())

    def _parse_escape(self):
        self._advance()
        c = self._peek()

        if not c.isalnum():
            return Literal(self._advance())
        elif c.isdigit():
            num = int(self._parse_digit(3))

            if 1 <= num <= 9 or self.group_manager.is_finished(num):
                if not self.group_manager.is_finished(num):
                    raise ParserError(f"Invalid reference to group {num}")
                
                return BackReference(num)

            raise NotImplementedError("escape sequence not parsable yet")
        elif c in self.CHAR_ESCAPE_SEQS:
            return Literal(self.CHAR_ESCAPE_SEQS[self._advance()])
        elif c in self.ESCAPE_GROUPS:
            return self.ESCAPE_GROUPS[self._advance()]

        pass

    def _parse_digit(self, max_digits: int = None):
        ret = ""
        counter = 0

        while (max_digits is None or counter < max_digits) and self._peek().isdigit():
            ret += self._advance()

        return ret

    def _parse_group(self):
        groupno = self._start_group()
        self._consume("(")
        group = Group(self._parse_expr(), groupno)
        self._consume(")")
        self._finish_group(groupno)
        return group

    def _parse_quantifier(self, atom):
        if self._peek() not in self.QUANTIFIERS:
            return atom

        meta = self._advance()
        if meta == "*":
            return KleeneStar(atom)
        elif meta == "+":
            return KleenePlus(atom)


def parse(regex):
    return RegexParser(regex).parse()
