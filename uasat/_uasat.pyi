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

from typing import List, Iterable, Optional


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

    @property
    def signature(self) -> str:
        """
        Returns the name and version of the CaDiCaL library.
        """

    CALC: Solver
    """
    A static calculator instance that supports all the standard boolean
    operations but does not allow any SAT solving.
    """  # pylint: disable=W0105

    def __bool__(self) -> bool:
        """
        Retruns TRUE if this is a real solver instance, and FALSE
        if this is just the calculator instance.
        """

    def __or__(self, other: Solver) -> Solver:
        """
        Returns a pointer to either this or the other solver, whichever is
        not the static calculator instance. If neither is and they are
        different then an error is returned.
        """

    def add_variable(self, count: int = 1) -> int:
        """
        Adds a new variable to the solver and returns the corresponding
        literal as an integer. If more than one is requested, then the
        first literal is returned and the rest are consecutive numbers.
        """

    @property
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

    @property
    def num_clauses(self) -> int:
        """
        Returns the number of clauses in the solver.
        """

    def solve(self) -> bool:
        """
        Solves the formula defined by the added clauses. If the formula is
        satisfiable, then `True` is returned. If the formula is
        unsatisfiable, then `False` is returned. If the solver runs out
        of resources or was terminated, then an error is raised.
        """

    def solve_with(self, assumptions: List[int]) -> bool:
        """
        Solves the formula defined by the set of clauses under the given
        assumptions.
        """

    @property
    def status(self) -> Optional[bool]:
        """
        Returns the status of the solver, which is NONE if the instance
        has not been solved, TRUE if a solution was found, and FALSE if
        there is no solution. This is the same value as you get as the
        return value of the solve method.
        """

    def get_value(self, lit: int) -> Optional[bool]:
        """
        Returns the value of the given literal in the last solution. The
        status of the solver must be `True`. The returned value is
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

    def bool_maj(self, lit0: int, lit1: int, lit2: int) -> int:
        """
        Returns the majority of three elements.
        """

    def bool_iff(self, lit0: int, lit1: int, lit2: int) -> int:
        """
        Returns 'lit1' if 'lit0' is true, otherwise 'lit2' is returned.
        """

    def fold_all(self, lits: Iterable[int]) -> int:
        """
        Computes the conjunction of the elements.
        """

    def fold_any(self, lits: Iterable[int]) -> int:
        """
        Computes the disjunction of the elements.
        """

    def fold_one(self, lits: Iterable[int]) -> int:
        """
        Computes the exactly one predicate over the given elements.
        """

    def fold_amo(self, lits: Iterable[int]) -> int:
        """
        Computes the at most one predicate over the given elements.
        """

    def comp_eq(self, lits0: Iterable[int], lits1: Iterable[int]) -> int:
        """
        Returns true if the two sequences are equal.
        """

    def comp_ne(self, lits0: Iterable[int], lits1: Iterable[int]) -> int:
        """
        Returns true if the two sequences are not equal.
        """

    def comp_le(self, lits0: Iterable[int], lits1: Iterable[int]) -> int:
        """
        Returns true if the first sequence is smaller than or equal to the
        second one as a binary number when the least significant digit is
        the first one. So [TRUE, FALSE] = 1 is smaller than [FALSE, TRUE] = 2.
        The two sequences must have the same length.
        """

    def comp_lt(self, lits0: Iterable[int], lits1: Iterable[int]) -> int:
        """
        Returns true if the first sequence is smaller than the second one
        as a binary number hen the least significant digit is the first one.
        The two sequences must have the same length.
        """

    def comp_ge(self, lits0: Iterable[int], lits1: Iterable[int]) -> int:
        """
        Returns true if the first sequence is greater than or equal to the
        second one as a binary number when the least significant digit is
        the first one. The two sequences must have the same length.
        """

    def comp_gt(self, lits0: Iterable[int], lits1: Iterable[int]) -> int:
        """
        Returns true if the first sequence is greater than the second one
        as a binary number hen the least significant digit is the first one.
        The two sequences must have the same length.
        """


class BitVec(object):
    """
    A vector of literals of a solver. If the solver is None, then all literals
    are either TRUE or FALSE. Otherwise, the value of the literals are not yet
    known.
    """

    def __init__(self, solver: Solver, literals: List[int]):
        """
        Constructs a new bit vector instance. If the solver is the calculator,
        then all literals must be either TRUE or FALSE.
        """

    @staticmethod
    def variable(solver: Solver, length: int) -> BitVec:
        """
        Constructs a new bit vector of length length filled with fresh
        new literals from the solver.
        """

    @property
    def solver(self) -> Solver:
        """
        Returns the solver whose literals this vector contains. If the solver
        is None, then all literals are either TRUE or FALSE.
        """

    @property
    def literals(self) -> List[int]:
        """
        Returns a copy of this vector as a python list. Generally you should
        not use this method as you can index and use this class as a regular
        list.
        """

    def __len__(self) -> int:
        """
        Returns the length of the vector.
        """

    def __getitem__(self, index: int) -> int:
        """
        Returns the given literal in this vector.
        """

    def slice(self, start: int, stop: int, step: int = 1) -> BitVec:
        """
        Returns a subslice of this vector.
        """

    def __repr__(self) -> str:
        """
        Returns the list of literals as a string.
        """

    def solution(self) -> BitVec:
        """
        When this bit vector is backed by a solver and there exists a solution,
        then this method returns the value of these literals in the solution.
        """

    def __invert__(self) -> BitVec:
        """
        Negates all literals of this vector.
        """

    def __and__(self, other: BitVec) -> BitVec:
        """
        Returns the element wise logical and of this vector and another one
        of the same length.
        """

    def __or__(self, other: BitVec) -> BitVec:
        """
        Returns the element wise logical or of this vector and another one
        of the same length.
        """

    def __xor__(self, other: BitVec) -> BitVec:
        """
        Returns the element wise logical xor of this vector and another one
        of the same length.
        """

    def comp_eq(self, other: BitVec) -> BitVec:
        """
        Compares this vector with another one of the same length and returns
        TRUE in a single element vector if the two are equal.
        """

    def comp_ne(self, other: BitVec) -> BitVec:
        """
        Compares this vector with another one of the same length and returns
        TRUE in a single element vector if the two are not equal.
        """

    def comp_le(self, other: BitVec) -> BitVec:
        """
        Compares this vector with another one of the same length and returns
        TRUE in a single element vector if the first is less than or equal
        to the other one as seen as a binary number in little endian order.
        """

    def comp_lt(self, other: BitVec) -> BitVec:
        """
        Compares this vector with another one of the same length and returns
        TRUE in a single element vector if the first is less than the other
        one as seen as a binary number in little endian order.
        """

    def comp_ge(self, other: BitVec) -> BitVec:
        """
        Compares this vector with another one of the same length and returns
        TRUE in a single element vector if the first is greater than or equal
        to the other one as seen as a binary number in little endian order.
        """

    def comp_gt(self, other: BitVec) -> BitVec:
        """
        Compares this vector with another one of the same length and returns
        TRUE in a single element vector if the first is greater than the other
        one as seen as a binary number in little endian order.
        """

    def fold_all(self) -> BitVec:
        """
        Computes the conjunction of the elements and returns a single element
        vector.
        """

    def fold_any(self) -> BitVec:
        """
        Computes the disjunction of the elements and returns a single element
        vector.
        """

    def fold_one(self) -> BitVec:
        """
        Computes the exactly one predicate over the given elements and returns
        a single element vector.
        """

    def fold_amo(self) -> BitVec:
        """
        Computes the at most one predicate over the given elements and returns
        a single element vector.
        """

    def ensure_all(self):
        """
        Makes sure that all literal in this bit vector is true. If this is a
        solver instance, then all literals are forced true with a new clause.
        If this is a calculator instance, then an assertion error is thrown
        if not all literals are true.
        """

    def ensure_any(self):
        """
        Makes sure that at least one literal in this bit vector is true. If
        this is a solver instance, then a single clause is added to the solver.
        If this is a calculator instance, then an assertion error is thrown
        if all literals are false.
        """

    def ensure_one(self):
        """
        Makes sure that exactly one literal in this bit vector is true. If
        this is a solver instance, then a single clause is added to the solver.
        If this is a calculator instance, then an assertion error is thrown
        if all literals are false.
        """

    def ensure_amo(self):
        """
        Makes sure that at most one literal in this bit vector is true. If
        this is a solver instance, then a single clause is added to the solver.
        If this is a calculator instance, then an assertion error is thrown
        if all literals are false.
        """
