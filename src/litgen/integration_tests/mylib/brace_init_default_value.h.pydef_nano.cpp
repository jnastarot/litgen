// ============================================================================
// This file was autogenerated
// It is presented side to side with its source: brace_init_default_value.h
// It is not used in the compilation
//    (see integration_tests/bindings/pybind_mylib.cpp which contains the full binding
//     code, including this code)
// ============================================================================

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/function.h>
#include "mylib_main/mylib.h"

namespace py = nanobind;

// <litgen_glue_code>  // Autogenerated code below! Do not edit!

// </litgen_glue_code> // Autogenerated code end


void py_init_module_mylib(py::module_& m)
{
    // <litgen_pydef> // Autogenerated code below! Do not edit!
    ////////////////////    <generated_from:brace_init_default_value.h>    ////////////////////
    auto pyClassFooBrace =
        py::class_<FooBrace>
            (m, "FooBrace", "")
        .def("__init__", [](
        std::vector<int> int_values = {1, 2, 3})
        {
            auto r = std::make_unique<FooBrace>();
            r->int_values = int_values;
            return r;
        }
        )
        .def_rw("int_values", &FooBrace::int_values, "")
        .def_rw("dict_string_int", &FooBrace::dict_string_int, "")
        ;


    m.def("fn_brace",
        FnBrace, py::arg("foo_brace") = FooBrace{}, py::arg("ints") = std::vector<int>{1, 2, 3});
    ////////////////////    </generated_from:brace_init_default_value.h>    ////////////////////

    // </litgen_pydef> // Autogenerated code end
}
