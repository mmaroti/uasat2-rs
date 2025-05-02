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

from typing import List, Callable
from typeguard import typechecked

from .uasat import Solver


class Elem:
    @typechecked
    def __init__(self, domain: 'Domain', solver: Solver, lits: List[int]):
        assert domain.length == len(lits)
        self.domain = domain
        self.solver = solver
        self.lits = lits

    @property
    @typechecked
    def length(self) -> int:
        return len(self.lits)


class Domain:
    @typechecked
    def __init__(self, length: int):
        self.length = length

    @typechecked
    def contains(self, elem: Elem) -> Elem:
        raise NotImplementedError()

    @typechecked
    def decode(self, elem: Elem) -> str:
        raise NotImplementedError()

    @typechecked
    def _comp(self, op: Callable[[Solver, Elem, Elem], Elem], elem0: Elem, elem1: Elem) -> Elem:
        assert elem0.domain == self and elem1.domain == self \
            and elem0.solver == elem1.solver
        lit = op(elem0.solver, elem0.lits, elem1.lits)
        return Elem(BOOLEAN, elem0.solver, [lit])

    @typechecked
    def comp_eq(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._comp(Solver.comp_eq, elem0, elem1)

    @typechecked
    def comp_le(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._comp(Solver.comp_le, elem0, elem1)

    @typechecked
    def comp_lt(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._comp(Solver.comp_lt, elem0, elem1)

    @typechecked
    def bool_iff(self, elem0: Elem, elem1: Elem, elem2: Elem) -> Elem:
        assert elem0.domain == BOOLEAN \
            and elem1.domain == self and elem2.domain == self \
            and elem0.solver == elem1.solver == elem2.solver
        test = elem0.lits[0]
        lits = [elem0.solver.bool_iff(test, l1, l2)
                for l1, l2 in zip(elem1.lits, elem2.lits)]
        return Elem[self, elem0.solver, lits]


class Boolean(Domain):
    def __init__(self):
        super().__init__(1)

    @typechecked
    def contains(self, elem: Elem) -> Elem:
        assert elem.domain == self
        return Elem(self, elem.solver, Solver.TRUE)

    @typechecked
    def decode(self, elem: Elem) -> str:
        assert elem.domain == self
        lit = elem.lits[0]
        if lit == Solver.TRUE:
            return "1"
        elif lit == Solver.FALSE:
            return "0"
        else:
            raise ValueError("invalid elem")

    @typechecked
    def bool_lift(self, solver: Solver, value: bool) -> Elem:
        return Elem(self, solver, [Solver.bool_lift(value)])

    @typechecked
    def bool_not(self, elem: Elem) -> Elem:
        assert elem.domain == self
        return Elem(self, elem.solver, Solver.bool_not(elem.lits[0]))

    @typechecked
    def _bool2(self, op: Callable[[Solver, int, int], int], elem0: Elem, elem1: Elem) -> Elem:
        assert elem0.domain == self and elem1.domain == self \
            and elem0.solver == elem1.solver
        lit = op(elem0.solver, elem0.lits[0], elem1.lits[0])
        return Elem(self, elem0.solver, [lit])

    @typechecked
    def bool_or(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._bool2(Solver.bool_or, elem0, elem1)

    @typechecked
    def bool_and(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._bool2(Solver.bool_and, elem0, elem1)

    @typechecked
    def bool_imp(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._bool2(Solver.bool_imp, elem0, elem1)

    @typechecked
    def bool_xor(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._bool2(Solver.bool_xor, elem0, elem1)

    @typechecked
    def bool_equ(self, elem0: Elem, elem1: Elem) -> Elem:
        return self._bool2(Solver.bool_equ, elem0, elem1)


BOOLEAN = Boolean()


class SmallSet(Domain):
    @typechecked
    def __init__(self, size: int):
        super().__init__(size)
        self.size = size

    @typechecked
    def contains(self, elem: Elem) -> Elem:
        assert elem.domain == self
        lit = elem.solver.fold_one(elem.lits)
        return Elem(BOOLEAN, elem.solver, [lit])

    @typechecked
    def decode(self, elem: Elem) -> str:
        assert elem.domain == self
        val = None
        for i in range(self.size):
            if elem.lits[i] == Solver.TRUE:
                assert val is None
                val = i
            else:
                assert elem.lits[i] == Solver.FALSE
        if val is None:
            raise ValueError("invalid elem")
        return str(val)
