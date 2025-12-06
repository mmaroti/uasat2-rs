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

        if isinstance(term, ForAll):
            return ForAll(variables + term.variables, term.subterm)
        else:
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

        if isinstance(term, Exists):
            return Exists(variables + term.variables, term.subterm)
        else:
            return Exists(variables, term)

    @staticmethod
    def forall2(domains: List['Domain'], callable: Callable[..., 'Term']):
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

    @staticmethod
    def exists2(domains: List['Domain'], callable: Callable[..., 'Term']):
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
        return Domain.forall2(
            self.domains[:-1], lambda *vars: self.domains[-1].forall(
                lambda x, y: ~self(*vars, x) | ~self(*vars, y) | (x == y)))

    def existential(self) -> 'Term':
        assert len(self.domains) >= 1
        return Domain.forall2(
            self.domains[:-1], lambda *vars: self.domains[-1].exists(
                lambda x: self(*vars, x)))


class Term:
    def __init__(self, domain: Domain):
        self.domain = domain

    @property
    def free_variables(self) -> Set['Variable']:
        raise NotImplementedError()

    def __invert__(self) -> 'Term':
        assert self.domain == BOOLEAN

        if isinstance(self, Not):
            return self.subterm
        else:
            return Not(self)

    def __and__(self, other: 'Term') -> 'Term':
        assert self.domain == BOOLEAN and other.domain == BOOLEAN

        if isinstance(self, And):
            subterms = list(self.subterms)
        else:
            subterms = [self]

        if isinstance(other, And):
            subterms.extend(other.subterms)
        else:
            subterms.append(other)

        return And(*subterms)

    def __or__(self, other: 'Term') -> 'Term':
        assert self.domain == BOOLEAN and other.domain == BOOLEAN

        if isinstance(self, Or):
            subterms = list(self.subterms)
        else:
            subterms = [self]

        if isinstance(other, Or):
            subterms.extend(other.subterms)
        else:
            subterms.append(other)

        return Or(*subterms)

    def __xor__(self, other: 'Term') -> 'Term':
        assert self.domain == BOOLEAN and other.domain == BOOLEAN

        if isinstance(self, Or):
            subterms = list(self.subterms)
        else:
            subterms = [self]

        if isinstance(other, Or):
            subterms.extend(other.subterms)
        else:
            subterms.append(other)

        return Xor(*subterms)

    def __eq__(self, other: 'Term') -> 'Term':  # type: ignore
        return Equ(self, other)

    def format(self, precedence: int) -> str:
        return str(self)

    def __str__(self) -> str:
        raise NotImplementedError()


class Variable(Term):
    next_index: int = 0

    def __init__(self, domain: Domain, index: int):
        Term.__init__(self, domain)
        self.index = index

    @property
    def free_variables(self) -> Set['Variable']:
        return set((self,))

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

    def __str__(self) -> str:
        return "~" + str(self.subterm)


class And(Term):
    def __init__(self, *subterms: Term):
        assert all(t.domain == BOOLEAN for t in subterms)
        Term.__init__(self, BOOLEAN)
        self.subterms = subterms

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for t in self.subterms:
            vars.update(t.free_variables)
        return vars

    def __str__(self) -> str:
        return "(" + " & ".join(str(t) for t in self.subterms) + ")"


class Or(Term):
    def __init__(self, *subterms: Term):
        assert all(t.domain == BOOLEAN for t in subterms)
        Term.__init__(self, BOOLEAN)
        self.subterms = subterms

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for t in self.subterms:
            vars.update(t.free_variables)
        return vars

    def __str__(self) -> str:
        return "(" + " | ".join(str(t) for t in self.subterms) + ")"


class Xor(Term):
    def __init__(self, *subterms: Term):
        assert all(t.domain == BOOLEAN for t in subterms)
        Term.__init__(self, BOOLEAN)
        self.subterms = subterms

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for t in self.subterms:
            vars.update(t.free_variables)
        return vars

    def __str__(self) -> str:
        return "(" + " ^ ".join(str(t) for t in self.subterms) + ")"


TRUE = And()
FALSE = Or()


class ForAll(Term):
    def __init__(self, variables: List[Variable], subterm: Term):
        assert subterm.domain == BOOLEAN
        Term.__init__(self, BOOLEAN)
        self.variables = variables
        self.subterm = subterm

    def __str__(self) -> str:
        return "![" + ",".join(str(v) for v in self.variables) + "]: " \
            + str(self.subterm)

    @property
    def free_variables(self) -> Set[Variable]:
        return self.subterm.free_variables.difference(self.variables)


class Exists(Term):
    def __init__(self, variables: List[Variable], subterm: Term):
        assert subterm.domain == BOOLEAN
        Term.__init__(self, BOOLEAN)
        self.variables = variables
        self.subterm = subterm

    def __str__(self) -> str:
        return "?[" + ",".join(str(v) for v in self.variables) + "]: " \
            + str(self.subterm)

    @property
    def free_variables(self) -> Set[Variable]:
        return self.subterm.free_variables.difference(self.variables)


class Equ(Term):
    def __init__(self, elem0: Term, elem1: Term):
        assert elem0.domain == elem1.domain
        Term.__init__(self, BOOLEAN)
        self.elem0 = elem0
        self.elem1 = elem1

    @property
    def free_variables(self) -> Set[Variable]:
        return self.elem0.free_variables.union(self.elem1.free_variables)

    def __str__(self) -> str:
        return str(self.elem0) + "==" + str(self.elem1)
