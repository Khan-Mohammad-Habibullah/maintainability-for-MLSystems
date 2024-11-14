import os
import re
from collections import defaultdict
import ast
import ML_components

# method that returns python file names
def find_python_files(folder):
    python_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

# method that returns the list of all files that dont end in .py
def list_non_python_files(folder_path):
    non_python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if not file.endswith('.py'):
                non_python_files.append(os.path.join(root, file))
    
    return non_python_files

# method that, for py_file_paths, finds all static accesses to non python files
def get_non_python_file_calls_in_method(py_file_path, non_python_files_in_project):
    method_calls = {}
    with open(py_file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=py_file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_name = node.name
                non_python_files = []

                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        if isinstance(subnode.func, ast.Name):
                            if subnode.func.id == 'open':
                                if len(subnode.args) > 0 and isinstance(subnode.args[0], ast.Str):
                                    file_name = subnode.args[0].s
                                    if not file_name.endswith('.py'):  
                                        non_python_files.append(file_name)
                        elif isinstance(subnode.func, ast.Attribute):
                            if subnode.func.attr in ('read_csv', 'read_json', 'to_csv', 'to_json'):
                                if len(subnode.args) > 0 and isinstance(subnode.args[0], ast.Str):
                                    file_name = subnode.args[0].s
                                    if not file_name.endswith('.py'):
                                        non_python_files.append(file_name) 
                        elif isinstance(subnode.func, ast.Attribute):
                            if subnode.func.attr in ('load', 'dump'):
                                if isinstance(subnode.func.value, ast.Name) and subnode.func.value.id == 'json':
                                    if len(subnode.args) > 0 and isinstance(subnode.args[0], ast.Str):
                                        file_name = subnode.args[0].s
                                        if not file_name.endswith('.py'):
                                            non_python_files.append(file_name)
                    if isinstance(subnode, ast.Str):
                        if subnode.s in non_python_files_in_project:
                            non_python_files.append(subnode.s)
                
                if non_python_files:
                    method_calls[method_name] = non_python_files

    return method_calls

# function to extract library calls
def extract_library_calls(py_file_path):
    library_calls_in_functions = {}
    with open(py_file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=py_file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef): 
                function_name = node.name  
                library_calls = []
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):  
                        if isinstance(subnode.func, ast.Attribute):
                            parts = []
                            current_node = subnode.func
                            while isinstance(current_node, ast.Attribute):
                                parts.append(current_node.attr)
                                current_node = current_node.value
                            if isinstance(current_node, ast.Name):
                                parts.append(current_node.id)
                            library_call = ".".join(reversed(parts))
                            library_calls.append(library_call)
                
                if library_calls:
                    library_calls_in_functions[function_name] = library_calls

    return library_calls_in_functions

# function to find all python files
def find_python_files(folder):
    python_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

# function that finds for all methods in a file what instance variables are accessed
def extract_function_parameters(file_path):
    function_parameters = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Check if the line contains a function definition
            if "def " in line:
                # Use regular expression to extract function name and parameters
                match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)', line)
                if match:
                    function_name = match.group(1)
                    parameters = match.group(2).split(',') if match.group(2) else []
                    # Strip whitespace and filter out 'self'
                    parameters = [param.strip() for param in parameters if param.strip() != 'self']
                    function_parameters[function_name] = parameters
    return function_parameters

# method that finds all instance variables in a given file
def extract_instance_variables(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())

    instance_var_dict = {}

    class FunctionVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_function = None

        def visit_FunctionDef(self, node):
            self.current_function = node.name
            if self.current_function not in instance_var_dict:
                instance_var_dict[self.current_function] = []
            self.generic_visit(node)
            self.current_function = None

        def visit_Attribute(self, node):
            if isinstance(node.value, ast.Name) and node.value.id == 'self':
                if self.current_function:
                    instance_var_dict[self.current_function].append(node.attr)
            self.generic_visit(node)

    FunctionVisitor().visit(tree)

    # Remove duplicates from the lists
    for func, vars in instance_var_dict.items():
        instance_var_dict[func] = list(set(vars))

    return instance_var_dict

# method that extracts function input variables for all methods in a file
def extract_parameters(line):
    start = line.find('(') + 1
    end = line.find(')') - 1
    return line[start:end]

# method to create and adjacency graph of all connected methods in a file
def build_graph(functions):
    graph = defaultdict(set)
    parameter_to_functions = defaultdict(set)

    for function, params in functions.items():
        for param in params:
            parameter_to_functions[param].add(function)

    for funcs in parameter_to_functions.values():
        funcs = list(funcs)
        for i in range(len(funcs)):
            for j in range(i + 1, len(funcs)):
                graph[funcs[i]].add(funcs[j])
                graph[funcs[j]].add(funcs[i])

    return graph

# method that extracts all reachable neighbours(functions) for a node(function) in the graph
def get_reachable_functions(graph):

    def dfs(node, graph, visited):
        visited.add(node)
        reachable = [node]
        for neighbor in graph[node]:
            if neighbor not in visited:
                reachable.extend(dfs(neighbor, graph, visited))
        return reachable

    reachable_dict = {}
    for func in graph:
        visited = set()
        reachable_dict[func] = dfs(func, graph, visited)
    
    return reachable_dict

# method to find the unique pairs count (for the LCC formula)
def unique_pairs_count(n):
    if n < 2:
        return 0
    return n * (n - 1) / 2

# method to find the nr of functions in a file
def get_nr_functions_in_file(file_name):
    return len(extract_function_parameters(file_name))

# method to add file access and library call connections to the shared variable use connections
def add_other_connections(instance_variables,method_files_dict,library_calls):
    final_dict = {}
    for func in instance_variables:
        final_dict[func] = instance_variables[func]
        if func in method_files_dict.keys():
            final_dict[func].extend(method_files_dict[func])
        if func in library_calls.keys():
            final_dict[func].extend(library_calls[func])
    return final_dict

# method to calculate the median cohesion (not used atm)
def calculate_median_cohesion(cohesion_list):
        cohesion_list.sort()
        cohesion_count = len(cohesion_list)
        if cohesion_count % 2 == 0:
            cohesion_median = (cohesion_list[(cohesion_count//2)-1] + cohesion_list[(cohesion_count//2)])/2
        else:
            cohesion_median = cohesion_list[(cohesion_count)//2]
        return cohesion_median

def main():

    to_measure_over_DA = ML_components.latexocr_DA
    to_measure_over_TP = ML_components.latexocr_TP
    to_measure_over_ML = ML_components.latexocr_ML
    to_measure_over_NON = ML_components.latexocr_NON
    folder_path = ["github/LaTeX-OCR-main"]

    folder_paths = [
        "github/face_recognition-master",
        "github/faceswap-master",
        "github/Open-Assistant-main",
        "github/DeepFaceLive-master",
        "github/CLIP-main",
        "github/EasyOCR-master",
        "github/DocsGPT-main",
        "github/ChatterBot-master",
        "github/albumentations-main",
        "github/deepface-master"
        ]

    for project in folder_path:
        if not os.path.isdir(project):
            print("Invalid folder path.")
            return
        
        python_files = find_python_files(project)
        cohesion_list = []
        cohesion_list_DA = []
        cohesion_list_TP = []
        cohesion_list_ML = []
        cohesion_list_NON = []
        for file in python_files:
            instance_variables = extract_instance_variables(file)
            graph = build_graph(instance_variables)
            connections = get_reachable_functions(graph)
            unique_connected_pairs = 0
            nr_unique_pairs = unique_pairs_count(len(instance_variables))

            for i, func in enumerate(connections.keys()):
                for other_func in list(connections.keys())[i + 1:]:  #
                    if other_func in connections[func]: 
                        unique_connected_pairs += 1

            if nr_unique_pairs != 0:
                cohesion = unique_connected_pairs / nr_unique_pairs
                cohesion_list.append(cohesion)
                if file in to_measure_over_DA:
                    cohesion_list_DA.append(cohesion)
                if file in to_measure_over_TP:
                    cohesion_list_TP.append(cohesion)
                if file in to_measure_over_ML:
                    cohesion_list_ML.append(cohesion)
                if file in to_measure_over_NON:
                    cohesion_list_NON.append(cohesion)
            else:
                cohesion_list.append(1)
                if file in to_measure_over_DA:
                    cohesion_list_DA.append(1)
                if file in to_measure_over_TP:
                    cohesion_list_TP.append(1)
                if file in to_measure_over_ML:
                    cohesion_list_ML.append(cohesion)
                if file in to_measure_over_NON:
                    cohesion_list_NON.append(1)
        cohesion_mean = sum(cohesion_list) / max(len(cohesion_list),1)            
        print("project "+project +" has a mean cohesion of " + str(cohesion_mean))
        cohesion_mean = sum(cohesion_list_DA) / max(len(cohesion_list_DA),1)
        print("project "+project +" has a mean DA cohesion of " + str(cohesion_mean))
        cohesion_mean = sum(cohesion_list_TP) / max(len(cohesion_list_TP),1)
        print("project "+project +" has a mean TP cohesion of " + str(cohesion_mean))
        cohesion_mean = sum(cohesion_list_ML) / max(len(cohesion_list_ML),1)
        print("project "+project +" has a mean ML cohesion of " + str(cohesion_mean))
        cohesion_mean = sum(cohesion_list_NON) / max(len(cohesion_list_NON),1)
        print("project "+project +" has a mean NON cohesion of " + str(cohesion_mean))


if __name__ == "__main__":
    main()
