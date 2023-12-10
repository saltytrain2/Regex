from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union
from copy import deepcopy
from collections import defaultdict

import graphviz as gviz


class State:
    def __init__(self, name: str):
        self.name = name
        self.transitions: list[Transition] = []

    def add_transition(self, transition):
        self.transitions.append(transition)

    def edges(self):
        return [(self.name, t.get_target_name()) for t in self.transitions]

    def get_name(self):
        return self.name

    def __hash__(self): return hash(self.name)

    def __str__(self):
        return self.name

    def __iter__(self):
        return reversed(self.transitions)


@dataclass
class Transition:
    match_symbol: Matcher
    target_name: str
    target_state: State
    start_group: int | None
    end_group: int | None

    def get_target_name(self):
        return self.target_name

    def match(self, input, i, groups):
        return self.match_symbol.match(input, i, groups)

    def get_target_state(self):
        return self.target_state

    def is_epsilon_transition(self, groups=None):
        return self.match_symbol.is_epsilon(groups)

    def is_pure_epsilon_transition(self, groups=None):
        return self.is_epsilon_transition(groups) and not self.is_group_transition()

    def is_group_transition(self):
        return self.is_starting_group() or self.is_ending_group()

    def is_starting_group(self):
        return self.start_group is not None

    def is_ending_group(self):
        return self.end_group is not None

    def num_consumed(self, groups):
        return self.match_symbol.num_consumed(groups)

    def log(self):
        edge_str = self.match_symbol.log()
        if self.start_group is not None:
            edge_str += f"\nStart: {self.start_group}"
        elif self.end_group is not None:
            edge_str += f"\nEnd: {self.end_group}"

        return edge_str


class Matcher(ABC):
    @abstractmethod
    def match(self, input: str, i: int, groups: dict[int | str, str]):
        return False

    @abstractmethod
    def log(self):
        return ""

    @abstractmethod
    def is_epsilon(self, groups: dict[int | str, str]):
        return False

    @abstractmethod
    def num_consumed(self, groups: dict[int | str, str]):
        return 0


class CharacterMatcher(Matcher):
    def __init__(self, c):
        self.c = c

    def log(self):
        return "'" + self.c + "'"

    def match(self, input, i, groups):
        return len(input) > i and input[i] == self.c

    def is_epsilon(self, groups):
        return False

    def num_consumed(self, groups):
        return 1


class EpsilonMatcher(Matcher):
    def log(self):
        return "ε"

    def match(self, input, i, groups):
        return True

    def is_epsilon(self, groups):
        return True

    def num_consumed(self, groups):
        return 0


class RangeMatcher(Matcher):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def log(self):
        return self.start + "-" + self.end

    def match(self, input, i, groups):
        return len(input) > i and self.start <= input[i] <= self.end

    def is_epsilon(self, groups):
        return False

    def num_consumed(self, groups):
        return 1


class BackReferenceMatcher(Matcher):
    def __init__(self, reference):
        self.reference = reference

    def log(self):
        return r"\\" + str(self.reference)

    def match(self, input, i, groups):
        if self.reference not in groups:
            return True

        return input[i:i+len(groups[self.reference].substr)] == groups[self.reference].substr

    def is_epsilon(self, groups):
        if groups is None:
            return True

        return groups[self.reference].substr == ""

    def num_consumed(self, groups):
        return len(groups[self.reference].substr)


class InverseMatcher(Matcher):
    def __init__(self, matcher: Matcher):
        self.matcher = matcher

    def log(self):
        return "!" + self.matcher.log()

    def match(self, input, i, groups):
        return not self.matcher.match(input, i, groups)

    def is_epsilon(self, groups):
        return False  # not matching always consumes an input

    def num_consumed(self, groups):
        return 1  # not matching always consumes one input


class GroupMatcher(Matcher):
    def __init__(self, *args):
        self.matches = list(args)

    def log(self):
        return "[" + "".join(self.matches) + "]"

    def match(self, input, i, groups):
        return any(m.match(input, i) for m in self.matches)

    def is_epsilon(self):
        return False

    def num_consumed(self, groups):
        return 1


@dataclass
class _Match:
    start: int
    end: int = None
    substr: str = None


@dataclass
class TraversalState:
    start: int
    end: int
    state: str
    cur_cycle: set[str]
    groups: dict[int | str, _Match]

    def get_state(self):
        return self.state

    def get_start(self):
        return self.start

    def get_end(self):
        return self.end

    def get_cur_cycle(self):
        return self.cur_cycle

    def start_group(self, name):
        self.groups[name] = _Match(self.end)

    def end_group(self, name, s: str):
        self.groups[name].substr = s[self.groups[name].start: self.end]
        self.groups[name].end = self.end


class Match:

    def __init__(self, groups):
        self.groups: dict[str | int, _Match] = groups

    def group(self, i: Union[str, int] = 0):
        return self.groups[i].substr

    def span(self, i: Union[str, int] = 0):
        return (self.groups[i].start, self.groups[i].end)

    def start(self, i: Union[str, int] = 0):
        return self.groups[i].start

    def end(self, i: Union[str, int] = 0):
        return self.groups[i].end


class NFA:
    def __init__(self):
        self.states: dict[str, State] = {}
        self.start_state: str = ""
        self.end_states: set[str] = set()

    def state_iter(self):
        yield from self.states

    def get_transitions(self, state: str):
        return [transition for transition in self.states[state]]

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

    def dump(self, filename: str, filepath: str, format: str):
        graph = gviz.Digraph()

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
        
        graph.render(filename=filename, directory=filepath, format=format, engine="dot", cleanup=True)

    def match(self, s: str):
        return self._search(s, 0)

    def search(self, s: str, start=0):
        for i in range(start, len(s) + 1):
            if (m := self._search(s, i)) is not None:
                return m

        return None

    def finditer(self, s: str):
        cur = 0
        while (m := self.search(s, cur)) is not None:
            yield m

            cur = m.end()

            if m.end() == m.start():
                cur += 1

            if cur > len(s):
                break

    def _search(self, s: str, start: int):
        """If any substring in s matches, this returns true
        """
        paths = [TraversalState(start, start, self.start_state, set(), {})]

        while paths:
            path = paths.pop()

            if path.get_state() in self.end_states:
                return Match(path.groups)

            for transition in self.states[path.get_state()]:
                if transition.match(s, path.get_end(), path.groups):
                    if transition.is_epsilon_transition(path.groups) and path.get_state() in path.get_cur_cycle():
                        continue
                    elif transition.is_epsilon_transition(path.groups):
                        new_cycle = set(path.get_cur_cycle())
                        new_cycle.add(path.get_state())
                    else:
                        new_cycle = set()

                    new_path = TraversalState(
                        path.get_start(),
                        path.get_end() + transition.num_consumed(path.groups),
                        transition.get_target_state().get_name(),
                        new_cycle,
                        deepcopy(path.groups),
                    )

                    if transition.is_starting_group():
                        new_path.start_group(transition.start_group)
                    elif transition.is_ending_group():
                        new_path.end_group(transition.end_group, s)

                    paths.append(new_path)

        return None


class OptimizerModule(ABC):
    def __init__(self, optimizer: Optimizer):
        self.optimizer = optimizer

    @abstractmethod
    def optimize(self):
        return None


class EpsilonEliminator(OptimizerModule):

    def optimize(self):
        pass


class DFAConverter(OptimizerModule):

    def optimize(self):
        pass


class Optimizer:
    O1_OPTIMIZATIONS = [EpsilonEliminator]

    def __init__(self, nfa: NFA):
        self.nfa = nfa
        self.epsilon_closure = self._calculate_epsilon_closure()

    def get_epsilon_closure(self):
        return self.epsilon_closure

    def update(self):
        self.epsilon_closure = self._calculate_epsilon_closure()

    def optimize(self, level="O0"):
        level = int(level[1])

        if level >= 1:
            for optimizing_module in self.O1_OPTIMIZATIONS:
                optimizing_module(self).optimize()
                self.update()

        return self.nfa

    def _calculate_epsilon_closure(self):
        closure: dict[set[str]] = defaultdict(set)

        for state in self.nfa.state_iter():
            frontier = self._transition_frontier(state)

            while frontier:
                next_state = frontier.pop()
                for transition in self.nfa.get_transitions(next_state):
                    if transition.is_epsilon_transition() and not transition.is_group_transition():
                        frontier.append(transition.get_target_name())
                closure[state].add(next_state)

        return closure

    def _transition_frontier(self, state: str):
        return [transition.get_target_name() for transition in self.nfa.get_transitions(state)]

