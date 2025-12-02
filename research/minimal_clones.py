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

from uasat import Solver, BitVec, Relation, Operation


class Clone:
    def __init__(self, operations: List[Operation], relations: List[Relation]):
        self.operations = operations
        self.relations = relations

    def __repr__(self) -> str:
        return f"Clone({self.operations}, {self.relations})"


def preserves(operations: List[Operation], relations: List[Relation]) -> BitVec:
    t = BitVec(Solver.CALC, [Solver.TRUE])
    for o in operations:
        for r in relations:
            t &= o.preserves(r)
    return t


class MinimalClones:
    def __init__(self, size: int,
                 max_relation_arity: int,
                 max_operation_arity: int):
        self.size = size
        self.max_relation_arity = max_relation_arity
        self.max_operation_arity = max_operation_arity
        self.clones: List[Clone] = []

    def condition(self, solver: Solver) -> List[Operation]:
        raise NotImplementedError()

    def find_initial(self) -> Optional[Clone]:
        solver = Solver()
        operations = self.condition(solver)

        relations: List[Relation] = []
        for c in self.clones:
            r = Relation.variable(self.size, self.max_relation_arity, solver)
            relations.append(r)

            preserves(operations, [r]).ensure_true()
            preserves(c.operations, [r]).ensure_false()

        if not solver.solve():
            return None

        print(f"Found {len(relations)} initial relations")
        return Clone(
            [o.solution() for o in operations],
            [r.solution() for r in relations])

    def prune_initial(self,
                      initial: List[Optional[Relation]],
                      relation: Relation):
        assert len(initial) == len(self.clones)

        for i, r in enumerate(initial):
            if r is not None and not preserves(self.clones[i].operations, [relation]).value():
                initial[i] = None

    def find_next_rel(self,
                      initial: List[Optional[Relation]],
                      relations: List[Relation],
                      relation_arity: int,
                      operation_arity: int) -> Optional[Clone]:

        solver = Solver()
        operations = self.condition(solver)

        next_relation = Relation.variable(self.size, relation_arity, solver)
        separator = Operation.variable(self.size, operation_arity, solver)

        preserves(operations, relations).ensure_true()
        preserves(operations, [next_relation]).ensure_true()

        for r in initial:
            if r is not None:
                preserves(operations, [r]).ensure_true()

        preserves([separator], relations).ensure_true()
        preserves([separator], [next_relation]).ensure_false()

        if not solver.solve():
            return None

        print(f"Found next relation of arity {relation_arity}")
        next_relation = next_relation.solution()
        self.prune_initial(initial, next_relation)

        return Clone([o.solution() for o in operations],
                     relations + [next_relation])

    def find_minimal(self) -> Optional[Clone]:
        clone = self.find_initial()
        if clone is None:
            print("No more minimal clone found")
            return None

        initial: List[Optional[Relation]] = list(clone.relations)
        clone = Clone(clone.operations, [])

        for relation_arity in range(1, self.max_relation_arity + 1):
            for operation_arity in range(1, self.max_operation_arity + 1):
                while True:
                    next = self.find_next_rel(
                        initial, clone.relations, relation_arity, operation_arity)
                    if next is None:
                        break
                    clone = next

        print("Found new minimal clone:")
        print(clone)
        self.clones.append(clone)
        return clone


class MinimalMaltsev(MinimalClones):
    def __init__(self, size: int,
                 max_relation_arity: int,
                 max_operation_arity: int):
        MinimalClones.__init__(self, size,
                               max_relation_arity,
                               max_operation_arity)

    def condition(self, solver: Solver) -> List[Operation]:
        oper = Operation.variable(self.size, 3, solver)

        oper.polymer([0, 1, 1]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()
        oper.polymer([0, 0, 1]).comp_eq(
            Operation.projection(self.size, 2, 1)).ensure_true()

        return [oper]


class MinimalGumm1(MinimalClones):
    def __init__(self, size: int,
                 max_relation_arity: int,
                 max_operation_arity: int):
        MinimalClones.__init__(self, size,
                               max_relation_arity,
                               max_operation_arity)

    def condition(self, solver: Solver) -> List[Operation]:
        oper1 = Operation.variable(self.size, 3, solver)
        oper2 = Operation.variable(self.size, 3, solver)

        oper1.polymer([0, 0, 1]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()
        oper1.polymer([0, 1, 0]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()
        oper1.polymer([0, 1, 1]).comp_eq(
            oper2.polymer([0, 1, 1])).ensure_true()
        oper2.polymer([0, 0, 1]).comp_eq(
            Operation.projection(self.size, 2, 1)).ensure_true()

        return [oper1, oper2]


if __name__ == '__main__':
    clones = MinimalMaltsev(3, 3, 3)
    while clones.find_minimal() is not None:
        pass
