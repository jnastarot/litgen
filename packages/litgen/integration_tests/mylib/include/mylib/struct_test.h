#include "mylib/api_marker.h"

#include <stdio.h>
#include <vector>
#include <string>


// A superb struct
struct MyStruct            // MY_API
{
    MyStruct(int factor = 10, const std::string& message = "hello"): factor(factor), message(message) {}
    ~MyStruct() {}


    ///////////////////////////////////////////////////////////////////////////
    // Simple struct members
    ///////////////////////////////////////////////////////////////////////////
    int factor = 10, delta = 0;
    std::string message;


    ///////////////////////////////////////////////////////////////////////////
    // Stl container members
    ///////////////////////////////////////////////////////////////////////////

    // By default, modifications from python are not propagated to C++ for stl containers
    // (see https://pybind11.readthedocs.io/en/stable/advanced/cast/stl.html)
    std::vector<int> numbers;
    // However you can call dedicated modifying methods
    MY_API void append_number_from_cpp(int v) { numbers.push_back(v); }


    ///////////////////////////////////////////////////////////////////////////
    // Fixed size *numeric* array members
    //
    // They will be published as a py::array, and modifications will be propagated
    // on both sides transparently.
    ///////////////////////////////////////////////////////////////////////////

    int values[2] = {0, 1};
    bool flags[3] = {false, true, false};
    // points is a fixed size array, but not of a numeric type. It will *not* be published!
    Point2 points[2];


    ///////////////////////////////////////////////////////////////////////////
    // Simple methods
    ///////////////////////////////////////////////////////////////////////////

    // calc: example of simple method
    MY_API int calc(int x) { return x * factor + delta; }
    // set_message: another example of simple method
    MY_API void set_message(const std::string & m) { message = m;}

    // unpublished_calc: this function should not be published (no MY_API marker)
    int unpublished_calc(int x) { return x * factor + delta + 3;}

    ///////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////

    // Instance() is a method that returns a pointer that should use `return_value_policy::reference`
    static MyStruct& Instance() { static MyStruct instance; return instance; }  // return_value_policy::reference
};

MY_API MyStruct* FooInstance() { return & MyStruct::Instance(); } // return_value_policy::reference


// StructNotRegistered should not be published, as it misses the marker "// MY_API"
// By default, all enums, namespaces and classes are published,
// but you can decide to include only "marked" ones, via this litgen option:
//       options.srcml_options.api_suffixes = ["MY_API"]
//
// Note: Do not remove the empty line below, otherwise this comment would become part of
//       the enum's doc, and cause it to be registered (since it contains "MY_API")

struct StructNotRegistered
{
    int a = 0;
};