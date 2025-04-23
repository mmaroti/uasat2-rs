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


class Solver(object):
    """
    The CaDiCaL incremental SAT solver. The literals are unwrapped positive
    and negative integers, exactly as in the DIMACS format.

    Attributes:
        TRUE: The always true literal.
        FALSE: The always false literal.
    """

    def __init__(self):
        """
        Constructs a new solver instance. The literal 1 is always added
        by default to the solver and serves as the true value.
        """

    @staticmethod
    def with_config(config: str) -> Solver:
        """
        Constructs a new solver with one of the following pre-defined
        configurations of advanced internal options:
        * `default`: set default advanced internal options
        * `plain`: disable all internal preprocessing options
        * `sat`: set internal options to target satisfiable instances
        * `unsat`: set internal options to target unsatisfiable instances
        """

    def signature(self) -> str:
        """
        Returns the name and version of the CaDiCaL library.
        """

    def add_variable(self) -> int:
        """
        Adds a new variable to the solver and returns the corresponding
        literal as an integer.
        """

    def num_variables(self) -> int:
        """
        Returns the number of variables in the solver.
        """

    def add_clause(self, clause: List[int]):
        """
        Adds the given clause to the solver. Negated literals are negative
        integers, positive literals are positive ones. All literals must be
        non-zero.
        """

    def add_clause1(self, lit0: int):
        """
        Adds the unary clause to the solver.
        """

    def add_clause2(self, lit0: int, lit1: int):
        """
        Adds the binary clause to the solver.
        """

    def add_clause3(self, lit0: int, lit1: int, lit2: int):
        """
        Adds the ternary clause to the solver.
        """

    def add_clause4(self, lit0: int, lit1: int, lit2: int, lit3: int):
        """
        Adds the quaternary clause to the solver.
        """

    def num_clauses(self) -> int:
        """
        Returns the number of clauses in the solver.
        """

    def solve(self) -> Optional[bool]:
        """
        Solves the formula defined by the added clauses. If the formula is
        satisfiable, then `True` is returned. If the formula is
        unsatisfiable, then `False` is returned. If the solver runs out
        of resources or was terminated, then `None` is returned.
        """

    def solve_with(self, assumptions: List[int]) -> Optional[bool]:
        """
        Solves the formula defined by the set of clauses under the given
        assumptions.
        """

    def get_value(self, lit: int) -> Optional[bool]:
        """
        Returns the value of the given literal in the last solution. The
        state of the solver must be `True`. The returned value is
        `None` if the formula is satisfied regardless of the value of the
        literal.
        """

    TRUE: int
    FALSE: int

    @staticmethod
    def bool_not(lit: int) -> int:
        """
        Returns the negated literal.
        """

    @staticmethod
    def bool_lift(val: bool) -> int:
        """
        Returns the always true or false literal.
        """

    def bool_or(self, lit0: int, lit1: int) -> int:
        """
        Returns the disjunction of a pair of elements.
        """

    def bool_and(self, lit0: int, lit1: int) -> int:
        """
        Computes the disjunction of the elements.
        """

    def bool_imp(self, lit0: int, lit1: int) -> int:
        """
        Returns the logical implication of a pair of elements.
        """

    def bool_xor(self, lit0: int, lit1: int) -> int:
        """
        Returns the exclusive or of a pair of elements.
        """

    def bool_equ(self, lit0: int, lit1: int) -> int:
        """
        Returns the logical equivalence of a pair of elements.
        """

    def fold_all(self, lits: List[int]) -> int:
        """
        Computes the conjunction of the elements.
        """

    def fold_any(self, lits: List[int]) -> int:
        """
        Computes the disjunction of the elements.
        """

    def fold_one(self, lits: List[int]) -> int:
        """
        Computes the exactly one predicate over the given elements.
        """

    def fold_amo(self, lits: List[int]) -> int:
        """
        Computes the at most one predicate over the given elements.
        """

    def comp_equ(self, lits0: List[int], lits1: List[int]) -> int:
        """
        Returns true if the two sequences are equal.
        """

    def comp_neq(self, lits0: List[int], lits1: List[int]) -> int:
        """
        Returns true if the two sequences are not equal.
        """
