// ============================================================================
// This file was autogenerated
// It is presented side to side with its source: return_value_policy_test.h
// It is not used in the compilation
//    (see integration_tests/bindings/pybind_mylib.cpp which contains the full binding
//     code, including this code)
// ============================================================================

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/numpy.h>
#include "mylib/mylib.h"

namespace py = pybind11;

// <litgen_glue_code>  // Autogenerated code below! Do not edit!

// </litgen_glue_code> // Autogenerated code end


void py_init_module_mylib(py::module& m)
{
    // <litgen_pydef> // Autogenerated code below! Do not edit!
    ////////////////////    <generated_from:return_value_policy_test.h>    ////////////////////
    auto pyClassMyConfig =
        py::class_<MyConfig>
            (m, "MyConfig", "")
        .def(py::init<>()) // implicit default constructor
        .def_static("instance",
            &MyConfig::Instance,
            "return_value_policy::reference",
            pybind11::return_value_policy::reference)
        .def_readwrite("value", &MyConfig::value, "")
        ;


    m.def("my_config_instance",
        MyConfigInstance,
        "return_value_policy::reference",
        pybind11::return_value_policy::reference);
    ////////////////////    </generated_from:return_value_policy_test.h>    ////////////////////

    // </litgen_pydef> // Autogenerated code end
}
