from __future__ import annotations

from typing import Union, cast, Tuple

import munch  # type: ignore

from srcmlcpp.srcml_types import *
from srcmlcpp.srcml_exception import SrcMlException

from litgen.internal import cpp_to_python
from litgen.internal.context.litgen_context import LitgenContext
from litgen.internal.adapted_types.adapted_comment import (
    AdaptedComment,
    AdaptedEmptyLine,
)
from litgen.internal.adapted_types.adapted_decl import AdaptedDecl
from litgen.internal.adapted_types.adapted_element import AdaptedElement
from litgen.internal.adapted_types.adapted_function import AdaptedFunction
from litgen.internal.adapted_types.adapted_enum import AdaptedEnum


@dataclass
class AdaptedClassMember(AdaptedDecl):
    """A specialization of AdaptedDecl for class member variables"""

    class_parent: AdaptedClass

    def __init__(self, lg_context: LitgenContext, decl: CppDecl, class_parent: AdaptedClass) -> None:
        self.class_parent = class_parent
        super().__init__(lg_context, decl)

    def __str__(self) -> str:
        name_cpp = self.decl_name_cpp()
        name_python = self.decl_name_python()
        if name_python != name_cpp:
            return f"AdaptedClassMember({self.decl_name_cpp()} -> {self.decl_name_python()})"
        else:
            return f"AdaptedClassMember({self.decl_name_cpp()})"

    def _is_numeric_c_array(self) -> bool:
        """Returns true if this member is a numeric C array, for example:
        int values[10];
        """
        options = self.options
        cpp_decl = self.cpp_element()
        array_typename = cpp_decl.cpp_type.str_code()
        if array_typename not in options.member_numeric_c_array_types_list():
            return False
        shall_replace = code_utils.does_match_regex(options.member_numeric_c_array_replace__regex, cpp_decl.decl_name)
        if not shall_replace:
            return False
        if cpp_decl.c_array_size_as_int() is None:
            return False
        return True

    def _check_can_add_c_array_known_fixed_size(self) -> bool:
        options = self.options
        cpp_decl = self.cpp_element()
        array_typename = cpp_decl.cpp_type.str_code()
        if array_typename not in options.member_numeric_c_array_types_list():
            cpp_decl.emit_warning(
                """
                AdaptedClassMember: Only numeric C Style arrays are supported
                Hint: use a vector, or extend `options.c_array_numeric_member_types`
                """,
            )
            return False

        shall_replace = code_utils.does_match_regex(options.member_numeric_c_array_replace__regex, cpp_decl.decl_name)
        if not shall_replace:
            cpp_decl.emit_warning(
                """
                AdaptedClassMember: Detected a numeric C Style array, but will not export it.
                Hint: modify `options.member_numeric_c_array_replace__regex`
                """,
            )
            return False

        if cpp_decl.c_array_size_as_int() is None:
            array_size_str = cpp_decl.c_array_size_as_str()
            cpp_decl.emit_warning(
                f"""
                AdaptedClassMember: Detected a numeric C Style array, but its size is not parsable.
                Hint: may be, add the value "{array_size_str}" to `options.c_array_numeric_member_size_dict`
                """,
            )
            return False

        return True

    def check_can_publish(self) -> bool:
        """Returns true if this member can be published as a property of the class"""
        cpp_decl = self.cpp_element()

        if cpp_decl.is_bitfield():  # is_bitfield()
            cpp_decl.emit_warning(
                f"AdaptedClassMember: Skipped bitfield member {cpp_decl.decl_name}",
            )
            return False
        elif cpp_decl.is_c_array_fixed_size_unparsable():
            cpp_decl.emit_warning(
                """
                AdaptedClassMember: Can't parse the size of this array.
                Hint: use a vector, or extend `options.c_array_numeric_member_types`
                """,
            )
            return False
        elif cpp_decl.is_c_array_known_fixed_size():
            return self._check_can_add_c_array_known_fixed_size()
        else:
            return True

    def decl_type_python(self) -> str:
        if self._is_numeric_c_array():
            return "np.ndarray"
        else:
            return super().decl_type_python()

    def decl_value_python(self) -> str:
        if self._is_numeric_c_array():
            return ""
        else:
            return super().decl_value_python()

    def comment_array(self) -> str:
        if self._is_numeric_c_array():
            array_typename = self.cpp_element().cpp_type.str_code()
            array_size = self.cpp_element().c_array_size_as_int()
            msg = f"  # ndarray[type={array_typename}, size={array_size}]"

            decl_value_python_original = super().decl_value_python()
            if len(decl_value_python_original) > 0:
                msg += " default:" + decl_value_python_original

            return msg
        else:
            return ""

    def _str_pydef_lines_numeric_array(self) -> List[str]:
        # Cf. https://stackoverflow.com/questions/58718884/binding-an-array-using-pybind11

        qualified_struct_name = self.class_parent.cpp_element().qualified_struct_name()
        location = self.info_original_location_cpp()
        name_python = self.decl_name_python()
        name_cpp = self.decl_name_cpp()
        comment = self.comment_pydef_one_line()

        array_typename = self.cpp_element().cpp_type.str_code()
        array_size = self.cpp_element().c_array_size_as_int()
        assert array_size is not None

        template_code = f"""
            .def_property("{name_python}",{location}
                []({qualified_struct_name} &self) -> pybind11::array
                {{
                    auto dtype = pybind11::dtype(pybind11::format_descriptor<{array_typename}>::format());
                    auto base = pybind11::array(dtype, {{{array_size}}}, {{sizeof({array_typename})}});
                    return pybind11::array(dtype, {{{array_size}}}, {{sizeof({array_typename})}}, self.{name_cpp}, base);
                }}, []({qualified_struct_name}& self) {{}},
                "{comment}")
            """
        r = code_utils.unindent_code(template_code, flag_strip_empty_lines=True)  # + "\n"
        lines = r.split("\n")
        return lines

    def _str_pydef_lines_field(self) -> List[str]:
        qualified_struct_name = self.class_parent.cpp_element().qualified_struct_name()
        location = self.info_original_location_cpp()
        name_python = self.decl_name_python()
        name_cpp = self.decl_name_cpp()
        comment = self.comment_pydef_one_line()

        pybind_definition_mode = "def_readwrite"
        cpp_type = self.cpp_element().cpp_type
        if cpp_type.is_const():
            pybind_definition_mode = "def_readonly"
        if cpp_type.is_static():
            pybind_definition_mode += "_static"

        r = f'.{pybind_definition_mode}("{name_python}", &{qualified_struct_name}::{name_cpp}, "{comment}"){location}'
        return [r]

    # override
    def cpp_element(self) -> CppDecl:
        return cast(CppDecl, self._cpp_element)

    # override
    def _str_stub_lines(self) -> List[str]:
        code_lines: List[str] = []

        if not self.comment_python_shall_place_at_end_of_line():
            code_lines += self.comment_python_previous_lines()

        decl_name_python = self.decl_name_python()
        decl_type_python = self.decl_type_python()

        default_value_python = self.decl_value_python()
        if len(default_value_python) > 0:
            maybe_defaultvalue_python = default_value_python
            maybe_equal = " = "
        else:
            maybe_defaultvalue_python = ""
            maybe_equal = ""

        if not self.comment_python_shall_place_at_end_of_line():
            maybe_comment = ""
        else:
            maybe_comment = self.comment_python_end_of_line()

        maybe_comment_array = self.comment_array()

        location = self.info_original_location_python()

        decl_template = f"{decl_name_python}: {decl_type_python}{maybe_equal}{maybe_defaultvalue_python}{maybe_comment_array}{maybe_comment}{location}"
        code_lines += [decl_template]

        code_lines = self._cpp_original_code_lines() + code_lines
        return code_lines

    # override
    def _str_pydef_lines(self) -> List[str]:
        if self._is_numeric_c_array():
            return self._str_pydef_lines_numeric_array()
        else:
            return self._str_pydef_lines_field()


@dataclass
class AdaptedClass(AdaptedElement):
    adapted_public_children: List[
        Union[AdaptedEmptyLine, AdaptedComment, AdaptedClassMember, AdaptedFunction, AdaptedClass, AdaptedEnum]
    ]
    adapted_protected_methods: List[AdaptedFunction]

    def __init__(self, lg_context: LitgenContext, class_: CppStruct):
        super().__init__(lg_context, class_)
        self.adapted_public_children = []
        self._fill_public_children()

        self.adapted_protected_methods = []
        self._fill_protected_methods()

    def __str__(self):
        r = f"AdaptedClass({self.cpp_element().class_name})"
        return r

    # override
    def cpp_element(self) -> CppStruct:
        return cast(CppStruct, self._cpp_element)

    def class_name_python(self) -> str:
        r = cpp_to_python.add_underscore_if_python_reserved_word(self.cpp_element().class_name)
        return r

    def _shall_publish_protected_methods(self) -> bool:
        r = code_utils.does_match_regex(
            self.options.class_expose_protected_methods__regex, self.cpp_element().class_name
        )
        return r

    def _shall_override_virtual_methods_in_python(self) -> bool:
        active = code_utils.does_match_regex(
            self.options.class_override_virtual_methods_in_python__regex, self.cpp_element().class_name
        )
        if not active:
            return False
        virtual_methods = self._virtual_method_list()
        r = len(virtual_methods) > 0
        return r

    def _add_adapted_class_member(self, cpp_decl_statement: CppDeclStatement) -> None:
        for cpp_decl in cpp_decl_statement.cpp_decls:
            is_excluded_by_name = code_utils.does_match_regex(
                self.options.member_exclude_by_name__regex, cpp_decl.decl_name
            )
            is_excluded_by_type = code_utils.does_match_regex(
                self.options.member_exclude_by_type__regex, cpp_decl.cpp_type.str_code()
            )
            if not is_excluded_by_name and not is_excluded_by_type:
                adapted_class_member = AdaptedClassMember(self.lg_context, cpp_decl, self)
                if adapted_class_member.check_can_publish():
                    self.adapted_public_children.append(adapted_class_member)

    def _fill_protected_methods(self) -> None:
        if not self._shall_publish_protected_methods():
            return
        for child in self.cpp_element().get_protected_elements():
            if isinstance(child, CppFunctionDecl):
                if not code_utils.does_match_regex(self.options.fn_exclude_by_name__regex, child.function_name):
                    is_overloaded = self.cpp_element().is_method_overloaded(child)
                    self.adapted_protected_methods.append(AdaptedFunction(self.lg_context, child, is_overloaded))

    def _fill_public_children(self) -> None:
        public_elements = self.cpp_element().get_public_elements()
        for child in public_elements:
            try:
                if isinstance(child, CppEmptyLine):
                    self.adapted_public_children.append(AdaptedEmptyLine(self.lg_context, child))
                elif isinstance(child, CppComment):
                    self.adapted_public_children.append(AdaptedComment(self.lg_context, child))
                elif isinstance(child, CppFunctionDecl):
                    if not code_utils.does_match_regex(self.options.fn_exclude_by_name__regex, child.function_name):
                        is_overloaded = self.cpp_element().is_method_overloaded(child)
                        self.adapted_public_children.append(AdaptedFunction(self.lg_context, child, is_overloaded))
                elif isinstance(child, CppDeclStatement):
                    self._add_adapted_class_member(child)
                elif isinstance(child, CppUnprocessed):
                    continue
                elif isinstance(child, CppStruct):
                    adapted_subclass = AdaptedClass(self.lg_context, child)
                    self.adapted_public_children.append(adapted_subclass)
                elif isinstance(child, CppEnum):
                    adapted_enum = AdaptedEnum(self.lg_context, child)
                    self.adapted_public_children.append(adapted_enum)
                else:
                    child.emit_warning(
                        f"Public elements of type {child.tag()} are not supported in python conversion",
                    )
            except SrcMlException as e:
                child.emit_warning(str(e))

    # override
    def _str_stub_lines(self) -> List[str]:
        from litgen.internal.adapted_types.line_spacer import LineSpacerPython

        line_spacer = LineSpacerPython(self.options)

        class_name = self.class_name_python()
        title = f"class {class_name}:"
        title_lines = [title]

        body_lines: List[str] = []
        for element in self.adapted_public_children:
            element_lines = element._str_stub_lines()

            spacing_lines = line_spacer.spacing_lines(element, element_lines)
            body_lines += spacing_lines
            body_lines += element_lines

        if len(self.adapted_protected_methods) > 0:
            body_lines += ["", "# <protected_methods>"]
            for element in self.adapted_protected_methods:
                element_lines = element._str_stub_lines()

                spacing_lines = line_spacer.spacing_lines(element, element_lines)
                body_lines += spacing_lines
                body_lines += element_lines
            body_lines += ["# </protected_methods>", ""]

        r = self._str_stub_layout_lines(title_lines, body_lines)
        return r

    def _scope_intro_outro(self) -> Tuple[str, str]:
        scope = self.cpp_element().cpp_scope(False)
        nb_scope_parts = len(scope.scope_parts)
        intro = ""
        outro = "} " * nb_scope_parts

        for scope_part in scope.scope_parts:
            if scope_part.scope_type == CppScopeType.Namespace:
                intro += f"namespace {scope_part.scope_name} {{ "
            else:
                raise SrcMlException("Bad scope for protected member")

        for scope_part in reversed(scope.scope_parts):
            if scope_part.scope_type == CppScopeType.Namespace:
                outro += f" // namespace {scope_part.scope_name} "

        return intro, outro

    def _virtual_method_list(self) -> List[AdaptedFunction]:
        r = []
        for child in self.adapted_public_children:
            if isinstance(child, AdaptedFunction):
                if child.cpp_element().is_virtual_method():
                    r.append(child)
        for child in self.adapted_protected_methods:
            if child.cpp_element().is_virtual_method():
                r.append(child)
        return r

    def _store_glue_override_virtual_methods_in_python(self) -> None:
        # See https://pybind11.readthedocs.io/en/stable/advanced/classes.html#overriding-virtual-functions-in-python
        if not self._shall_override_virtual_methods_in_python():
            return

        trampoline_class_template = code_utils.unindent_code(
            """
            // helper type to enable overriding virtual methods in python
            class {trampoline_class_name} : public {class_name}
            {
            public:
                using {class_name}::{class_name};

            {trampoline_list}
            };
            """,
            flag_strip_empty_lines=True,
        )

        trampoline_lines = []
        virtual_methods = self._virtual_method_list()
        for virtual_method in virtual_methods:
            trampoline_lines += virtual_method.glue_override_virtual_methods_in_python()

        replacements = munch.Munch()
        replacements.trampoline_class_name = self.cpp_element().class_name + "_trampoline"
        replacements.class_name = self.cpp_element().class_name
        replacements.trampoline_list = code_utils.indent_code(
            "\n".join(trampoline_lines), indent_str=self.options.indent_cpp_spaces()
        )

        publicist_class_code = code_utils.process_code_template(trampoline_class_template, replacements, {})

        ns_intro, ns_outro = self._scope_intro_outro()

        glue_code: List[str] = []
        glue_code += [ns_intro]
        glue_code += publicist_class_code.split("\n")
        glue_code += [ns_outro]

        glue_code_str = "\n" + "\n".join(glue_code) + "\n"
        self.lg_context.virtual_methods_glue_code += glue_code_str

    def _store_glue_protected_methods(self) -> None:
        # See https://pybind11.readthedocs.io/en/stable/advanced/classes.html#binding-protected-member-functions
        if not self._shall_publish_protected_methods():
            return
        if len(self.adapted_protected_methods) == 0:
            return

        def using_list() -> List[str]:
            r = []
            for child in self.adapted_protected_methods:
                class_name = self.cpp_element().class_name
                method_name = child.cpp_element().function_name
                r.append(f"using {class_name}::{method_name};")
            return r

        publicist_class_template = code_utils.unindent_code(
            """
            // helper type for exposing protected functions
            class {publicist_class_name} : public {class_name}
            {
            public:
            {using_list}
            };
        """,
            flag_strip_empty_lines=True,
        )

        replacements = munch.Munch()
        replacements.publicist_class_name = self.cpp_element().class_name + "_publicist"
        replacements.class_name = self.cpp_element().class_name
        replacements.using_list = code_utils.indent_code(
            "\n".join(using_list()), indent_str=self.options.indent_cpp_spaces()
        )

        publicist_class_code = code_utils.process_code_template(publicist_class_template, replacements, {})

        ns_intro, ns_outro = self._scope_intro_outro()

        glue_code: List[str] = []
        glue_code += [ns_intro]
        glue_code += publicist_class_code.split("\n")
        glue_code += [ns_outro]

        glue_code_str = "\n" + "\n".join(glue_code) + "\n"
        self.lg_context.protected_methods_glue_code += glue_code_str

    # override
    def _str_pydef_lines(self) -> List[str]:
        if self.cpp_element().is_templated_class():
            self.cpp_element().emit_warning("Template classes are not yet supported")
            return []

        self._store_glue_protected_methods()
        self._store_glue_override_virtual_methods_in_python()

        options = self.options
        _i_ = options.indent_cpp_spaces()

        bare_struct_name = self.cpp_element().class_name
        location = self.info_original_location_cpp()
        comment = self.comment_pydef_one_line()

        code_intro = ""
        pydef_class_var = cpp_to_python.cpp_scope_to_pybind_var_name(options, self.cpp_element())
        pydef_class_var_parent = cpp_to_python.cpp_scope_to_pybind_parent_var_name(options, self.cpp_element())
        qualified_struct_name = self.cpp_element().qualified_struct_name()

        if self.cpp_element().has_private_dtor():
            code_intro += f"auto {pydef_class_var} = py::class_<{qualified_struct_name}, std::unique_ptr<{qualified_struct_name}, py::nodelete>>{location}\n"
        elif self._shall_override_virtual_methods_in_python():
            scope = self.cpp_element().cpp_scope(False).str_cpp()
            scope_prefix = scope + "::" if len(scope) > 0 else ""
            qualified_trampoline_name = scope_prefix + self.cpp_element().class_name + "_trampoline"
            code_intro += (
                f"auto {pydef_class_var} = py::class_<{qualified_struct_name}, {qualified_trampoline_name}>{location}\n"
            )
        else:
            code_intro += f"auto {pydef_class_var} = py::class_<{qualified_struct_name}>{location}\n"
        code_intro += f'{_i_}({pydef_class_var_parent}, "{bare_struct_name}", "{comment}")\n'

        if options.generate_to_string:
            code_outro = f'{_i_}.def("__repr__", [](const {qualified_struct_name}& v) {{ return ToString(v); }});'
        else:
            code_outro = f"{_i_};"

        code = code_intro

        if not self.cpp_element().has_non_default_ctor() and not self.cpp_element().has_deleted_default_ctor():
            code += f"{_i_}.def(py::init<>()) // implicit default constructor\n"
        if self.cpp_element().has_deleted_default_ctor():
            code += f"{_i_}// (default constructor explicitly deleted)\n"

        def is_class_or_enum(e: AdaptedElement) -> bool:
            return isinstance(e, AdaptedClass) or isinstance(e, AdaptedEnum)

        def not_is_class_or_enum(e: AdaptedElement) -> bool:
            return not (isinstance(e, AdaptedClass) or isinstance(e, AdaptedEnum))

        children_except_inner_classes = list(filter(not_is_class_or_enum, self.adapted_public_children))
        children_inner_classes = list(filter(is_class_or_enum, self.adapted_public_children))

        for child in children_except_inner_classes:
            decl_code = child.str_pydef()
            code += code_utils.indent_code(decl_code, indent_str=options.indent_cpp_spaces())

        for child in self.adapted_protected_methods:
            # Temporarily change the name of the parent struct, to use the publicist class
            parent_struct = child.cpp_element().parent_struct_if_method()
            assert parent_struct is not None
            original_class_name = parent_struct.class_name
            parent_struct.class_name = self.cpp_element().class_name + "_publicist"
            decl_code = child.str_pydef()
            parent_struct.class_name = original_class_name

            code += code_utils.indent_code(decl_code, indent_str=options.indent_cpp_spaces())

        code = code + code_outro

        if len(children_inner_classes) > 0:
            code += "\n{" + f" // inner classes & enums of {self.class_name_python()}\n"
            for child in children_inner_classes:
                decl_code = child.str_pydef()
                code += code_utils.indent_code(decl_code, indent_str=options.indent_cpp_spaces())
            code += "}" + f" // end of inner classes & enums of {self.class_name_python()}"

        lines = code.split("\n")
        return lines
