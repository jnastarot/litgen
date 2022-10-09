# ============================================================================
# This file was autogenerated
# It is presented side to side with its source: class_adapt_test.h
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
####################    <generated_from:class_adapt_test.h>    ####################


class Color4:
    def __init__(self, _rgba: List[int]) -> None:
        """ The constructor params will automatically be "adapted" into std::array<uint8_t, 4>"""
        pass

    # This member will be stored as a modifiable numpy array
    rgba: np.ndarray  # ndarray[type=uint8_t, size=4]
####################    </generated_from:class_adapt_test.h>    ####################

# </litgen_stub> // Autogenerated code end!