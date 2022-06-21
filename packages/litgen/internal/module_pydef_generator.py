from typing import List, Union

from codemanip import code_utils
from litgen.internal import cpp_to_python
from litgen.internal.adapted_types.adapted_types import *
from litgen.internal.cpp_to_python import info_original_location_cpp
from litgen.options import LitgenOptions
from srcmlcpp.srcml_types import *


def generate_boxed_types_binding_code(options: LitgenOptions) -> str:
    boxed_structs = cpp_to_python.BoxedImmutablePythonType.struct_codes()
    boxed_bindings = cpp_to_python.BoxedImmutablePythonType.binding_codes(options)
    if len(boxed_structs) > 0:
        boxed_inner_code = boxed_structs + "\n" + boxed_bindings
        boxed_inner_code = code_utils.unindent_code(boxed_inner_code)

        boxed_code = f"""

                // <Autogenerated_Boxed_Types>
                // Start
                {boxed_inner_code}// End
                // </Autogenerated Boxed Types>


                """
        boxed_code = code_utils.unindent_code(boxed_code)
        return boxed_code
    else:
        return ""


def generate_pydef(
    cpp_unit: Union[CppUnit, CppBlock],
    options: LitgenOptions,
    current_namespaces: List[str] = [],
    add_boxed_types_definitions: bool = False,
) -> str:

    adapted_block = AdaptedBlock(cpp_unit, options)
    block_code = adapted_block.str_pydef()

    if add_boxed_types_definitions:
        code = generate_boxed_types_binding_code(options) + block_code
    else:
        code = block_code
    return code
