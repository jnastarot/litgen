"""Workaround for https://github.com/srcML/srcML/issues/1833

    void Foo(int v = 0 );
is correctly parsed as a function_decl

However,
    void Foo(int v = {} );
is parsed as a decl_stmt
"""
from __future__ import annotations

import litgen
from codemanip import code_utils


def test_fn_brace():
    code = "void f(V v={1, 2});"
    options = litgen.LitgenOptions()
    options.fn_params_adapt_mutable_param_with_default_value__regex = r""
    generated_code = litgen.generate_code(options, code)
    # print(generated_code.pydef_code)
    code_utils.assert_are_codes_equal(
        generated_code.pydef_code,
        """
        m.def("f",
            f, py::arg("v") = V{1, 2});
        """,
    )
    code_utils.assert_are_codes_equal(
        generated_code.stub_code,
        '''
        def f(v: V = V(1, 2)) -> None:
            pass
            '''
    )


def test_struct_brace():
    code = """
        struct Foo {
            std::vector<int> l={1};
            V v = {1, 2, 3};
        };
    """
    options = litgen.LitgenOptions()
    generated_code = litgen.generate_code(options, code)
    # print(generated_code.pydef_code)
    code_utils.assert_are_codes_equal(
        generated_code.pydef_code,
        """
        auto pyClassFoo =
            py::class_<Foo>
                (m, "Foo", "")
            .def(py::init<>([](
            const std::optional<const std::vector<int>> & l = std::nullopt, const std::optional<const V> & v = std::nullopt)
            {
                auto r = std::make_unique<Foo>();
                if (l.has_value())
                    r->l = l.value();
                else
                    r->l = {1};
                if (v.has_value())
                    r->v = v.value();
                else
                    r->v = {1, 2, 3};
                return r;
            })
            , py::arg("l") = py::none(), py::arg("v") = py::none()
            )
            .def_readwrite("l", &Foo::l, "")
            .def_readwrite("v", &Foo::v, "")
            ;
            """,
    )

    # print(generated_code.stub_code)
    code_utils.assert_are_codes_equal(
        generated_code.stub_code,
        '''
        class Foo:
            l: List[int] = List[int](1)
            v: V = V(1, 2, 3)
            def __init__(self, l: Optional[List[int]] = None, v: Optional[V] = None) -> None:
                """Auto-generated default constructor with named params
                ---
                Python bindings defaults:
                    If any of the params below is None, then its default value below will be used:
                        l: initialized with 1
                        v: initialized with 1, 2, 3
                """
                pass
        ''',
    )
