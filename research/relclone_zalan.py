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

from uasat import Relation, Operation, Solver
from uasat.clones import FunClone, FindRelClone, MaximalClones
from uasat.critical_rels import CriticalRels
from uasat.conditions import MajorityCond, MaltsevCond, FindAllMinConds
from typing import List


def minimal_majority3():
    finder = FindAllMinConds(3, MajorityCond(), debug=False)
    finder.find_minimal_conditions(2)
    finder.print_result()

def minimal_maltsev2():
    finder = FindAllMinConds(2, MaltsevCond(), debug=False)
    finder.find_minimal_conditions(3)
    finder.print_result()

def minimal_maltsev3():
    finder = FindAllMinConds(3, MaltsevCond(), debug=False)
    finder.find_minimal_conditions(4)
    finder.print_result()


def maltsev2_relclone():
    minority = Operation(2, 3, [0, 1, 1, 0, 1, 0, 0, 1])

    find = FindRelClone(FunClone(2, [minority]))

    if True:
        find.find_relations(4, 4, "min", debug=True)
    else:
        find.add_relations([
            Relation(2, 1, [True, False]),
            Relation(2, 1, [False, True]),
            Relation(2, 2, [False, True, True, False]),
            Relation(2, 3, [True, False, False, True,
                     False, True, True, False]),
        ])


def majority2_relclone():
    majority = Operation(2, 3, [0, 0, 0, 1, 0, 1, 1, 1])

    find = FindRelClone(FunClone(2, [majority]))

    if True:
        find.find_relations(4, 4, "max", debug=True)
    else:
        find.add_relations([
            Relation(2, 1, [True, False]),
            Relation(2, 1, [False, True]),
            Relation(2, 2, [False, True, True, True]),
            Relation(2, 2, [True, False, True, True]),
            Relation(2, 2, [True, True, True, False]),
        ])


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

        relations.append(Relation.variable(self.size, 3, solver))
        # relations[-1].fold_amo(1).fold_all().ensure_true()

        return relations


def majority2_minimal():
    clones = MaximalMajority(2, 3, 3)
    while clones.find_maximal([]):
        pass


if __name__ == '__main__':
    # maltsev2_relclone()
    # majority2_relclone()
    # majority2_minimal()
    minimal_maltsev3()
