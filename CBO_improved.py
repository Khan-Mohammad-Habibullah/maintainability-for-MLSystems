import os
import ast
import copy
import ML_components

# method that returns python file names
def find_python_file_names(folder):
    python_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.py'):
                python_files.append(file[:-2])
    return python_files

# method to find all python files
def find_python_files(folder):
    python_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

# method to find what non-code files are accessed by each code file
def find_file_access_patterns(py_file_path):

    accessed_files = []
    
    with open(py_file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=py_file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    if len(node.args) > 0 and isinstance(node.args[0], ast.Str):
                        accessed_files.append(node.args[0].s)
                elif isinstance(node.func, ast.Attribute) and node.func.attr in ('read_csv', 'read_json'):
                    if len(node.args) > 0 and isinstance(node.args[0], ast.Str):
                        accessed_files.append(node.args[0].s)
    return accessed_files

# method to extract the names of all functions within a file
def extract_function_names(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
    
    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if the function name is __init__
            if node.name == "__init__":
                # Find the parent class name
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and node in parent.body:
                        #function_names.append(parent.name)
                        break
            elif node.name != "__str__":
                function_names.append(node.name)
    
    return function_names

# method to extract file variables (only file/class wide, not local)
def extract_class_properties(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
    
    class_properties = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            properties = set()
            
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Assign):
                    for target in subnode.targets:
                        if isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                properties.add(target.attr)
                        
                if isinstance(subnode, ast.AnnAssign):
                    target = subnode.target
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            properties.add(target.attr)
            
            class_properties = list(properties)
    return class_properties

# method that creates a dictionary of the unique number of external methods for each other file called by file: file_path
# key [other_file] value [nr of unique methods of this file called by file: file_path]
def count_call_occurrences(file_path, string_list, methods_in_files):

    occurrences = {string[:]: 0 for string in string_list}
    with open(file_path, 'r') as file:
        for line in file:
            for file_with_methods in methods_in_files:
                for method in methods_in_files[file_with_methods]:
                    method_call_str = "." + method + "("
                    if method_call_str in line:
                        occurrences[file_with_methods] += 1
                        methods_in_files[file_with_methods].remove(method)

    return occurrences

# method that creates a dictionary of the unique number of external variables for each other file called by file: file_path
# key [other_file] value [nr of unique variables of this file called by file: file_path]
def count_var_occurrences(file_path, string_list, variables_in_files):

    occurrences = {string[:]: 0 for string in string_list}
    
    with open(file_path, 'r') as file:
        for line in file:
            for file_with_variables in variables_in_files:
                for method in variables_in_files[file_with_variables]:
                    variable_call_str = "." + method
                    if variable_call_str in line:
                        occurrences[file_with_variables] += 1
                        variables_in_files[file_with_variables].remove(method)
    return occurrences

# method that implements the CBO formula (entire project)
def calculate_CBO(python_file_paths, methods, function_call_occurrences, variables, variable_call_occurrences):
    called_files = {}
    called_data_files = {}
    total_CBO = 0
    nr_files = 0
    for file_path in python_file_paths:
        called_files[file_path] = []
        called_data_files[file_path] = []
        coupled_data_files = find_file_access_patterns(file_path)
        for data_file in coupled_data_files:
            called_data_files[file_path].append(data_file)
        for other_file_path in function_call_occurrences:
            if file_path != other_file_path:
                if "test" not in file_path and "test" not in other_file_path:
                    if function_call_occurrences[file_path][other_file_path] > 0 or function_call_occurrences[other_file_path][file_path] > 0:
                        called_files[file_path].append(other_file_path)
                    elif variable_call_occurrences[file_path][other_file_path] > 0 or variable_call_occurrences[other_file_path][file_path] > 0:
                        called_files[file_path].append(other_file_path)
    for file in called_files:
        if len(called_files[file]) != 0:
            total_CBO += len(called_files[file]) + len(called_data_files[file])
            nr_files += 1
    if nr_files != 0: 
        return total_CBO/nr_files
    else:
        return 0

# method that implements the CBO formula (only for the files in to_measure_over)
def calculate_component_CBO(python_file_paths, methods, function_call_occurrences, variables, variable_call_occurrences, to_measure_over):
    called_files = {}
    called_data_files = {}
    total_CBO = 0
    nr_files = 0
    for file_path in python_file_paths:
        called_files[file_path] = []
        called_data_files[file_path] = []
        coupled_data_files = find_file_access_patterns(file_path)
        for data_file in coupled_data_files:
            called_data_files[file_path].append(data_file)
        for other_file_path in function_call_occurrences:
            if file_path != other_file_path:
                if "test" not in file_path and "test" not in other_file_path:
                    if function_call_occurrences[file_path][other_file_path] > 0 or function_call_occurrences[other_file_path][file_path] > 0:
                        called_files[file_path].append(other_file_path)
                    elif variable_call_occurrences[file_path][other_file_path] > 0 or variable_call_occurrences[other_file_path][file_path] > 0:
                        called_files[file_path].append(other_file_path)
    for file in called_files:
        if file in to_measure_over:
            if len(called_files[file]) != 0:
                total_CBO += len(called_files[file]) + len(called_data_files[file])
                nr_files += 1
    if nr_files != 0: 
        return total_CBO/nr_files
    else:
        return 0

def main():
    # edit the following five lines to select all subcomponents for a project and the project name
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
        "github/deepface-master",
        "github/LaTeX-OCR-main"
        ]

    for project in folder_path:
        if not os.path.isdir(project):
            print("Invalid folder path.")
            return
        
        methods_in_files = {}
        variables_in_files = {}
        python_file_paths = find_python_files(project)
        for file in python_file_paths:
            methods_in_files[file] = extract_function_names(file)
            variables_in_files [file] = extract_class_properties(file)
        function_call_occurrences = {}
        variable_call_occurrences = {}
        for file in python_file_paths:
            methods = copy.deepcopy(methods_in_files)
            function_call_occurrences[file] = count_call_occurrences(file, python_file_paths, methods)
            methods = copy.copy(methods_in_files)
            variables = copy.deepcopy(variables_in_files)
            variable_call_occurrences[file] = count_var_occurrences(file, python_file_paths, variables)
            variables = copy.copy(variables_in_files)
        CBO = calculate_CBO(python_file_paths, methods, function_call_occurrences, variables, variable_call_occurrences)
        print("mean coupling for " + project + " is " + str(CBO))
        CBO = calculate_component_CBO(python_file_paths, methods, function_call_occurrences, variables, variable_call_occurrences, to_measure_over_DA)
        print("mean coupling for Data Aqcuisition " + project + " is " + str(CBO))
        CBO = calculate_component_CBO(python_file_paths, methods, function_call_occurrences, variables, variable_call_occurrences, to_measure_over_TP)
        print("mean coupling for Training Pipeline " + project + " is " + str(CBO))
        CBO = calculate_component_CBO(python_file_paths, methods, function_call_occurrences, variables, variable_call_occurrences, to_measure_over_ML)
        print("mean coupling for Data ML " + project + " is " + str(CBO))
        CBO = calculate_component_CBO(python_file_paths, methods, function_call_occurrences, variables, variable_call_occurrences, to_measure_over_NON)
        print("mean coupling for Data Non_ML " + project + " is " + str(CBO))
if __name__ == "__main__":
    main()