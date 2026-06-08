from tools.calculator_tool import calculate
from tools.datetime_tool import get_current_datetime


def test_calculate_addition():
    assert calculate("2 + 2")["result"] == 4


def test_calculate_complex():
    assert calculate("(10 + 5) * 2")["result"] == 30


def test_calculate_percentage():
    result = calculate("1250 * 0.21")["result"]
    assert abs(result - 262.5) < 0.001


def test_calculate_invalid_returns_error():
    result = calculate("import os")
    assert "error" in result


def test_datetime_has_required_keys():
    result = get_current_datetime()
    assert all(k in result for k in ("datetime", "date", "time", "weekday"))
