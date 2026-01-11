# Copyright (C) 2025, Miklos Maroti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Callable, List, Optional, Set
import inspect


class Domain:
    def __init__(self, name: str, size: Optional[int]):
        self.name = name
        self.size = size

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Domain) and \
            self.name == value.name and self.size == value.size

    def __hash__(self) -> int:
        return hash(self.name) + 1973 * hash(self.size)

    def forall(self, callable: Callable[..., 'Term'],
               num_vars: Optional[int] = None) -> 'Term':
        if num_vars is None:
            num_vars = len(inspect.signature(callable).parameters)

        variables = [Variable(self, Variable.next_index + i)
                     for i in range(num_vars)]
        Variable.next_index += num_vars
        try:
            term = callable(*variables)
            assert isinstance(term, Term) and term.domain == BOOLEAN
        finally:
            Variable.next_index -= num_vars

        return ForAll(variables, term)

    def exists(self, callable: Callable[..., 'Term'],
               num_vars: Optional[int] = None) -> 'Term':
        if num_vars is None:
            num_vars = len(inspect.signature(callable).parameters)

        variables = [Variable(self, Variable.next_index + i)
                     for i in range(num_vars)]
        Variable.next_index += num_vars
        try:
            term = callable(*variables)
            assert isinstance(term, Term) and term.domain == BOOLEAN
        finally:
            Variable.next_index -= num_vars

        return Exists(variables, term)

    def __str__(self) -> str:
        return self.name


BOOLEAN = Domain("boolean", 2)


class Operator:
    def __init__(self, symbol: str, domains: List[Domain], codomain: Domain):
        self.symbol = symbol
        self.domains = domains
        self.codomain = codomain

    @property
    def arity(self) -> int:
        return len(self.domains)

    def __call__(self, *subterms: 'Term') -> 'Term':
        return Apply(self, *subterms)


class Relation(Operator):
    def __init__(self, symbol: str, domains: List[Domain]):
        Operator.__init__(self, symbol, domains, BOOLEAN)

    def functional(self) -> 'Term':
        assert len(self.domains) >= 1
        return forall(
            self.domains[:-1], lambda *vars: self.domains[-1].forall(
                lambda x, y: imp(self(*vars, x), self(*vars, y), equ(x, y))))

    def existential(self) -> 'Term':
        assert len(self.domains) >= 1
        return forall(
            self.domains[:-1], lambda *vars: self.domains[-1].exists(
                lambda x: self(*vars, x)))


class Definition:
    def __init__(self, variables: List['Variable'], term: 'Term'):
        assert len(set(variables)) == len(variables)
        assert term.free_variables.issubset(variables)
        self.variables = variables
        self.term = term

    @property
    def domains(self) -> List[Domain]:
        return [v.domain for v in self.variables]

    @property
    def codomain(self) -> Domain:
        return self.term.domain

    @property
    def arity(self) -> int:
        return len(self.variables)


class Term:
    """
    Represents an expression whose value is in the given domain. The expression
    may have free variables and can use quantors and operators.
    """

    def __init__(self, domain: Domain):
        self.domain = domain

    @property
    def free_variables(self) -> Set['Variable']:
        """
        Returns the set of free variables of this term.
        """
        raise NotImplementedError()

    def operators(self) -> Set[Operator]:
        """
        Returns the set of operators used in this term.
        """
        raise NotImplementedError()

    def __invert__(self) -> 'Term':
        assert self.domain == BOOLEAN

        if isinstance(self, Not):
            return self.subterm
        else:
            return Not(self)

    def __and__(self, other: 'Term') -> 'Term':
        return And(self, other)

    def __or__(self, other: 'Term') -> 'Term':
        return Or(self, other)

    def __xor__(self, other: 'Term') -> 'Term':
        return Xor(self, other)

    def __str__(self) -> str:
        raise NotImplementedError()


class Variable(Term):
    next_index: int = 0

    def __init__(self, domain: Domain, index: int):
        Term.__init__(self, domain)
        self.index = index

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Variable) and \
            self.domain == value.domain and self.index == value.index

    def __hash__(self) -> int:
        return hash(self.domain) + 2011 * self.index

    @property
    def free_variables(self) -> Set['Variable']:
        return set((self,))

    def operators(self) -> Set[Operator]:
        return set()

    def __str__(self) -> str:
        return "x" + str(self.index)


class Apply(Term):
    def __init__(self, operator: Operator, *subterms: Term):
        assert operator.arity == len(subterms)
        assert all(t.domain == d for t, d in zip(subterms, operator.domains))
        Term.__init__(self, operator.codomain)
        self.operator = operator
        self.subterms = subterms

    @property
    def free_variables(self) -> Set['Variable']:
        vars = set()
        for t in self.subterms:
            vars.update(t.free_variables)
        return vars

    def operators(self) -> Set[Operator]:
        ops = set((self.operator, ))
        for t in self.subterms:
            ops.update(t.operators())
        return ops

    def __str__(self) -> str:
        return self.operator.symbol + "(" + \
            ",".join(str(t) for t in self.subterms) + ")"


class Not(Term):
    def __init__(self, subterm: Term):
        assert subterm.domain == BOOLEAN
        Term.__init__(self, BOOLEAN)
        self.subterm = subterm

    @property
    def free_variables(self) -> Set[Variable]:
        return self.subterm.free_variables

    def operators(self) -> Set[Operator]:
        return self.subterm.operators()

    def __str__(self) -> str:
        return "~" + str(self.subterm)


class And(Term):
    def __init__(self, *subterms: Term):
        Term.__init__(self, BOOLEAN)
        self.subterms = []
        for t in subterms:
            assert t.domain == BOOLEAN
            if isinstance(t, And):
                self.subterms.extend(t.subterms)
            else:
                self.subterms.append(t)

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for t in self.subterms:
            vars.update(t.free_variables)
        return vars

    def operators(self) -> Set[Operator]:
        ops = set()
        for t in self.subterms:
            ops.update(t.operators())
        return ops

    def __str__(self) -> str:
        return "(" + " & ".join(str(t) for t in self.subterms) + ")"


class Or(Term):
    def __init__(self, *subterms: Term):
        Term.__init__(self, BOOLEAN)
        self.subterms = []
        for t in subterms:
            assert t.domain == BOOLEAN
            if isinstance(t, Or):
                self.subterms.extend(t.subterms)
            else:
                self.subterms.append(t)

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for t in self.subterms:
            vars.update(t.free_variables)
        return vars

    def operators(self) -> Set[Operator]:
        ops = set()
        for t in self.subterms:
            ops.update(t.operators())
        return ops

    def __str__(self) -> str:
        return "(" + " | ".join(str(t) for t in self.subterms) + ")"


class Xor(Term):
    def __init__(self, *subterms: Term):
        Term.__init__(self, BOOLEAN)
        self.subterms = []
        for t in subterms:
            assert t.domain == BOOLEAN
            if isinstance(t, Xor):
                self.subterms.extend(t.subterms)
            else:
                self.subterms.append(t)

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for t in self.subterms:
            vars.update(t.free_variables)
        return vars

    def operators(self) -> Set[Operator]:
        ops = set()
        for t in self.subterms:
            ops.update(t.operators())
        return ops

    def __str__(self) -> str:
        return "(" + " ^ ".join(str(t) for t in self.subterms) + ")"


TRUE = And()
FALSE = Or()


class ForAll(Term):
    def __init__(self, variables: List[Variable], subterm: Term):
        Term.__init__(self, BOOLEAN)

        assert subterm.domain == BOOLEAN
        if isinstance(subterm, ForAll):
            variables += subterm.variables
            subterm = subterm.subterm

        self.variables = variables
        self.subterm = subterm

    def __str__(self) -> str:
        return "![" + ",".join(str(v) for v in self.variables) + "]: " \
            + str(self.subterm)

    @property
    def free_variables(self) -> Set[Variable]:
        return self.subterm.free_variables.difference(self.variables)

    def operators(self) -> Set[Operator]:
        return self.subterm.operators()


class Exists(Term):
    def __init__(self, variables: List[Variable], subterm: Term):
        Term.__init__(self, BOOLEAN)

        assert subterm.domain == BOOLEAN
        if isinstance(subterm, Exists):
            variables += subterm.variables
            subterm = subterm.subterm

        self.variables = variables
        self.subterm = subterm

    def __str__(self) -> str:
        return "?[" + ",".join(str(v) for v in self.variables) + "]: " \
            + str(self.subterm)

    @property
    def free_variables(self) -> Set[Variable]:
        return self.subterm.free_variables.difference(self.variables)

    def operators(self) -> Set[Operator]:
        return self.subterm.operators()


class Equ(Term):
    def __init__(self, elem0: Term, elem1: Term):
        assert elem0.domain == elem1.domain
        Term.__init__(self, BOOLEAN)
        self.elem0 = elem0
        self.elem1 = elem1

    @property
    def free_variables(self) -> Set[Variable]:
        return self.elem0.free_variables.union(self.elem1.free_variables)

    def operators(self) -> Set[Operator]:
        return self.elem0.operators().union(self.elem1.operators())

    def __str__(self) -> str:
        return str(self.elem0) + "==" + str(self.elem1)


class Iff(Term):
    def __init__(self, test: Term, elem0: Term, elem1: Term):
        assert test.domain == BOOLEAN and elem0.domain == elem1.domain
        Term.__init__(self, elem0.domain)
        self.test = test
        self.elem0 = elem0
        self.elem1 = elem1

    @property
    def free_variables(self) -> Set[Variable]:
        return self.test.free_variables.union(self.elem0.free_variables).union(
            self.elem1.free_variables)

    def operators(self) -> Set[Operator]:
        return self.test.operators().union(self.elem0.operators()).union(
            self.elem1.operators())

    def __str__(self) -> str:
        return "(" + str(self.test) + " ? " + str(self.elem0) + " : " + str(self.elem1) + ")"


def forall(domains: List['Domain'], callable: Callable[..., 'Term']):
    variables = [Variable(d, Variable.next_index + i)
                 for i, d in enumerate(domains)]

    Variable.next_index += len(domains)
    try:
        term = callable(*variables)
        assert isinstance(term, Term) and term.domain == BOOLEAN
    finally:
        Variable.next_index -= len(domains)

    if isinstance(term, ForAll):
        return ForAll(variables + term.variables, term.subterm)
    else:
        return ForAll(variables, term)


def exists(domains: List['Domain'], callable: Callable[..., 'Term']):
    variables = [Variable(d, Variable.next_index + i)
                 for i, d in enumerate(domains)]

    Variable.next_index += len(domains)
    try:
        term = callable(*variables)
        assert isinstance(term, Term) and term.domain == BOOLEAN
    finally:
        Variable.next_index -= len(domains)

    if isinstance(term, Exists):
        return Exists(variables + term.variables, term.subterm)
    else:
        return Exists(variables, term)


def equ(left: Term, right: Term):
    return Equ(left, right)


def imp(*terms: Term):
    assert len(terms) >= 1
    return Or(*([~t for t in terms[:-1]] + [terms[-1]]))
