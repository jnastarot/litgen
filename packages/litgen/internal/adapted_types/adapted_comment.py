from dataclasses import dataclass
from typing import List, cast

from srcmlcpp.srcml_types import CppComment, CppEmptyLine

from litgen.internal import cpp_to_python
from litgen.internal.adapted_types.adapted_element import AdaptedElement
from litgen.options import LitgenOptions


@dataclass
class AdaptedEmptyLine(AdaptedElement):
    def __init__(self, cpp_empty_line: CppEmptyLine, options: LitgenOptions) -> None:
        super().__init__(cpp_empty_line, options)

    # override
    def cpp_element(self) -> CppEmptyLine:
        return cast(CppEmptyLine, self._cpp_element)

    # override
    def _str_stub_lines(self) -> List[str]:
        if self.options.python_reproduce_cpp_layout:
            return [""]
        else:
            return []

    # override
    def _str_pydef_lines(self) -> List[str]:
        return []


@dataclass
class AdaptedComment(AdaptedElement):
    def __init(self, cpp_comment: CppComment, options: LitgenOptions):
        super().__init__(cpp_comment, options)

    # override
    def cpp_element(self) -> CppComment:
        return cast(CppComment, self._cpp_element)

    # override
    def _str_stub_lines(self) -> List[str]:
        comment_cpp = self.cpp_element().comment
        comment_python = cpp_to_python._comment_apply_replacements(comment_cpp, self.options)

        def add_comment_token(line: str):
            return "# " + line

        comment_python_lines = list(map(add_comment_token, comment_python.split("\n")))
        return comment_python_lines

    # override
    def _str_pydef_lines(self) -> List[str]:
        return []