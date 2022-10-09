# ============================================================================
# This file was autogenerated
# It is presented side to side with its source: namespace_test.h
#    (see integration_tests/bindings/lg_mylib/__init__pyi which contains the full
#     stub code, including this code)
# ============================================================================

# type: ignore
import sys
from typing import Literal, List, Any, Optional, Tuple, Dict
import numpy as np
from enum import Enum, auto
import numpy

# <litgen_stub> // Autogenerated code below! Do not edit!
####################    <generated_from:namespace_test.h>    ####################


def foo_root() -> int:
    pass



"""MY_API This namespace should not be outputted as a submodule (it is considered a root namespace)"""



# <submodule Inner>
class Inner: # Proxy class that introduces typings for the *submodule* Inner
    # (This corresponds to a C++ namespace. All method are static!)
    """ this is an inner namespace (this comment should become the namespace doc)"""
    def foo_inner() -> int:
        pass
    def foo_inner2() -> int:
        pass

# </submodule Inner>
####################    </generated_from:namespace_test.h>    ####################

# </litgen_stub> // Autogenerated code end!
