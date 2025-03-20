import pytest
import uasat


def test_sum_as_string():
    assert uasat.sum_as_string(1, 1) == "3"
