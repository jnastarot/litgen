# ============================================================================
# This file was autogenerated
# It is presented side to side with its source: qualified_scoping_test.h
#    (see integration_tests/bindings/lg_mylib/__init__pyi which contains the full
#     stub code, including this code)
# ============================================================================

# type: ignore

# <litgen_stub> // Autogenerated code below! Do not edit!
####################    <generated_from:qualified_scoping_test.h>    ####################
# <submodule n>
class n:  # Proxy class that introduces typings for the *submodule* n
    pass  # (This corresponds to a C++ namespace. All method are static!)

    class S:
        def __init__(self) -> None:
            """Auto-generated default constructor"""
            pass

    class EC(enum.Enum):
        a = enum.auto()  # (= 0)

    class E(enum.Enum):
        a = enum.auto()  # (= 0)
    @staticmethod
    @overload
    def foo(e: EC = EC.a) -> None:
        pass
    @staticmethod
    @overload
    def foo(e: E = E.a) -> None:
        pass
    @staticmethod
    @overload
    def foo(e: E = E.a, s: S = S()) -> None:
        pass

# </submodule n>
####################    </generated_from:qualified_scoping_test.h>    ####################

# </litgen_stub> // Autogenerated code end!
