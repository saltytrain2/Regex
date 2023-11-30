from abc import ABC, abstractmethod
from collections import deque
from typing import Iterable, Union

import networkx as nx
import graphviz as gviz


class State:
    def __init__(self, name):
        self.name = name
        self.transitions = []

    def add_transition(self, transition):
        self.transitions.append(transition)

    def edges(self):
        return [(self.name, t.get_target_name()) for t in self.transitions]

    def get_name(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __iter__(self):
        return iter(self.transitions)


class Transition:
    def __init__(self, match_symbol, target_name, target_state, start_group, end_group):
        self.match_symbol = match_symbol
        self.target_name = target_name
        self.target_state = target_state
        self.start_group = start_group
        self.end_group = end_group
    
    def get_target_name(self):
        return self.target_name

    def match(self, input, i):
        return self.match_symbol.match(input, i)

    def get_target_state(self):
        return self.target_state

    def is_epsilon_transition(self):
        return self.match_symbol.is_epsilon()

    def log(self):
        return self.match_symbol.log()


class Matcher(ABC):
    @abstractmethod
    def match(self, input, i):
        return False

    @abstractmethod
    def log(self):
        return ""

    @abstractmethod
    def is_epsilon(self):
        return False


class CharacterMatcher(Matcher):
    def __init__(self, c):
        self.c = c

    def log(self):
        return self.c

    def match(self, input, i):
        return len(input) > i and input[i] == self.c

    def is_epsilon(self):
        return False


class EpsilonMatcher(Matcher):
    def log(self):
        return "ε"

    def match(self, input, i):
        return True

    def is_epsilon(self):
        return True


class RangeMatcher(Matcher):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def log(self):
        return self.start + "-" + self.end

    def match(self, input, i):
        return len(input) > i and self.start <= input[i] <= self.end

    def is_epsilon(self):
        return False


class GroupMatcher(Matcher):
    def __init__(self, *args):
        self.matches = list(args)

    def log(self):
        return "[" + "".join(self.matches) + "]"

    def match(self, input, i):
        return any(m.match(input, i) for m in self.matches)

    def is_epsilon(self):
        return False


class TraversalState:
    def __init__(self, index: int, state: str):
        self.index = index
        self.state = state

    def get_state(self):
        return self.state

    def get_index(self):
        return self.index


class Match:
    def __init__(self):
        self.groups: dict[str] = {}

    def group(self, i: Union[str, int]):
        return self.groups[i]


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

    def add_group(self):
        self.num_groups += 1
        return self.num_groups - 1

    def add_transition(self, start, end, match, start_group=None, end_group=None):
        assert start in self.states and end in self.states
        self.states[start].add_transition(Transition(match, end, self.states[end], start_group, end_group))

    def dump(self, output_file="./nfa.pdf", format="pdf"):
        graph = gviz.Digraph("nfa", format=format)
        
        for state_name in self.states.keys():
            shape = "circle" if state_name not in self.end_states else "doublecircle"
            graph.node(state_name, label=state_name, shape=shape)
        
        for state_name in self.states:
            for transitions in self.states[state_name]:
                graph.edge(
                    state_name,
                    transitions.get_target_name(),
                    label=transitions.log(),
                )

        graph.node("_", shape="point")
        graph.edge("_", self.start_state)

        graph.render(directory=".")

    def search(self, s: str):
        """If any substring in s matches, this returns true
        """
        paths = deque([TraversalState(0, self.start_state)])

        while paths:
            path = paths.popleft()

            if path.get_state() in self.end_states:
                return True

            for transition in self.states[path.get_state()]:
                if transition.match(s, path.get_index()):
                    paths.append(
                        TraversalState(
                            path.get_index() + (0 if transition.is_epsilon_transition() else 1),
                            transition.get_target_state().get_name(),
                        )
                    )

        return False


