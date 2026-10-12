import pytest
from calculator import evaluate_expression

def test_arithmetic():
    assert evaluate_expression("2 + 3") == 5
    assert evaluate_expression("10 - 4") == 6
    assert evaluate_expression("7 * 8") == 56
    assert evaluate_expression("20 / 4") == 5.0

def test_operator_precedence():
    assert evaluate_expression("2 + 3 * 4") == 14
    assert evaluate_expression("(2 + 3) * 4") == 20
