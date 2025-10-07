/*
* Copyright (C) 2025, Miklos Maroti
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

mod solver;
pub use solver::*;

mod bitvec;
pub use bitvec::*;

use pyo3::prelude::*;

/// The uasat module implemented in Rust.
#[pymodule]
#[pyo3(name = "_uasat")]
fn uasat(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySolver>()?;
    m.add_class::<PyBitVec>()?;
    Ok(())
}
