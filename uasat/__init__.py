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

"""
UASAT library making it easy to work with a SAT solver and solve problems
related to universal algebra.
"""

__version__ = "0.1.1"

from ._uasat import Solver, BitVec
from .operation import Operation, Constant
from .relation import Relation
from .algebra import Algebra, SmallAlg, ProductAlg

__all__ = [
    "Solver",
    "BitVec",
    "Relation",
    "Operation",
    "Constant",
    "Algebra",
    "SmallAlg",
    "ProductAlg",
]
