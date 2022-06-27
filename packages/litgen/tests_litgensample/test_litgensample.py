# type: ignore
import numpy as np

import litgensample


def test_c_array():
    #
    # Test const c arrays / non void function
    # MY_API inline int add_c_array2(const int values[2]) { return values[0] + values[1];}
    #
    a = [5, 6]
    r = litgensample.add_c_array2(a)
    assert r == 11

    got_exception = False
    try:
        litgensample.add_c_array2([1, 2, 3])
    except TypeError:
        got_exception = True
    assert got_exception

    #
    # Test const c arrays / void function
    # MY_API inline void log_c_array2(const int values[2]) { printf("%i, %i\n", values[0], values[1]); }
    #
    a = [5, 6]
    litgensample.log_c_array2(a)  # This should print "5, 6\n"

    #
    # Test non const c arrays with numeric type (which will be boxed)
    # MY_API inline void change_c_array(unsigned long values[2])
    # {
    #     values[0] = values[1] + values[0];
    # values[1] = values[0] * values[1];
    # }
    #
    a = litgensample.BoxedUnsignedLong(5)
    b = litgensample.BoxedUnsignedLong(6)
    litgensample.change_c_array2(a, b)
    assert a.value == 11
    assert b.value == 66

    # Test non const c arrays with struct type (which will *not* be boxed)
    #     MY_API inline void GetPoints(Point2 out[2]) { out[0] = {0, 1}; out[1] = {2, 3}; }
    pt1 = litgensample.Point2()
    pt2 = litgensample.Point2()
    litgensample.get_points(pt1, pt2)
    assert pt1.x == 0 and pt1.y == 1 and pt2.x == 2 and pt2.y == 3


def test_c_buffers():
    #
    # Non templated call
    #
    x = np.array((1, 2, 3, 4, 5), np.uint8)
    litgensample.add_inside_buffer(x, 5)
    assert (x == np.array((6, 7, 8, 9, 10), np.uint8)).all()
    #
    # templated call
    #
    # With default float type
    x = np.array((1.0, 2.0, 3.0))
    litgensample.mul_inside_buffer(x, 3.0)
    assert (x == np.array((3.0, 6.0, 9.0))).all()
    # With default int type
    x = np.array((1, 2, 3))
    litgensample.mul_inside_buffer(x, 3)
    assert (x == np.array((3, 6, 9))).all()
    # With range of types
    data_types = [np.float32, np.uint8, np.uint32, np.int64]  # np.float128 is not supported by all versions of numpy
    for data_type in data_types:
        x = np.array((1, 2, 3), data_type)
        litgensample.mul_inside_buffer(x, 3)
        assert (x == np.array((3, 6, 9), data_type)).all()
    # With unsupported type (float16 is not supported by C++)
    got_exception = False
    data_type = np.float16
    x = np.array((1, 2, 3), data_type)
    try:
        litgensample.mul_inside_buffer(x, 3)
    except RuntimeError:
        got_exception = True
    assert got_exception


def test_c_string_list():
    strings = ["Hello", "Wonderful", "World"]
    a = litgensample.BoxedInt()
    b = litgensample.BoxedInt()
    total_size = litgensample.c_string_list_total_size(strings, a, b)
    assert total_size == len("Hello") + len("Wonderful") + len("World")
    assert a.value == total_size
    assert b.value == total_size + 1


def test_c_array_numeric_member_types():
    foo = litgensample.Foo()

    assert (foo.values == [0, 1]).all()
    foo.values[0] = 42
    assert (foo.values == [42, 1]).all()

    assert (foo.flags == [False, True, False]).all()
    foo.flags[0] = True
    assert (foo.flags == [True, True, False]).all()


def test_modifiable_immutable():
    a = litgensample.BoxedBool(True)
    assert a.value == True
    litgensample.toggle_bool_pointer(a)
    assert a.value == False
    litgensample.toggle_bool_reference(a)
    assert a.value == True
    litgensample.toggle_bool_nullable(a)
    assert a.value == False
    litgensample.toggle_bool_nullable(None)


def test_return_value_policy_reference():
    i1 = litgensample.foo_instance()
    i1.delta = 42
    i2 = litgensample.foo_instance()
    assert i2.delta == 42
    i2.delta = 56
    i3 = litgensample.foo_instance()
    assert i3.delta == 56
    print("zut")


def test_overload():
    assert litgensample.add_overload(3, 4) == 7
    assert litgensample.add_overload(3, 4, 3) == 10
    fo = litgensample.FooOverload()
    assert fo.add_overload(3, 4) == 7
    assert fo.add_overload(3, 4, 3) == 10


def test_manual():
    outer = litgensample.Outer()
    inner1 = outer.GetInner()
    inner2 = outer.GetInner()
    inner1.x = 1
    assert inner2.x == 1


def test_nullable_param():
    b = litgensample.BoxedBool(True)
    litgensample.toggle_bool_nullable(b)
    assert b.value == False
    litgensample.toggle_bool_nullable()


def test_modify_string():
    s = litgensample.BoxedString("Say ")
    litgensample.modify_string(s)
    assert s.value == "Say hello"


def test_adapt_modifiable_immutable_to_return():
    r = litgensample.slider_bool_int("Hello", 2)
    assert r == (True, 3)

    r = litgensample.slider_void_int("Hello", 2)
    assert r == 3

    r = litgensample.slider_bool_int2("Hello", 1, 2)
    assert r == (False, 2, 4)


# test_adapt_modifiable_immutable_to_return()
# test_modify_string()
# test_manual()
# test_return_value_policy_reference()
# test_modifiable_immutable()
# test_c_array()
# test_c_buffers()
# test_c_string_list()
# test_c_array_numeric_member_types()t
# test_pointers()
