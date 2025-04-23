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

use pyo3::prelude::*;
use std::sync::{Arc, Mutex};

use super::Solver;

#[derive(Clone)]
#[pyclass(frozen, sequence)]
pub struct Elem {
    solver: Option<Arc<Mutex<Solver>>>,
    literals: Arc<[i32]>,
    start: usize,
    length: usize,
}

#[pymethods]
impl Elem {
    fn __len__(&self) -> usize {
        self.length
    }

    fn __getitem__(&self, index: usize) -> i32 {
        self.literals[self.start + index]
    }

    fn __or__(&self, other: &Elem) -> Elem {
        let solver = self.solver.map_or_else(|s| s.lock().unwrap());
    }
}
