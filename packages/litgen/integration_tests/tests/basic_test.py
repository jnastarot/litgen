import lg_mylib


def test_functions():
    assert lg_mylib.my_add(3, 4) == 7

    assert lg_mylib.my_mul(3, 4) == 12
    assert lg_mylib.my_sub(3, 4) == -1


def test_not_published():
    assert "my_div" not in dir(lg_mylib)


def test_doc():
    assert "Subtracts two numbers" in lg_mylib.my_sub.__doc__

    assert "Adds two numbers" in lg_mylib.my_add.__doc__
    assert "Title that should be published as a top comment" not in lg_mylib.my_add.__doc__

    assert lg_mylib.my_mul.__doc__ == "my_mul(a: int, b: int) -> int\n"


def test_generic_function():
    r = lg_mylib.my_generic_function(1, 2, 3, a=4, b=5, c=6)
    assert r == 9  # == args.size() + 2 * kwargs.size()
