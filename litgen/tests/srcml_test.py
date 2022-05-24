import os, sys; _THIS_DIR = os.path.dirname(__file__); sys.path = [_THIS_DIR + "/.."] + sys.path

import litgen.internal.srcml as srcml
import litgen.internal.code_utils as code_utils

import logging


def assert_code_unmodified_by_srcml(code: str):
    """
    We transform the code to xml (srcML), and assert that it can safely be translated back to the same code
    """
    root = srcml.code_to_srcml(code)
    code2 = srcml.srcml_to_code(root)
    assert code2 == code


def test_srcml_xml():
    code = "int a = 1"
    element = srcml.code_to_srcml(code, False)
    xml_str = srcml.srcml_to_str(element)
    expected_xml_str = """<?xml version="1.0" ?>
        <ns0:unit xmlns:ns0="http://www.srcML.org/srcML/src" revision="1.0.0" language="C++" filename="/var/folders/hj/vlpl655s0gz58f0tfgghv0g40000gn/T/tmph4tcp71f.h">
           <ns0:decl>
              <ns0:type>
                 <ns0:name>int</ns0:name>
              </ns0:type>
               
              <ns0:name>a</ns0:name>
               
              <ns0:init>
                 = 
                 <ns0:expr>
                    <ns0:literal type="number">1</ns0:literal>
                 </ns0:expr>
              </ns0:init>
           </ns0:decl>
        </ns0:unit>    
    """

    def remove_first_two_lines(s: str):
        # We remove the first lines because of the unwanted file name
        lines = s.splitlines()
        r = "\n".join(lines[2:])
        return r

    code_utils.assert_are_equal_ignore_spaces(remove_first_two_lines(xml_str), remove_first_two_lines(expected_xml_str))


def test_srcml_does_not_modify_code():
    assert_code_unmodified_by_srcml("int a = 1;")
    assert_code_unmodified_by_srcml("void foo(int x, int y=5){};")
    assert_code_unmodified_by_srcml("""
    #include <nonexistingfile.h>
    #define TRUC
    // A super nice function
    template<typename T> constexpr T add(const T& a, T b) { return a + b;}
    
    /* A dummy comment */
                            ;;TRUC;;TRUC; TRUC TRUC   ;;;; // and some gratuitous elements
    // A lambda
    auto fnSub = [](int a, int b) { return b - a;};
    """)


def test_srcml_repr():
    code = "int a;"
    element = srcml.first_code_element_with_tag(code, "decl_stmt")
    cpp_decl_statement  = srcml.parse_decl_stmt(element)
    repr_cpp_decl_statement = repr(cpp_decl_statement)
    repr_expected = 'CppDeclStatement(cpp_decls=[CppDecl(cpp_type=CppType(name=\'int\', specifiers=[], modifiers=[], argument_list=[]), name=\'a\', init=\'\')])'
    assert repr_cpp_decl_statement == repr_expected


def test_cpp_element_positions():
    code = """
    {
        /* 
        A multiline 
        comment
        */
    }
    """
    element = srcml.first_code_element_with_tag(code, "block")
    cpp_block = srcml.parse_block(element)
    assert str(cpp_block.start) == "2:5"
    assert str(cpp_block.end) == "7:5"


def test_parse_cpp_decl_statement():
    # Basic test
    code = "int a;"
    element = srcml.first_code_element_with_tag(code, "decl_stmt")
    cpp_decl_statement  = srcml.parse_decl_stmt(element)
    code_utils.assert_are_equal_ignore_spaces(cpp_decl_statement, "int a")

    # # Test with *, initial value and east/west const translation
    code = "int const *a=nullptr;"
    element = srcml.first_code_element_with_tag(code, "decl_stmt")
    cpp_decl_statement  = srcml.parse_decl_stmt(element)
    code_utils.assert_are_equal_ignore_spaces(cpp_decl_statement, "const int * a = nullptr")

    # Test with several variables + modifiers
    code = "int a = 3, &b = b0, *c;"
    element = srcml.first_code_element_with_tag(code, "decl_stmt")
    cpp_decl_statement  = srcml.parse_decl_stmt(element)
    code_utils.assert_are_codes_equal(cpp_decl_statement, """
        int a = 3
        int & b = b0
        int * c
    """)


    # Test with double pointer, which creates a double modifier
    code = "uchar **buffer;"
    element = srcml.first_code_element_with_tag(code, "decl_stmt")
    cpp_decl_statement  = srcml.parse_decl_stmt(element)
    code_utils.assert_are_codes_equal(cpp_decl_statement, "uchar * * buffer")

    # Test with a template type
    code = "std::map<int, std::string>x = {1, 2, 3};"
    element = srcml.first_code_element_with_tag(code, "decl_stmt")
    cpp_decl_statement  = srcml.parse_decl_stmt(element)
    code_utils.assert_are_codes_equal(cpp_decl_statement, "std::map<int, std::string> x = {1, 2, 3}")


def test_parse_function_decl():
    # Basic test with repr
    code = "int foo();"
    element = srcml.first_code_element_with_tag(code, "function_decl")
    function_decl  = srcml.parse_function_decl(element)
    assert repr(function_decl) == "CppFunctionDecl(specifiers=[], type=CppType(name='int', specifiers=[], modifiers=[], argument_list=[]), name='foo', parameter_list=CppParameterList(parameters=[]))"

    # Basic test with str
    code = "int foo();"
    element = srcml.first_code_element_with_tag(code, "function_decl")
    function_decl  = srcml.parse_function_decl(element)
    assert str(function_decl) == "int foo()"


    # Test with params and default values
    code = "int add(int a, int b = 5);"
    element = srcml.first_code_element_with_tag(code, "function_decl")
    function_decl  = srcml.parse_function_decl(element)
    code_utils.assert_are_codes_equal(function_decl, "int add(int a, int b = 5)")

    # Test with template types
    code = """
    std::vector<std::pair<size_t, int>>     enumerate(std::vector<int>&   const    xs);
    """
    element = srcml.first_code_element_with_tag(code, "function_decl")
    function_decl  = srcml.parse_function_decl(element)
    code_utils.assert_are_codes_equal(function_decl, "std::vector<std::pair<size_t, int>> enumerate(const std::vector<int> & xs)")

    # Test with type declared after ->
    code = "auto divide(int a, int b) -> double;"
    element = srcml.first_code_element_with_tag(code, "function_decl")
    function_decl  = srcml.parse_function_decl(element)
    code_utils.assert_are_codes_equal(function_decl, "double divide(int a, int b)")


    # Test with inferred type
    code = "auto minimum(int&&a, int b = 5);"
    element = srcml.first_code_element_with_tag(code, "function_decl")
    function_decl  = srcml.parse_function_decl(element)
    code_utils.assert_are_codes_equal(function_decl, "auto minimum(int && a, int b = 5)")


def test_parse_function_definition():
    code = "int foo() {return 42;}"
    element = srcml.first_code_element_with_tag(code, "function")
    function_srcml  = srcml.parse_function(element)
    function_str = str(function_srcml)
    code_utils.assert_are_codes_equal(function_str, "int foo() { OMITTED_BLOCK; }")


def test_nice_warning_message():
    code = """
    void foo(int x, int^ y); // ^ is not an authorized modifier!
    """
    element = srcml.first_code_element_with_tag(code, "function_decl")
    got_exception = False
    try:
        function_srcml  = srcml.parse_function_decl(element)
    except srcml.SrcMlException as e:
        got_exception = True
        message = str(e)

        expected_short_message_on_first_line = 'modifier "^" is not authorized'
        first_message_line = message.splitlines()[0]
        assert expected_short_message_on_first_line in first_message_line

        expected_detailed_infos = [
            "Position:2:21: Issue inside parent cpp_element of type <class 'srcml_types.CppType'> (parsed by litgen.internal.srcml.parse_type)",
            "Issue found in its srcml child, with this C++ code:",
            "Parent cpp_element original C++ code:",
            "int^",
            "Parent cpp_element code, as currently parsed by litgen (of type <class 'srcml_types.CppType'>)"
            ]
        for expected_detailed_info in expected_detailed_infos:
            assert expected_detailed_info in message

        expected_call_stack_info = """
        Python call stack info:
              File "/Users/pascal/dvp/OpenSource/ImGuiWork/litgen/litgen/internal/srcml.py", line xxx, in parse_type
        """
        import re
        message_no_line_number = re.sub(r'\d', 'x', message)
        assert expected_call_stack_info in message_no_line_number

    assert got_exception == True


def test_struct_srcml():
    code = """
    struct a {
        int x;
    };
    """
    element = srcml.first_code_element_with_tag(code, "struct", False)
    srcml_str = srcml.srcml_to_str(element)
    expected_str = """
        <?xml version="1.0" ?>
        <ns0:struct
            xmlns:ns0="http://www.srcML.org/srcML/src">
                   struct                    
            <ns0:name>a</ns0:name>
            <ns0:block>
                      {                      
                <ns0:public type="default">
                    <ns0:decl_stmt>
                        <ns0:decl>
                            <ns0:type>
                                <ns0:name>int</ns0:name>
                            </ns0:type>
                            <ns0:name>x</ns0:name>
                        </ns0:decl>
                            ;                         
                    </ns0:decl_stmt>
                </ns0:public>
                      }                   
            </ns0:block>
                   ;                
        </ns0:struct>
        """
    code_utils.assert_are_codes_equal(code_utils.force_one_space(srcml_str), code_utils.force_one_space(expected_str))


def test_parse_struct_decl():
    code = """
    struct a 
    {
        
        int a, b = 2;
        int add(int a, int b);        
        // Sustract
        int sub(int a, int b) { return b - a;}
        
        struct A {
        };
    };
    """
    element = srcml.first_code_element_with_tag(code, "struct")
    struct = srcml.parse_struct_or_class(element)
    # code_utils.assert_are_codes_equal(struct, "")
    # print(struct)


def test_parse_block():
    code = """
    {
        int z,w =2;
        int add(int a, int b);        
     
        // Sustract
        int sub(int a, int b) {
            int c = 56; 
            callMummy();
            return b - a - c;
        }
        
        struct A {
        };
        
        namespace internal
        {
            bool flag;
        }    
        
        enum MyEnum
        {
            A = 0;
        };
        
        enum class MyEnumClass
        {
            B = 1;
        };
    }
    """
    element = srcml.first_code_element_with_tag(code, "block")
    cpp_block = srcml.parse_block(element)
    block_str = str(cpp_block)
    # print(block_str)

    expected_str = """
        // <CppBlockContent>
        int z
        int w = 2
        int add(int a, int b)
        // Sustract
        int sub(int a, int b) { OMITTED_BLOCK; }
        struct A
        {
            public:
        
        };
        
        namespace internal
        {
            bool flag
        }
        
        enum MyEnum
        {
             A = 0
        }
        
        enum MyEnumClass
        {
             B = 1
        }
        
        // </CppBlockContent>
    """

    code_utils.assert_are_codes_equal(block_str, expected_str)
    #print(block)


#test_parse_struct_decl()
#test_struct_srcml()
#test_parse_block2()
test_parse_block()
