#!/usr/bin/env python3
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
from uasat import Solver


SOLVER = Solver()


def print_all_solutions(literals: List[int]):
    result = []
    while SOLVER.solve():
        values = [SOLVER.get_value(lit) for lit in literals]
        result.append(values)
        clause = [SOLVER.bool_xor(Solver.bool_lift(val), lit)
                  for (val, lit) in zip(values, literals)]
        SOLVER.add_clause(clause)

    for value in sorted(result):
        print(value)


class Index:
    def __init__(self, length: int, value: Optional[int] = None):
        if value is None:
            self.lits = [SOLVER.add_variable() for _ in range(length)]
            SOLVER.add_clause1(SOLVER.fold_one(self.lits))
        else:
            assert 0 <= value < length
            self.lits = [SOLVER.FALSE for _ in range(length)]
            self.lits[value] = SOLVER.TRUE

    def __eq__(self, other: 'Index') -> int:
        return SOLVER.comp_eq(self.lits, other.lits)

    def __lt__(self, other: 'Index') -> int:
        return SOLVER.comp_lt(self.lits, other.lits)

    def __le__(self, other: 'Index') -> int:
        return SOLVER.comp_le(self.lits, other.lits)


class Elem:
    def __init__(self, length: int, position: int):
        self.arg0 = Index(length)
        self.arg1 = Index(length)
        self.arg2 = Index(length)
        self.arg3 = Index(length)

        limit = Index(length, position)
        SOLVER.add_clause1(self.arg0 <= limit)
        SOLVER.add_clause1(self.arg1 <= limit)
        SOLVER.add_clause1(self.arg2 <= limit)
        SOLVER.add_clause1(self.arg3 <= limit)

        self.eq01 = self.arg0 == self.arg1
        self.eq12 = self.arg1 == self.arg2
        self.eq23 = self.arg2 == self.arg3
        self.eq30 = self.arg3 == self.arg0

        # f(x,y,x,x) = f(y,x,x,x)
        SOLVER.add_clause1(Solver.bool_not(
            SOLVER.bool_and(self.eq23, self.eq30)))

        # f(x,x,y,x) = f(y,x,x,x)
        SOLVER.add_clause1(Solver.bool_not(
            SOLVER.bool_and(self.eq01, self.eq30)))

        # f(x,x,x,y) = f(y,x,x,x)
        SOLVER.add_clause1(Solver.bool_not(
            SOLVER.bool_and(self.eq01, self.eq12)))


def test():
    elem = Elem(2, 1)
    print_all_solutions(elem.arg0.lits + elem.arg1.lits +
                        elem.arg2.lits + elem.arg3.lits)


if __name__ == '__main__':
    test()
