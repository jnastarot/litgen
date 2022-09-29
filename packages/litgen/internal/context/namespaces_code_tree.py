from __future__ import annotations
from typing import Dict, List, Set

from codemanip import code_utils

from litgen.internal.context.type_synonyms import *
from litgen.options import LitgenOptions


class NamespacesCodeTree:
    """Stores namespaces and sub-namespace (modules and submodules in python) code

    Two instances NamespacesCodeTree are stored inside LitgenContext (for pydef and for stub code)

    - they are filled during calls to `AdaptedNamespace._str_stub_lines()` and `AdaptedNamespace._str_pydef_lines()`
      (i.e. AdaptedNamespace does not output code immediately, but stores it in the context)
    - their content is outputted by AdaptedUnit (which calls full_tree_code())
    """

    _namespace_code: Code
    _sub_namespaces_code: Dict[CppNamespaceName, NamespacesCodeTree]

    _created_namespaces: Set[CppQualifiedNamespaceName]

    _namespace_code_intro: str
    _namespace_code_outro: str
    _code_type: PydefOrStub
    _options: LitgenOptions

    def __init__(self, options: LitgenOptions, code_type: PydefOrStub) -> None:
        self._namespace_code = ""
        self._sub_namespaces_code = {}
        self._created_namespaces = set()
        self._code_type = code_type
        self._options = options

        if code_type == PydefOrStub.Stub:
            self._namespace_code_intro = "\n# <submodule NS_NAME>\n"
            self._namespace_code_outro = "\n# </submodule NS_NAME>\n"
        elif code_type == PydefOrStub.Pydef:
            self._namespace_code_intro = "\n{ // <namespace NS_NAME>\n"
            self._namespace_code_outro = "\n} // </namespace NS_NAME>\n"

    def full_tree_code(self, indent_str: str, current_namespace_name: str = "") -> str:
        r = ""

        if len(current_namespace_name) == 0:
            is_namespace_ignored = True
        else:
            is_namespace_ignored = code_utils.does_match_regex(
                self._options.namespace_ignored__regex, current_namespace_name
            )

        if not is_namespace_ignored:
            r += self._namespace_code_intro.replace("NS_NAME", current_namespace_name)

        r += self._namespace_code

        for ns_name, sub_namespace_stub_code in self._sub_namespaces_code.items():
            sub_code = sub_namespace_stub_code.full_tree_code(indent_str, ns_name)
            if not is_namespace_ignored:
                sub_code = code_utils.indent_code(sub_code, indent_str=indent_str)
            r += sub_code

        if not is_namespace_ignored:
            r += self._namespace_code_outro.replace("NS_NAME", current_namespace_name)

        return r

    def _store_code_in_tree(self, namespace_names: List[CppNamespaceName], code: str):
        ns_name = namespace_names[0]
        if ns_name not in self._sub_namespaces_code.keys():
            self._sub_namespaces_code[ns_name] = NamespacesCodeTree(self._options, self._code_type)

        if len(namespace_names) == 1:
            self._sub_namespaces_code[ns_name]._namespace_code += code
        else:
            self._sub_namespaces_code[ns_name]._store_code_in_tree(namespace_names[1:], code)

    def store_code(self, qualified_namespace_name: CppQualifiedNamespaceName, code: str) -> None:
        namespaces_names = qualified_namespace_name.split("::")
        self._store_code_in_tree(namespaces_names, code)

    def was_namespace_created(self, qualified_namespace_name: CppQualifiedNamespaceName) -> bool:
        r = qualified_namespace_name in self._created_namespaces
        return r

    def register_namespace_creation(self, qualified_namespace_name: CppQualifiedNamespaceName) -> None:
        self._created_namespaces.add(qualified_namespace_name)