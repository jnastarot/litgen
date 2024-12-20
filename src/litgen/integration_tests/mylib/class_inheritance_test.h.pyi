# ============================================================================
# This file was autogenerated
# It is presented side to side with its source: class_inheritance_test.h
#    (see integration_tests/bindings/lg_mylib/__init__pyi which contains the full
#     stub code, including this code)
# ============================================================================

# type: ignore
# ruff: noqa: F821

# <litgen_stub> // Autogenerated code below! Do not edit!
####################    <generated_from:class_inheritance_test.h>    ####################

# pybind11 supports bindings for multiple inheritance, nanobind does not
# #ifdef BINDING_MULTIPLE_INHERITANCE
#
# #endif
#

def binding_multiple_inheritance() -> bool:
    pass

def make_dog() -> Animals.Animal:
    """Test that downcasting works: the return type is Animal, but it should bark!"""
    pass

# <submodule animals>
class animals:  # Proxy class that introduces typings for the *submodule* animals
    pass  # (This corresponds to a C++ namespace. All method are static!)

    class Animal:
        def __init__(self, name: str) -> None:
            pass
        name: str

    class Dog(Animals.Animal):
        def __init__(self, name: str) -> None:
            pass
        def bark(self) -> str:
            pass

# </submodule animals>

# <submodule home>
class home:  # Proxy class that introduces typings for the *submodule* home
    pass  # (This corresponds to a C++ namespace. All method are static!)

    class Pet:
        def is_pet(self) -> bool:
            pass
        def __init__(self) -> None:
            """Auto-generated default constructor"""
            pass

    class PetDog(Animals.Dog, Home.Pet):
        def __init__(self, name: str) -> None:
            pass
        def bark(self) -> str:
            pass

# </submodule home>
####################    </generated_from:class_inheritance_test.h>    ####################

# </litgen_stub> // Autogenerated code end!
