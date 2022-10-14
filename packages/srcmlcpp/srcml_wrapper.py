"""SrcmlWrapper is a wrapper around the nodes in the xml tree produced by srcml"""

from __future__ import annotations
import copy
from typing import Callable, List, Optional
from xml.etree import ElementTree as ET

from codemanip import code_utils
from codemanip.code_position import CodeContextWithCaret, CodePosition

from srcmlcpp.internal import code_cache, srcml_caller, srcml_utils
from srcmlcpp.srcmlcpp_options import SrcmlcppOptions


class SrcmlWrapper:
    """A wrapper around the nodes in the xml tree produced by srcml"""

    # Misc options: in this class, we only use the encoding
    options: SrcmlcppOptions
    # the xml tree created by srcML
    srcml_xml: ET.Element
    # the filename from which this tree was parsed
    filename: Optional[str] = None

    # members that are always copied as shallow members (this is intentionally a static list)
    SrcmlWrapper__deep_copy_force_shallow_ = ["options", "srcml_xml"]

    def __init__(self, options: SrcmlcppOptions, srcml_xml: ET.Element, filename: Optional[str]) -> None:
        """Create a wrapper from a xml sub node
        :param options:  the options
        :param srcml_xml: the xml node which will be wrapped
        :param parent: the parent
        :param filename: the name of the file from which this node was extracted
        """

        self.options = options
        self.srcml_xml = srcml_xml

        # param sanity check
        if filename is not None:
            if len(filename) == 0:
                self.raise_exception("filename params must either be `None` or non empty!")

        self.filename = filename

    def __deepcopy__(self, memo=None):
        """SrcmlWrapper.__deepcopy__: force shallow copy of SrcmlcppOptions and srcml_xml (ET.Element)
        This improves the performance a lot.
        Reason:
        - options are global during parsing
        - srcml_xml is a heavy object that is created once for all during invocation of srcml exe
          When we deepcopy, we intent to modify only moving parts inside this package (srcmlcpp).
        """

        # __deepcopy___ "manual":
        #   See https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        #   (Antony Hatchkins's answer here)

        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k not in SrcmlWrapper.SrcmlWrapper__deep_copy_force_shallow_:
                setattr(result, k, copy.deepcopy(v, memo))
            else:
                setattr(result, k, v)
        return result

    def tag(self) -> str:
        """The xml tag
        https://www.tutorialspoint.com/xml/xml_tags.htm"""
        assert self.srcml_xml.tag is not None
        return srcml_utils.clean_tag_or_attrib(self.srcml_xml.tag)

    def has_text(self):
        return self.srcml_xml.text is not None

    def text(self) -> Optional[str]:
        """Text part of the xml element"""
        return self.srcml_xml.text

    def has_name(self) -> bool:
        name_children = srcml_utils.children_with_tag(self.srcml_xml, "name")
        return len(name_children) == 1

    def name_code(self) -> Optional[str]:
        """Returns the C++ code corresponding to the name extracted from the srcML xml tree.

        * In simple cases, it will be a simple text extraction, for example with the code:
            int a = 10;
          The decl name node will look like
            <name>a</name>

        * Sometimes, we will need to call srcml to reconstruct the code.
          For example, with the code:
            int* a[10];
          The decl name node will look like
               <name>
                    <name>a</name>
                    <index>[
                        <expr>
                            <literal type="number">10</literal>
                        </expr>]
                    </index>
                </name>
        """
        if not self.has_name():
            return None
        name_element = srcml_utils.child_with_tag(self.srcml_xml, "name")
        assert name_element is not None
        if name_element.text is not None:
            return name_element.text
        else:
            return srcml_caller.srcml_to_code(name_element)

    def attribute_value(self, attr_name: str) -> Optional[str]:
        """Gets the attribute value if present"""
        if attr_name in self.srcml_xml.attrib:
            return self.srcml_xml.attrib[attr_name]
        else:
            return None

    def start(self) -> CodePosition:
        """Start position in the C++ code"""
        start = srcml_utils.element_start_position(self.srcml_xml)
        return CodePosition(-1, -1) if start is None else start

    def end(self) -> CodePosition:
        """End position in the C++ code"""
        end = srcml_utils.element_end_position(self.srcml_xml)
        return CodePosition(-1, -1) if end is None else end

    def str_code_verbatim(self) -> str:
        """Return the exact C++ code from which this xml node was constructed by calling the executable srcml"""
        r = srcml_caller.srcml_to_code(self.srcml_xml, encoding=self.options.encoding)
        return r

    def str_xml(self, beautify: bool = True) -> str:
        """An xml string representing the content of the xml node"""
        r = srcml_utils.srcml_to_str(self.srcml_xml, bare=not beautify)
        return r

    def _str_simplified_yaml(self) -> str:
        """Return the xml tree formatted in a yaml inspired format. Should be deprecated"""
        return srcml_utils.srcml_to_str_readable(self.srcml_xml)

    def to_file(self, filename: str) -> None:
        """Save to file as xml"""
        srcml_utils.srcml_write_to_file(self.options.encoding, self.srcml_xml, filename)

    def make_wrapped_children(self) -> List[SrcmlWrapper]:
        """Extract the xml sub nodes and wraps them"""
        r = []
        for child_xml in self.srcml_xml:
            r.append(SrcmlWrapper(self.options, child_xml, self.filename))
        return r

    def wrapped_children_with_tag(self, tag: str) -> List[SrcmlWrapper]:
        """Extract the xml sub nodes and wraps them"""
        children = self.make_wrapped_children()

        r = list(filter(lambda child: child.tag() == tag, children))
        return r

    def visit_xml_breadth_first(self, xml_visitor_function: SrcmlXmVisitorFunction, depth: int = 0) -> None:
        """Visits all the elements, and run the given function on them.
        Runs the visitor on the parent first, then on its children
        """
        xml_visitor_function(self, depth)
        for child in self.make_wrapped_children():
            child.visit_xml_breadth_first(xml_visitor_function, depth + 1)

    def raise_exception(self, message: str) -> None:
        """raises a SrcmlcppException which will display the message with a context
        that gives the location of this element in the code"""
        from srcmlcpp.internal.srcmlcpp_exception_detailed import SrcmlcppExceptionDetailed

        raise SrcmlcppExceptionDetailed(self, message)

    def emit_warning(self, message: str) -> None:
        """emits a warning which will display the message with a context
        that gives the location of this element in the code"""
        message = self._format_message(message, "Warning")
        from srcmlcpp.internal.srcmlcpp_exception_detailed import emit_warning_if_not_quiet

        emit_warning_if_not_quiet(self.options, message)

    def _warning_message_str(self, message: str, message_header: str = "Warning") -> str:
        r = self._format_message(message, message_header=message_header)
        return r

    def short_xml_info(self) -> str:
        r = f"tag={self.tag()}"
        if self.has_name():
            r += f" name={self.name_code()}"
        return r

    def __str__(self):
        return self.short_xml_info()

    def _show_element_info(self) -> str:
        element_tag = self.tag()
        concerned_code = self.str_code_context_with_caret(max_lines=2)
        message = f"""
        While parsing a "{element_tag}", corresponding to this C++ code:
        {self.str_code_location()}
{code_utils.indent_code(concerned_code, 12)}
        """
        return message

    def _format_message(self, additional_message: str, message_header: str = "Warning") -> str:
        from srcmlcpp.internal.srcmlcpp_exception_detailed import _get_python_call_info, show_python_callstack

        message = ""

        if "while parsing" not in additional_message.lower():
            message += self._show_element_info()

            if self.options.flag_show_python_callstack:
                python_caller_function_name, python_error_line = _get_python_call_info()
                message += show_python_callstack(python_error_line)

        if len(additional_message) > 0:
            message = (
                code_utils.unindent_code(additional_message, flag_strip_empty_lines=True)
                + "\n"
                + code_utils.unindent_code(message, flag_strip_empty_lines=True)
            )

        message = message_header + ": " + message

        return message

    def str_code_context_with_caret(self, max_lines: int) -> str:
        context: CodeContextWithCaret
        r = ""
        full_code = code_cache.get_cached_code(self.filename)
        if len(full_code) > 0:
            full_code_lines = [""] + full_code.split("\n")

            start = self.start()
            end = self.end()
            if start.line >= 0 and end.line >= 0:
                if end.line > start.line + max_lines:
                    end.line = start.line + max_lines

                concerned_lines = full_code_lines[start.line : end.line + 1]
                new_start = CodePosition(0, start.column)
                new_end = CodePosition(
                    end.line - start.line,
                    end.column,
                )
                context = CodeContextWithCaret(concerned_lines, new_start, new_end)
                r = str(context)
            else:
                r = self.str_code_verbatim()
        else:
            r = self.str_code_verbatim()

        return r

    def str_code_location(self) -> str:
        if self.filename is None:
            header_filename = "Position"
        else:
            header_filename = self.filename

        start = self.start()
        if start.line >= 0:
            return f"{header_filename}:{start.line}:{start.column}"
        else:
            return f"{header_filename}"


# This defines the type of function that will visit all the children
# * first parameter: current child
# * second parameter: depth
SrcmlXmVisitorFunction = Callable[[SrcmlWrapper, int], None]