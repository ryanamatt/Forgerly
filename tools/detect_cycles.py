import os
import ast

def get_imports(path):
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except:
            return []
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    return imports

def find_cycles():
    root_dir = "src/python"
    graph = {}
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                mod_name = file[:-3]
                graph[mod_name] = get_imports(full_path)
    
    print("--- Potential Import Loops ---")
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            if neighbor in graph and node in graph[neighbor]:
                print(f"Cycle detected: {node} <--> {neighbor}")

if __name__ == "__main__":
    find_cycles()