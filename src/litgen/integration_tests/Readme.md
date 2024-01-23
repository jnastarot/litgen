# litgen integration tests

This folder contains a full suite of integration tests for litgen.
- It builds a native C++ library called "mylib"
- It builds a python binding library called "lg_mylib" (with a corresponding pip package name "lg-mylib")

You can install the "lg-mylib" pip package with:
```bash
pip install [-e] .
```

## List of tests and documentation

The different tests are available at [mylib/](mylib/include/mylib).

It is advised to read the different header files inside [mylib/](mylib/), since they are thoroughly
commented and can help understand litgen.


## Folder structure

This folder structure is based on [lg_skbuild_template](https://github.com/pthom/lg_skbuild_template)

Below is a summary of the structure:

```
./
├── pyproject.toml                            # Pip configuration file
├── setup.py                                  # Pip configuration file
├── CMakeLists.txt                            # CMakeLists (used also by pip, via skbuild)
├── requirements-dev.txt
├── Readme.md                                 # this file
├── _skbuild/                                 # temp build directory when building via pip
├── autogenerate_mylib.py                     # This script will read headers in mylib/ and
│                                             # generate bindings using litgen inside:
│                                             #    - bindings/pybind_mylib.cpp (C++ publishing code)
│                                             #    - bindings/lg_mylib/__init__.pyi (stubs)
├── bindings/
│         ├── lg_mylib/
│         │         ├── __init__.py
│         │         ├── __init__.pyi          # file generated by litgen
│         │         └── py.typed
│         ├── module.cpp
│         ├── litgen_glue_code.h              # file generated by litgen
│         └── pybind_mylib.cpp                # file generated by litgen
├── lg_cmake_utils/                           # lg_cmake_utils is a submodule that contains utilities
│         ├── lg_add_imgui_target.cmake       # that make it easier to write cmake code for Pip modules
│         ├── ...
│
├── mylib/                                    # mylib/: contains the C++ library that will be
│         │                                   #  wrapped in a python module
│         │
│         ├── mylib_main/                     # Library "main files"
│         │         ├── CMakeLists.txt
│         │         ├── api_marker.h
│         │         ├── mylib.cpp
│         │         └── mylib.h               # includes all headers from mylib
│         │
│         ├── basic_test.h                    # Some test code in C++ for wich bindings will be generated
│         ├── basic_test.h.pydef.cpp          # Auto-generated pybind11 bindings for this file
│         ├── basic_test.h.pyi                # Auto-generated stub file for this file
│         ├── basic_test.py                   # This is a python test that will check the bindings
│         │
│         ├── c_string_list_test.h            # Some test code in C++ for wich bindings will be generated
│         ├── c_string_list_test.h.pydef.cpp  # Auto-generated pybind11 bindings for this file
│         ├── c_string_list_test.h.pyi        # Auto-generated stub file for this file
│         ├── c_string_list_test.py           # This is a python test that will check the bindings
│         │
│         ├── c_style_array_test.h            # Etc. There are lots of other tests
│                                             # Each of this file is documented, and should
│                                             # help understand litgen better
│                                             # help understand litgen better
│
├── mylib_amalgamation/
│         └── mylib_amalgamation.h            # amalgamated header for mylib/
```