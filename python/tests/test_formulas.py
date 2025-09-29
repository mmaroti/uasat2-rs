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

from uasat.formulas import Domain, Relation


def test_formulas():
    dom = Domain("dom", 3)
    rel = Relation("rel", [dom, dom])
    frm = dom.forall(lambda x, y, z: ~rel(x, y) | ~rel(y, z) | rel(x, z))
    print(frm)
    print(rel.functional())
    print(rel.existential())


if __name__ == '__main__':
    test_formulas()
