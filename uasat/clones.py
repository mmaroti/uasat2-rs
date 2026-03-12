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

from typing import List, Optional, Iterable

from ._uasat import Solver, BitVec
from .operation import Operation
from .relation import Relation


class FunClone:
    def __init__(self, size: int, operations: List[Operation]):
        for o in operations:
            assert o.size == size and not o.solver
        self.size = size
        self.operations = operations

    def __repr__(self) -> str:
        return f"FunClone({self.size}, {self.operations})"


class RelClone:
    def __init__(self, size: int, relations: List[Relation]):
        for r in relations:
            assert r.size == size and not r.solver
        self.size = size
        self.relations = relations

    def __repr__(self) -> str:
        return f"RelClone({self.size}, {self.relations})"


def preserves(operations: Iterable[Operation], relations: Iterable[Relation]) -> BitVec:
    t = BitVec(Solver.CALC, [Solver.TRUE])
    for o in operations:
        for r in relations:
            t &= o.preserves(r)
    return t


class FindRelClone:
    """
    This class can be used to find a relational clone approximation of
    a functional clone. The clone defined by the found relations will
    be above the starting functional clone and can be made as close to
    it as possible.
    """

    def __init__(self, fun_clone: FunClone):
        self.size = fun_clone.size
        self.operations = fun_clone.operations
        self.relations: List[Relation] = []

    def result(self) -> RelClone:
        return RelClone(self.size, self.relations)

    def add_relations(self, relations: List[Relation]):
        """
        Adds the given relations to the relational clone approximation.
        """
        for rel in relations:
            assert rel.size == self.size and not rel.solver
            preserves(self.operations, [rel]).ensure_true()
            self.relations.append(rel)

    def find_relation(self, rel_arity: int, fun_arity: int,
                      select: str = "any") -> Optional[Relation]:
        """
        Finds a new relation that makes the relational clone approximation
        closer to the functional clone. The arity of the new relation is
        specified and the fun_arity is used to find a separating operation
        that ensures that the new relation is indeed makes the relational
        clone closer. If the selection criteria is max or min, then among
        all possible relations we select a maximal or minimal one.
        """
        assert select in ("any", "max", "min")

        result = None
        while True:
            solver = Solver()

            new_relation = Relation.variable(self.size, rel_arity, solver)
            sep_operation = Operation.variable(self.size, fun_arity, solver)

            preserves(self.operations, [new_relation]).ensure_true()
            preserves([sep_operation], self.relations).ensure_true()
            preserves([sep_operation], [new_relation]).ensure_false()

            if select == "max" and result is not None:
                (~result | new_relation).ensure_all()
                (~result & new_relation).ensure_any()
            elif select == "min" and result is not None:
                (~new_relation | result).ensure_all()
                (~new_relation & result).ensure_any()

            if not solver.solve():
                return result

            result = new_relation.solution()
            if select == "any":
                return result

    def execute(self, max_rel_arity: int, fun_arity: int,
                select: str = "any",
                debug: bool = False):
        """
        Adds all relations of up to max_rel_arity that can be repeatedly found
        using the find_relation method.
        """
        for rel_arity in range(1, max_rel_arity + 1):
            while True:
                rel = self.find_relation(rel_arity, fun_arity, select)
                if rel is None:
                    break
                if debug:
                    print(rel)
                self.relations.append(rel)

    def __repr__(self) -> str:
        return f"FindRelClone({FunClone(self.size, self.operations)})"


class FindFunClone:
    """
    This class can be used to find a functional clone approximation of
    a relational clone. The clone defined by the found operations will
    be below the starting relational clone and can be made as close to
    it as possible.
    """

    def __init__(self, rel_clone: RelClone):
        self.size = rel_clone.size
        self.relations = rel_clone.relations
        self.operations: List[Operation] = []

    def result(self) -> FunClone:
        return FunClone(self.size, self.operations)

    def add_operations(self, operations: List[Operation]):
        """
        Adds the given operations to the fun functional clone approximation.
        """
        for oper in operations:
            assert oper.size == self.size and not oper.solver
            preserves([oper], self.relations).ensure_true()
            self.operations.append(oper)

    def find_operation(self, fun_arity: int, rel_arity: int,
                       select: str = "any") -> Optional[Operation]:
        """
        Finds a new operation that makes the functional clone approximation
        closer to the relational clone. The arity of the new operation is
        specified and the rel_arity is used to find a separating relation
        that ensures that the new operation is indeed makes the functional
        clone closer. If the selection criteria is max or min, then among
        all possible separating relations we select a maximal or minimal one.
        """
        assert select in ("any", "max", "min")

        result_fun = None
        result_rel = None
        while True:
            solver = Solver()

            new_funtion = Operation.variable(self.size, fun_arity, solver)
            sep_relation = Relation.variable(self.size, rel_arity, solver)

            preserves([new_funtion], self.relations).ensure_true()
            preserves(self.operations, [sep_relation]).ensure_true()
            preserves([new_funtion], [sep_relation]).ensure_false()

            if not solver.solve():
                return result_fun

            if select == "max" and result_rel is not None:
                (~result_rel | sep_relation).ensure_all()
                (~result_rel & sep_relation).ensure_any()
            elif select == "min" and result_rel is not None:
                (~sep_relation | result_rel).ensure_all()
                (~sep_relation & result_rel).ensure_any()

            result_fun = new_funtion.solution()
            if select == "any":
                return result_fun
            result_rel = sep_relation.solution()

    def execute(self, max_fun_arity: int, rel_arity: int,
                select: str = "any",
                debug: bool = False):
        """
        Adds all relations of up to max_rel_arity that can be repeatedly found
        using the find_relation method.
        """
        for fun_arity in range(1, max_fun_arity + 1):
            while True:
                fun = self.find_operation(fun_arity, rel_arity, select)
                if fun is None:
                    break
                if debug:
                    print(fun)
                self.operations.append(fun)

    def __repr__(self) -> str:
        return f"FindFunClone({RelClone(self.size, self.relations)})"


class Clone:
    def __init__(self, operations: List[Operation], relations: List[Relation]):
        self.operations = operations
        self.relations = relations

    def __repr__(self) -> str:
        return f"Clone({self.operations}, {self.relations})"


class MinimalClones:
    def __init__(self, size: int,
                 max_relation_arity: int):
        self.size = size
        self.max_relation_arity = max_relation_arity
        self.minimal_clones: List[Clone] = []

    def maltsev_condition(self, solver: Solver) -> List[Operation]:
        raise NotImplementedError()

    def find_minimal(self, relations: List[Relation],
                     avoid_existing: bool = True) -> Optional[Clone]:
        """
        Finds a quasi-minimal clone generated by the maltsev condition
        operations, which is below the polymorphism clone of the given list
        of input relations. The input relations are extended up to the
        maximum relation arity to make this clone as minimal as possible.
        If avoid_existing is true, then the set of relations is extended
        first to avoid all existing minimal clones. If avoid_existing is
        false, then the caller must guarantee that none of the existing
        minimal clones are below the polymorphism clone of the input
        relations.
        """
        relations = list(relations)

        solver = Solver()
        operations = self.maltsev_condition(solver)
        preserves(operations, relations).ensure_true()

        new_relations: List[Relation] = []
        if avoid_existing:
            for c in self.minimal_clones:
                if not preserves(c.operations, relations).value():
                    continue

                new_relation = Relation.variable(
                    self.size, self.max_relation_arity, solver)
                new_relations.append(new_relation)

                preserves(operations, [new_relation]).ensure_true()
                preserves(c.operations, [new_relation]).ensure_false()

        if not solver.solve():
            return None

        operations = [o.solution() for o in operations]
        relations.extend([r.solution() for r in new_relations])

        for relation_arity in range(1, self.max_relation_arity + 1):
            while True:
                solver = Solver()
                new_operations = self.maltsev_condition(solver)
                preserves(new_operations, relations).ensure_true()

                new_relation = Relation.variable(
                    self.size, relation_arity, solver)
                preserves(new_operations, [new_relation]).ensure_true()
                preserves(operations, [new_relation]).ensure_false()

                if not solver.solve():
                    break

                operations = [o.solution() for o in new_operations]
                relations.append(new_relation.solution())

        clone = Clone(operations, relations)
        print("Adding minimal clone", clone)
        self.minimal_clones.append(clone)
        return clone

    def avoid_minimal(self, relations: List[Relation]) -> Optional[Clone]:
        """
        Extends the list of relations with extra ones such that the clone of
        its polymorphisms is not above any of the existing quasi-minimal clone.
        """
        relations = list(relations)

        solver = Solver()
        operations = self.maltsev_condition(solver)
        preserves(operations, relations).ensure_true()

        if not solver.solve():
            return None

        operations = [o.solution() for o in operations]

        for relation_arity in range(1, self.max_relation_arity + 1):
            while True:
                solver = Solver()
                new_operations = self.maltsev_condition(solver)
                preserves(new_operations, relations).ensure_true()

                new_relation = Relation.variable(
                    self.size, relation_arity, solver)
                preserves(new_operations, [new_relation]).ensure_true()
                preserves(operations, [new_relation]).ensure_false()

                if not solver.solve():
                    break

                operations = [o.solution() for o in new_operations]
                relations.append(new_relation.solution())

        clone = Clone(operations, relations)
        print("Adding minimal clone", clone)
        self.minimal_clones.append(clone)
        return clone


class MaximalClones(MinimalClones):
    def __init__(self, size: int,
                 max_relation_arity: int,
                 max_operation_arity: int):
        MinimalClones.__init__(self, size, max_relation_arity)
        self.max_operation_arity = max_operation_arity
        self.maximal_clones: List[Clone] = []

    def relation_condition(self, solver: Solver) -> List[Relation]:
        raise NotImplementedError()

    def find_maximal(self, operations: List[Operation],
                     avoid_existing: bool = True) -> Optional[Clone]:
        """
        Finds a quasi-maximal clone given by the polimorphism clone of a
        relation condition, which is not above any of the quasi-minimal
        clones and it is above the clone generated by the given list of input
        operations. The input operations are extended up to the maximum
        operation arity to make this polimorphism clone as maximal as possible.
        If avoid_existing is true, then the set of operations is extended
        first to avoid all existing maximal clones. If avoid_existing is
        false, then the caller must guarantee that none of the existing
        maximal clones are above the clone generated by the input operations.
        """
        operations = list(operations)

        while True:
            solver = Solver()

            relations = self.relation_condition(solver)
            preserves(operations, relations).ensure_true()

            for c in self.minimal_clones:
                preserves(c.operations, relations).ensure_false()

            new_operations = []
            if avoid_existing:
                for c in self.maximal_clones:
                    if not preserves(operations, c.relations).value():
                        continue

                    new_operation = Operation.variable(
                        self.size, self.max_operation_arity, solver)
                    new_operations.append(new_operation)

                    preserves([new_operation], relations).ensure_true()
                    preserves([new_operation], c.relations).ensure_false()

            if not solver.solve():
                return None

            relations = [r.solution() for r in relations]

            clone = self.find_minimal(relations, avoid_existing=False)
            if clone is None:
                operations.extend([o.solution() for o in new_operations])
                break

        for operation_arity in range(1, self.max_operation_arity + 1):
            while True:
                solver = Solver()

                new_relations = self.relation_condition(solver)
                preserves(operations, new_relations).ensure_true()

                for c in self.minimal_clones:
                    preserves(c.operations, new_relations).ensure_false()

                new_operation = Operation.variable(
                    self.size, operation_arity, solver)

                preserves([new_operation], new_relations).ensure_true()
                preserves([new_operation], relations).ensure_false()

                if not solver.solve():
                    break

                new_relations = [r.solution() for r in new_relations]
                new_operation = new_operation.solution()

                clone = self.find_minimal(new_relations, avoid_existing=False)

                if clone is None:
                    print("Adding new lower operation", new_operation)
                    relations = new_relations
                    operations.append(new_operation)

        clone = Clone(operations, relations)
        print("Adding maximal clone", clone)
        self.maximal_clones.append(clone)
        return clone
