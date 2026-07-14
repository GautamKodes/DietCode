import os
import json
from search import semantic_search_files
from graph import get_impact_path
from db import get_db

def generate_raw_brief(task: str, file_map_text: str):
    search_results = semantic_search_files(task, top_n=2)
    related_files = [r[1] for r in search_results]
    
    all_paths = []
    affected_files = set()
    for f in related_files:
        paths = get_impact_path(f)
        for p in paths:
            all_paths.append(p)
            for file in p:
                affected_files.add(file)

    for f in related_files:
        if f in affected_files:
            affected_files.remove(f)

    return related_files, list(affected_files), all_paths

def resolve_targets(input_str: str):
    terms = input_str.replace(",", " ").split()
    resolved = set()
    
    conn = get_db()
    cur = conn.cursor()
    
    for term in terms:
        term = term.strip()
        if not term:
            continue
            
        if os.path.exists(term):
            resolved.add(term)
            continue
            
        cur.execute("""
            SELECT files.filepath 
            FROM symbols 
            JOIN files ON symbols.file_id = files.id 
            WHERE symbols.name = ?
        """, (term,))
        symbol_rows = cur.fetchall()
        if symbol_rows:
            for r in symbol_rows:
                resolved.add(r["filepath"])
            continue

        cur.execute("SELECT filepath FROM files")
        all_files = cur.fetchall()
        for f_row in all_files:
            filepath = f_row["filepath"]
            base = os.path.basename(filepath)
            name_no_ext = os.path.splitext(base)[0]
            if term.lower() in (base.lower(), name_no_ext.lower()):
                resolved.add(filepath)

    conn.close()
    return list(resolved)

def build_mission_brief(task: str, force_files: str = None, mode: str = "web"):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT value FROM project_meta WHERE key = 'summary'")
    summary_row = cur.fetchone()
    project_summary = summary_row["value"] if summary_row else "Python software project."

    cur.execute("SELECT filepath, summary FROM files")
    all_files = cur.fetchall()
    
    file_map_lines = []
    for f_row in all_files:
        path = f_row["filepath"]
        summary = f_row["summary"] or "No description."
        file_map_lines.append(f"- {path}: {summary}")
    file_map_text = "\n".join(file_map_lines)

    if force_files:
        related_files = resolve_targets(force_files)
        all_paths = []
        affected_files = set()
        for f in related_files:
            paths = get_impact_path(f)
            for p in paths:
                all_paths.append(p)
                for file in p:
                    affected_files.add(file)
        for f in related_files:
            if f in affected_files:
                affected_files.remove(f)
    else:
        related_files, affected_files, all_paths = generate_raw_brief(task, file_map_text)

    if not related_files:
        conn.close()
        return "No relevant files or symbols found in the codebase for this task."

    associated_lines = []
    file_contents = []
    for f in related_files:
        cur.execute("""
            SELECT s.name 
            FROM symbols s
            JOIN files f_tab ON s.file_id = f_tab.id
            WHERE f_tab.filepath = ?
        """, (f,))
        syms = cur.fetchall()
        sym_names = ", ".join([s["name"] for s in syms])
        if sym_names:
            associated_lines.append(f"- {f} (Symbols: {sym_names})")
        else:
            associated_lines.append(f"- {f}")
        
        if mode == "web":
            try:
                with open(f, "r", encoding="utf-8") as file_handle:
                    content = file_handle.read()
                    file_contents.append(f"### File: {f}\n```python\n{content}\n```")
            except Exception:
                pass
            
    conn.close()

    associated_text = "\n".join(associated_lines)
    
    path_strings = []
    for p in all_paths:
        path_strings.append(" -> ".join(p))
    paths_text = "\n".join([f"- {p}" for p in path_strings]) if path_strings else "None"

    if mode == "agent":
        fallback_brief = f"""# AGENT INSTRUCTION PROMPT

Act as an autonomous coding agent. Execute the following coding task in my repository.
You have direct read and write tool access to the workspace.

## Task
"{task}"

## Project Overview
{project_summary}

## Codebase File Map
Here is a list of all other files in this codebase and their high-level descriptions:
{file_map_text}

## Targeted Files to Modify
You are allowed to read and modify ONLY these files:
{associated_text}

## Downstream Dependency Cascades (Watch out for regressions!)
If you modify the targeted files, the following code paths are affected. You MUST update the imports or calls in these files if you change their dependencies:
{paths_text}

## Rules and Constraints
1. Workspace Reading: Use your file-reading tools (like cat or view_file) to read the targeted files directly. Do not request code contents from the user.
2. Code Modification: Apply your edits directly to the targeted files using your file edit or replacement tools.
3. Backward Compatibility: Existing functionality (such as Python code indexing) must continue to work unchanged.
4. Dependencies: Do not add new third-party dependencies or packages unless explicitly requested.
5. Target Escape Hatch: If this task cannot be fully implemented within the targeted files listed above, output no functional changes and write a clear block comment in the modified files explaining which additional files (such as parser.py or indexer.py) must be modified to achieve the goal.
"""
    else:
        code_blocks_text = "\n\n".join(file_contents)
        fallback_brief = f"""# AI INSTRUCTION PROMPT

Act as an expert software engineer. Execute the following coding task in my repository.

## Task
"{task}"

## Project Overview
{project_summary}

## Codebase File Map
Here is a list of all other files in this codebase and their high-level descriptions:
{file_map_text}

## Targeted Files to Modify
Modify ONLY these files. Do not create new files unless explicitly requested:
{associated_text}

## Downstream Dependency Cascades (Watch out for regressions!)
If you modify the targeted files, the following code paths are affected. You MUST update the imports or calls in these files if you change their dependencies:
{paths_text}

## Rules and Constraints
1. Backward Compatibility: Existing functionality (such as Python code indexing) must continue to work unchanged.
2. Dependencies: Do not add new third-party dependencies or packages unless explicitly requested.
3. Target Escape Hatch: If this task cannot be fully implemented within the targeted files listed above, output no functional changes and write a clear block comment explaining which additional files (such as parser.py or indexer.py) must be modified to achieve the goal.

## Output Formatting Instructions (Token Saving)
1. Proposed Change Map: Before writing any code blocks, output a compact, tree-style visual map of your proposed modifications (using ├── and └──) indicating which files you are updating and a 1-sentence description of the change in each.
2. Human-Readable Code Changes: Output the COMPLETE updated function or class blocks that need modification. Specify clearly which functions/classes to replace in which files. Do not output raw machine diff patches (like unified diffs or patch lines).
3. No Conversational Text: Do not write conversational summaries, explanations, introduction text, or explanations after the code blocks.
4. New Files: If you determine that new files must be created, show them in the Proposed Change Map and provide their complete content.

## Source Code of Targeted Files
Below is the current content of the files targeted for modification:

{code_blocks_text}
"""
    return fallback_brief
