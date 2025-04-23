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

from typing import List, Optional
from typeguard import typechecked

from .uasat import Solver


@typechecked
def join_solvers(sol1: Optional[Solver], sol2: Optional[Solver]) -> Optional[Solver]:
    if sol2 is None:
        return sol1
    else:
        assert sol1 is None or sol1 == sol2
        return sol2


class Domain:
    @typechecked
    def __init__(self, length: int):
        self.length = length


class Element:
    @typechecked
    def __init__(self, solver: Optional[Solver], literals: List[int]):
        self.solver = solver
        self.literals = literals

    @property
    @typechecked
    def length(self) -> int:
        return len(self.literals)

    @typechecked
    def __and__(self, other: 'Element') -> 'Element':
        assert self.length == other.length


class Operator:
    @typechecked
    def __init__(self, domains: List[Domain], codomain: Domain):
        self.domains = domains
        self.codomain = codomain

    @property
    @typechecked
    def arity(self) -> int:
        return len(self.domains)

    @typechecked
    def _get_solver(self, elems: List[Element]) -> Solver:
        assert len(elems) == len(self.domains)
        solver = None
        for elem, dom in zip(elems, self.domains):
            assert elem.length == dom.length
            if solver is None:
                solver = elem.solver
            else:
                assert solver == elem.solver
        return solver

    @typechecked
    def evaluate(self, elems: List[Element]) -> Element:
        raise NotImplementedError()


BOOLEAN = Domain(1)


class BooleanOp2(Operator):
    def __init__(self, oper):
        super().__init__([BOOLEAN, BOOLEAN], BOOLEAN)
        self.oper = oper

    def evaluate(self, elems: List[Element]) -> Element:
        solver = self._get_solver(elems)


BOOLEAN_AND = BooleanOp2(Solver.bool_and)


class Boolean:
    def __init__(self):
        super().__init__(1)

    def contains(self, elem: Element) -> Element:
        assert self.compatible(elem)
        return [elem.solver.bool_true()]

    def bool_and(self, elem0: Element, elem1: Element) -> Element:
        elem2 = elem0.solver.bool_and(elem0.literals[0], elem1.literals[0])
        return Element(self, elem0.solver, [elem2])


class Fixed(Domain):
    def __init__(self, size: int):
        super().__init__(size)

    def contains(self, elem: Element) -> Element:
        return [elem.solver.fold_one(elem.literals)]


class Product(Domain):
    def __init__(self, factors: List[Domain]):
        super().__init__(sum(f.length for f in factors))
        self.factors = factors


class Power(Domain):
    def __init__(self, base: Domain, exponent: Domain):
        super().__init__(base.num_bits ** exponent.num_bits)
        self.base = base
        self.exponent = exponent
