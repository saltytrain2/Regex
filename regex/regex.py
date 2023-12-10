from .parser import parse, NFABuilder, ASTPrinter
from .finite_automata import Optimizer


class Regex:
    def __init__(self, regex, opt="O0"):
        self.opt = opt
        self.ast = parse(regex)
        self.nfa = Optimizer(self.build_nfa(self.ast)).optimize(opt)

    def build_nfa(self, ast):
        builder = NFABuilder()
        ast.accept(builder)
        return builder.get_nfa()

    def match(self, s: str):
        return self.nfa.match(s)

    def search(self, s: str):
        return self.nfa.search(s)

    def finditer(self, s: str):
        yield from self.nfa.finditer(s)

    def dump_nfa(self, filename="nfa", filepath=".", format="pdf"):
        return self.nfa.dump(filename, filepath, format)

    def dump_ast(self, filename="ast", filepath=".", format="pdf"):
        printer = ASTPrinter()
        self.ast.accept(printer)
        printer.dump(filename, filepath, format)

    def findall(self, s: str):
        return [g.group(0) for g in self.finditer(s)]

    pass


def search(regex: str, s: str):
    return Regex(regex).search(s)


def match(regex: str, s: str):
    return Regex(regex).match(s)


def finditer(regex: str, s: str):
    return Regex(regex).finditer(s)


def findall(regex: str, s: str):
    return Regex(regex).findall(s)
