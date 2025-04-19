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


class Solver(object):
    """
    The CaDiCaL incremental SAT solver. The literals are unwrapped positive
    and negative integers, exactly as in the DIMACS format.
    """

    def __init__(): ...

    def add_clause(self, literals: List[int]) -> None:
        """
        Adds the given clause to the solver. Negated literals are negative
        integers, positive literals are positive ones. All literals must be
        non-zero.
        """
