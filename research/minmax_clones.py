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

from typing import List

from uasat import Solver, Relation, Operation
from uasat.clones import MaximalClones


class MaximalMaltsev(MaximalClones):
    def __init__(self, size: int,
                 max_relation_arity: int,
                 max_operation_arity: int,
                 relation_method: str,
                 ):
        MaximalClones.__init__(self, size,
                               max_relation_arity,
                               max_operation_arity)
        self.relation_method = relation_method

    def maltsev_condition(self, solver: Solver) -> List[Operation]:
        oper = Operation.variable(self.size, 3, solver)

        oper.polymer([0, 1, 1]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()
        oper.polymer([0, 0, 1]).comp_eq(
            Operation.projection(self.size, 2, 1)).ensure_true()

        return [oper]

    def singletons(self) -> List[Relation]:
        return [Relation.singleton(self.size, [i]) for i in range(self.size)]

    def relation_condition(self, solver: Solver) -> List[Relation]:
        relations = self.singletons()

        if self.relation_method == "rel_2":
            relations.append(Relation.variable(self.size, 2, solver))
        elif self.relation_method == "rel_22":
            relations.append(Relation.variable(self.size, 2, solver))
            relations.append(Relation.variable(self.size, 2, solver))
        elif self.relation_method == "rel_3":
            relations.append(Relation.variable(self.size, 3, solver))
        elif self.relation_method == "rel_33":
            relations.append(Relation.variable(self.size, 3, solver))
            relations.append(Relation.variable(self.size, 3, solver))
        elif self.relation_method == "refl_2":
            relations.append(Relation.variable(self.size, 2, solver))
            relations[-1].reflexive().ensure_true()
        elif self.relation_method == "refl_3":
            relations.append(Relation.variable(self.size, 3, solver))
            relations[-1].reflexive().ensure_true()
        elif self.relation_method == "part_2":
            relations.append(Relation.variable(self.size, 2, solver))
            relations[-1].fold_amo(1).fold_all().ensure_true()
        elif self.relation_method == "part_3":
            relations.append(Relation.variable(self.size, 3, solver))
            relations[-1].fold_amo(1).fold_all().ensure_true()
        else:
            raise ValueError("Unknown relation method")

        return relations


def test_minimal_maltsev_2():
    clones = MaximalMaltsev(2, 3, 3, "rel_3")
    while clones.find_minimal([]):
        pass


def test_maximal_maltsev_2():
    clones = MaximalMaltsev(2, 3, 3, "rel_3")
    while clones.find_maximal([]):
        pass


def test_maximal_maltsev_3():
    clones = MaximalMaltsev(3, 3, 4, "refl_2")
    while clones.find_maximal([]):
        pass


class MaximalMajority(MaximalClones):
    def __init__(self, size: int, max_relation_arity, max_operation_arity):
        MaximalClones.__init__(
            self, size, max_relation_arity, max_operation_arity)

    def maltsev_condition(self, solver: Solver) -> List[Operation]:
        oper = Operation.variable(self.size, 3, solver)

        oper.polymer([1, 0, 0]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()
        oper.polymer([0, 1, 0]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()
        oper.polymer([0, 0, 1]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()

        return [oper]

    def relation_condition(self, solver: Solver) -> List[Relation]:
        relations = []

        for i in range(self.size):
            relations.append(Relation.singleton(self.size, [i]))

        for i in range(self.size - 1):
            for j in range(i + 1, self.size):
                relations.append(Relation.tuples(self.size, 1, [(i,), (j,)]))

        relations.append(Relation.variable(self.size, 3, solver))
        # relations[-1].fold_amo(1).fold_all().ensure_true()

        return relations


def test_maximal_majority():
    clones = MaximalMajority(3, 2, 3)
    while clones.find_maximal([]):
        pass


if __name__ == '__main__':
    test_maximal_maltsev_3()
