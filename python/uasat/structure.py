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
    def __init__(self, size: int, arity: int, table: List[bool] | BitVec | Solver):
        assert size >= 1 and arity >= 0
        length = size ** arity

        if isinstance(table, BitVec):
            assert len(table) == length
        elif isinstance(table, Solver):
            table = BitVec.new_variable(table, length)
        else:
            assert len(table) == length
            table = BitVec(Solver.CALC, [Solver.bool_lift(b) for b in table])

        self.size = size
        self.arity = arity
        self.table = table

    @staticmethod
    def diagonal(size: int, arity: int = 2) -> 'Relation':
        assert size >= 1 and arity >= 0

        if size <= 1:
            table = [Solver.TRUE]
        else:
            length = size ** arity
            table = [Solver.FALSE for _ in range(length)]

            step = (size ** arity - 1) // (size - 1)
            for idx in range(0, length, step):
                table[idx] = Solver.TRUE

        return Relation(size, arity, BitVec(Solver.CALC, table))

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
        for _ in range(self.size ** new_arity):
            table.append(self.table[pos])
            for idx in range(new_arity):
                pos += strides[idx]
                indices[idx] += 1
                if indices[idx] < self.size:
                    break
                indices[idx] = 0
                pos -= strides[idx] * self.size

        table = BitVec(self.solver, table)
        return Relation(self.size, new_arity, table)

    def fold_any(self, count: Optional[int]):
        if count is None:
            count = self.arity
        assert 0 <= count <= self.arity

        step = self.size ** count
        table = []
        for idx in range(0, self.length, step):
            part = self.table.slice(idx, idx + step)
            table.append(self.solver.fold_any(part.literals))
        table = BitVec(self.solver, table)
        return Relation(self.size, self.arity - count, table)

    def fold_all(self, count: Optional[int]):
        if count is None:
            count = self.arity
        assert 0 <= count <= self.arity

        step = self.size ** count
        table = []
        for idx in range(0, self.length, step):
            part = self.table.slice(idx, idx + step)
            table.append(self.solver.fold_all(part.literals))
        table = BitVec(self.solver, table)
        return Relation(self.size, self.arity - count, table)

    def fold_one(self, count: Optional[int]):
        if count is None:
            count = self.arity
        assert 0 <= count <= self.arity

        step = self.size ** count
        table = []
        for idx in range(0, self.length, step):
            part = self.table.slice(idx, idx + step)
            table.append(self.solver.fold_one(part.literals))
        table = BitVec(self.solver, table)
        return Relation(self.size, self.arity - count, table)

    def solution(self) -> 'Relation':
        return Relation(self.size, self.arity, self.table.get_value())

    def decode(self) -> List[bool]:
        assert not self.table.solver
        return [self.table[i] == Solver.TRUE for i in range(self.length)]

    def __repr__(self) -> str:
        return str(self.table)

    def comp_eq(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_eq(other.table)

    def comp_ne(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ne(other.table)

    def comp_le(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_le(other.table)

    def comp_lt(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_lt(other.table)

    def comp_ge(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ge(other.table)

    def comp_gt(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_gt(other.table)

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

    def antisymmetric(self) -> BitVec:
        assert self.arity == 2
        rel = self & self.polymer([1, 0])
        rel = ~rel | Relation.diagonal(self.size, 2)
        return rel.table.fold_all()

    def compose(self, other: 'Relation') -> 'Relation':
        assert self.arity == other.arity == 2
        return (self.polymer([1, 0], 3) & self.polymer([0, 2], 3)).fold_any(1)

    def transitive(self) -> BitVec:
        assert self.arity == 2
        return (~self.compose(self) | self).table.fold_all()


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
                part = table.slice(start, start + size)
                table.solver.add_clause1(table.solver.fold_one(part.literals))

        self.size = size
        self.arity = arity
        self.table = table

    @staticmethod
    def projection(size: int, arity: int, coord: int) -> 'Operation':
        assert 1 <= size and 0 <= coord < arity

        table = Relation.diagonal(size, 2).polymer([0, coord + 1], arity + 1)
        return Operation(size, arity, table.table)

    @staticmethod
    def element(size: int, index: int) -> 'Operation':
        assert 0 <= index < size

        table = [Solver.FALSE for _ in range(size)]
        table[index] = Solver.TRUE
        return Operation(size, 0, BitVec(Solver.CALC, table))

    @property
    def length(self):
        return len(self.table)

    @property
    def solver(self):
        return self.table.solver

    @property
    def graph(self) -> Relation:
        return Relation(self.size, self.arity + 1, self.table)

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
        for _ in range(self.size ** new_arity):
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
        return Operation(self.size, new_arity, table)

    def solution(self) -> 'Operation':
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

    def comp_eq(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_eq(other.table)

    def comp_ne(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ne(other.table)

    def comp_le(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_le(other.table)

    def comp_lt(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_lt(other.table)

    def comp_ge(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ge(other.table)

    def comp_gt(self, other: 'Operation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_gt(other.table)
