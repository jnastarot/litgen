// ============================================================================
// This file was autogenerated
// It is presented side to side with its source: inner_class_test.h
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
    ////////////////////    <generated_from:inner_class_test.h>    ////////////////////

    { // <namespace SomeNamespace>
        py::module_ pyNsSomeNamespace = m.def_submodule("SomeNamespace", "namespace SomeNamespace");
        auto pyNsSomeNamespace_ClassParentStruct =
            py::class_<SomeNamespace::ParentStruct>
                (pyNsSomeNamespace, "ParentStruct", "")
            .def(py::init<>()) // implicit default constructor
            .def_readwrite("inner_struct", &SomeNamespace::ParentStruct::inner_struct, "")
            .def_readwrite("inner_enum", &SomeNamespace::ParentStruct::inner_enum, "")
            ;
        { // inner classes & enums of ParentStruct
            auto pyNsSomeNamespace_ClassParentStruct_ClassInnerStruct =
                py::class_<SomeNamespace::ParentStruct::InnerStruct>
                    (pyNsSomeNamespace_ClassParentStruct, "InnerStruct", "")
                .def_readwrite("value", &SomeNamespace::ParentStruct::InnerStruct::value, "")
                .def(py::init<int>(),
                    py::arg("value") = 10)
                .def("add",
                    &SomeNamespace::ParentStruct::InnerStruct::add, py::arg("a"), py::arg("b"))
                ;
            py::enum_<SomeNamespace::ParentStruct::InnerEnum>(pyNsSomeNamespace_ClassParentStruct, "InnerEnum", py::arithmetic(), "")
                .value("zero", SomeNamespace::ParentStruct::InnerEnum::Zero, "")
                .value("one", SomeNamespace::ParentStruct::InnerEnum::One, "")
                .value("two", SomeNamespace::ParentStruct::InnerEnum::Two, "")
                .value("three", SomeNamespace::ParentStruct::InnerEnum::Three, "");
        } // end of inner classes & enums of ParentStruct
    } // </namespace SomeNamespace>
    ////////////////////    </generated_from:inner_class_test.h>    ////////////////////

    // </litgen_pydef> // Autogenerated code end
}
