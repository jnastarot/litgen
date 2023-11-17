# ============================================================================
# This file was autogenerated
# It is presented side to side with its source: class_copy_test.h
#    (see integration_tests/bindings/lg_mylib/__init__pyi which contains the full
#     stub code, including this code)
# ============================================================================

from typing import overload

# type: ignore

# <litgen_stub> // Autogenerated code below! Do not edit!
####################    <generated_from:class_copy_test.h>    ####################
class Copyable_ImplicitCopyCtor:
    a: int = 1
    def __init__(self, a: int = 1) -> None:
        """Auto-generated default constructor with named params"""
        pass

class Copyable_ExplicitCopyCtor:
    @overload
    def __init__(self) -> None:
        pass
    @overload
    def __init__(self, other: Copyable_ExplicitCopyCtor) -> None:
        pass
    a: int = 1

class Copyable_ExplicitPrivateCopyCtor:
    @overload
    def __init__(self) -> None:
        pass
    a: int = 1

class Copyable_DeletedCopyCtor:
    a: int = 1
    @overload
    def __init__(self) -> None:
        pass

# <submodule aaa>
class aaa:  # Proxy class that introduces typings for the *submodule* aaa
    pass  # (This corresponds to a C++ namespace. All method are static!)

    #  ------------------------------------------------------------------------
    #      <template specializations for class Copyable_Template>
    class Copyable_Template_int:  # Python specialization for Copyable_Template<int>
        value: int
        def __init__(self, value: int = int()) -> None:
            """Auto-generated default constructor with named params"""
            pass
    #      </template specializations for class Copyable_Template>
    #  ------------------------------------------------------------------------

# </submodule aaa>
####################    </generated_from:class_copy_test.h>    ####################

# </litgen_stub> // Autogenerated code end!
