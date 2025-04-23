/*
* Copyright (C) 2019-2025, Miklos Maroti
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

use pyo3::exceptions::PyIndexError;
use pyo3::prelude::*;

use super::PySolver;

#[pyclass(frozen, sequence, name = "BitVec")]
pub struct PyBitVec {
    solver: Option<Py<PySolver>>,
    literals: Box<[i32]>,
}

#[pymethods]
impl PyBitVec {
    /// Creates a new bit vector with the associated solver and literals.
    #[new]
    pub fn new<'py>(
        py: Python<'py>,
        solver: Option<Py<PySolver>>,
        literals: Vec<i32>,
    ) -> PyResult<Py<PyBitVec>> {
        let literals = literals.into_boxed_slice();
        Py::new(py, PyBitVec { solver, literals })
    }

    /// Returns the associated solver for this bit vector. If the solver is
    /// `None``, then all literals are `TRUE`` or `FALSE``. Otherwise, the
    /// elements are literals of the solver and their value is not yet known.
    #[getter]
    pub fn get_solver<'py>(me: &Bound<'py, Self>) -> Option<Py<PySolver>> {
        me.get().solver.as_ref().map(|x| x.clone_ref(me.py()))
    }

    pub fn __len__(&self) -> usize {
        self.literals.len()
    }

    pub fn __getitem__(&self, index: usize) -> PyResult<i32> {
        if index >= self.literals.len() {
            Err(PyIndexError::new_err("index out of range"))
        } else {
            Ok(self.literals[index])
        }
    }
}
