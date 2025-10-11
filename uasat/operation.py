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

from typing import List, Optional, Sequence

from ._uasat import BitVec, Solver
from .relation import Relation


class PartialOp:
    def __init__(self, size: int, arity: int, table: List[Optional[int]] | BitVec | Solver):
        assert size >= 1 and arity >= 0
        length = size ** (arity + 1)

        if isinstance(table, BitVec):
            assert len(table) == length
        elif isinstance(table, Solver):
            table = BitVec.new_variable(table, length)
            for start in range(0, length, size):
                table.slice(start, start + size).ensure_amo()
        else:
            table2 = [Solver.FALSE for _ in range(length)]
            assert len(table) == length // size
            for idx, val in enumerate(table):
                if val is None:
                    continue
                assert 0 <= val < size
                table2[idx * size + val] = Solver.TRUE
            table = BitVec(Solver.CALC, table2)

        self.size = size
        self.arity = arity
        self.table = table

    @property
    def length(self):
        return len(self.table)

    @property
    def solver(self):
        return self.table.solver

    def as_relation(self) -> Relation:
        return Relation(self.size, self.arity + 1, self.table)

    @staticmethod
    def new_proj(size: int, arity: int, coord: int) -> 'PartialOp':
        assert 1 <= size and 0 <= coord < arity

        table = Relation.new_diag(
            size, 2).polymer([0, coord + 1], arity + 1)
        return PartialOp(size, arity, table.table)

    @staticmethod
    def new_const(size: int, index: Optional[int]) -> 'PartialOp':
        assert index is None or 0 <= index < size

        table = [Solver.FALSE for _ in range(size)]
        if index is not None:
            table[index] = Solver.TRUE
        return PartialOp(size, 0, BitVec(Solver.CALC, table))

    def polymer(self, new_vars: Sequence[int], new_arity: Optional[int] = None) -> 'PartialOp':
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
        return PartialOp(self.size, new_arity, table)

    def domain(self) -> 'Relation':
        return self.as_relation().fold_any(1)

    def solution(self) -> 'PartialOp':
        return PartialOp(self.size, self.arity, self.table.get_value())

    def decode(self) -> List[Optional[int]]:
        assert not self.table.solver

        result = []
        for start in range(0, self.length, self.size):
            value = None
            for i in range(self.size):
                if self.table[start + i] == Solver.TRUE:
                    value = i
                    break
            result.append(value)
        return result

    def __repr__(self) -> str:
        return f"PartialOp({self.size}, {self.arity}, {self.solution().decode()})"

    def compose(self, args: List['PartialOp']) -> 'PartialOp':
        assert self.arity == len(args) and self.arity >= 1
        new_arity = args[0].arity
        total = self.arity + 1 + new_arity

        # 0..arity-1: temporary, arity: output, arity+1..arity+new_arity: input
        rel = self.as_relation().polymer(
            [self.arity] + list(range(0, self.arity)),
            total)
        for idx, arg in enumerate(args):
            rel &= arg.as_relation().polymer(
                [idx] + list(range(self.arity + 1, total)),
                total)
        rel = rel.fold_any(self.arity)
        rel.fold_amo(1).table.ensure_all()
        return PartialOp(self.size, new_arity, rel.table)

    def comp_eq(self, other: 'PartialOp') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_eq(other.table)

    def comp_ne(self, other: 'PartialOp') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ne(other.table)

    def comp_le(self, other: 'PartialOp') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_le(other.table)

    def comp_lt(self, other: 'PartialOp') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_lt(other.table)

    def comp_ge(self, other: 'PartialOp') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ge(other.table)

    def comp_gt(self, other: 'PartialOp') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_gt(other.table)


class Operation:
    def __init__(self, size: int, arity: int, table: List[int] | BitVec | Solver):
        assert size >= 1 and arity >= 0
        length = size ** (arity + 1)

        if isinstance(table, BitVec):
            assert len(table) == length
        elif isinstance(table, Solver):
            table = BitVec.new_variable(table, length)
            for start in range(0, length, size):
                table.slice(start, start + size).ensure_one()
        else:
            table2 = [Solver.FALSE for _ in range(length)]
            assert len(table) == length // size
            for idx, val in enumerate(table):
                assert 0 <= val < size
                table2[idx * size + val] = Solver.TRUE
            table = BitVec(Solver.CALC, table2)

        self.size = size
        self.arity = arity
        self.table = table

    @staticmethod
    def new_proj(size: int, arity: int, coord: int) -> 'Operation':
        assert 1 <= size and 0 <= coord < arity

        table = Relation.new_diag(
            size, 2).polymer([0, coord + 1], arity + 1)
        return Operation(size, arity, table.table)

    @staticmethod
    def new_const(size: int, index: int) -> 'Operation':
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

    def as_relation(self) -> Relation:
        return Relation(self.size, self.arity + 1, self.table)

    def as_partialop(self) -> PartialOp:
        return PartialOp(self.size, self.arity, self.table)

    def polymer(self, new_vars: Sequence[int], new_arity: Optional[int] = None) -> 'Operation':
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
        return f"Operation({self.size}, {self.arity}, {self.solution().decode()})"

    def compose(self, args: List['Operation']) -> 'Operation':
        assert self.arity == len(args) and self.arity >= 1
        new_arity = args[0].arity
        total = self.arity + 1 + new_arity

        # 0..arity-1: temporary, arity: output, arity+1..arity+new_arity: input
        rel = self.as_relation().polymer(
            [self.arity] + list(range(0, self.arity)),
            total)
        for idx, arg in enumerate(args):
            rel &= arg.as_relation().polymer(
                [idx] + list(range(self.arity + 1, total)),
                total)
        rel = rel.fold_any(self.arity)
        rel.fold_one(1).table.ensure_all()
        return Operation(self.size, new_arity, rel.table)

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


class Constant(Operation):
    def __init__(self, size: int, table: List[int] | BitVec | Solver):
        super().__init__(size, 0, table)

    def solution(self) -> 'Constant':
        return Constant(self.size, self.table.get_value())

    def __repr__(self) -> str:
        return f"Constant({self.size}, {self.solution().decode()})"
