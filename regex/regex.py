from .parser import parse, NFABuilder


class Regex:
    def __init__(self, regex, opt="O0"):
        self.opt = opt
        self.nfa = self.build_nfa(regex, opt)

    def build_nfa(self, regex, opt):
        ast = parse(regex)
        builder = NFABuilder()

        ast.accept(builder)
        return builder.get_nfa()

    def match(self, s: "str"):
        return self.nfa.match(s)

    def dump(self, filename="nfa", filepath=".", format="pdf"):
        return self.nfa.dump(filename, filepath, format)

    pass


def search(regex: str, s: str):
    return Regex(regex).search(s)
