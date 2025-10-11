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
from . import operation


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

    @property
    def length(self):
        return len(self.table)

    @property
    def solver(self):
        return self.table.solver

    @staticmethod
    def new_diag(size: int, arity: int = 2) -> 'Relation':
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

    @staticmethod
    def new_full(size: int, arity: int) -> 'Relation':
        return Relation.new_const(size, arity, Solver.CALC, Solver.TRUE)

    @staticmethod
    def new_empty(size: int, arity: int) -> 'Relation':
        return Relation.new_const(size, arity, Solver.CALC, Solver.FALSE)

    @staticmethod
    def new_const(size: int, arity: int, solver: Solver, value: int) -> 'Relation':
        assert size >= 1 and arity >= 0

        length = size ** arity
        table = [value for _ in range(length)]
        return Relation(size, arity, BitVec(solver, table))

    @staticmethod
    def new_singleton(size: int, coord: List[int]) -> 'Relation':
        assert size >= 1

        length = size ** len(coord)
        table = [Solver.FALSE for _ in range(length)]

        pos = 0
        for c in reversed(coord):
            pos *= size
            pos += c
        table[pos] = Solver.TRUE

        return Relation(size, len(coord), BitVec(Solver.CALC, table))

    def polymer(self, new_vars: Sequence[int], new_arity: Optional[int] = None) -> 'Relation':
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

    def polymer_swap(self, var0: int, var1: int) -> 'Relation':
        assert 0 <= var0 < self.arity and 0 <= var1 < self.arity
        if var0 == var1:
            return self

        new_vars = list(range(self.arity))
        new_vars[var0] = var1
        new_vars[var1] = var0
        return self.polymer(new_vars, self.arity)

    def polymer_rotate(self, offset: int) -> 'Relation':
        if offset % self.arity == 0:
            return self
        new_vars = [(i + offset) % self.arity for i in range(self.arity)]
        return self.polymer(new_vars, self.arity)

    def polymer_insert(self, var: int) -> 'Relation':
        assert 0 <= var <= self.arity
        new_vars = [i if i < var else i + 1 for i in range(self.arity)]
        return self.polymer(new_vars, self.arity + 1)

    def fold_any(self, count: Optional[int] = None):
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

    def fold_all(self, count: Optional[int] = None):
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

    def fold_one(self, count: Optional[int] = None):
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

    def fold_amo(self, count: Optional[int] = None):
        if count is None:
            count = self.arity
        assert 0 <= count <= self.arity

        step = self.size ** count
        table = []
        for idx in range(0, self.length, step):
            part = self.table.slice(idx, idx + step)
            table.append(self.solver.fold_amo(part.literals))
        table = BitVec(self.solver, table)
        return Relation(self.size, self.arity - count, table)

    def solution(self) -> 'Relation':
        return Relation(self.size, self.arity, self.table.get_value())

    def decode(self) -> List[bool]:
        assert not self.solver
        return [self.table[i] == Solver.TRUE for i in range(self.length)]

    def __repr__(self) -> str:
        return f"Relation({self.size}, {self.arity}, {self.solution().decode()})"

    def comp_eq(self, other: 'Relation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_eq(other.table)

    def comp_ne(self, other: 'Relation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ne(other.table)

    def comp_le(self, other: 'Relation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_le(other.table)

    def comp_lt(self, other: 'Relation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_lt(other.table)

    def comp_ge(self, other: 'Relation') -> BitVec:
        assert self.size == other.size and self.arity == other.arity
        return self.table.comp_ge(other.table)

    def comp_gt(self, other: 'Relation') -> BitVec:
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
        """
        Returns TRUE (a single element BitVec) if this relation is reflexive.
        """
        diag = self.polymer([0 for _ in range(self.arity)])
        return diag.table.fold_all()

    def symmetric(self) -> BitVec:
        assert self.arity == 2
        return (~self | self.polymer([1, 0])).table.fold_all()

    def antisymm(self) -> BitVec:
        assert self.arity == 2
        rel = self & self.polymer([1, 0])
        rel = ~rel | Relation.new_diag(self.size, 2)
        return rel.table.fold_all()

    def compose(self, other: 'Relation') -> 'Relation':
        assert self.arity == other.arity == 2
        return (self.polymer([1, 0], 3) & self.polymer([0, 2], 3)).fold_any(1)

    def transitive(self) -> BitVec:
        assert self.arity == 2
        return (~self.compose(self) | self).table.fold_all()

    def product(self, other: 'Relation') -> 'Relation':
        assert other.size == self.size

        rel1 = self.polymer(range(self.arity), self.arity + other.arity)
        rel2 = other.polymer(range(self.arity, self.arity + other.arity),
                             self.arity + other.arity)
        return rel1 & rel2

    def evaluate(self, operations: List['Relation']) -> 'Relation':
        assert len(operations) == self.arity and self.arity >= 1
        oper_arity = operations[0].arity
        assert oper_arity >= 1
        assert all(oper.arity == oper_arity and oper.size == self.size
                   for oper in operations)

        if oper_arity == 1:
            return self._evaluate_n1(operations)
        elif self.arity == 1:
            return self._evaluate_1m(operations[0])
        elif oper_arity == 2:
            return self._evaluate_n2(operations)
        elif self.arity == 2:
            return self._evaluate_2m(operations[0], operations[1])
        elif oper_arity == 3:
            return self._evaluate_n3(operations)
        else:
            raise NotImplementedError()

    def _evaluate_n1(self, opers: List['Relation']) -> 'Relation':
        assert len(opers) == self.arity and self.arity >= 1
        assert all(oper.arity == 1 and oper.size == self.size
                   for oper in opers)
        rel = opers[0]
        for oper in opers[1:]:
            rel = rel.product(oper)
        return rel

    def _evaluate_1m(self, oper: 'Relation') -> 'Relation':
        assert self.arity == 1 and oper.arity >= 1
        oper = oper.polymer_rotate(-1)
        while oper.arity > 1:
            oper &= self.polymer([0], oper.arity)
            oper = oper.fold_any(1)
        return oper

    def _evaluate_n2(self, opers: List['Relation']) -> 'Relation':
        assert len(opers) == self.arity and self.arity >= 1
        assert all(oper.arity == 2 and oper.size == self.size
                   for oper in opers)
        rel = self
        for oper in opers:
            rel = rel.polymer_insert(0)
            rel &= oper.polymer([0, 1], rel.arity)
            rel = rel.polymer_rotate(-1)
            rel = rel.fold_any(1)
        return rel

    def _evaluate_2m(self, oper0: 'Relation', oper1: 'Relation') -> 'Relation':
        assert self.arity == 2 and oper0.arity == oper1.arity
        assert oper0.size == self.size and oper1.size == self.size
        rel = self.polymer([0, 1], oper0.arity + 1)
        test = oper0.polymer_rotate(-1)
        for _ in range(oper0.arity - 1):
            test = test.polymer_insert(1)
            test &= rel
            test = test.fold_any(1)
            test = test.polymer_rotate(-1)
        test = test.polymer_insert(1)
        test &= oper1.polymer_insert(0)
        test = test.polymer_rotate(-2)
        test = test.fold_any(oper0.arity - 1)
        return test

    def _evaluate_n3(self, opers: List['Relation']) -> 'Relation':
        assert len(opers) == self.arity and self.arity >= 1
        assert all(oper.arity == 3 and oper.size == self.size
                   for oper in opers)
        rel = self.polymer(range(0, 2 * self.arity, 2), 2 * self.arity)
        rel &= self.polymer(range(1, 2 * self.arity, 2), 2 * self.arity)
        for oper in opers:
            rel = rel.polymer_insert(0)
            rel &= oper.polymer([0, 1, 2], rel.arity)
            rel = rel.polymer_rotate(-1)
            rel = rel.fold_any(2)
        return rel

    def _evaluate_nm(self, opers: List['Relation']) -> 'Relation':
        assert len(opers) == self.arity and self.arity >= 1
        oper_arity = opers[0].arity
        assert oper_arity >= 1
        assert all(oper.arity == oper_arity and oper.size == self.size
                   for oper in opers)

        rel = Relation.new_full(self.size, self.arity * oper_arity)
        for idx, oper in enumerate(opers):
            rel &= oper.polymer(range(idx, rel.arity, self.arity), rel.arity)

        for idx in range(self.arity, rel.arity, self.arity):
            rel &= self.polymer(range(idx, idx + self.arity), rel.arity)

        rel = rel.polymer_rotate(-self.arity)
        rel = rel.fold_any(self.arity * (oper_arity - 1))
        assert rel.arity == self.arity
        return rel

    def closure(self, operation: 'operation.Operation') -> 'Relation':
        oper = operation.as_relation()
        return self.evaluate([oper for _ in range(self.arity)])

    def preserves(self, operation: 'operation.Operation') -> BitVec:
        rel = self.closure(operation)
        return (~rel | self).table.fold_all()
