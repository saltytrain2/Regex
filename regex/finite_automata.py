from abc import ABC, abstractmethod


class State:
    def __init__(self, name):
        self.name = name
        self.transitions = []

    def add_transition(self, transition):
        self.transitions.append(transition)

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __iter__(self):
        return iter(self.transitions)


class Transition:
    def __init__(self, match_symbol, target_state):
        self.match_symbol = match_symbol
        self.target_state = target_state

    def match(self, c):
        return self.match_symbol.match(c)

    def get_target_state(self):
        return self.target_state


class Matcher(ABC):
    @abstractmethod
    def match(self, c):
        return False

    @abstractmethod
    def log(self):
        return ""


class CharacterMatcher(Matcher):
    def __init__(self, c):
        self.c = c

    def log(self):
        return self.c

    def match(self, c):
        return c == self.c


class EpsilonMatcher(Matcher):
    def log(self):
        return "e"

    def match(self, c):
        return True


class RangeMatcher(Matcher):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def log(self):
        return self.start + "-" + self.end

    def match(self, c):
        return self.start <= c <= self.end


class GroupMatcher(Matcher):
    def __init__(self, *args):
        self.matches = list(args)

    def log(self):
        return "[" + "".join(self.matches) + "]"

    def match(self, c):
        for m in self.matches:
            if m.match(c):
                return True

        return False


class NFA:
    def __init__(self):
        self.states = {}
        self.start_state = ""
        self.end_states = set()

    def set_start_state(self, state: str):
        self.start_state = state

    def add_end_state(self, state: str):
        self.end_states.add(state)

    def add_state(self):
        state = "q" + str(len(self.states))
        self.states[state] = State(state)
        return state
    
    def add_transition(self, start, end, match):
        assert start in self.states and end in self.states
        self.states[start].add_transition(Transition(match, self.states[end]))

    def search(self, s: str):
        stack = [self.states[self.start_state]]

        for c in s:
            tmp = []

            for state in stack:
                for transition in state:
                    if transition.match(c):
                        tmp.append(transition.get_target_state())

            if len(tmp) == 0:
                return False
            
            stack = tmp

        return any(str(state) in self.end_states for state in stack)



