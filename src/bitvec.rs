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
    solver: Option<Py<PySolver>>,
    literals: Box<[i32]>,
}

fn get_solver(py: Python<'_>, solvers: &[&Option<Py<PySolver>>]) -> PyResult<Option<Py<PySolver>>> {
    let mut result: Option<&Py<PySolver>> = None;
    for solver in solvers.iter().copied().flatten() {
        if result.is_none() {
            result = Some(solver)
        } else if !solver.is(result.unwrap()) {
            return Err(PyValueError::new_err("incompatible solvers"));
        }
    }
    Ok(result.map(|r| r.clone_ref(py)))
}

#[pymethods]
impl PyBitVec {
    /// Creates a new bit vector with the associated solver and literals.
    #[new]
    pub fn new(solver: Option<Py<PySolver>>, literals: Vec<i32>) -> PyResult<PyBitVec> {
        if solver.is_none() {
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
    pub fn get_solver(me: &Bound<'_, Self>) -> Option<Py<PySolver>> {
        me.get().solver.as_ref().map(|x| x.clone_ref(me.py()))
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

    pub fn __invert__(me: &Bound<'_, Self>) -> PyBitVec {
        let solver = me.get().solver.as_ref().map(|s| s.clone_ref(me.py()));
        let literals = me
            .get()
            .literals
            .iter()
            .map(|&lit| PySolver::bool_not(lit))
            .collect();
        PyBitVec { solver, literals }
    }

    pub fn __and__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let solver = get_solver(me.py(), &[&me.get().solver, &other.solver])?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());

        if let Some(s) = solver.as_ref() {
            let mut solver = s.get().lock().unwrap();
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                literals.push(solver.bool_and(a, b));
            }
        } else {
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                debug_assert!(a == PySolver::TRUE || a == PySolver::FALSE);
                debug_assert!(b == PySolver::TRUE || b == PySolver::FALSE);
                literals.push(PySolver::bool_lift(
                    a == PySolver::TRUE && b == PySolver::TRUE,
                ));
            }
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __or__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let solver = get_solver(me.py(), &[&me.get().solver, &other.solver])?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());

        if let Some(s) = solver.as_ref() {
            let mut solver = s.get().lock().unwrap();
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                literals.push(solver.bool_or(a, b));
            }
        } else {
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                debug_assert!(a == PySolver::TRUE || a == PySolver::FALSE);
                debug_assert!(b == PySolver::TRUE || b == PySolver::FALSE);
                literals.push(PySolver::bool_lift(
                    a == PySolver::TRUE || b == PySolver::TRUE,
                ));
            }
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __xor__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let solver = get_solver(me.py(), &[&me.get().solver, &other.solver])?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());

        if let Some(s) = solver.as_ref() {
            let mut solver = s.get().lock().unwrap();
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                literals.push(solver.bool_xor(a, b));
            }
        } else {
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                debug_assert!(a == PySolver::TRUE || a == PySolver::FALSE);
                debug_assert!(b == PySolver::TRUE || b == PySolver::FALSE);
                literals.push(PySolver::bool_lift(a != b));
            }
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __eq__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let solver = get_solver(me.py(), &[&me.get().solver, &other.solver])?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut lit;
        if let Some(s) = solver.as_ref() {
            let mut solver = s.get().lock().unwrap();
            lit = solver.comp_eq(
                me.get().literals.iter().copied(),
                other.literals.iter().copied(),
            );
        } else {
            lit = PySolver::TRUE;
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                debug_assert!(a == PySolver::TRUE || a == PySolver::FALSE);
                debug_assert!(b == PySolver::TRUE || b == PySolver::FALSE);
                if a != b {
                    lit = PySolver::FALSE;
                    break;
                }
            }
        }

        let literals = vec![lit].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __ne__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let mut res = Self::__eq__(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }

    pub fn __le__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let solver = get_solver(me.py(), &[&me.get().solver, &other.solver])?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut lit;
        if let Some(s) = solver.as_ref() {
            let mut solver = s.get().lock().unwrap();
            lit = solver.comp_le(
                me.get().literals.iter().copied(),
                other.literals.iter().copied(),
            );
        } else {
            lit = PySolver::TRUE;
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                debug_assert!(a == PySolver::TRUE || a == PySolver::FALSE);
                debug_assert!(b == PySolver::TRUE || b == PySolver::FALSE);
                if a != b {
                    lit = b;
                }
            }
        }

        let literals = vec![lit].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __gt__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let mut res = Self::__le__(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }

    pub fn __ge__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let solver = get_solver(me.py(), &[&me.get().solver, &other.solver])?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut lit;
        if let Some(s) = solver.as_ref() {
            let mut solver = s.get().lock().unwrap();
            lit = solver.comp_ge(
                me.get().literals.iter().copied(),
                other.literals.iter().copied(),
            );
        } else {
            lit = PySolver::TRUE;
            for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
                debug_assert!(a == PySolver::TRUE || a == PySolver::FALSE);
                debug_assert!(b == PySolver::TRUE || b == PySolver::FALSE);
                if a != b {
                    lit = a;
                }
            }
        }

        let literals = vec![lit].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __lt__(me: &Bound<'_, Self>, other: &PyBitVec) -> PyResult<PyBitVec> {
        let mut res = Self::__ge__(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }
}
