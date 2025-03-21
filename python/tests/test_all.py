import pytest
import uasat


def test_sum_as_string():
    assert uasat.sum_as_string(1, 1) == "2"


def test_cadical_signature():
    # solver = uasat.Solver.with_config("unsat")
    solver = uasat.Solver()
    assert solver.signature() == "cadical-1.3.0"
