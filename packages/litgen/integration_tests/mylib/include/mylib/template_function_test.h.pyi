# ============================================================================
# This file was autogenerated
# It is presented side to side with its source: template_function_test.h
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
####################    <generated_from:template_function_test.h>    ####################


# AddTemplated is a template function that will be implemented for the types ["int", "double", "std::string"]
#
# See inside autogenerate_mylib.py:
#     options.fn_template_options.add_specialization(r"^AddTemplated$", ["int", "double", "std::string"])

#  ------------------------------------------------------------------------
#      <template specializations for function AddTemplated>
def add_templated(a: int, b: int) -> int:
    pass


def add_templated(a: float, b: float) -> float:
    pass


def add_templated(a: str, b: str) -> str:
    pass
#      </template specializations for function AddTemplated>
#  ------------------------------------------------------------------------


# SumVectorAndCArray is a template function that will be implemented for the types ["int", "std::string"]
#
# Here, we test two additional thing:
#  - nesting of the T template parameter into a vector
#  - mixing template and function parameter adaptations (here other_values[2] will be transformed into a List[T]
#
# See inside autogenerate_mylib.py:
#     options.fn_template_options.add_specialization(r"^SumVector", ["int", "std::string"])

#  ------------------------------------------------------------------------
#      <template specializations for function SumVectorAndCArray>
def sum_vector_and_c_array(xs: List[int], other_values: List[int]) -> int:
    pass


def sum_vector_and_c_array(xs: List[str], other_values: List[str]) -> str:
    pass
#      </template specializations for function SumVectorAndCArray>
#  ------------------------------------------------------------------------


# Same test, as a method

class FooTemplateFunctionTest:
    #  ------------------------------------------------------------------------
    #      <template specializations for function SumVectorAndCArray>
    def sum_vector_and_c_array(
        self,
        xs: List[int],
        other_values: List[int]
        ) -> int:
        pass

    def sum_vector_and_c_array(
        self,
        xs: List[str],
        other_values: List[str]
        ) -> str:
        pass
    #      </template specializations for function SumVectorAndCArray>
    #  ------------------------------------------------------------------------
####################    </generated_from:template_function_test.h>    ####################

# </litgen_stub> // Autogenerated code end!
