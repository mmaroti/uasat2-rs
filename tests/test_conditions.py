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

from uasat import FunClone
from uasat.conditions import MajorityCond, FindMinCond, FindAllMinConds


def test_majority():
    finder1 = FindAllMinConds(3, MajorityCond(), debug=True)

    while True:
        clone = finder1.find_initial(2)
        if clone is None:
            break

        print("Initial clone:", clone)

        finder2 = FindMinCond(3, MajorityCond(), clone, debug=True)
        finder2.find_relations(2)

        clone = finder2.result()
        print("Minimal clone:", clone)

        finder1.add_clone(clone)


if __name__ == '__main__':
    test_majority()
