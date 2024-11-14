// ============================================================================
// This file was autogenerated
// It is presented side to side with its source: template_class_test.h
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
    ////////////////////    <generated_from:template_class_test.h>    ////////////////////
    auto pyClassMyTemplateClass_int =
        py::class_<MyTemplateClass<int>>
            (m, "MyTemplateClass_int", "")
        .def_rw("values", &MyTemplateClass<int>::values, "")
        .def(py::init<>(),
            "Standard constructor")
        .def("__init__",
            [](MyTemplateClass<int> * self, const std::array<int, 2>& v)
            {
                auto ctor_wrapper = [](MyTemplateClass<int>* self, const int v[2]) ->  void
                {
                    new(self) MyTemplateClass<int>(v); // placement new
                };
                auto ctor_wrapper_adapt_fixed_size_c_arrays = [&ctor_wrapper](MyTemplateClass<int> * self, const std::array<int, 2>& v)
                {
                    ctor_wrapper(self, v.data());
                };

                ctor_wrapper_adapt_fixed_size_c_arrays(self, v);
            },
            py::arg("v"),
            "Constructor that will need a parameter adaptation")
        .def("sum",
            &MyTemplateClass<int>::sum, "Standard method")
        .def("sum2",
            [](MyTemplateClass<int> & self, const std::array<int, 2>& v) -> int
            {
                auto sum2_adapt_fixed_size_c_arrays = [&self](const std::array<int, 2>& v) -> int
                {
                    auto lambda_result = self.sum2(v.data());
                    return lambda_result;
                };

                return sum2_adapt_fixed_size_c_arrays(v);
            },
            py::arg("v"),
            "Method that requires a parameter adaptation")
        ;
    auto pyClassMyTemplateClass_string =
        py::class_<MyTemplateClass<std::string>>
            (m, "MyTemplateClass_string", "")
        .def_rw("values", &MyTemplateClass<std::string>::values, "")
        .def(py::init<>(),
            "Standard constructor")
        .def("__init__",
            [](MyTemplateClass<std::string> * self, const std::array<std::string, 2>& v)
            {
                auto ctor_wrapper = [](MyTemplateClass<std::string>* self, const std::string v[2]) ->  void
                {
                    new(self) MyTemplateClass<std::string>(v); // placement new
                };
                auto ctor_wrapper_adapt_fixed_size_c_arrays = [&ctor_wrapper](MyTemplateClass<std::string> * self, const std::array<std::string, 2>& v)
                {
                    ctor_wrapper(self, v.data());
                };

                ctor_wrapper_adapt_fixed_size_c_arrays(self, v);
            },
            py::arg("v"),
            "Constructor that will need a parameter adaptation")
        .def("sum",
            &MyTemplateClass<std::string>::sum, "Standard method")
        .def("sum2",
            [](MyTemplateClass<std::string> & self, const std::array<std::string, 2>& v) -> std::string
            {
                auto sum2_adapt_fixed_size_c_arrays = [&self](const std::array<std::string, 2>& v) -> std::string
                {
                    auto lambda_result = self.sum2(v.data());
                    return lambda_result;
                };

                return sum2_adapt_fixed_size_c_arrays(v);
            },
            py::arg("v"),
            "Method that requires a parameter adaptation")
        ;
    ////////////////////    </generated_from:template_class_test.h>    ////////////////////

    // </litgen_pydef> // Autogenerated code end
}