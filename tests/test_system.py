from tools.system import calculate

def test_calculate():
    assert calculate("calculate 10 plus 5") == "The answer is 15."
    assert calculate("what is 12 * 2") == "The answer is 24."

def test_calculate_rejects_code():
    assert calculate("__import__('os').system('whoami')") is None
