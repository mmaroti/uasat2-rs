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

use pyo3::exceptions::{PyIndexError, PyValueError};
use pyo3::prelude::*;

use super::PySolver;
use std::fmt::Write;

#[pyclass(frozen, sequence, name = "BitVec")]
pub struct PyBitVec {
    solver: Py<PySolver>,
    literals: Box<[i32]>,
}

#[pymethods]
impl PyBitVec {
    /// Creates a new bit vector with the associated solver and literals.
    #[new]
    pub fn new(solver: Py<PySolver>, literals: Vec<i32>) -> PyResult<Self> {
        if !solver.get().__bool__() {
            for &a in literals.iter() {
                if a != PySolver::TRUE && a != PySolver::FALSE {
                    return Err(PyValueError::new_err("invalid literal"));
                }
            }
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    /// Returns the associated solver for this bit vector. If the solver is
    /// `None``, then all literals are `TRUE`` or `FALSE``. Otherwise, the
    /// elements are literals of the solver and their value is not yet known.
    #[getter]
    pub fn get_solver(me: &Bound<'_, Self>) -> Py<PySolver> {
        me.get().solver.clone_ref(me.py())
    }

    /// Returns a copy of the list of literals.
    #[getter]
    pub fn get_literals(&self) -> Vec<i32> {
        self.literals.to_vec()
    }

    pub fn __repr__(&self) -> String {
        let mut res: String = "[".into();
        let mut iter = self.literals.iter();
        if let Some(a) = iter.next() {
            write!(&mut res, "{}", a).unwrap();
            for a in iter {
                write!(&mut res, ", {}", a).unwrap();
            }
        }
        write!(&mut res, "]").unwrap();
        res
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

    pub fn slice(me: &Bound<'_, Self>, start: usize, length: usize) -> PyResult<Self> {
        let literals = &me.get().literals;
        if start + length > literals.len() {
            Err(PyIndexError::new_err("invalid slice indices"))
        } else {
            let solver = me.get().solver.clone_ref(me.py());
            let literals: Vec<i32> = literals[start..(start + length)].into();
            let literals = literals.into_boxed_slice();
            Ok(PyBitVec { solver, literals })
        }
    }

    pub fn __invert__(me: &Bound<'_, Self>) -> Self {
        let solver = me.get().solver.clone_ref(me.py());
        let literals = me
            .get()
            .literals
            .iter()
            .map(|&lit| PySolver::bool_not(lit))
            .collect();
        PyBitVec { solver, literals }
    }

    pub fn __and__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            literals.push(solver.get().bool_and(a, b)?);
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __or__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            literals.push(solver.get().bool_or(a, b)?);
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __xor__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            literals.push(solver.get().bool_xor(a, b)?);
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __eq__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut res = PySolver::TRUE;
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            let c = solver.get().bool_equ(a, b)?;
            res = solver.get().bool_and(res, c)?;
        }

        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __ne__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let mut res = Self::__eq__(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }

    pub fn __le__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut res = PySolver::TRUE;
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            let c = solver.get().bool_xor(a, b)?;
            res = solver.get().bool_iff(c, b, res)?;
        }

        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __gt__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let mut res = Self::__le__(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }

    pub fn __ge__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut res = PySolver::TRUE;
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            let c = solver.get().bool_xor(a, b)?;
            res = solver.get().bool_iff(c, a, res)?;
        }

        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __lt__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let mut res = Self::__ge__(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }
}
