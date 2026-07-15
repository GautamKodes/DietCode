import os
import tree_sitter_python as tspython
try:
    import tree_sitter_rust as tsrust
except ImportError:
    tsrust = None
try:
    import tree_sitter_java as tsjava
except ImportError:
    tsjava = None
try:
    import tree_sitter_javascript as tsjs
except ImportError:
    tsjs = None
try:
    import tree_sitter_typescript as tsts
except ImportError:
    tsts = None
from tree_sitter import Language, Parser

def parse_file(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".rs":
        if tsrust is None:
            return [], []
        language = Language(tsrust.language())
    elif ext == ".java":
        if tsjava is None:
            return [], []
        language = Language(tsjava.language())
    elif ext in (".js", ".jsx"):
        if tsjs is None:
            return [], []
        language = Language(tsjs.language())
    elif ext in (".ts", ".tsx"):
        if tsts is None:
            return [], []
        if ext == ".tsx":
            language = Language(tsts.language_tsx())
        else:
            language = Language(tsts.language_typescript())
    else:
        language = Language(tspython.language())

    parser = Parser(language)

    with open(filepath, "rb") as f:
        code_bytes = f.read()
        
    tree = parser.parse(code_bytes)
    root_node = tree.root_node
    
    symbols = []
    imports = []
    
    stack = [root_node]
    while stack:
        node = stack.pop()
        
        if node.type in (
            "function_definition", "function_item", "method_declaration", "constructor_declaration", 
            "class_declaration", "function_declaration", "method_definition",
            "interface_declaration", "record_declaration", "enum_declaration", "type_alias_declaration"
        ):
            name_node = node.child_by_field_name("name")
            if not name_node:
                for child in node.children:
                    if child.type in ("identifier", "property_identifier"):
                        name_node = child
                        break
            if name_node:
                name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
                sym_type = "class" if node.type in (
                    "class_declaration", "interface_declaration", "record_declaration", 
                    "enum_declaration", "type_alias_declaration"
                ) else "function"
                symbols.append({
                    "name": name,
                    "type": sym_type,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "content": code_bytes[node.start_byte:node.end_byte].decode("utf-8")
                })
        elif node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(code_bytes[child.start_byte:child.end_byte].decode("utf-8"))
                elif child.type == "aliased_import":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        imports.append(code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8"))
                elif child.type == "string":
                    import_path = code_bytes[child.start_byte:child.end_byte].decode("utf-8").strip("'\"")
                    imports.append(import_path)
        elif node.type == "import_from_statement":
            for child in node.children:
                if child.type in ("dotted_name", "relative_import"):
                    imports.append(code_bytes[child.start_byte:child.end_byte].decode("utf-8"))
                    break
        elif node.type == "use_declaration":
            imports.append(
                code_bytes[node.start_byte:node.end_byte]
                .decode("utf-8")
                .replace("use", "", 1)
                .replace(";", "")
                .strip()
            )
        elif node.type == "import_declaration":
            import_text = code_bytes[node.start_byte:node.end_byte].decode("utf-8").strip()
            if import_text.startswith("import "):
                import_name = import_text.replace("import ", "", 1).rstrip(";").strip()
                imports.append(import_name)
        elif node.type == "call_expression":
            function_node = node.child_by_field_name("function")
            if function_node and code_bytes[function_node.start_byte:function_node.end_byte].decode("utf-8") == "require":
                arguments_node = node.child_by_field_name("arguments")
                if arguments_node and arguments_node.children:
                    for arg in arguments_node.children:
                        if arg.type == "string":
                            import_path = code_bytes[arg.start_byte:arg.end_byte].decode("utf-8").strip("'\"")
                            imports.append(import_path)
                            break
            
        for child in reversed(node.children):
            stack.append(child)

    return symbols, imports