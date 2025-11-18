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


class Operation:
    def __init__(self, size: int, arity: int, table: BitVec | List[Optional[int]]):
        assert size >= 1 and arity >= 0

        if not isinstance(table, BitVec):
            table2 = [Solver.FALSE for _ in range(size * len(table))]
            for idx, val in enumerate(table):
                if val is not None:
                    assert 0 <= val < size
                    table2[idx * size + val] = Solver.TRUE
            table = BitVec(Solver.CALC, table2)

        assert len(table) == size ** (arity + 1)
        self.size = size
        self.arity = arity
        self.table = table

    @property
    def length(self):
        return len(self.table)

    @property
    def solver(self):
        return self.table.solver

    @staticmethod
    def variable(size: int, arity: int, solver: Solver, partop: bool = False) -> 'Operation':
        assert size >= 1 and arity >= 0
        length = size ** (arity + 1)

        table = BitVec.variable(solver, length)
        for start in range(0, length, size):
            if not partop:
                table.slice(start, start + size).ensure_one()
            else:
                table.slice(start, start + size).ensure_amo()

        return Operation(size, arity, table)

    @staticmethod
    def projection(size: int, arity: int, coord: int) -> 'Operation':
        assert 1 <= size and 0 <= coord < arity

        table = Relation.diagonal(
            size, 2).polymer([0, coord + 1], arity + 1)
        return Operation(size, arity, table.table)

    def as_relation(self) -> Relation:
        return Relation(self.size, self.arity + 1, self.table)

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
        return Operation(self.size, self.arity, self.table.solution())

    def decode(self) -> List[Optional[int]]:
        assert not self.table.solver

        result = []
        for start in range(0, self.length, self.size):
            for i in range(self.size):
                if self.table[start + i] == Solver.TRUE:
                    result.append(i)
                    break
            else:
                result.append(None)

        assert len(result) == self.size ** self.arity
        return result

    def __repr__(self) -> str:
        return f"Operation({self.size}, {self.arity}, {self.solution().decode()})"

    def compose(self, args: Sequence['Operation'], partop: bool = False) -> 'Operation':
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
        if not partop:
            rel.fold_one(1).ensure_all()
        else:
            rel.fold_amo(1).ensure_all()
        return Operation(self.size, new_arity, rel.table)

    def apply(self, rel: Relation) -> Relation:
        oper = self.as_relation()
        return rel.evaluate([oper for _ in range(rel.arity)])

    def idempotent(self) -> BitVec:
        diag = self.polymer([0 for _ in range(self.arity)], 1)
        return diag.comp_eq(Operation.projection(self.size, 1, 0))

    def preserves(self, rel: Relation) -> BitVec:
        return (~self.apply(rel) | rel).table.fold_all()

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

    def domain(self) -> Relation:
        return self.as_relation().fold_any(1)


class Constant(Operation):
    def __init__(self, size: int, table: BitVec | int):
        if isinstance(table, BitVec):
            super().__init__(size, 0, table)
        else:
            super().__init__(size, 0, [table])

    @staticmethod
    def constant(  # pyright: ignore[reportIncompatibleMethodOverride]
        size: int,
        index: Optional[int],
    ) -> 'Constant':
        assert index is None or 0 <= index < size

        table = [Solver.FALSE for _ in range(size)]
        if index is not None:
            table[index] = Solver.TRUE
        return Constant(size, BitVec(Solver.CALC, table))

    @staticmethod
    def variable(  # pyright: ignore[reportIncompatibleMethodOverride]
            size: int,
            solver: Solver,
            partop: bool = False
    ) -> 'Constant':
        assert size >= 1
        table = BitVec.variable(solver, size)
        if not partop:
            table.ensure_one()
        else:
            table.ensure_amo()
        return Constant(size, table)

    def solution(self) -> 'Constant':
        return Constant(self.size, self.table.solution())

    def decode(  # pyright: ignore[reportIncompatibleMethodOverride]
            self) -> Optional[int]:
        assert not self.table.solver

        for i in range(self.size):
            if self.table[i] == Solver.TRUE:
                return i
        return None

    def __repr__(self) -> str:
        return f"Constant({self.size}, {self.solution().decode()})"
