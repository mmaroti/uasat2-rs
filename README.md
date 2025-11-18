# UASAT: a SAT solver based universal algebra calculator

This is a python library to aid universal algebraic research by generating
simple examples and counterexamples. For example you can work with finitary
relations and operations on a finite set and express various contraints
between them. The underlying SAT solver is CaDiCaL 1.9.5, which is an
incremental SAT solver. This can be used to enumberate and count examples.
All relations and operations are represented by multi-dimensional matrices
with literal entries. When performing operations on these object new
literals and clauses are added automatically to the solver. The usual
operations on relations and operations are supported, as seen in the
following two small examples.


```python
from uasat import Solver, Relation, Operation

def test_number_of_posets():
    """
    Counting the number of labeled 3-element posets.
    """

    solver = Solver()

    rel = Relation.variable(3, 2, solver)
    rel.reflexive().ensure_true()
    rel.antisymm().ensure_true()
    rel.transitive().ensure_true()

    count = 0
    while solver.solve():
        val = rel.solution()
        print(val.decode())
        count += 1
        (rel ^ val).ensure_any()
    assert count == 19


def test_polymorphisms_of_c3():
    """
    Find all binary polymorphisms of the reflexive oriented 3-cycle.
    """

    rel = Relation.tuples(3, 2, [
        (0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 0),
    ])

    solver = Solver()

    op = Operation.variable(rel.size, 2, solver)
    op.preserves(rel).ensure_true()

    count = 0
    while solver.solve():
        val = op.solution()
        print(val.decode())
        count += 1
        (op.table ^ val.table).ensure_any()
    assert count == 9
```

## Installation

Use `pip install uasat` to install the package from PyPI (maybe use a virtual
environment). You do NOT need to download the source from github or build the
library yourself, but you can certainly do that. The code of the library with
some research scripts are available at
[https://github.com/mmaroti/uasat2-rs]().
You can test the library is properly installed with the following command
`python3 -c "import uasat; help(uasat.Solver)"`.

## Development

Some of the functionality of the library is implemented in `rust`. The CaDiCaL
SAT solver is implemented in `c++` but compiled by `rust`. The `python`
interfaces to the `rust` objects is implemented using `maturin`. Use
`maturin develop` to compile the library on your machine, and set up a virtual
environment. Then run `python3 -m pytest` to run the validation tests. Build
with `maturin build` and `maturin build --sdist`, and upload with
`twine upload -r testpypi target/wheels/*`.
