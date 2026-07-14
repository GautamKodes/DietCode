import tree_sitter_python as tspython
from tree_sitter import Language, Parser

def parse_file(filepath: str):
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)

    with open(filepath, "rb") as f:
        code_bytes = f.read()
        
    tree = parser.parse(code_bytes)
    root_node = tree.root_node
    
    symbols = []
    imports = []
    
    def traverse(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
                symbols.append({
                    "name": name,
                    "type": "function",
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
        elif node.type == "import_from_statement":
            for child in node.children:
                if child.type in ("dotted_name", "relative_import"):
                    imports.append(code_bytes[child.start_byte:child.end_byte].decode("utf-8"))
                    break
        for child in node.children:
            traverse(child)

    traverse(root_node)
    
    return symbols, imports