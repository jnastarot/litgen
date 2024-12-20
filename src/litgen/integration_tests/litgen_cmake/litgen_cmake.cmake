set(litgen_cmake_help_message "

This Cmake module provides two public functions:


litgen_find_pybind11()
*******************************************************************************
litgen_find_pybind11() will find pybind11 and Python3
When building via CMake, you may have to specify Python_EXECUTABLE via
     -DPython_EXECUTABLE=/path/to/your/venv/bin/python


litgen_setup_module(bound_library python_native_module_name python_module_name)
*******************************************************************************
litgen_setup_module is a helper function that will:
* link the python native module (.so) to the bound C++ library (bound_library)
* set the install path of the native module to '.' (so that pip install works)
* automatically copy the native module to the python module folder after build
(so that editable mode works even when you modify the C++ library and rebuild)
* set the VERSION_INFO macro to the project version defined in CMakeLists.txt

")

# When building outside of skbuild, we need to add the path to pybind11 provided by pip
function(_lg_add_pybind11_pip_cmake_prefix_path)
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c
        "import pybind11; print(pybind11.get_cmake_dir())"
        OUTPUT_VARIABLE pybind11_cmake_dir
        OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ECHO STDOUT
        RESULT_VARIABLE _result
    )
    if(NOT _result EQUAL 0)
        message(FATAL_ERROR "
            Make sure pybind11 is installed via pip:
                pip install pybind11
            Also, make sure you are using the correct python executable:
                -DPython_EXECUTABLE=/path/to/your/venv/bin/python
        ")
    endif()
    set(CMAKE_PREFIX_PATH ${CMAKE_PREFIX_PATH} "${pybind11_cmake_dir}" PARENT_SCOPE)
endfunction()


function(litgen_find_pybind11)
    if(SKBUILD)
        # we only need the Development.Module component to build native modules
        find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module)
    else()
        # when building via CMake, we need the full Development component,
        # to be able to debug the native module
        find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development)
    endif()
    set(Python_EXECUTABLE ${Python_EXECUTABLE} CACHE PATH "Python executable" FORCE)

    if(NOT SKBUILD)
        # when building via CMake, we need to add the path to pybind11 provided by pip
        # (skbuild does it automatically)
        _lg_add_pybind11_pip_cmake_prefix_path()
    endif()

    find_package(pybind11 CONFIG REQUIRED)
endfunction()


macro(litgen_find_nanobind)
    # cf https://nanobind.readthedocs.io/en/latest/building.html
    if (CMAKE_VERSION VERSION_LESS 3.18)
        set(DEV_MODULE Development)
    else()
        set(DEV_MODULE Development.Module)
    endif()

    find_package(Python 3.8 COMPONENTS Interpreter ${DEV_MODULE} REQUIRED)

    # Detect the installed nanobind package and import it into CMake
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
        OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)
    find_package(nanobind CONFIG REQUIRED)

    if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
        set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
        set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
    endif()
endmacro()


function(litgen_setup_module
    # Parameters explanation, with an example: let's say we want to build binding for a C++ library named "foolib",
    bound_library               #  name of the C++ for which we build bindings ("foolib")
    python_native_module_name   #  name of the native python module that provides bindings (for example "_foolib")
    python_module_name          #  name of the standard python module that will import the native module (for example "foolib")
    editable_bindings_folder    # path to the folder containing the python bindings for editable mode (for example "_stubs/")
)
    target_link_libraries(${python_native_module_name} PRIVATE ${bound_library})

    # Set python_native_module_name install path to ${python_module_name} (required by skbuild)
    install(TARGETS ${python_native_module_name} DESTINATION ${python_module_name})

    # Set VERSION_INFO macro to the project version defined in CMakeLists.txt (absolutely optional)
    target_compile_definitions(${python_native_module_name} PRIVATE VERSION_INFO=${PROJECT_VERSION})

    # Copy the python module for editable mode
    set(bindings_module_folder ${editable_bindings_folder}/${python_module_name})
    set(python_native_module_editable_location ${bindings_module_folder}/$<TARGET_FILE_NAME:${python_native_module_name}>)
    add_custom_target(
        ${python_module_name}_deploy_editable
        ALL
        COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:${python_native_module_name}> ${python_native_module_editable_location}
        DEPENDS ${python_native_module_name}
    )

    # Also copy the python module to the site-packages folder (for non-editable mode)
    # First, ask python for site-packages folder
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c "import site, os; print([p.replace('\\\\', '/') for p in site.getsitepackages() if 'site-packages' in p][0])"
        OUTPUT_VARIABLE python_site_packages
        OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ECHO STDOUT
        RESULT_VARIABLE _result_python_site_packages
    )
    if(NOT _result_python_site_packages EQUAL 0)
        message(FATAL_ERROR "Failed to get python site-packages folder")
    endif()
    set(python_native_module_editable_location_site_packages ${python_site_packages}/${python_module_name}/$<TARGET_FILE_NAME:${python_native_module_name}>)
    add_custom_target(
        ${python_module_name}_deploy_editable_site_packages
        ALL
        COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:${python_native_module_name}> ${python_native_module_editable_location_site_packages}
        DEPENDS ${python_native_module_name})
    # message(STATUS "Python native module will be copied to ${python_native_module_editable_location_site_packages}")

endfunction()
