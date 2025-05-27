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

from .uasat import Solver


class Universe:
    def __init__(self, size: int):
        self.size = size


class Relation:
    def __init__(self, universe: Universe, arity: int,
                 literals: Optional[List[int]] = None,
                 solver: Solver = Solver.STATIC):
        assert arity >= 0

        length = 1
        for _ in range(arity):
            length *= self.universe.size

        if literals is not None:
            assert len(literals) == length
        else:
            literals = [solver.add_variable() for _ in range(length)]

        self.universe = universe
        self.solver = solver
        self.arity = arity
        self.literals = literals

    @property
    def length(self):
        return len(self.literals)

    def polymer(self, new_vars: List[int], new_arity: Optional[int]) -> 'Relation':
        assert len(new_vars) == self.arity
        if new_arity is None:
            new_arity = max(new_vars) + 1

        size = self.universe.size
        strides = [0 for _ in range(new_arity)]

        length = 1
        for var in new_vars:
            assert 0 <= var < new_arity
            strides[var] += length
            length *= size

        pos = 0
        literals = []
        indices = [0 for _ in range(new_arity)]
        for _ in range(length):
            literals.append(self.literals[pos])
            for idx in range(new_arity):
                pos += strides[idx]
                indices[pos] += 1
                if indices[pos] < size:
                    break
                indices[pos] = 0
                pos -= strides[idx] * size

        return Relation(universe=self.universe,
                        arity=new_arity,
                        literals=literals,
                        solver=self.solver)

    def diagonal(self) -> 'Relation':
        return self.polymer([0 for _ in range(self.arity)], 1)
