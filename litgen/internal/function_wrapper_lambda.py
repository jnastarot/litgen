"""
We create a lambda in all cases. This helps overloads resolution, because ImPlot uses a lot of them.
For example:
````cpp
    IMPLOT_API void SetupAxisFormat(ImAxis axis, const char* fmt);
    IMPLOT_API void SetupAxisFormat(ImAxis axis, ImPlotFormatter formatter, void* data = NULL);
````
In this case, a function pointer like &SetupAxisFormat is ambiguous.

Easy case: functions without buffer
***********************************
The function overload:
    IMPLOT_API void SetupAxisFormat(ImAxis axis, const char* fmt);

We will create the lambda:
    [](ImAxis axis, const char* fmt)
    {
        return SetupAxisFormat(axis, fmt);
    },

Case with native arrays
***********************

A declaration like (which is templated on T):
    IMPLOT_TMP void PlotScatter(const char* label_id, const T* values, int count, int stride=sizeof(T));

Shall be wrapped like this:
    [](const char* label_id, const py::array& values, int stride = -1)
    {
        if (stride == -1)
            stride = values.itemsize();
        auto count = values.shape(0);
        return PlotScatter(label_id, values, count, stride);
    },
"""
from code_types import *
import code_types
import code_utils
from options import CodeStyleOptions
import copy


def _possible_buffer_pointer_types(options: CodeStyleOptions):
    types =   [t + "*" for t in options.buffer_types] \
            + [t + " *" for t in options.buffer_types]
    return types


def _possible_buffer_template_pointer_types(options: CodeStyleOptions):
    types =   [t + "*" for t in options.buffer_template_types] \
              + [t + " *" for t in options.buffer_template_types]
    return types


def _looks_like_param_buffer_standard(param: PydefAttribute, options: CodeStyleOptions) -> bool:
    if not options.buffer_flag_replace_by_array:
        return False
    for possible_buffer_type in _possible_buffer_pointer_types(options):
        if code_utils.contains_pointer_type(param.type_cpp, possible_buffer_type):
            return True
    return False


def _looks_like_param_template_buffer(param: PydefAttribute, options: CodeStyleOptions) -> bool:
    if not options.buffer_flag_replace_by_array:
        return False
    for possible_buffer_type in _possible_buffer_template_pointer_types(options):
        if code_utils.contains_pointer_type(param.type_cpp, possible_buffer_type):
            return True
    return False


def _looks_like_param_buffer_template_or_not(param: PydefAttribute, options: CodeStyleOptions) -> bool:
    return _looks_like_param_buffer_standard(param, options) or _looks_like_param_template_buffer(param, options)


def _looks_like_buffer_size_name(param: PydefAttribute, options: CodeStyleOptions) -> bool:
    return code_utils.does_match_regexes(options.buffer_size_regexes, param.name_cpp)


def is_buffer_size_name_at_idx(params: List[PydefAttribute], options: CodeStyleOptions, idx_param: int) -> bool:
    if idx_param == 0:
        return False

    # Test if this is a size preceded by a buffer
    param_n0 = params[idx_param]
    param_n1 = params[idx_param - 1]
    if _looks_like_buffer_size_name(param_n0, options) and _looks_like_param_buffer_template_or_not(param_n1, options):
        return True

    return False


def _is_param_buffer_at_idx_template_or_not(params: List[PydefAttribute], options: CodeStyleOptions, idx_param: int) -> bool:
    if idx_param > len(params) - 2:
        return False

    if not _looks_like_param_buffer_template_or_not(params[idx_param], options):
        return False

    # Test if this is a buffer (optionally followed by other buffers), then followed by a size
    nb_additional_buffers = 1
    idx_next_param = idx_param + 1
    while nb_additional_buffers < 5 and idx_next_param < len(params):
        if _looks_like_buffer_size_name(params[idx_next_param], options):
            return True
        if not _looks_like_param_buffer_template_or_not(params[idx_next_param], options):
            return False
        idx_next_param += 1
        nb_additional_buffers += 1

    return False


def _contains_buffer(params: List[PydefAttribute], options: CodeStyleOptions) -> bool:
    for idx in range(len(params)):
        if _is_param_buffer_at_idx_template_or_not(params, options, idx):
            return True
    return False


def _contains_template_buffer(params: List[PydefAttribute], options: CodeStyleOptions) -> bool:
    if not _contains_buffer(params, options):
        return False
    result = False
    buffer_params_list=  _buffer_params_list(params, options)
    for buffer_param in buffer_params_list:
        is_template_buffer = _looks_like_param_template_buffer(buffer_param, options)
        if is_template_buffer:
            result = True
    return result


def _first_template_buffer_param(params: List[PydefAttribute], options: CodeStyleOptions) -> Optional[PydefAttribute]:
    buffer_params_list=  _buffer_params_list(params, options)
    for buffer_param in buffer_params_list:
        is_template_buffer = _looks_like_param_template_buffer(buffer_param, options)
        if is_template_buffer:
            return buffer_param
    return None


def _first_buffer_param(params: List[PydefAttribute], options: CodeStyleOptions) -> Optional[PydefAttribute]:
    buffer_params_list=  _buffer_params_list(params, options)
    for buffer_param in buffer_params_list:
        is_buffer = _looks_like_param_buffer_template_or_not(buffer_param, options)
        if is_buffer:
            return buffer_param
    return None


def is_param_variadic_format(params: List[PydefAttribute], options: CodeStyleOptions, idx_param: int) -> bool:
    if idx_param == 0:
        return False
    param = params[idx_param]
    previous_param = params[idx_param - 1]
    return param.name_cpp == "..." and (previous_param.type_cpp == "const char *" or previous_param.type_cpp == "const char*")


def _is_first_param_of_variadic_format(params: List[PydefAttribute], options: CodeStyleOptions, idx_param: int) -> bool:
    if idx_param == len(params) - 1:
        return False
    param = params[idx_param]
    next_param = params[idx_param + 1]
    return next_param.name_cpp == "..." and (param.type_cpp == "const char *" or param.type_cpp == "const char*")


def is_default_sizeof_param(param: PydefAttribute, options: CodeStyleOptions) -> bool:
    if not options.buffer_flag_replace_by_array:
        return False
    return param.default_value_cpp.strip().startswith("sizeof")


def _param_buffer_replaced_by_array(param: PydefAttribute, options: CodeStyleOptions) -> PydefAttribute:
    if not options.buffer_flag_replace_by_array:
        return param

    for possible_buffer_type in _possible_buffer_pointer_types(options) + _possible_buffer_template_pointer_types(options):
        if code_utils.contains_pointer_type(param.type_cpp, possible_buffer_type):
            param_copy = copy.deepcopy(param)
            param_copy.type_cpp = param.type_cpp.replace(possible_buffer_type, "py::array &")
            return param_copy
    return param


def _buffer_params_list(params: List[PydefAttribute], options: CodeStyleOptions) -> List[PydefAttribute]:
    if not options.buffer_flag_replace_by_array:
        return []
    r = []
    for idx_param, param in enumerate(params):
        if _is_param_buffer_at_idx_template_or_not(params, options, idx_param):
            r.append(param)
    return r


def _make_call_function(function_infos: FunctionsInfos, is_method, options: CodeStyleOptions) -> List[str]:
    params = function_infos.get_parameters()
    is_template = _contains_template_buffer(params, options)
    first_template_buffer_param = _first_template_buffer_param(params, options)
    return_str1 = "" if function_infos.function_code.return_type_cpp == "void" else "return "
    return_str2 = " return;" if function_infos.function_code.return_type_cpp == "void" else ""
    self_prefix = "self." if is_method else ""

    code_lines = []
    if is_template:
        assert first_template_buffer_param is not None
        code_lines.append(f"    char array_type = {first_template_buffer_param.name_cpp}.dtype().char_();")

        for py_array_type in code_types.py_array_types():

            cast_type = code_types.py_array_type_to_cpp_type(py_array_type) + "*"

            code_lines.append(f"    if (array_type == '{py_array_type}')")
            attrs_function_call = _lambda_params_call(params, options, cast_type)
            code_lines.append(f"        {{ {return_str1}{self_prefix}{function_infos.function_name_cpp()}({attrs_function_call});{return_str2} }}")

        code_lines.append("")
        code_lines.append(f'    // If we arrive here, the array type is not supported!')
        code_lines.append(f'    throw std::runtime_error(std::string("Bad array type: ") + array_type );')

    else:
        if _contains_buffer(params, options):
            first_buffer_param = _first_buffer_param(params, options)
            expected_py_array_type = code_types.cpp_type_to_py_array_type(first_buffer_param.type_cpp)
            error_message = f"""
                Bad type!  Expected a buffer of native type:
                            {first_buffer_param.type_cpp}
                        Which is equivalent to 
                            {expected_py_array_type}
                        (using py::array::dtype().char_() as an id)
            """
            error_message_docstring = f'std::string(R"msg({error_message})msg")'

            code_lines.append(f"    char array_type = {first_buffer_param.name_cpp}.dtype().char_();")
            code_lines.append(f"    if (array_type != '{expected_py_array_type}')")
            code_lines.append(f'        throw std::runtime_error({error_message_docstring});')

        cast_type = None
        attrs_function_call = _lambda_params_call(params, options, cast_type)
        code_lines.append(f"    {{ {return_str1}{self_prefix}{function_infos.function_name_cpp()}({attrs_function_call});{return_str2} }}")

    return code_lines


def _template_body_code(function_infos: FunctionsInfos, is_method: bool, options: CodeStyleOptions) -> List[str]:

    params = function_infos.get_parameters()

    r = []

    #
    # Process buffer params
    #
    buffer_params_list=  _buffer_params_list(params, options)
    for buffer_param in buffer_params_list:
        is_const = buffer_param.type_cpp.startswith("const")
        is_template_buffer = _looks_like_param_template_buffer(buffer_param, options)
        if is_const:
            code_template = """
                // convert PARAM_NAME_CPP (py::array&) to C standard buffer (const)
                const void* PARAM_NAME_CPP_buffer = PARAM_NAME_CPP.data();
                int PARAM_NAME_CPP_count = PARAM_NAME_CPP.shape()[0];
            """[1:]
        else:
            code_template = """
                // convert PARAM_NAME_CPP (py::array&) to C standard buffer (mutable)
                void* PARAM_NAME_CPP_buffer = PARAM_NAME_CPP.mutable_data();
                int PARAM_NAME_CPP_count = PARAM_NAME_CPP.shape()[0];
            """[1:]
        code_template = code_utils.indent_code_force(code_template, 4)

        code = code_template
        code = code.replace("PARAM_NAME_CPP", buffer_param.name_cpp)

        r += code.split("\n")

    #
    # Process sizeof params
    #
    idx_sizeof_param = 0
    for sizeof_param in params:
        if not is_default_sizeof_param(sizeof_param, options):
            continue
        assert idx_sizeof_param < len(buffer_params_list)
        related_buffer_param = buffer_params_list[idx_sizeof_param]

        code_template = """
    // process SIZEOF_PARAM_NAME default value (which was a sizeof in C++)
    int BUFFER_PARAM_NAME_CPP_SIZEOF_PARAM_NAME = SIZEOF_PARAM_NAME;
    if (BUFFER_PARAM_NAME_CPP_SIZEOF_PARAM_NAME == -1)
        BUFFER_PARAM_NAME_CPP_SIZEOF_PARAM_NAME = (int)BUFFER_PARAM_NAME_CPP.itemsize();
        """[1:]
        code = code_template
        code = code.replace("SIZEOF_PARAM_NAME", sizeof_param.name_cpp)
        code = code.replace("BUFFER_PARAM_NAME_CPP", related_buffer_param.name_cpp)
        r += code.split("\n")

        idx_sizeof_param += 1

    #
    # call the function at the end of the lambda
    #
    r += _make_call_function(function_infos, is_method, options)
    return r


def _lambda_params_signature(
        params: List[PydefAttribute],
        options: CodeStyleOptions,
        parent_struct_name: str = "") -> str:

    if not options.buffer_flag_replace_by_array:
        return code_types._pydef_attributes_as_cpp_declaration(params)

    new_params: List[PydefAttribute] = []

    if len(parent_struct_name) > 0:
        new_params.append( PydefAttribute(type_cpp=parent_struct_name + "&", name_cpp="self") )

    idx_param = 0
    while idx_param < len(params):
        param = params[idx_param]
        flag_replaced = False
        # Process buffer params: replace by array
        if _is_param_buffer_at_idx_template_or_not(params, options, idx_param):
            new_param = _param_buffer_replaced_by_array(param, options)
            new_params.append(new_param)
            flag_replaced = True
        # Process count params: do not use in the lambda signature
        if is_buffer_size_name_at_idx(params, options, idx_param):
            flag_replaced = True
        # Process sizeof params (in the case of templated functions): set as -1 by default (the lambda code will initialize it if needed)
        if is_default_sizeof_param(param, options):
            new_param = copy.deepcopy(param)
            new_param.default_value_cpp = "-1"
            new_params.append(new_param)
            flag_replaced = True
        if is_param_variadic_format(params, options, idx_param):
            flag_replaced = True

        if not flag_replaced:
            new_params.append(param)

        idx_param += 1

    return code_types._pydef_attributes_as_cpp_declaration(new_params)


def _lambda_params_call(
        params: List[PydefAttribute],
        options: CodeStyleOptions,
        forced_cast_type: Optional[str]
        ) -> str:

    if not options.buffer_flag_replace_by_array:
        return pydef_attributes_as_cpp_function_params(params)

    buffer_params_list=  _buffer_params_list(params, options)
    idx_buffer_params_list = 0
    idx_count_param = 0
    idx_sizeof_param = 0

    new_params_code = []
    idx_param = 0
    while idx_param < len(params):
        param = params[idx_param]
        flag_replaced = False
        # Process buffer params: replace by buffer created in the lambda
        if _is_param_buffer_at_idx_template_or_not(params, options, idx_param):
            buffer_param = buffer_params_list[idx_buffer_params_list]
            buffer_variable_name = f"{buffer_param.name_cpp}_buffer"

            cast_type_this_param = buffer_param.type_cpp
            if forced_cast_type is not None:
                cast_type_this_param = forced_cast_type
                if buffer_param.type_cpp.startswith("const"):
                    cast_type_this_param = "const " + cast_type_this_param

            param_code = f"static_cast<{cast_type_this_param}>({buffer_variable_name})"
            new_params_code.append(param_code)
            idx_buffer_params_list += 1
            flag_replaced = True
        # Process count params: replace by variable created in the lambda
        if is_buffer_size_name_at_idx(params, options, idx_param):
            assert idx_count_param < len(buffer_params_list)
            buffer_param = buffer_params_list[idx_count_param]
            size_variable_name = f"{buffer_param.name_cpp}_count"
            new_params_code.append(size_variable_name)
            idx_count_param += 1
            flag_replaced = True
        # Process sizeof params: replace by variable created in the lambda
        if is_default_sizeof_param(param, options):
            assert idx_sizeof_param < len(buffer_params_list)
            buffer_param = buffer_params_list[idx_sizeof_param]
            variable_name = "BUFFER_PARAM_NAME_CPP_SIZEOF_PARAM_NAME"
            variable_name = variable_name.replace("BUFFER_PARAM_NAME_CPP", buffer_param.name_cpp)
            variable_name = variable_name.replace("SIZEOF_PARAM_NAME", param.name_cpp)
            new_params_code.append(variable_name)
            idx_sizeof_param += 1
            flag_replaced = True
        if _is_first_param_of_variadic_format(params, options, idx_param):
            new_params_code.append('"%s"')
        if is_param_variadic_format(params, options, idx_param):
            flag_replaced = True

        if not flag_replaced:
            new_params_code.append(param.name_cpp)

        idx_param += 1

    code = ", ".join(new_params_code)
    return code


def make_function_wrapper_lambda(
        function_infos: FunctionsInfos,
        options: CodeStyleOptions,
        parent_struct_name: str = ""
        ) -> str:

    code_lines = []

    def add_line(line):
        code_lines.append(line)

    attrs_lambda_signature = _lambda_params_signature(function_infos.get_parameters(), options, parent_struct_name)

    add_line(f"[]({attrs_lambda_signature})")
    add_line("{")

    is_method = len(parent_struct_name) > 0
    code_lines += _template_body_code(function_infos, is_method, options)

    add_line("},")
    return "\n".join(code_lines)


def make_method_wrapper_lambda(
        function_infos: FunctionsInfos,
        options: CodeStyleOptions,
        parent_struct_name: str) -> str:

    lambda_code = make_function_wrapper_lambda(function_infos, options, parent_struct_name)
    return lambda_code
