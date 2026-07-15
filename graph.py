import os
import re
import networkx as nx
from db import get_db

def build_dependency_graph():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, filepath FROM files")
    files = cur.fetchall()
    
    module_to_file = {}
    project_files = []
    for f in files:
        filepath = f["filepath"]
        project_files.append(filepath)
        filename = os.path.basename(filepath)
        module_name = os.path.splitext(filename)[0]
        module_to_file[module_name] = filepath

    G = nx.DiGraph()
    for filepath in project_files:
        G.add_node(filepath)

    cur.execute("""
        SELECT files.filepath as importer_path, imports.imported_module
        FROM imports
        JOIN files ON imports.file_id = files.id
    """)
    imports = cur.fetchall()

    for imp in imports:
        importer = imp["importer_path"]
        imported = imp["imported_module"]
        
        target = None
        if imported in module_to_file:
            target = module_to_file[imported]
        else:
            module_path = imported.replace(".", "/")
            for filepath in project_files:
                if filepath.endswith(module_path + ".py") or filepath.endswith(module_path + ".java") or filepath.endswith(module_path + ".rs"):
                    target = filepath
                    break
        
        if target and target != importer:
            G.add_edge(target, importer)

    cur.execute("""
        SELECT s.name, f.filepath 
        FROM symbols s
        JOIN files f ON s.file_id = f.id
        WHERE s.type = 'class'
    """)
    classes = cur.fetchall()
    
    class_to_files = {}
    for cls in classes:
        name = cls["name"]
        path = cls["filepath"]
        if name not in class_to_files:
            class_to_files[name] = set()
        class_to_files[name].add(path)
        
    class_names_set = set(class_to_files.keys())
    
    file_contents = {}
    for filepath in project_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_contents[filepath] = f.read()
        except Exception:
            file_contents[filepath] = ""

    for filepath in project_files:
        code = file_contents[filepath]
        if not code:
            continue
            
        words = set(re.findall(r'\b\w+\b', code))
        matched = words.intersection(class_names_set)
        
        for cls_name in matched:
            for cls_file in class_to_files[cls_name]:
                if cls_file != filepath:
                    G.add_edge(cls_file, filepath)

    conn.close()
    return G

def get_impact_tree(filepath: str):
    G = build_dependency_graph()
    normalized_target = os.path.abspath(filepath)
    
    resolved_target = None
    for node in G.nodes:
        if os.path.abspath(node) == normalized_target:
            resolved_target = node
            break
            
    if not resolved_target:
        normalized_suffix = filepath.replace("\\", "/")
        for node in G.nodes:
            normalized_node = node.replace("\\", "/")
            if normalized_node.endswith("/" + normalized_suffix) or normalized_node == normalized_suffix:
                resolved_target = node
                break
                
    if not resolved_target:
        return None
        
    return nx.bfs_tree(G, resolved_target)

def get_impact_path(target_filepath: str):
    G = build_dependency_graph()
    normalized_target = os.path.abspath(target_filepath)
    
    resolved_target = None
    for node in G.nodes:
        if os.path.abspath(node) == normalized_target:
            resolved_target = node
            break
            
    if not resolved_target:
        normalized_suffix = target_filepath.replace("\\", "/")
        for node in G.nodes:
            normalized_node = node.replace("\\", "/")
            if normalized_node.endswith("/" + normalized_suffix) or normalized_node == normalized_suffix:
                resolved_target = node
                break
                
    if not resolved_target:
        return []
        
    affected = list(nx.descendants(G, resolved_target))
    paths = []
    for node in affected:
        try:
            path = nx.shortest_path(G, resolved_target, node)
            paths.append(path)
        except nx.NetworkXNoPath:
            pass
    return paths
