import pytest
from mathx import add, sub, mul, div

@pytest.mark.parametrize("a,b,e", [(1, 2, 3), (0, 0, 0), (-1, 1, 0), (2.5, 2.5, 5.0)])
def test_add(a, b, e):
    print("add case", a, b)
    assert add(a, b) == e

@pytest.mark.parametrize("a,b,e", [(5, 2, 3), (0, 1, -1), (1, 1, 0)])
def test_sub(a, b, e):
    assert sub(a, b) == e

@pytest.mark.parametrize("a,b,e", [(3, 4, 12), (0, 9, 0), (-2, 3, -6)])
def test_mul(a, b, e):
    assert mul(a, b) == e

def test_div():
    assert div(8, 2) == 4
    with pytest.raises(ZeroDivisionError):
        div(1, 0)
