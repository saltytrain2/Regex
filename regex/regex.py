from .parser import RegexParser, NFABuilder


class Regex:
    def __init__(self, regex, opt="O0"):
        self.opt = opt
        self.nfa = self.build_nfa(regex, opt)

    def build_nfa(self, regex, opt):
        ast = RegexParser.parse(regex)
        builder = NFABuilder()

        ast.accept(builder)
        return builder.get_nfa()
        
    def search(self, s: "str"):
        return self.nfa.search(s)

    pass
