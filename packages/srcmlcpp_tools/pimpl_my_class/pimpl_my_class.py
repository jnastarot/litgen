from dataclasses import dataclass
from munch import Munch  # type: ignore
from xml.etree import ElementTree as ET  # noqa

from codemanip import code_utils
from srcmlcpp.srcml_types import *


# Todo: const, constexpr, and other methods specifiers


@dataclass
class PimplResult:
    header_code: str = ""
    glue_code: str = ""


@dataclass
class PimplOptions:
    pimpl_suffixes: List[str]
    indent_str: str = "    "
    indent_public: str = "  "
    max_consecutive_empty_lines = 1
    line_feed_before_block: bool = True
    impl_member_name = "mPImpl"

    def __init__(self) -> None:
        self.pimpl_suffixes = ["_pimpl", "_impl", "pimpl", "impl"]


class PimplMyClass:
    impl_class: CppStruct
    options: PimplOptions

    def __init__(self, options: PimplOptions, impl_class: CppStruct) -> None:
        self.impl_class = impl_class
        self.options = options

    def _impl_class_name(self) -> str:
        return self.impl_class.class_name

    def _published_class_name(self) -> str:
        impl_class_name = self._impl_class_name()
        for suffix in self.options.pimpl_suffixes:
            if impl_class_name.lower().endswith(suffix):
                return impl_class_name[: -len(suffix)]
        raise Exception(f"pImpl class name needs to end with a suffix among {self.options.pimpl_suffixes}")

    def _published_method_impl(self, cpp_function: CppFunctionDecl) -> str:
        template = code_utils.unindent_code(
            """
        {return_type} {class_published}::{method_name}({params_list}) {maybe_const}{ {maybe_return}{impl_name}->{method_name}({param_names}); }
        """,
            flag_strip_empty_lines=True,
        )

        replacements = Munch()
        replacements.class_published = self._published_class_name()
        replacements.impl_name = self.options.impl_member_name
        replacements.return_type = cpp_function.return_type.str_code()
        replacements.method_name = cpp_function.function_name
        replacements.params_list = cpp_function.parameter_list.str_code()
        replacements.maybe_return = "" if cpp_function.return_type.is_void() else "return "
        replacements.param_names = cpp_function.parameter_list.names_only_for_call()
        replacements.maybe_const = "const " if "const" in cpp_function.specifiers else ""

        replacements_by_line = Munch()

        r = code_utils.process_code_template(template, replacements, replacements_by_line)
        return r

    def _published_method_decl(self, cpp_function: CppFunctionDecl) -> str:
        template = code_utils.unindent_code(
            """
        {top_comment}
        {return_type} {method_name}({params_list}){maybe_const};{maybe_eol_comment}
        """,
            flag_strip_empty_lines=True,
        )

        replacements = Munch()
        replacements.top_comment = cpp_function.cpp_element_comments.top_comment_code(add_eol=False)
        replacements.return_type = cpp_function.return_type.str_code()
        replacements.method_name = cpp_function.function_name
        replacements.params_list = cpp_function.parameter_list.str_code()
        replacements.maybe_eol_comment = cpp_function.cpp_element_comments.eol_comment_code()
        replacements.maybe_const = " const" if "const" in cpp_function.specifiers else ""

        replacements_by_line = Munch()
        replacements_by_line.top_comment = cpp_function.cpp_element_comments.top_comment_code(add_eol=False)

        r = code_utils.process_code_template(template, replacements, replacements_by_line)
        return r

    def _published_constructor_impl(self, cpp_constructor: CppConstructorDecl) -> str:
        template = code_utils.unindent_code(
            """
    {class_published}::{class_published}({param_list}) : {impl_name}(std::make_unique<{class_impl}>({param_names})) { }
        """,
            flag_strip_empty_lines=True,
        )

        replacements = Munch()
        replacements.param_list = str(cpp_constructor.parameter_list)
        replacements.class_published = self._published_class_name()
        replacements.class_impl = self._impl_class_name()
        replacements.impl_name = self.options.impl_member_name
        replacements.param_names = cpp_constructor.parameter_list.names_only_for_call()

        replacements_by_line = Munch()

        r = code_utils.process_code_template(template, replacements, replacements_by_line)
        return r

    def _published_constructor_decl(self, cpp_constructor: CppConstructorDecl) -> str:
        template = code_utils.unindent_code(
            """
    {top_comment}
    {class_published}({param_list});{maybe_eol_comment}
        """,
            flag_strip_empty_lines=True,
        )

        replacements = Munch()
        replacements.top_comment = cpp_constructor.cpp_element_comments.top_comment_code(add_eol=False)
        replacements.class_published = self._published_class_name()
        replacements.param_list = str(cpp_constructor.parameter_list)
        replacements.maybe_eol_comment = cpp_constructor.cpp_element_comments.eol_comment_code()

        replacements_by_line = Munch()
        replacements_by_line.top_comment = cpp_constructor.cpp_element_comments.top_comment_code(add_eol=False)

        r = code_utils.process_code_template(template, replacements, replacements_by_line)
        return r

    def _glue_code(self) -> str:
        r = ""
        for public_block in self.impl_class.get_public_blocks():
            for child in public_block.block_children:
                if isinstance(child, CppConstructorDecl):
                    r += self._published_constructor_impl(child) + "\n"
                elif isinstance(child, CppFunctionDecl):
                    r += self._published_method_impl(child) + "\n"

        r += f"{self._published_class_name()}::~{self._published_class_name()}() = default;\n"
        return r

    def _published_method_decls(self) -> str:
        published_methods = ""
        for public_block in self.impl_class.get_public_blocks():
            for child in public_block.block_children:
                if isinstance(child, CppConstructorDecl):
                    published_methods += self._published_constructor_decl(child) + "\n"
                elif isinstance(child, CppFunctionDecl):
                    published_methods += self._published_method_decl(child) + "\n"
                elif isinstance(child, CppEmptyLine):
                    published_methods += "\n"
                elif isinstance(child, CppComment):
                    published_methods += str(child) + "\n"
        return code_utils.indent_code(published_methods, indent_str=self.options.indent_str)

    def _header_code(self) -> str:
        template = code_utils.unindent_code(
            """
        {class_or_struct} {impl_class_name};

        {top_comment}
        {class_or_struct} {published_class_name}{maybe_eol_comment}{linefeed_or_space}{
        {i}{maybe_public}
        {published_methods}

        {_i_}~{published_class_name}();
        {i}private:
        {_i_}std::unique_ptr<{impl_class_name}> {impl_name};
        };
        """,
            flag_strip_empty_lines=True,
        )

        is_class = isinstance(self.impl_class, CppClass)

        replacements = Munch()
        replacements.linefeed_or_space = "\n" if self.options.line_feed_before_block else " "
        replacements._i_ = self.options.indent_str
        replacements.i = self.options.indent_public
        replacements.class_or_struct = "class" if is_class else "struct"
        replacements.maybe_eol_comment = self.impl_class.cpp_element_comments.eol_comment_code()
        replacements.published_class_name = self._published_class_name()
        replacements.impl_class_name = self._impl_class_name()
        replacements.impl_name = self.options.impl_member_name
        replacements.published_methods = self._published_method_decls()

        replacements_by_line = Munch()
        replacements_by_line.top_comment = self.impl_class.cpp_element_comments.top_comment_code(add_eol=False)
        replacements_by_line.maybe_public = "public:" if is_class else ""

        r = code_utils.process_code_template(template, replacements, replacements_by_line)

        if self.options.max_consecutive_empty_lines >= 0:
            r = code_utils.code_set_max_consecutive_empty_lines(r, self.options.max_consecutive_empty_lines)

        return r

    def result(self) -> PimplResult:
        r = PimplResult()
        r.glue_code = self._glue_code()
        r.header_code = self._header_code()
        return r