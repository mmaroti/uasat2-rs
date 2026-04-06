# Copyright (C) 2026, Miklos Maroti
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

from ._uasat import Solver
from .operation import Operation, Relation
from .clones import preserves, FunClone


class FunctionalCond:
    def create(self, size: int, solver: Solver) -> List[Operation]:
        raise NotImplementedError()


class MaltsevCond(FunctionalCond):
    def create(self, size: int, solver: Solver) -> List[Operation]:
        oper = Operation.variable(size, 3, solver)

        oper.polymer([0, 1, 1]).comp_eq(
            Operation.projection(size, 2, 0)).ensure_true()
        oper.polymer([0, 0, 1]).comp_eq(
            Operation.projection(size, 2, 1)).ensure_true()

        return [oper]


class MajorityCond(FunctionalCond):
    def create(self, size: int, solver: Solver) -> List[Operation]:
        oper = Operation.variable(size, 3, solver)

        oper.polymer([0, 0, 1]).comp_eq(
            Operation.projection(size, 2, 0)).ensure_true()
        oper.polymer([0, 1, 0]).comp_eq(
            Operation.projection(size, 2, 0)).ensure_true()
        oper.polymer([1, 0, 0]).comp_eq(
            Operation.projection(size, 2, 0)).ensure_true()

        return [oper]


class SiggersCond(FunctionalCond):
    def create(self, size: int, solver: Solver) -> List[Operation]:
        oper = Operation.variable(size, 4, solver)

        oper.polymer([0, 0, 0, 0]).comp_eq(
            Operation.projection(size, 1, 0)).ensure_true()
        oper.polymer([0, 1, 2, 0]).comp_eq(
            oper.polymer([1, 0, 1, 2])).ensure_true()

        return [oper]


class FindMinCond:
    """
    This class can be used to find a minimal functional clone among all clones
    satisfying a functional condition. The found clone will be below an initial
    functional clone. First, we approximnate this initial functional clone by
    adding relations, then make this functional condition as small as possible
    by adding further relations.
    """

    def __init__(self, size: int, condition: FunctionalCond,
                 initial: Optional[FunClone],
                 debug: bool = False):
        assert size >= 1 and (initial is None or initial.size == size)

        self.size = size
        self.condition = condition
        self.relations = []
        self.debug = debug

        if initial is None:
            solver = Solver()
            operations = self.condition.create(self.size, solver)
            if not solver.solve():
                raise ValueError("No solution found")
            self.operations = [o.solution() for o in operations]
        else:
            self.operations = initial.operations
            assert all(o.size == self.size for o in self.operations)

    def result(self) -> FunClone:
        return FunClone(self.size, self.operations)

    def add_relations(self, relations: List[Relation]):
        """
        Adds the given relations to the relational clone pushing down the
        minimal functional clone satisfying the functional condition.
        """
        for rel in relations:
            assert rel.size == self.size and not rel.solver
        self.relations.extend(relations)

        solver = Solver()
        operations = self.condition.create(self.size, solver)
        preserves(operations, self.relations).ensure_true()
        if not solver.solve():
            raise ValueError("No solution found")

        self.operations = [o.solution() for o in operations]

    def find_relation1(self, rel_arity: int) -> Optional[Relation]:
        """
        Finds a new relation that makes the relational clone closer to the
        already selected functional clone. If a new relation is found, then it
        is automatically added to the list of relations bounding the
        functional condition
        """

        solver = Solver()

        new_relation = Relation.variable(self.size, rel_arity, solver)
        sep_operations = self.condition.create(self.size, solver)

        preserves(self.operations, [new_relation]).ensure_true()
        preserves(sep_operations, self.relations).ensure_true()
        preserves(sep_operations, [new_relation]).ensure_false()

        if not solver.solve():
            return None

        new_relation = new_relation.solution()
        if self.debug:
            print(" ", new_relation)

        self.relations.append(new_relation)
        return new_relation

    def find_relation2(self, rel_arity: int) -> Optional[Relation]:
        """
        Finds a new relation that makes the functional condition smaller. If
        a new relation is found, then it is automatically added to the list of
        relations bounding the functional condition and the result is updated
        to the new functional condition.
        """

        solver = Solver()

        new_relation = Relation.variable(self.size, rel_arity, solver)
        new_operations = self.condition.create(self.size, solver)

        preserves(new_operations, self.relations).ensure_true()
        preserves(new_operations, [new_relation]).ensure_true()
        preserves(self.operations, [new_relation]).ensure_false()

        if not solver.solve():
            return None

        new_relation = new_relation.solution()
        if self.debug:
            print(" ", new_relation)

        self.operations = [o.solution() for o in new_operations]
        self.relations.append(new_relation)
        return new_relation

    def find_relations(self, max_rel_arity: int):
        """
        Adds all relations of up to max_rel_arity that can be repeatedly found
        using the find_relation method.
        """

        if self.debug:
            print("Initial relations:")
        for rel_arity in range(1, max_rel_arity + 1):
            while self.find_relation1(rel_arity):
                pass

        if self.debug:
            print("Minimizer relations:")
        for rel_arity in range(1, max_rel_arity + 1):
            while self.find_relation2(rel_arity):
                pass


class FindAllMinConds:
    """
    This class can be used to find all minimal functional clones among all clones
    satisfying a functional condition.
    """

    def __init__(self, size: int, condition: FunctionalCond,
                 debug: bool = False):
        assert size >= 1
        self.size = size
        self.condition = condition
        self.debug = debug
        self.fun_clones: List[FunClone] = []

    def add_clone(self, clone: FunClone):
        assert clone.size == self.size
        self.fun_clones.append(clone)

    def find_initial(self, rel_arity: int) -> Optional[FunClone]:
        """
        Finds an initial functional clone that is not above any of the already
        selected minimal clones.
        """

        solver = Solver()
        operations = self.condition.create(self.size, solver)

        relations: List[Relation] = []
        for clone in self.fun_clones:
            rel = Relation.variable(self.size, rel_arity, solver)
            preserves(clone.operations, [rel]).ensure_false()
            preserves(operations, [rel]).ensure_true()
            relations.append(rel)

        if not solver.solve():
            return None

        return FunClone(self.size, [o.solution() for o in operations])
