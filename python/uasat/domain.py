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

from typeguard import typechecked

from .uasat import Solver, BitVec


class Domain:
    @typechecked
    def __init__(self, length: int):
        self.length = length

    @typechecked
    def contains(self, elem: BitVec) -> BitVec:
        raise NotImplementedError()

    @typechecked
    def decode(self, elem: BitVec) -> str:
        raise NotImplementedError()

    @typechecked
    def bool_iff(self, elem0: BitVec, elem1: BitVec, elem2: BitVec) -> BitVec:
        assert len(elem0) == 1 and len(elem1) == len(elem2) == self.length
        solver = elem0.solver or elem1.solver or elem2.solver
        test = elem0.lits[0]
        lits = [solver.bool_iff(test, l1, l2)
                for l1, l2 in zip(elem1.literals, elem2.literals)]
        return BitVec[self, elem0.solver, lits]


class Boolean(Domain):
    def __init__(self):
        super().__init__(1)

    @typechecked
    def contains(self, elem: BitVec) -> BitVec:
        return BitVec(elem.solver, Solver.TRUE)

    @typechecked
    def decode(self, elem: BitVec) -> str:
        assert len(elem) == self.length
        lit = elem.lits[0]
        if lit == Solver.TRUE:
            return "1"
        elif lit == Solver.FALSE:
            return "0"
        else:
            raise ValueError("invalid elem")

    @typechecked
    def bool_lift(self, solver: Solver, value: bool) -> BitVec:
        return BitVec(solver, [Solver.bool_lift(value)])

    @typechecked
    def bool_not(self, elem: BitVec) -> BitVec:
        assert len(elem) == self.length
        return ~elem

    @typechecked
    def bool_or(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        elem0 | elem1

    @typechecked
    def bool_and(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        elem0 & elem1

    @typechecked
    def bool_imp(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        (~elem0) | elem1

    @typechecked
    def bool_xor(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        elem0 ^ elem1

    @typechecked
    def bool_equ(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        ~elem0 ^ elem1


BOOLEAN = Boolean()


class SmallSet(Domain):
    @typechecked
    def __init__(self, size: int):
        super().__init__(size)
        self.size = size

    @typechecked
    def contains(self, elem: BitVec) -> BitVec:
        assert len(elem) == self.length
        lit = elem.solver.fold_one(elem.literals)
        return BitVec(elem.solver, [lit])

    @typechecked
    def decode(self, elem: BitVec) -> str:
        assert len(elem) == self.length
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
