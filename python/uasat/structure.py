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

from .uasat import BitVec, Solver


class Relation:
    def __init__(self, size: int, arity: int, table: BitVec | Solver):
        assert size >= 1 and arity >= 0
        length = size ** arity

        if isinstance(table, BitVec):
            assert len(table) == length
        else:
            assert isinstance(table, Solver)
            table = BitVec.new_variable(table, length)

        self.size = size
        self.arity = arity
        self.table = table

    @property
    def length(self):
        return len(self.table)

    @property
    def solver(self):
        return self.table.solver

    def polymer(self, new_vars: List[int], new_arity: Optional[int] = None) -> 'Relation':
        assert len(new_vars) == self.arity
        if new_arity is None:
            new_arity = max(new_vars) + 1

        strides = [0 for _ in range(new_arity)]

        length = 1
        for var in new_vars:
            assert 0 <= var < new_arity
            strides[var] += length
            length *= self.size

        pos = 0
        table = []
        indices = [0 for _ in range(new_arity)]
        for _ in range(length):
            table.append(self.table[pos])
            for idx in range(new_arity):
                pos += strides[idx]
                indices[idx] += 1
                if indices[idx] < self.size:
                    break
                indices[idx] = 0
                pos -= strides[idx] * self.size

        table = BitVec(self.solver, table)
        return Relation(self.size, self.arity, table)

    def get_value(self) -> 'Relation':
        return Relation(self.size, self.arity, self.table.get_value())

    def decode(self) -> List[bool]:
        assert not self.table.solver
        return [self.table[i] == Solver.TRUE for i in range(self.length)]

    def __repr__(self) -> str:
        return str(self.table)

    def __eq__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table == other.table

    def __ne__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table != other.table

    def __le__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table <= other.table

    def __lt__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table < other.table

    def __ge__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table >= other.table

    def __gt__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table > other.table

    def __invert__(self) -> 'Relation':
        return Relation(self.size, self.arity, ~self.table)

    def __and__(self, other: 'Relation') -> 'Relation':
        assert self.size == other.size and self.arity == other.arity
        return Relation(self.size, self.arity, self.table & other.table)

    def __or__(self, other: 'Relation') -> 'Relation':
        assert self.size == other.size and self.arity == other.arity
        return Relation(self.size, self.arity, self.table | other.table)

    def __xor__(self, other: 'Relation') -> 'Relation':
        assert self.size == other.size and self.arity == other.arity
        return Relation(self.size, self.arity, self.table ^ other.table)

    def reflexive(self) -> BitVec:
        diag = self.polymer([0 for _ in range(self.arity)])
        return diag.table.fold_all()

    def symmetric(self) -> BitVec:
        assert self.arity == 2
        return (~self | self.polymer([1, 0])).table.fold_all()


class Operation:
    def __init__(self, size: int, arity: int, table: BitVec | Solver):
        assert size >= 1 and arity >= 0
        length = size ** (arity + 1)

        if isinstance(table, BitVec):
            assert len(table) == length
        else:
            assert isinstance(table, Solver)
            table = BitVec.new_variable(table, length)
            for start in range(0, length, size):
                part = table.slice(start, size)
                table.solver.add_clause1(table.solver.fold_one(part.literals))

        self.size = size
        self.arity = arity
        self.table = table

    @property
    def length(self):
        return len(self.table)

    @property
    def solver(self):
        return self.table.solver

    def polymer(self, new_vars: List[int], new_arity: Optional[int] = None) -> 'Operation':
        assert len(new_vars) == self.arity
        if new_arity is None:
            new_arity = max(new_vars) + 1

        strides = [0 for _ in range(new_arity)]

        length = self.size
        for var in new_vars:
            assert 0 <= var < new_arity
            strides[var] += length
            length *= self.size

        pos = 0
        table = []
        indices = [0 for _ in range(new_arity)]
        for _ in range(length // self.size):
            for pos2 in range(pos, pos + self.size):
                table.append(self.table[pos2])
            for idx in range(new_arity):
                pos += strides[idx]
                indices[idx] += 1
                if indices[idx] < self.size:
                    break
                indices[idx] = 0
                pos -= strides[idx] * self.size

        table = BitVec(self.solver, table)
        return Operation(self.size, self.arity, table)

    def get_value(self) -> 'Operation':
        return Operation(self.size, self.arity, self.table.get_value())

    def decode(self) -> List[int]:
        assert not self.table.solver

        result = []
        for start in range(0, self.length, self.size):
            for i in range(self.size):
                if self.table[start + i] == Solver.TRUE:
                    result.append(i)
                    break
        return result

    def __repr__(self) -> str:
        return str(self.table)

    def __eq__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table == other.table

    def __ne__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table != other.table

    def __le__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table <= other.table

    def __lt__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table < other.table

    def __ge__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table >= other.table

    def __gt__(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table > other.table
