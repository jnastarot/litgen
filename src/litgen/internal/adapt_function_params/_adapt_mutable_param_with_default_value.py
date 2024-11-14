"""Adapter for mutable parameters with default values.
See https://docs.python.org/3/faq/programming.html#why-are-default-values-shared-between-objects

This code:

```python
def use_foo(foo = Foo()):
    # potentially mutable operations on foo
    ...
```
is problematic, because the default value of `foo` is shared between all calls to `use_foo_python`!

This is fundamentally different from C++ default arguments, where the default value is evaluated each time the function is called.

This adapter will make it so that default arguments for bound C++ functions behave like C++ default arguments,
which is probably what the C++ code author intended.

The principle is that for this C++ code:
```cpp
// User defined code (for which binding will be generated)
// ==============================================================
void use_foo(const Foo &foo = Foo());
```

We will generate bindings that will re-evaluate the default value each time the function is called (if needed).

The generated pydef code will look like this:

```cpp
    // We replace the bare function definition with a lambda that calls the function with the default value
    module_immvision.def(
        "use_foo",
        [](std::optional<const Foo> foo = std::nullopt)
        {
            const Foo & foo_or_default = foo.has_value() ? (*foo) : (Foo());
            use_foo(foo_or_default);
        },
        nb::arg("foo") = nb::none()
    );

```
"""
import copy
from typing import Optional, Callable
from codemanip import code_utils
from litgen.internal.adapt_function_params._lambda_adapter import LambdaAdapter
from litgen.internal.adapted_types import AdaptedFunction
from litgen.internal import cpp_to_python, LitgenContext
from srcmlcpp import CppScope, CppEnum
from srcmlcpp.cpp_types import CppParameter, CppType
from dataclasses import dataclass


def _can_access_enum_with_type(
        current_scope: CppScope,   # Represent e.g. "A::B::C"
        cpp_type_str: str,         # A type name being checked (e.g. MyEnum, A::MyEnum)
        cpp_enum: CppEnum,         # The enum being checked (e.g. "A::MyEnum")
        ) -> bool:
    """
    Check if the current scope can access the enum with the given type name.

    Args:
        current_scope (CppScope): The current scope in the code.
        cpp_type_str (str): The type name being checked.
        enum_name_with_scope (str): The fully qualified name of the enum.

    Returns:
        bool: True if the enum can be accessed with the given type name from the current scope.
    """
    # Remove leading "::" for uniformity
    is_enum_class = cpp_enum.enum_type == "class"
    if not is_enum_class:
        return False

    enum_name_with_scope = cpp_enum.cpp_scope_str(include_self=True)
    cpp_type_str = cpp_type_str.lstrip(":")

    # If cpp_type_str is unqualified, we need to check each scope in the hierarchy
    # Generate possible fully qualified names by prepending scopes from innermost to outermost
    for scope in current_scope.scope_hierarchy_list:
        # Use the qualified_name method to construct the fully qualified name
        full_type_name = scope.qualified_name(cpp_type_str)
        # Compare with the enum's fully qualified name
        if full_type_name == enum_name_with_scope:
            return True
    return False


def _can_access_enum_with_value(
        current_scope: CppScope,   # Represent e.g. "A::B::C"
        cpp_value_str: str,        # A value name being checked (e.g. MyEnum::a, A::MyEnum::a)
        cpp_enum: CppEnum          # The enum being checked (e.g. "A::MyEnum")
        ) -> bool:

    if cpp_enum.enum_type == "class":
        def compute_cpp_type_str() -> str | None:
            if "::" in cpp_value_str:
                # split and take everything except the last element
                r = "::".join(cpp_value_str.split("::")[:-1])
                return r
            return None
        cpp_type_str = compute_cpp_type_str()
        if cpp_type_str is None:
            return False
        return _can_access_enum_with_type(current_scope, cpp_type_str, cpp_enum)
    else:
        return False  # C enum are too shady
        # enum_name_with_scope = cpp_enum.cpp_scope_str(include_self=False)
        # # Generate possible fully qualified names by prepending scopes from innermost to outermost
        # for scope in current_scope.scope_hierarchy_list:
        #     # Use the qualified_name method to construct the fully qualified name
        #     full_value_name = scope.qualified_name(cpp_value_str)
        #     # Compare with the enum's fully qualified name
        #     if full_value_name.startswith(enum_name_with_scope + "_"):
        #         return True
        # return False




@dataclass
class _ImmutableCallables:
    fn_immutables_types: Callable[[str], bool]
    fn_immutables_values: Callable[[str], bool]


def _immutable_functions_default(lg_context: LitgenContext, code_scope: CppScope) -> _ImmutableCallables:
    options = lg_context.options

    def _fn_immutables_values(cpp_value_str: str) -> bool:
        for cpp_enum in lg_context.encountered_cpp_enums:
            if _can_access_enum_with_value(code_scope, cpp_value_str, cpp_enum):
                return True
            # if cpp_type_str.startswith(enum_type + "_"):
            #     return True

        _fn_immutables_values_user = options.fn_params_adapt_mutable_param_with_default_value__fn_is_known_immutable_value
        if _fn_immutables_values_user is not None:
            return _fn_immutables_values_user(cpp_value_str)
        else:
            return False

    def _fn_immutables_types(cpp_type_str: str) -> bool:
        for cpp_enum in lg_context.encountered_cpp_enums:
            if _can_access_enum_with_type(code_scope, cpp_type_str, cpp_enum):
                return True

        _fn_immutables_types_user = options.fn_params_adapt_mutable_param_with_default_value__fn_is_known_immutable_type
        if _fn_immutables_types_user is not None:
            return _fn_immutables_types_user(cpp_type_str)
        return False

    return _ImmutableCallables(_fn_immutables_types, _fn_immutables_values)



def was_mutable_param_with_default_value_made_optional(lg_context: LitgenContext, cpp_param: CppParameter) -> bool:
    options = lg_context.options
    option_active = options.fn_params_adapt_mutable_param_with_default_value__to_autogenerated_named_ctor
    if not option_active:
        return False
    immutable_callables = _immutable_functions_default(lg_context, cpp_param.cpp_scope(include_self=False))
    r = cpp_param.seems_mutable_param_with_default_value(immutable_callables.fn_immutables_types, immutable_callables.fn_immutables_values)
    return r


def adapt_mutable_param_with_default_value(adapted_function: AdaptedFunction) -> Optional[LambdaAdapter]:
    options = adapted_function.options
    is_autogenerated_named_ctor = "Auto-generated default constructor with named params" in adapted_function.cpp_element().cpp_element_comments.comment_on_previous_lines
    apply_because_autogen = options.fn_params_adapt_mutable_param_with_default_value__to_autogenerated_named_ctor and is_autogenerated_named_ctor
    match_regex = code_utils.does_match_regex(
        options.fn_params_adapt_mutable_param_with_default_value__regex,
        adapted_function.cpp_adapted_function.function_name,
    )
    if not (apply_because_autogen or match_regex):
        return None

    old_function_params: list[CppParameter] = adapted_function.cpp_adapted_function.parameter_list.parameters

    immutable_callables = _immutable_functions_default(adapted_function.lg_context, adapted_function.cpp_element().cpp_scope(include_self=False))

    def needs_adapt() -> bool:
        for old_adapted_param in adapted_function.adapted_parameters():
            cpp_param = old_adapted_param.cpp_element()
            if cpp_param.seems_mutable_param_with_default_value(immutable_callables.fn_immutables_types, immutable_callables.fn_immutables_values):
                return True
        return False

    if not needs_adapt():
        return None

    def _fn_cpp_type_to_optional(cpp_type: CppType) -> CppType:
        type_copy = copy.copy(cpp_type)
        if type_copy.is_reference():
            type_copy.modifiers.remove("&")
        opt_type_code = f"const std::optional<{type_copy.str_code()}> &"
        import srcmlcpp

        opt_type = srcmlcpp.code_to_cpp_type(adapted_function.options.srcmlcpp_options, opt_type_code)
        return opt_type

    def _fn_optional_to_const_noref(cpp_type: CppType) -> str:
        type_copy = copy.copy(cpp_type)
        if "&" in type_copy.modifiers:
            type_copy.modifiers.remove("&")
        if "const" not in type_copy.specifiers:
            type_copy.specifiers.append("const")
        r = type_copy.str_code()
        return r

    lambda_adapter = LambdaAdapter()

    lambda_adapter.new_function_infos = copy.deepcopy(adapted_function.cpp_adapted_function)
    new_function_params = []

    new_function_comment_lines = {}

    for old_param in old_function_params:
        was_replaced = False
        if old_param.seems_mutable_param_with_default_value(immutable_callables.fn_immutables_types, immutable_callables.fn_immutables_values):
            was_replaced = True

            param_name = old_param.decl.decl_name
            param_type = old_param.decl.cpp_type

            # param_or: the parameter that will be passed to the original function
            # (where std::optional<T> is replaced by T)
            param_or__name = f"{param_name}_or_default"
            param_or__type_noref = _fn_optional_to_const_noref(param_type)
            param_or__real_default = cpp_to_python.var_value_to_python(adapted_function.lg_context, old_param.decl.initial_value_code)
            new_function_comment_lines[param_name] =  param_or__real_default

            # Create new calling param (std::optional<T>)
            new_param = copy.deepcopy(old_param)
            new_decl = new_param.decl
            new_decl.initial_value_code = "std::nullopt"
            new_decl.cpp_type = _fn_cpp_type_to_optional(param_type)
            new_function_params.append(new_param)

            # Fill lambda_input_code
            _i_ = options._indent_cpp_spaces()
            lambda_input_code = f"""
            {param_or__type_noref}& {param_or__name} = [&]() -> {param_or__type_noref} {{
            {_i_}if ({param_name}.has_value())
            {_i_}{_i_}return {param_name}.value();
            {_i_}else
            {_i_}{_i_}return {old_param.decl.initial_value_code};
            }}();
            """
            lambda_input_code = code_utils.unindent_code(lambda_input_code, flag_strip_empty_lines=False)
            lambda_adapter.lambda_input_code += lambda_input_code

            # Fill adapted_cpp_parameter_list (those that will call the original C style function)
            lambda_adapter.adapted_cpp_parameter_list.append(param_or__name)

        if not was_replaced:
            new_function_params.append(old_param)
            lambda_adapter.adapted_cpp_parameter_list.append(old_param.decl.decl_name)

    lambda_adapter.new_function_infos.parameter_list.parameters = new_function_params

    lambda_adapter.lambda_name = (
        adapted_function.cpp_adapted_function.function_name + "_adapt_mutable_param_with_default_value"
    )

    # Add comment lines to the function
    if options.fn_params_adapt_mutable_param_with_default_value__add_comment:
        cpp_comments = adapted_function.cpp_element().cpp_element_comments
        cpp_comments.add_comment_on_previous_lines("---")
        cpp_comments.add_comment_on_previous_lines("Python bindings defaults:")
        if len(new_function_comment_lines) == 1:
            param_name = list(new_function_comment_lines.keys())[0]
            param_default_value = new_function_comment_lines[param_name]
            comment = f"    If {param_name} is None, then its default value will be: {param_default_value}"
            cpp_comments.add_comment_on_previous_lines(comment)
        else:
            cpp_comments.add_comment_on_previous_lines("    If any of the params below is None, then its default value below will be used:")
            for param_name, param_default_value in new_function_comment_lines.items():
                comment = f"        {param_name}: {param_default_value}"
                cpp_comments.add_comment_on_previous_lines(comment)

    return lambda_adapter
