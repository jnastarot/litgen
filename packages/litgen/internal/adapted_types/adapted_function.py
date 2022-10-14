from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import List, Optional, cast

from munch import Munch  # type: ignore

from codemanip import code_utils

from srcmlcpp.cpp_types import *

import litgen
from litgen import LitgenOptions
from litgen.internal import cpp_to_python
from litgen.internal.adapted_types.adapted_decl import AdaptedDecl
from litgen.internal.adapted_types.adapted_element import AdaptedElement
from litgen.internal.context.litgen_context import LitgenContext


@dataclass
class AdaptedParameter(AdaptedElement):
    def __init__(self, lg_context: LitgenContext, param: CppParameter) -> None:
        super().__init__(lg_context, param)

    # override
    def cpp_element(self) -> CppParameter:
        return cast(CppParameter, self._cpp_element)

    # override
    def _str_stub_lines(self) -> List[str]:
        raise NotImplementedError()

    # override
    def _str_pydef_lines(self) -> List[str]:
        raise NotImplementedError()

    def is_modifiable_python_immutable_fixed_size_array(self) -> bool:
        is_python_immutable = self.adapted_decl().is_immutable_for_python()

        type_modifiers = self.cpp_element().decl.cpp_type.modifiers
        type_specifiers = self.cpp_element().decl.cpp_type.specifiers

        has_no_modifiers = type_modifiers == []
        is_fixed_size_array = self.cpp_element().decl.is_c_array_known_fixed_size()
        is_const = "const" in type_specifiers

        r = has_no_modifiers and is_fixed_size_array and is_python_immutable and not is_const
        return r

    def is_modifiable_python_immutable_ref_or_pointer(self) -> bool:
        is_python_immutable = self.adapted_decl().is_immutable_for_python()

        type_modifiers = self.cpp_element().decl.cpp_type.modifiers
        type_specifiers = self.cpp_element().decl.cpp_type.specifiers

        is_reference_or_pointer = (type_modifiers == ["*"]) or (type_modifiers == ["&"])
        is_const = "const" in type_specifiers
        is_modifiable = is_reference_or_pointer and not is_const
        r = is_modifiable and is_python_immutable
        return r

    def adapted_decl(self) -> AdaptedDecl:
        adapted_decl = AdaptedDecl(self.lg_context, self.cpp_element().decl)
        return adapted_decl


@dataclass
class AdaptedFunction(AdaptedElement):
    """AdaptedFunction handles the pydef/stub code generation, for free-functions, methods, constructors, and operators.

    It is at the heart of litgen's function and parameters transformations.

    @see AdaptedElement: it extends AdaptedElement and overrides _str_pydef_lines and _str_stub_lines.

    AdaptedFunction is able to handle quite a lot of cases. Its code is separated in several logical sections:
        - Doc about functions parameters adaptation
        - Initialization and basic services
        - pydef and stub code generation
        - _cp_: (deep)copy handling
        - _tpl_: template classes handling
        - _virt_: virtual methods handling
        - _prot_: protected methods handling (when they are published)


    #  ============================================================================================
    #
    #    Doc about functions parameters adaptation
    #
    #  ============================================================================================


    Litgen may apply some adaptations to function  parameters:
        * C style buffers are transformed to py::arrays
        * C style strings lists are transformed to List[string]
        * C style arrays are boxed or transformed to List
        * variadic format params are discarded
        * (etc.)

    AdaptedFunction contain several important parameter for functions parameters adaptation.
        1. self._cpp_element: CppElementAndComment
        ------------------------------------------
            self._cpp_element: CppElementAndComment
                contains the original C++ function declaration (of type CppFunctionDecl, but stored
                as a CppElementAndComment)
            self.cpp_element() will return self_cpp_element, casted to CppFunctionDecl

        2. self.cpp_adapted_function: CppFunctionDecl
        ---------------------------------------------
            self.cpp_adapted_function is a CppFunctionDecl where some parameters might have been adapted.
            It does *not* have the same signature, as it was "adapted for python".

        3. cpp_adapter_code: Optional[str] = None
        -----------------------------------------
            cpp_adapter_code is some C++ code that will define lambda function(s) whose signature makes it
            possible to bind them to python. Those lambda function(s) ultimately call the original function.

        4. lambda_to_call: Optional[str] = None
        ---------------------------------------
            There might be a series of lambda inside `cpp_adapter_code`.
            lambda_to_call simply store the name the name of the last created lambda.
            If a successive lambda occurs, it will call `lambda_to_call` and its name
            will then be stored into `lambda_to_call`


    Below is a full concrete example in order to clarify.

    A/ Let's consider this C++ function
            ````cpp
            //     :param buffer:          1/    a C-style buffer
            //     :param count:                   the size of the buffer
            //     :param out_values:      2/    output double values (a C modifiable array)
            //     :param in_flags:        3/   input bool flags
            //     :param text and ... :   4/   (archaic) C-style formatted text
            void Foo(uint8_t * buffer, size_t count, double out_values[2], const bool in_flags[2], const char* text, ...);
            ````

            it is not easily portable to python, since all the parameters (except "count") are incompatible with
            a simple type translation to python.

    B/ In fact, when published in python, it will have the following python signature (in the stub file):

        ````python
        def foo(
            buffer: numpy.ndarray,                             # 1/   The C buffer was transformed into a py::array
            out_values_0: BoxedDouble,                         # 2/  Modifiable array params were "Boxed"
            out_values_1: BoxedDouble,                         #     (since float are immutable in python)
            in_flags: List[bool],                              # 3/ Const array params are passed as a list
            text: str                                          # 4/  Variadic ("...") params are removed from the signature
            ) -> None:
            pass
        ````

    C/ And the `cpp_adapted_function` C++ signature would be:
        ````cpp
        void Foo(
            py::array & buffer,
            BoxedDouble & out_values_0, BoxedDouble & out_values_1,
            const std::array<bool, 2>& in_flags,
            const char * text);
        ````

    D/ And `cpp_adapter_code` would contain some C++ code that defines several lambdas in order to adapt
    the new C++ signature to the original one.
    It will be generated by `apply_all_adapters` and it will look like:

        ````cpp
        auto Foo_adapt_c_buffers = [](               // First lambda that calls Foo()
            py::array & buffer,
            double out_values[2],
            const bool in_flags[2],
            const char * text, ... )
        {
            // ... Some glue code
            Foo(static_cast<uint8_t *>(buffer_from_pyarray), static_cast<size_t>(buffer_count), out_values, in_flags, text, );
        };

        auto Foo_adapt_fixed_size_c_arrays = [&Foo_adapt_c_buffers](   // Second lambda that calls the first lambda
            py::array & buffer,
            BoxedDouble & out_values_0, BoxedDouble & out_values_1,
            const std::array<bool, 2>& in_flags,
            const char * text, ... )
        {
            // ... Some glue code
            Foo_adapt_c_buffers(buffer, out_values_raw, in_flags.data(), text, );
        };

        auto Foo_adapt_variadic_format = [&Foo_adapt_fixed_size_c_arrays]( // Third lambda that calls the second lambda
            py::array & buffer,                                            // This is the lambda that is published
            BoxedDouble & out_values_0,                                    // as a python interface!
            BoxedDouble & out_values_1,
            const std::array<bool, 2>& in_flags,
            const char * text)
        {
            // ... Some glue code
            Foo_adapt_fixed_size_c_arrays(buffer, out_values_0, out_values_1, in_flags, "%s", text);
        };
        ````

    E/ And `lambda_to_call` will contain the name of the lambda that is published
      (in our example, it is "Foo_adapt_variadic_format")
    """

    # Members related to parameters adaptation: see "Doc about functions parameters adaptation"
    cpp_adapted_function: CppFunctionDecl
    cpp_adapter_code: Optional[str] = None
    lambda_to_call: Optional[str] = None
    # Other members
    return_value_policy: str = ""
    is_overloaded: bool = False
    is_type_ignore: bool = False
    is_vectorize_impl: bool = False
    has_adapted_template_buffer: bool = False

    #  ============================================================================================
    #
    #    Initialization
    #
    #  ============================================================================================

    def __init__(
        self,
        lg_context: LitgenContext,
        function_infos: CppFunctionDecl,
        is_overloaded: bool,
        initial_lambda_to_call: Optional[str] = None,
    ) -> None:
        from litgen.internal import adapt_function_params
        from litgen.internal.adapted_types import operators

        self.cpp_adapted_function = function_infos
        operators.raise_if_unsupported_operator(self.cpp_adapted_function)

        self.cpp_adapter_code = None
        self.lambda_to_call = initial_lambda_to_call
        super().__init__(lg_context, function_infos)
        self._pydef_fill_return_value_policy()
        self._stub_fill_is_type_ignore()

        self.is_overloaded = is_overloaded
        if code_utils.does_match_regex(self.options.fn_force_overload__regex, self.cpp_element().function_name):
            self.is_overloaded = True

        if self.cpp_element().is_inferred_return_type():
            self.cpp_element().cpp_element_comments.comment_end_of_line += "\n(C++ auto return type)"

        adapt_function_params.apply_all_adapters(self)

    @staticmethod
    def init_is_function_publishable(options: LitgenOptions, cpp_function: CppFunctionDecl) -> bool:
        """
        This static method is called even before construction. If it returns False,
        it mean that the CppFunctionDecl shall not be ported to python.
        """
        if cpp_function.is_destructor():
            return False

        if "delete" in cpp_function.specifiers:
            return False

        # Check options.fn_exclude_by_name__regex
        if code_utils.does_match_regex(options.fn_exclude_by_name__regex, cpp_function.function_name):
            return False

        # Exclude pointer to pointer
        if cpp_function.returns_pointer_to_pointer() or cpp_function.parameter_list.contains_pointer_to_pointer_param():
            return False

        # Check options.fn_exclude_by_param_type__regex
        reg = options.fn_exclude_by_param_type__regex
        if hasattr(cpp_function, "return_type"):
            if code_utils.does_match_regex(reg, cpp_function.return_type.str_code()):
                return False
        for param in cpp_function.parameter_list.parameters:
            if code_utils.does_match_regex(reg, param.decl.cpp_type.str_code()):
                return False

        # Check options.functions_api_prefixes_list
        if len(options.srcmlcpp_options.functions_api_prefixes_list()) > 0 and options.fn_exclude_non_api:
            if not hasattr(cpp_function, "return_type"):
                return True
            has_api_prefix = False
            for api_prefix in options.srcmlcpp_options.functions_api_prefixes_list():
                if api_prefix in cpp_function.return_type.specifiers:
                    has_api_prefix = True
            return has_api_prefix
        else:
            return True

    #  ============================================================================================
    #
    #    Basic services
    #
    #  ============================================================================================

    # override
    def cpp_element(self) -> CppFunctionDecl:
        return cast(CppFunctionDecl, self._cpp_element)

    def __str__(self) -> str:
        r = str(self.cpp_element())
        return r

    def is_method(self) -> bool:
        return self.cpp_element().is_method()

    def is_constructor(self) -> bool:
        r = self.cpp_element().is_constructor()
        return r

    def adapted_parameters(self) -> List[AdaptedParameter]:
        r: List[AdaptedParameter] = []
        for param in self.cpp_adapted_function.parameter_list.parameters:
            adapted_param = AdaptedParameter(self.lg_context, param)
            r.append(adapted_param)
        return r

    def shall_vectorize(self) -> bool:
        ns_name = self.cpp_element().cpp_scope(include_self=False).str_cpp()
        match_ns_name = code_utils.does_match_regex(self.options.fn_namespace_vectorize__regex, ns_name)
        match_fn_name = code_utils.does_match_regex(self.options.fn_vectorize__regex, self.cpp_element().function_name)
        r = match_ns_name and match_fn_name and not self.is_vectorize_impl
        return r

    #  ============================================================================================
    #
    #    _str_pydef_lines: main API for pydef code generation
    #    We override _str_pydef_lines methods from AdaptedElement
    #
    #    methods prefix: _pydef_
    #
    #  ============================================================================================

    # override
    def _str_pydef_lines(self) -> List[str]:
        from litgen.internal.adapted_types import operators

        # Bail out if this is a <=> operator (aka spaceship operator)
        # In this case, it will be split in 5 operators by calling 5 times _str_pydef_lines()
        if operators.is_spaceship_operator(self):
            new_functions = operators.cpp_split_spaceship_operator(self)
            r = []
            for new_function in new_functions:
                r += new_function._str_pydef_lines()
            return r

        # If this is a template function, implement as many versions
        # as mentioned in the options (see LitgenOptions.fn_template_options)
        # and bail out
        if self._tpl_is_template_non_specialized():
            template_instantiations = self._tpl_split_into_template_instantiations()
            if len(template_instantiations) == 0:
                return []
            else:
                r = []
                for template_instantiation in template_instantiations:
                    r += template_instantiation._str_pydef_lines()
                return r

        if self.is_constructor():
            if self._pydef_flag_needs_lambda():
                code = self._pydef_with_lambda_str_impl()
            else:
                code = self._pydef_constructor_str()
        else:
            if self._pydef_flag_needs_lambda():
                code = self._pydef_with_lambda_str_impl()
            else:
                code = self._pydef_without_lambda_str_impl()

        lines = code.split("\n")

        if self.shall_vectorize():
            new_vectorized_function = copy.copy(self)
            new_vectorized_function.is_vectorize_impl = True
            lines += new_vectorized_function._str_pydef_lines()

        return lines

    def _pydef_return_str(self) -> str:
        """Creates the return part of the pydef"""

        template_code = "{return_or_nothing}{self_prefix}{function_to_call}({params_call_inner})"

        return_or_nothing = "" if self.cpp_adapted_function.returns_void() else "return "
        self_prefix = "self." if (self.is_method() and self.lambda_to_call is None) else ""
        # fill function_to_call
        function_to_call = (
            self.lambda_to_call
            if self.lambda_to_call is not None
            else self.cpp_adapted_function.function_name_with_specialization()
        )
        # Fill params_call_inner
        params_call_inner = self.cpp_adapted_function.parameter_list.str_names_only_for_call()

        code = code_utils.replace_in_string(
            template_code,
            {
                "return_or_nothing": return_or_nothing,
                "self_prefix": self_prefix,
                "function_to_call": function_to_call,
                "params_call_inner": params_call_inner,
            },
        )
        return code

    def _pydef_end_arg_docstring_returnpolicy(self) -> str:
        template_code = code_utils.unindent_code(
            """
            {_i_}{maybe_py_arg}{maybe_comma}
            {_i_}{maybe_docstring}{maybe_comma}
            {_i_}{maybe_return_value_policy}{maybe_comma}
            {_i_}{maybe_keep_alive}{maybe_comma}
            {_i_}{maybe_call_guard}{maybe_comma}
            """,
            flag_strip_empty_lines=True,
        )

        # Standard replacements dict (r) and replacement dict with possible line removal (l)
        replace_tokens = Munch()
        replace_lines = Munch()

        # fill _i_
        replace_tokens._i_ = self.options.indent_cpp_spaces()

        # fill maybe_py_arg
        pyarg_codes = self._pydef_pyarg_list()
        if len(pyarg_codes) > 0:
            replace_lines.maybe_py_arg = ", ".join(pyarg_codes)
        else:
            replace_lines.maybe_py_arg = None

        # fill maybe_docstring
        comment = self.comment_pydef_one_line()
        if len(comment) == 0:
            replace_lines.maybe_docstring = None
        else:
            replace_lines.maybe_docstring = f'"{comment}"'

        # Fill maybe_return_value_policy
        return_value_policy = self.return_value_policy
        if len(return_value_policy) > 0:
            replace_lines.maybe_return_value_policy = f"pybind11::return_value_policy::{return_value_policy}"
        else:
            replace_lines.maybe_return_value_policy = None

        replace_lines.maybe_keep_alive = self._pydef_fill_keep_alive_from_function_comment()
        replace_lines.maybe_call_guard = self._pydef_fill_call_guard_from_function_comment()

        # Process template
        code = code_utils.process_code_template(
            input_string=template_code,
            replacements=replace_tokens,
            replacements_with_line_removal_if_not_found=replace_lines,
            flag_replace_maybe_comma=True,
        )

        code = code + ")"
        if not self.is_method():
            code = code + ";"

        return code

    def _pydef_method_creation_part(self) -> str:
        """Create the first code line of the pydef"""
        template_code = code_utils.unindent_code(
            """
            {module_or_class}.{def_maybe_static}("{function_name_python}",{location}
            """,
            flag_strip_empty_lines=True,
        )

        # Standard replacements dict (r) and replacement dict with possible line removal (l)
        replace_tokens = Munch()

        # fill module_or_class, function_name, location
        parent_cpp_module_var_name = cpp_to_python.cpp_scope_to_pybind_var_name(self.options, self.cpp_element())
        replace_tokens.module_or_class = "" if self.is_method() else parent_cpp_module_var_name
        if self.is_vectorize_impl:
            replace_tokens.function_name_python = (
                self.options.fn_vectorize_prefix + self.stub_function_name_python() + self.options.fn_vectorize_suffix
            )
        else:
            replace_tokens.function_name_python = self.stub_function_name_python()
        replace_tokens.location = self.info_original_location_cpp()
        replace_tokens.def_maybe_static = "def_static" if self.cpp_element().is_static() else "def"

        r = code_utils.process_code_template(template_code, replace_tokens)
        return r

    def _pydef_without_lambda_str_impl(self) -> str:
        """Create the full code of the pydef, with a direct call to the function or method"""
        template_code = code_utils.unindent_code(
            """
            {pydef_method_creation_part}
            {_i_}{function_pointer}{maybe_comma}{pydef_end_arg_docstring_returnpolicy}"""
        )[1:]

        # Standard replacements dict (r) and replacement dict with possible line removal (l)
        replace_tokens = Munch()
        replace_lines = Munch()

        # fill _i_
        replace_tokens._i_ = self.options.indent_cpp_spaces()

        replace_tokens.pydef_method_creation_part = self._pydef_method_creation_part()

        # fill function_pointer

        function_name = self.cpp_element().function_name_with_specialization()
        function_scope_prefix = self._pydef_str_parent_cpp_scope_prefix()

        if self.is_vectorize_impl:
            replace_tokens.function_pointer = f"py::vectorize({function_scope_prefix}{function_name})"
        else:
            replace_tokens.function_pointer = f"{function_scope_prefix}{function_name}"

        if self.is_method():
            replace_tokens.function_pointer = "&" + replace_tokens.function_pointer

        if self.is_overloaded:
            overload_types = self.cpp_element().parameter_list.str_types_only_for_overload()
            replace_tokens.function_pointer = f"py::overload_cast<{overload_types}>({replace_tokens.function_pointer})"

        # fill pydef_end_arg_docstring_returnpolicy
        replace_tokens.pydef_end_arg_docstring_returnpolicy = self._pydef_end_arg_docstring_returnpolicy()

        # If pydef_end_arg_docstring_returnpolicy is multiline, add \n
        if "\n" in replace_tokens.pydef_end_arg_docstring_returnpolicy:
            replace_tokens.pydef_end_arg_docstring_returnpolicy = (
                "\n" + replace_tokens.pydef_end_arg_docstring_returnpolicy
            )
        else:
            replace_tokens.pydef_end_arg_docstring_returnpolicy = (
                replace_tokens.pydef_end_arg_docstring_returnpolicy.lstrip()
            )

        # Process template
        code = code_utils.process_code_template(
            input_string=template_code,
            replacements=replace_tokens,
            replacements_with_line_removal_if_not_found=replace_lines,
            flag_replace_maybe_comma=True,
        )

        return code

    def _pydef_with_lambda_str_impl(self) -> str:
        """Create the full code of the pydef, with an inner lambda"""

        template_code = code_utils.unindent_code(
            """
            {pydef_method_creation_part}
            {_i_}[]({params_call_with_self_if_method}){lambda_return_arrow}
            {_i_}{
            {_i_}{_i_}{lambda_adapter_code}
            {maybe_empty_line}
            {_i_}{_i_}{return_code};
            {_i_}}{maybe_close_paren_if_ctor}{maybe_comma}{pydef_end_arg_docstring_returnpolicy}"""
        )[1:]

        function_infos = self.cpp_adapted_function

        # Standard replacement dict (r) and replacement dict with possible line removal (l)
        replace_tokens = Munch()
        replace_lines = Munch()

        # fill _i_
        replace_tokens._i_ = self.options.indent_cpp_spaces()

        if self.is_constructor():
            replace_tokens.pydef_method_creation_part = ".def(py::init("
            replace_tokens.maybe_close_paren_if_ctor = ")"
        else:
            replace_tokens.pydef_method_creation_part = self._pydef_method_creation_part()
            replace_tokens.maybe_close_paren_if_ctor = ""

        # fill params_call_with_self_if_method
        _params_list = function_infos.parameter_list.list_types_names_default_for_signature()
        if self.is_method() and not self.is_constructor():
            _self_param = f"{self._pydef_str_parent_cpp_scope()} & self"
            if function_infos.is_const():
                _self_param = "const " + _self_param
            _params_list = [_self_param] + _params_list
        replace_tokens.params_call_with_self_if_method = ", ".join(_params_list)

        # Fill lambda_return_arrow
        if self.cpp_adapted_function.returns_void():
            replace_tokens.lambda_return_arrow = ""
        else:
            full_return_type = self.cpp_adapted_function.str_full_return_type()
            replace_tokens.lambda_return_arrow = f" -> {full_return_type}"

        # fill return_code
        replace_tokens.return_code = self._pydef_return_str()

        # fill lambda_adapter_code
        replace_lines.lambda_adapter_code = self.cpp_adapter_code

        if replace_lines.lambda_adapter_code is not None:
            replace_lines.lambda_adapter_code = code_utils.indent_code(
                replace_lines.lambda_adapter_code,
                indent_str=self.options.indent_cpp_spaces() * 2,
                skip_first_line=True,
            )
            if replace_lines.lambda_adapter_code[-1] == "\n":
                replace_lines.lambda_adapter_code = replace_lines.lambda_adapter_code[:-1]

        # fill maybe_empty_line
        replace_lines.maybe_empty_line = "" if replace_lines.lambda_adapter_code is not None else None

        # fill pydef_end_arg_docstring_returnpolicy
        replace_tokens.pydef_end_arg_docstring_returnpolicy = self._pydef_end_arg_docstring_returnpolicy()
        # If pydef_end_arg_docstring_returnpolicy is multiline, add \n
        if "\n" in replace_tokens.pydef_end_arg_docstring_returnpolicy:
            replace_tokens.pydef_end_arg_docstring_returnpolicy = (
                "\n" + replace_tokens.pydef_end_arg_docstring_returnpolicy
            )

        # Process template
        code = code_utils.process_code_template(
            input_string=template_code,
            replacements=replace_tokens,
            replacements_with_line_removal_if_not_found=replace_lines,
            flag_replace_maybe_comma=True,
        )

        return code

    def _pydef_constructor_str(self) -> str:
        """
        A constructor decl look like this
            .def(py::init<ARG_TYPES_LIST>(),
            PY_ARG_LIST
            DOC_STRING);
        """

        template_code = code_utils.unindent_code(
            """
            .def(py::init<{arg_types}>(){maybe_comma}{location}
            {_i_}{maybe_pyarg}{maybe_comma}
            {_i_}{maybe_docstring}"""
        )[1:]

        function_infos = self.cpp_element()

        if "delete" in function_infos.specifiers:
            return ""

        _i_ = self.options.indent_cpp_spaces()

        arg_types = function_infos.parameter_list.str_types_only_for_overload()
        location = self.info_original_location_cpp()

        if len(self._pydef_pyarg_list()) > 0:
            maybe_pyarg = ", ".join(self._pydef_pyarg_list())
        else:
            maybe_pyarg = None

        if len(self.comment_pydef_one_line()) > 0:
            maybe_docstring = f'"{self.comment_pydef_one_line()}"'
        else:
            maybe_docstring = None

        # Apply simple replacements
        code = template_code
        code = code_utils.replace_in_string(
            code,
            {
                "_i_": _i_,
                "location": location,
                "arg_types": arg_types,
            },
        )

        # Apply replacements with possible line removal
        code = code_utils.replace_in_string_remove_line_if_none(
            code,
            {
                "maybe_docstring": maybe_docstring,
                "maybe_pyarg": maybe_pyarg,
            },
        )

        # Process maybe_comma
        code = code_utils.replace_maybe_comma(code)

        code = code_utils.add_item_before_cpp_comment(code, ")")

        return code

    def _pydef_flag_needs_lambda(self) -> bool:
        r = self.cpp_adapter_code is not None or self.lambda_to_call is not None
        return r

    def _pydef_pyarg_list(self) -> List[str]:
        pyarg_strs: List[str] = []
        for param in self.cpp_adapted_function.parameter_list.parameters:
            adapted_decl = AdaptedDecl(self.lg_context, param.decl)

            # Skip *args and **kwarg
            param_type_cpp = adapted_decl.cpp_element().cpp_type.str_code()
            param_type_cpp_simplified = (
                param_type_cpp.replace("const ", "").replace("pybind11::", "py::").replace(" &", "")
            )
            if param_type_cpp_simplified in ["py::args", "py::kwargs"]:
                continue

            pyarg_str = adapted_decl._str_pydef_as_pyarg()
            pyarg_strs.append(pyarg_str)
        return pyarg_strs

    def _pydef_fill_return_value_policy(self) -> None:
        """Parses the return_value_policy from the function end of line comment
        For example:
            // A static instance (which python shall not delete, as enforced by the marker return_policy below)
            static Foo& Instance() { static Foo instance; return instance; }       // py::return_value_policy::reference
        """
        token = "py::return_value_policy::"

        # Try to find it in eol comment (and clean eol comment if found)
        eol_comment = self.cpp_element().cpp_element_comments.comment_end_of_line
        maybe_return_policy = code_utils.find_word_after_token(eol_comment, token)
        if maybe_return_policy is not None:
            self.return_value_policy = maybe_return_policy
            eol_comment = eol_comment.replace(token + self.return_value_policy, "").rstrip()
            if eol_comment.lstrip().startswith("//"):
                eol_comment = eol_comment.lstrip()[2:]
            self.cpp_element().cpp_element_comments.comment_end_of_line = eol_comment
        else:
            comment_on_previous_lines = self.cpp_element().cpp_element_comments.comment_on_previous_lines
            maybe_return_policy = code_utils.find_word_after_token(comment_on_previous_lines, token)
            if maybe_return_policy is not None:
                self.return_value_policy = maybe_return_policy
                comment_on_previous_lines = comment_on_previous_lines.replace(token + self.return_value_policy, "")
                self.cpp_element().cpp_element_comments.comment_on_previous_lines = comment_on_previous_lines

        # Finally add a comment
        if len(self.return_value_policy) > 0:
            comment_on_previous_lines = self.cpp_element().cpp_element_comments.comment_on_previous_lines
            if len(comment_on_previous_lines) > 0 and comment_on_previous_lines[-1] != "\n":
                comment_on_previous_lines += "\n"
            comment_on_previous_lines += f"return_value_policy::{self.return_value_policy}"
            self.cpp_element().cpp_element_comments.comment_on_previous_lines = comment_on_previous_lines

        # Take options.fn_force_return_policy_reference_for_pointers into account
        function_name = self.cpp_adapted_function.function_name
        options = self.options
        returns_pointer = self.cpp_element().returns_pointer()
        returns_reference = self.cpp_element().returns_reference()
        matches_regex_pointer = code_utils.does_match_regex(
            options.fn_return_force_policy_reference_for_pointers__regex, function_name
        )
        matches_regex_reference = code_utils.does_match_regex(
            options.fn_return_force_policy_reference_for_references__regex, function_name
        )

        if (matches_regex_pointer and returns_pointer) or (matches_regex_reference and returns_reference):
            self.return_value_policy = "reference"

    def _pydef_fill_call_policy_from_function_comment(self, call_policy_token: str) -> Optional[str]:
        function_comment = self.cpp_element().cpp_element_comments.comment()
        if call_policy_token in function_comment:
            idx = function_comment.index(call_policy_token)
            comment_rest = function_comment[idx:]
            if "()" in comment_rest:
                idx2 = comment_rest.index("()")
                keep_alive_code = comment_rest[: idx2 + 2]
                return keep_alive_code
        return None

    def _pydef_fill_keep_alive_from_function_comment(self) -> Optional[str]:
        return self._pydef_fill_call_policy_from_function_comment("py::keep_alive")

    def _pydef_fill_call_guard_from_function_comment(self) -> Optional[str]:
        return self._pydef_fill_call_policy_from_function_comment("py::call_guard")

    def _pydef_str_parent_cpp_scope(self) -> str:
        if self.is_method():
            parent_struct = self.cpp_element().parent_struct_if_method()
            assert parent_struct is not None
            r = parent_struct.qualified_class_name_with_specialization()
        else:
            r = self.cpp_element().cpp_scope(include_self=False).str_cpp()
        return r

    def _pydef_str_parent_cpp_scope_prefix(self) -> str:
        r = self._pydef_str_parent_cpp_scope()
        if len(r) > 0:
            r += "::"
        return r

    #  ============================================================================================
    #
    #    _str_stub_lines: main API for stub code generation
    #    We override _str_stub_lines methods from AdaptedElement
    #
    #    methods prefix: _stub_
    #
    #  ============================================================================================

    # override
    def _str_stub_lines(self) -> List[str]:

        # Handle <=> (aka spaceship) operator, which is split in 5 operators!
        from litgen.internal.adapted_types import operators

        # Bail out if this is a <=> operator (aka spaceship operator)
        # In this case, it will be split in 5 operators by calling 5 times _str_stub_lines()
        if operators.is_spaceship_operator(self):
            new_functions = operators.cpp_split_spaceship_operator(self)
            r = []
            for new_function in new_functions:
                r += new_function._str_stub_lines()
            return r

        # If this is a template function, implement as many versions
        # as mentioned in the options (see LitgenOptions.fn_template_options)
        # and bail out
        if self._tpl_is_template_non_specialized():
            template_instantiations = self._tpl_split_into_template_instantiations()
            if len(template_instantiations) == 0:
                return []
            else:
                r = []
                for template_instantiation in template_instantiations:
                    if len(r) > 0:
                        if self.is_method():
                            r += [""]  # 1 empty lines between methods
                        else:
                            r += ["", ""]  # 2 empty lines between functions
                    r += template_instantiation._str_stub_lines()
                if self.options.fn_template_decorate_in_stub:
                    r = cpp_to_python.surround_python_code_lines(
                        r, f"template specializations for function {self.cpp_element().function_name}"
                    )
                return r

        if self.is_type_ignore:
            comment_python_type_ignore = "  # type: ignore"
        else:
            comment_python_type_ignore = ""

        # Fill a comment that will be written as an indication in the python stub
        comment_python_overridable = ""
        if self.cpp_element().is_virtual_method():
            parent_struct = self.cpp_element().parent_struct_if_method()
            assert parent_struct is not None
            is_overridable = code_utils.does_match_regex(
                self.options.class_override_virtual_methods_in_python__regex, parent_struct.class_name
            )
            if is_overridable:
                comment_python_overridable = " # overridable"
                if self.cpp_element().is_pure_virtual:
                    comment_python_overridable += " (pure virtual)"

        function_name_python = self.stub_function_name_python()
        if self.is_vectorize_impl:
            function_name_python = (
                self.options.fn_vectorize_prefix + function_name_python + self.options.fn_vectorize_suffix
            )
        function_def_code = f"def {function_name_python}("

        return_code = f") -> {self.stub_return_type_python()}:"
        if self.is_vectorize_impl:
            return_code = ") -> np.ndarray:"

        params_strs = self._stub_paramlist_call_python()

        # Try to add function decl + all params and return type on the same line
        def function_name_and_params_on_one_line() -> Optional[str]:
            first_code_line_full = function_def_code
            first_code_line_full += ", ".join(params_strs)
            first_code_line_full += return_code
            first_code_line_full += comment_python_type_ignore + comment_python_overridable
            if (
                self.options.python_max_line_length <= 0
                or len(first_code_line_full) < self.options.python_max_line_length
            ):
                return first_code_line_full
            else:
                return None

        # Else put params one by line
        def function_name_and_params_line_by_line() -> List[str]:
            params_strs_comma = []
            for i, param_str in enumerate(params_strs):
                if i < len(params_strs) - 1:
                    params_strs_comma.append(param_str + ", ")
                else:
                    params_strs_comma.append(param_str)
            lines = (
                [function_def_code + comment_python_type_ignore + comment_python_overridable]
                + params_strs_comma
                + [return_code]
            )
            return lines

        all_on_one_line = function_name_and_params_on_one_line()

        title_lines = [all_on_one_line] if all_on_one_line is not None else function_name_and_params_line_by_line()
        body_lines: List[str] = []

        r = self._str_stub_layout_lines(title_lines, body_lines)
        r = self._cpp_original_code_lines() + r

        if self.cpp_adapted_function.is_static_method():
            r = ["# (static method)"] + r

        if self.shall_vectorize():
            new_vectorized_function = copy.copy(self)
            new_vectorized_function.is_vectorize_impl = True
            r += new_vectorized_function._str_stub_lines()

        return r

    def stub_function_name_python(self) -> str:
        from litgen.internal.adapted_types import operators

        if self.is_constructor():
            return "__init__"
        elif self.cpp_adapted_function.is_operator():
            r = operators.cpp_to_python_operator_name(self.cpp_adapted_function)
            return r
        else:
            r = cpp_to_python.function_name_to_python(self.options, self.cpp_adapted_function.function_name)
            return r

    def stub_return_type_python(self) -> str:
        if self.cpp_element().is_inferred_return_type():
            return "Any"
        if self.is_constructor():
            return "None"
        else:
            return_type_cpp = self.cpp_adapted_function.str_full_return_type()
            return_type_python = cpp_to_python.type_to_python(self.options, return_type_cpp)
            return return_type_python

    def _stub_paramlist_call_python(self) -> List[str]:
        cpp_parameters = self.cpp_adapted_function.parameter_list.parameters
        r = []
        for param in cpp_parameters:
            param_name_python = cpp_to_python.var_name_to_python(self.options, param.decl.decl_name)
            param_type_cpp = param.decl.cpp_type.str_code()

            # Handle *args and **kwargs
            param_type_cpp_simplified = (
                param_type_cpp.replace("const ", "").replace("pybind11::", "py::").replace(" &", "")
            )
            if param_type_cpp_simplified == "py::args":
                r.append("*args")
                continue
            if param_type_cpp_simplified == "py::kwargs":
                r.append("**kwargs")
                continue

            param_type_python = cpp_to_python.type_to_python(self.options, param_type_cpp)
            if self.is_vectorize_impl:
                param_type_python = "np.ndarray"

            param_default_value = cpp_to_python.var_value_to_python(self.lg_context, param.default_value())

            param_code = f"{param_name_python}: {param_type_python}"
            if len(param_default_value) > 0:
                param_code += f" = {param_default_value}"

            r.append(param_code)

        if self.is_method() and not self.cpp_adapted_function.is_static_method():
            r = ["self"] + r
        return r

    def _stub_fill_is_type_ignore(self) -> None:
        token = "type: ignore"

        # Try to find it in eol comment (and clean eol comment if found)
        eol_comment = self.cpp_element().cpp_element_comments.comment_end_of_line
        if token in eol_comment:
            self.is_type_ignore = True
            eol_comment = eol_comment.replace(token, "").lstrip()
            if eol_comment.lstrip().startswith("//"):
                eol_comment = eol_comment.lstrip()[2:]
            self.cpp_element().cpp_element_comments.comment_end_of_line = eol_comment

    #  ============================================================================================
    #
    #    Template classes support: methods prefix = _tpl_
    #    https://pybind11.readthedocs.io/en/stable/advanced/functions.html#binding-functions-with-template-parameters
    #
    #    methods prefix: _tpl_
    #
    #  ============================================================================================

    def _tpl_is_one_param_template(self) -> bool:
        assert self._tpl_is_template_non_specialized()  # call this after _is_template()!
        nb_template_parameters = len(self.cpp_element().template.parameter_list.parameters)
        is_supported = nb_template_parameters == 1
        return is_supported

    def _tpl_is_template_non_specialized(self) -> bool:
        """Returns true if the function is a template
        and if no prior templated buffer adaptation was done
        (see _adapt_c_buffers.py)
        """
        if self.has_adapted_template_buffer:
            return False
        return self.cpp_element().is_template_partially_specialized()

    def _tpl_instantiate_template_for_type(
        self, cpp_type_str: str, naming_scheme: litgen.TemplateNamingScheme
    ) -> AdaptedFunction:
        assert self._tpl_is_template_non_specialized()
        assert self._tpl_is_one_param_template()

        new_cpp_function = self.cpp_element().with_specialized_template(
            CppTemplateSpecialization.from_type_str(cpp_type_str)
        )
        assert new_cpp_function is not None
        new_cpp_function.function_name = litgen.TemplateNamingScheme.apply(
            naming_scheme, new_cpp_function.function_name, cpp_type_str
        )
        new_adapted_function = AdaptedFunction(self.lg_context, new_cpp_function, self.is_overloaded)
        return new_adapted_function

    def _tpl_split_into_template_instantiations(self) -> List[AdaptedFunction]:
        assert self._tpl_is_template_non_specialized()

        matching_template_spec = None
        for template_spec in self.options.fn_template_options.specs:
            if code_utils.does_match_regex(template_spec.name_regex, self.cpp_element().function_name):
                matching_template_spec = template_spec

        if matching_template_spec is None:
            self.cpp_element().emit_warning(
                "Ignoring template function. You might need to set LitgenOptions.fn_template_options"
            )
            return []

        if not self._tpl_is_one_param_template() and len(matching_template_spec.cpp_types_list) > 0:
            self.cpp_element().emit_warning("Only one parameters template functions are supported")
            return []

        new_functions: List[AdaptedFunction] = []
        for cpp_type in matching_template_spec.cpp_types_list:
            new_function = self._tpl_instantiate_template_for_type(cpp_type, matching_template_spec.naming_scheme)
            new_functions.append(new_function)
        return new_functions

    #  ============================================================================================
    #
    #    Overriding virtual methods in python:
    #    cf https://pybind11.readthedocs.io/en/stable/advanced/classes.html#overriding-virtual-functions-in-python
    #
    #  ============================================================================================

    def virt_glue_override_virtual_methods_in_python(self, implemented_class: str) -> List[str]:
        assert self.cpp_element().is_virtual_method()

        template_code = code_utils.unindent_code(
            """
        {return_type} {function_name_cpp}({param_list}){maybe_const} override
        {
        {_i_}{PYBIND11_OVERRIDE_NAME}(
        {_i_}{_i_}{return_type}, // return type
        {_i_}{_i_}{implemented_class}, // parent class
        {_i_}{_i_}"{function_name_python}", // function name (python)
        {_i_}{_i_}{function_name_cpp}{maybe_comma_if_has_params} // function name (c++)
        {_i_}{_i_}{param_names} // params
        {_i_});
        }
        """,
            flag_strip_empty_lines=True,
        )

        parent_struct = self.cpp_element().parent_struct_if_method()
        has_params = len(self.cpp_element().parameter_list.parameters) > 0
        is_pure_virtual = self.cpp_element().is_pure_virtual
        assert parent_struct is not None

        replacements = Munch()
        replacements.PYBIND11_OVERRIDE_NAME = (
            "PYBIND11_OVERRIDE_PURE_NAME" if is_pure_virtual else "PYBIND11_OVERRIDE_NAME"
        )
        replacements._i_ = self.options.indent_cpp_spaces()
        replacements.return_type = self.cpp_element().return_type.str_return_type()
        replacements.function_name_cpp = self.cpp_element().function_name_with_specialization()
        replacements.function_name_python = cpp_to_python.function_name_to_python(
            self.options, self.cpp_element().function_name
        )
        replacements.maybe_const = " const" if self.cpp_element().is_const() else ""
        replacements.implemented_class = implemented_class
        replacements.param_list = self.cpp_element().parameter_list.str_types_names_default_for_signature()
        replacements.maybe_comma_if_has_params = "," if has_params else ""

        lines_replacements = Munch()
        lines_replacements.param_names = (
            self.cpp_element().parameter_list.str_names_only_for_call() if has_params else None
        )

        code = code_utils.process_code_template(template_code, replacements, lines_replacements)
        lines = code.split("\n")
        return lines
