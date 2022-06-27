#include "litgensample.h"
#include "litgensample_boxed_types.h"

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <stdint.h>

#include <stdio.h>

namespace py = pybind11;

struct Inner
{
    Inner() { printf("Construct Inner %p\n", this); }
    ~Inner() { printf("Destroy Inner %p\n", this); }
    int x = 0;
};

struct Outer
{
    Outer() { printf("Construct Outer %p\n", this); }
    ~Outer() { printf("Destroy Outer %p\n", this); }
    int y = 0;
    Inner& GetInner() {return inner; };
private:
    Inner inner;
};

Outer& outer_instance() {
    static Outer outer;
    return outer;
}

void py_init_module_litgensample(py::module& m)
{

    py::class_<Inner>(m, "Inner", "")
        .def(py::init<>())
        .def_readwrite("x", &Inner::x);

    py::class_<Outer>(m, "Outer", "")
        .def(py::init<>())
        .def_readwrite("y", &Outer::y)
        .def("GetInner", &Outer::GetInner
        , "some doc"
        , pybind11::return_value_policy::reference
        )
        ;

    m.def("outer_instance"
          //,outer_instance
          , []() -> Outer& { return outer_instance(); }
        //, pybind11::return_value_policy::reference
    );

    using namespace LiterateGeneratorExample;

    // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  AUTOGENERATED CODE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    // <litgen_pydef> // Autogenerated code below! Do not edit!
    ////////////////////    <generated_from:BoxedTypes>    ////////////////////
    // <Autogenerated_Boxed_Types>
    auto pyClassBoxedUnsignedLong = py::class_<BoxedUnsignedLong>
        (m, "BoxedUnsignedLong", "")
        .def_readwrite("value", &BoxedUnsignedLong::value, "")
        .def(py::init<unsigned long>(),
            py::arg("v") = 0)
        .def("__repr__",
            &BoxedUnsignedLong::__repr__)
        ;
    auto pyClassBoxedInt = py::class_<BoxedInt>
        (m, "BoxedInt", "")
        .def_readwrite("value", &BoxedInt::value, "")
        .def(py::init<int>(),
            py::arg("v") = 0)
        .def("__repr__",
            &BoxedInt::__repr__)
        ;
    auto pyClassBoxedBool = py::class_<BoxedBool>
        (m, "BoxedBool", "")
        .def_readwrite("value", &BoxedBool::value, "")
        .def(py::init<bool>(),
            py::arg("v") = false)
        .def("__repr__",
            &BoxedBool::__repr__)
        ;
    auto pyClassBoxedString = py::class_<BoxedString>
        (m, "BoxedString", "")
        .def_readwrite("value", &BoxedString::value, "")
        .def(py::init<std::string>(),
            py::arg("v") = "")
        .def("__repr__",
            &BoxedString::__repr__)
        ;
    // </Autogenerated_Boxed_Types>
    ////////////////////    </generated_from:BoxedTypes>    ////////////////////
    ////////////////////    <generated_from:litgensample.h>    ////////////////////
    // <namespace LiterateGeneratorExample>
    py::enum_<MyEnum>(m, "MyEnum", py::arithmetic(), " A super nice enum\n for demo purposes ( bool val = False )")
        .value("a", MyEnum_a, "This is value a")
        .value("aa", MyEnum_aa, "this is value aa")
        .value("aaa", MyEnum_aaa, "this is value aaa")
        .value("b", MyEnum_b, "This is value b")
        .value("c", MyEnum_c, " This is c\n with doc on several lines");


    m.def("add_c_array2",
        [](const std::array<int, 2>& values) -> int
        {
            auto add_c_array2_adapt_fixed_size_c_arrays = [](const std::array<int, 2>& values) -> int
            {
                auto r = add_c_array2(values.data());
                return r;
            };

            return add_c_array2_adapt_fixed_size_c_arrays(values);
        },     py::arg("values"));

    m.def("log_c_array2",
        [](const std::array<int, 2>& values)
        {
            auto log_c_array2_adapt_fixed_size_c_arrays = [](const std::array<int, 2>& values)
            {
                log_c_array2(values.data());
            };

            log_c_array2_adapt_fixed_size_c_arrays(values);
        },     py::arg("values"));

    m.def("change_c_array2",
        [](BoxedUnsignedLong & values_0, BoxedUnsignedLong & values_1)
        {
            auto change_c_array2_adapt_fixed_size_c_arrays = [](BoxedUnsignedLong & values_0, BoxedUnsignedLong & values_1)
            {
                unsigned long values_raw[2];
                values_raw[0] = values_0.value;
                values_raw[1] = values_1.value;

                change_c_array2(values_raw);

                values_0.value = values_raw[0];
                values_1.value = values_raw[1];
            };

            change_c_array2_adapt_fixed_size_c_arrays(values_0, values_1);
        },     py::arg("values_0"), py::arg("values_1"));


    auto pyClassPoint2 = py::class_<Point2>
        (m, "Point2", "Test with C array containing user defined struct (which will not be boxed)")
        .def(py::init<>()) // implicit default constructor
        .def_readwrite("x", &Point2::x, "")
        .def_readwrite("y", &Point2::y, "")
        ;


    m.def("get_points",
        [](Point2 & out_0, Point2 & out_1)
        {
            auto GetPoints_adapt_fixed_size_c_arrays = [](Point2 & out_0, Point2 & out_1)
            {
                Point2 out_raw[2];
                out_raw[0] = out_0;
                out_raw[1] = out_1;

                GetPoints(out_raw);

                out_0 = out_raw[0];
                out_1 = out_raw[1];
            };

            GetPoints_adapt_fixed_size_c_arrays(out_0, out_1);
        },     py::arg("out_0"), py::arg("out_1"));

    m.def("add_inside_buffer",
        [](py::array & buffer, uint8_t number_to_add)
        {
            auto add_inside_buffer_adapt_c_buffers = [](py::array & buffer, uint8_t number_to_add)
            {
                // convert py::array to C standard buffer (mutable)
                void * buffer_from_pyarray = buffer.mutable_data();
                py::ssize_t buffer_count = buffer.shape()[0];
                char buffer_type = buffer.dtype().char_();
                if (buffer_type != 'B')
                    throw std::runtime_error(std::string(R"msg(
                            Bad type!  Expected a numpy array of native type:
                                        uint8_t *
                                    Which is equivalent to
                                        B
                                    (using py::array::dtype().char_() as an id)
                        )msg"));

                add_inside_buffer(static_cast<uint8_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), number_to_add);
            };

            add_inside_buffer_adapt_c_buffers(buffer, number_to_add);
        },
        py::arg("buffer"), py::arg("number_to_add"),
        "Modifies a buffer by adding a value to its elements");

    m.def("buffer_sum",
        [](const py::array & buffer, int stride = -1) -> int
        {
            auto buffer_sum_adapt_c_buffers = [](const py::array & buffer, int stride = -1) -> int
            {
                // convert py::array to C standard buffer (const)
                const void * buffer_from_pyarray = buffer.data();
                py::ssize_t buffer_count = buffer.shape()[0];
                char buffer_type = buffer.dtype().char_();
                if (buffer_type != 'B')
                    throw std::runtime_error(std::string(R"msg(
                            Bad type!  Expected a numpy array of native type:
                                        const uint8_t *
                                    Which is equivalent to
                                        B
                                    (using py::array::dtype().char_() as an id)
                        )msg"));

                // process stride default value (which was a sizeof in C++)
                int buffer_stride = stride;
                if (buffer_stride == -1)
                    buffer_stride = (int)buffer.itemsize();

                auto r = buffer_sum(static_cast<const uint8_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), static_cast<size_t>(buffer_stride));
                return r;
            };

            return buffer_sum_adapt_c_buffers(buffer, stride);
        },
        py::arg("buffer"), py::arg("stride") = -1,
        "Returns the sum of a const buffer");

    m.def("add_inside_two_buffers",
        [](py::array & buffer_1, py::array & buffer_2, uint8_t number_to_add)
        {
            auto add_inside_two_buffers_adapt_c_buffers = [](py::array & buffer_1, py::array & buffer_2, uint8_t number_to_add)
            {
                // convert py::array to C standard buffer (mutable)
                void * buffer_1_from_pyarray = buffer_1.mutable_data();
                py::ssize_t buffer_1_count = buffer_1.shape()[0];
                char buffer_1_type = buffer_1.dtype().char_();
                if (buffer_1_type != 'B')
                    throw std::runtime_error(std::string(R"msg(
                            Bad type!  Expected a numpy array of native type:
                                        uint8_t *
                                    Which is equivalent to
                                        B
                                    (using py::array::dtype().char_() as an id)
                        )msg"));

                // convert py::array to C standard buffer (mutable)
                void * buffer_2_from_pyarray = buffer_2.mutable_data();
                py::ssize_t buffer_2_count = buffer_2.shape()[0];
                char buffer_2_type = buffer_2.dtype().char_();
                if (buffer_2_type != 'B')
                    throw std::runtime_error(std::string(R"msg(
                            Bad type!  Expected a numpy array of native type:
                                        uint8_t *
                                    Which is equivalent to
                                        B
                                    (using py::array::dtype().char_() as an id)
                        )msg"));

                add_inside_two_buffers(static_cast<uint8_t *>(buffer_1_from_pyarray), static_cast<uint8_t *>(buffer_2_from_pyarray), static_cast<size_t>(buffer_2_count), number_to_add);
            };

            add_inside_two_buffers_adapt_c_buffers(buffer_1, buffer_2, number_to_add);
        },
        py::arg("buffer_1"), py::arg("buffer_2"), py::arg("number_to_add"),
        "Modifies two buffers");

    m.def("mul_inside_buffer",
        [](py::array & buffer, double factor)
        {
            auto mul_inside_buffer_adapt_c_buffers = [](py::array & buffer, double factor)
            {
                // convert py::array to C standard buffer (mutable)
                void * buffer_from_pyarray = buffer.mutable_data();
                py::ssize_t buffer_count = buffer.shape()[0];

                // call the correct template version by casting
                char buffer_type = buffer.dtype().char_();
                if (buffer_type == 'B')
                    mul_inside_buffer(static_cast<uint8_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'b')
                    mul_inside_buffer(static_cast<int8_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'H')
                    mul_inside_buffer(static_cast<uint16_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'h')
                    mul_inside_buffer(static_cast<int16_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'I')
                    mul_inside_buffer(static_cast<uint32_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'i')
                    mul_inside_buffer(static_cast<int32_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'L')
                    mul_inside_buffer(static_cast<uint64_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'l')
                    mul_inside_buffer(static_cast<int64_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'f')
                    mul_inside_buffer(static_cast<float *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'd')
                    mul_inside_buffer(static_cast<double *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                else if (buffer_type == 'g')
                    mul_inside_buffer(static_cast<long double *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), factor);
                // If we reach this point, the array type is not supported!
                else
                    throw std::runtime_error(std::string("Bad array type ('") + buffer_type + "') for param buffer");
            };

            mul_inside_buffer_adapt_c_buffers(buffer, factor);
        },
        py::arg("buffer"), py::arg("factor"),
        "Modify an array by multiplying its elements (template function!)");

    m.def("c_string_list_total_size",
        [](const std::vector<std::string> & items, BoxedInt & output_0, BoxedInt & output_1) -> size_t
        {
            auto c_string_list_total_size_adapt_fixed_size_c_arrays = [](const char * const items[], int items_count, BoxedInt & output_0, BoxedInt & output_1) -> size_t
            {
                int output_raw[2];
                output_raw[0] = output_0.value;
                output_raw[1] = output_1.value;

                auto r = c_string_list_total_size(items, items_count, output_raw);

                output_0.value = output_raw[0];
                output_1.value = output_raw[1];
                return r;
            };
            auto c_string_list_total_size_adapt_c_string_list = [&c_string_list_total_size_adapt_fixed_size_c_arrays](const std::vector<std::string> & items, BoxedInt & output_0, BoxedInt & output_1) -> size_t
            {
                std::vector<const char *> items_ptrs;
                for (const auto& v: items)
                    items_ptrs.push_back(v.c_str());
                int items_count = static_cast<int>(items.size());

                auto r = c_string_list_total_size_adapt_fixed_size_c_arrays(items_ptrs.data(), items_count, output_0, output_1);
                return r;
            };

            return c_string_list_total_size_adapt_c_string_list(items, output_0, output_1);
        },     py::arg("items"), py::arg("output_0"), py::arg("output_1"));

    m.def("toggle_bool_pointer",
        [](BoxedBool & v)
        {
            auto ToggleBoolPointer_adapt_modifiable_immutable = [](BoxedBool & v)
            {
                bool * v_boxed_value = & (v.value);

                ToggleBoolPointer(v_boxed_value);
            };

            ToggleBoolPointer_adapt_modifiable_immutable(v);
        },
        py::arg("v"),
        "\n Modifiable immutable python types test\n\n Test with pointer");

    m.def("toggle_bool_nullable",
        [](BoxedBool * v = nullptr)
        {
            auto ToggleBoolNullable_adapt_modifiable_immutable = [](BoxedBool * v = nullptr)
            {
                bool * v_boxed_value = nullptr;
                if (v != nullptr)
                    v_boxed_value = & (v->value);

                ToggleBoolNullable(v_boxed_value);
            };

            ToggleBoolNullable_adapt_modifiable_immutable(v);
        },
        py::arg("v") = py::none(),
        "Test with nullable pointer");

    m.def("toggle_bool_reference",
        [](BoxedBool & v)
        {
            auto ToggleBoolReference_adapt_modifiable_immutable = [](BoxedBool & v)
            {
                bool & v_boxed_value = v.value;

                ToggleBoolReference(v_boxed_value);
            };

            ToggleBoolReference_adapt_modifiable_immutable(v);
        },
        py::arg("v"),
        "Test with reference");

    m.def("slider_bool_int",
        [](const char * label, int value) -> std::tuple<bool, int>
        {
            auto SliderBoolInt_adapt_modifiable_immutable_to_return = [](const char * label, int value) -> std::tuple<bool, int>
            {
                int * value_adapt_modifiable = & value;

                MY_API bool r = SliderBoolInt(label, value_adapt_modifiable);
                return std::make_tuple(r, value);
            };

            return SliderBoolInt_adapt_modifiable_immutable_to_return(label, value);
        },     py::arg("label"), py::arg("value"));

    m.def("slider_void_int",
        [](const char * label, int value) -> int
        {
            auto SliderVoidInt_adapt_modifiable_immutable_to_return = [](const char * label, int value) -> int
            {
                int * value_adapt_modifiable = & value;

                SliderVoidInt(label, value_adapt_modifiable);
                return value;
            };

            return SliderVoidInt_adapt_modifiable_immutable_to_return(label, value);
        },     py::arg("label"), py::arg("value"));

    m.def("slider_bool_int2",
        [](const char * label, int value1, int value2) -> std::tuple<bool, int, int>
        {
            auto SliderBoolInt2_adapt_modifiable_immutable_to_return = [](const char * label, int value1, int value2) -> std::tuple<bool, int, int>
            {
                int * value1_adapt_modifiable = & value1;
                int * value2_adapt_modifiable = & value2;

                MY_API bool r = SliderBoolInt2(label, value1_adapt_modifiable, value2_adapt_modifiable);
                return std::make_tuple(r, value1, value2);
            };

            return SliderBoolInt2_adapt_modifiable_immutable_to_return(label, value1, value2);
        },     py::arg("label"), py::arg("value1"), py::arg("value2"));

    m.def("slider_void_int_default_null",
        [](const char * label, std::optional<int> value = std::nullopt) -> std::tuple<bool, std::optional<int>>
        {
            auto SliderVoidIntDefaultNull_adapt_modifiable_immutable_to_return = [](const char * label, std::optional<int> value = std::nullopt) -> std::tuple<bool, std::optional<int>>
            {
                int * value_adapt_modifiable = nullptr;
                if (value.has_value())
                    value_adapt_modifiable = & value.value();

                MY_API bool r = SliderVoidIntDefaultNull(label, value_adapt_modifiable);
                return std::make_tuple(r, value);
            };

            return SliderVoidIntDefaultNull_adapt_modifiable_immutable_to_return(label, value);
        },     py::arg("label"), py::arg("value") = py::none());

    m.def("slider_void_int_array",
        [](const char * label, std::array<int, 3> value) -> std::tuple<bool, std::array<int, 3>>
        {
            auto SliderVoidIntArray_adapt_modifiable_immutable_to_return = [](const char * label, std::array<int, 3> value) -> std::tuple<bool, std::array<int, 3>>
            {
                int * value_adapt_modifiable = value.data();

                MY_API bool r = SliderVoidIntArray(label, value_adapt_modifiable);
                return std::make_tuple(r, value);
            };

            return SliderVoidIntArray_adapt_modifiable_immutable_to_return(label, value);
        },     py::arg("label"), py::arg("value"));

    m.def("add",
        add,
        py::arg("a"), py::arg("b"),
        "Adds two numbers");

    m.def("sub",
        sub, py::arg("a"), py::arg("b"));

    m.def("mul",
        mul, py::arg("a"), py::arg("b"));


    auto pyClassFoo = py::class_<Foo>
        (m, "Foo", "A superb struct")
        .def(py::init<>())
        .def_property("values",
            [](Foo &self) -> pybind11::array
            {
                auto dtype = pybind11::dtype(pybind11::format_descriptor<int>::format());
                auto base = pybind11::array(dtype, {2}, {sizeof(int)});
                return pybind11::array(dtype, {2}, {sizeof(int)}, self.values, base);
            }, [](Foo& self) {},
            "")
        .def_property("flags",
            [](Foo &self) -> pybind11::array
            {
                auto dtype = pybind11::dtype(pybind11::format_descriptor<bool>::format());
                auto base = pybind11::array(dtype, {3}, {sizeof(bool)});
                return pybind11::array(dtype, {3}, {sizeof(bool)}, self.flags, base);
            }, [](Foo& self) {},
            "")
        .def_readwrite("factor", &Foo::factor, "Multiplication factor")
        .def_readwrite("delta", &Foo::delta, "addition factor")
        .def("calc",
            &Foo::calc,
            py::arg("x"),
            "Do some math")
        ;


    m.def("foo_instance",
        FooInstance,
        "return_value_policy::reference",
        pybind11::return_value_policy::reference);

    m.def("add_overload",
        py::overload_cast<int, int>(add_overload), py::arg("a"), py::arg("b"));

    m.def("add_overload",
        py::overload_cast<int, int, int>(add_overload), py::arg("a"), py::arg("b"), py::arg("c"));


    auto pyClassFooOverload = py::class_<FooOverload>
        (m, "FooOverload", "")
        .def(py::init<>()) // implicit default constructor
        .def("add_overload",
            py::overload_cast<int, int>(&FooOverload::add_overload), py::arg("a"), py::arg("b"))
        .def("add_overload",
            py::overload_cast<int, int, int>(&FooOverload::add_overload), py::arg("a"), py::arg("b"), py::arg("c"))
        ;


    m.def("modify_string",
        [](BoxedString & s)
        {
            auto ModifyString_adapt_modifiable_immutable = [](BoxedString & s)
            {
                std::string * s_boxed_value = & (s.value);

                ModifyString(s_boxed_value);
            };

            ModifyString_adapt_modifiable_immutable(s);
        },
        py::arg("s"),
        "\n Test Boxed String\n");
    // </namespace LiterateGeneratorExample>
    ////////////////////    </generated_from:litgensample.h>    ////////////////////

    // </litgen_pydef> // Autogenerated code end
    // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  AUTOGENERATED CODE END !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
}
