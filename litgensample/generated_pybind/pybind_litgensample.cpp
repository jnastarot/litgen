#include "litgensample.h"

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

//#include <cstdint>
#include <stdint.h>

//#include "imgui_helper.hpp"
//#include "leaked_ptr.hpp"

void foo()
{
    int64_t r;
}

namespace py = pybind11;


void py_init_module_litgensample(py::module& m)
{
    using namespace LiterateGeneratorExample;

// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  AUTOGENERATED CODE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
// <autogen:pydef_cpp> // Autogenerated code below! Do not edit!

    auto pyClassFoo = py::class_<Foo>
        (m, "Foo", 
        "A superb struct")

        .def(py::init<>()) 
        .def_readwrite("factor", &Foo::factor, "Multiplication factor")
        .def_readwrite("delta", &Foo::delta, "addition factor")

        .def("calc",
            [](Foo& self, int x)
            {
                { return self.calc(x); }
            },
            py::arg("x"),
            "Do some math"
        )

        ; 


    m.def("add",
        [](int a, int b)
        {
            { return add(a, b); }
        },
        py::arg("a"),
        py::arg("b"),
        "Adds two numbers"
    );


    m.def("add",
        [](int a, int b, int c)
        {
            { return add(a, b, c); }
        },
        py::arg("a"),
        py::arg("b"),
        py::arg("c"),
        "Adds three numbers, with a surprise"
    );


    m.def("mul_inside_array",
        [](py::array & array, double factor)
        {
            // convert array (py::array&) to C standard buffer (mutable)
            void* array_buffer = array.mutable_data();
            int array_count = array.shape()[0];
            
            char array_type = array.dtype().char_();
            if (array_type == 'B')
                { mul_inside_array(static_cast<uint8_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'b')
                { mul_inside_array(static_cast<int8_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'H')
                { mul_inside_array(static_cast<uint16_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'h')
                { mul_inside_array(static_cast<int16_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'I')
                { mul_inside_array(static_cast<uint32_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'i')
                { mul_inside_array(static_cast<int32_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'L')
                { mul_inside_array(static_cast<uint64_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'l')
                { mul_inside_array(static_cast<int64_t*>(array_buffer), array_count, factor); return; }
            if (array_type == 'f')
                { mul_inside_array(static_cast<float*>(array_buffer), array_count, factor); return; }
            if (array_type == 'd')
                { mul_inside_array(static_cast<double*>(array_buffer), array_count, factor); return; }
            if (array_type == 'g')
                { mul_inside_array(static_cast<long double*>(array_buffer), array_count, factor); return; }

            // If we arrive here, the array type is not supported!
            throw std::runtime_error(std::string("Bad array type: ") + array_type );
        },
        py::arg("array"),
        py::arg("factor"),
        "Modify an array by adding a value to its elements"
    );


// </autogen:pydef_cpp> // Autogenerated code below! Do not edit!
// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  AUTOGENERATED CODE END !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

}