from app.tools.calculator import calculate


def test_basic_arithmetic():
    res = calculate("(125 * 8) + 450")
    assert res["success"] is True
    assert res["result"] == 1450


def test_percentage_calculation():
    res = calculate("15% of 2500")
    assert res["success"] is True
    assert res["result"] == 375


def test_square_root():
    res = calculate("sqrt(2025)")
    assert res["success"] is True
    assert res["result"] == 45


def test_discount_reverse_formula():
    res = calculate("2000 / (1 - 0.20)")
    assert res["success"] is True
    assert res["result"] == 2500


def test_powers_and_parentheses():
    res = calculate("2^10 + (5 * 4)")
    assert res["success"] is True
    assert res["result"] == 1044


def test_division_by_zero():
    res = calculate("100 / 0")
    assert res["success"] is False
    assert "Division by zero" in res["error"]


def test_negative_square_root():
    res = calculate("sqrt(-16)")
    assert res["success"] is False
    assert "negative" in res["error"]


def test_syntax_error():
    res = calculate("5 +* 3")
    assert res["success"] is False
    assert "Invalid mathematical syntax" in res["error"]


def test_empty_expression():
    res = calculate("   ")
    assert res["success"] is False
    assert "empty" in res["error"]


def test_forbidden_functions_rejected():
    res = calculate("__import__('os').system('ls')")
    assert res["success"] is False
