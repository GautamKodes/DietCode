from os import symlink

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

def parse_file(filepath: str):
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)

    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node
    symbols = []
    imports = []
    def traverse(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = code[name_node.start_byte:name_node.end_byte]
                symbols.append({
                    "name": name,
                    "type": "function",
                    "start_line" : node.start_point[0] + 1,
                    "end_line" : node.end_point[0] + 1,
                    "content": code[node.start_byte:node.end_byte]
                })
        elif node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(code[child.start_byte:child.end_byte])
                elif child.type=="aliased_import":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        imports.append(code[name_node.start_byte:name_node.end_byte])
        elif node.type == "import_from_statement":
            for child in node.children:
                if child.type in ("dotted_name", "relative_import"):
                    imports.append(code[child.start_byte:child.end_byte])
                    break
        for child in node.children:
            traverse(child)

    traverse(root_node)
    return symbols, imports