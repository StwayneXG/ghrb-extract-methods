import re
import javalang
import pandas as pd
import os
import json

# Paths
DIFF_PATH = "output/json_diffs/"

def is_function_line(line):
    trimmed_line = line.strip()
    if trimmed_line.startswith("//"):
        return False
    
    if "(" in trimmed_line and any(keyword in trimmed_line for keyword in ["private", "protected", "public", "static", "void"]):
        return True
    elif "JSType" in trimmed_line and "{" in trimmed_line:
        return True
    elif "class" in trimmed_line and "{" in trimmed_line:
        return True
    
    return False

def extract_method_name(line):
    # Trim the line for clean matching
    trimmed_line = line.strip()
    
    # Case 1: Check if it's a class declaration
    if "class" in trimmed_line:
        # Extract class name, which follows the 'class' keyword
        class_match = re.search(r'class\s+(\w+)', trimmed_line)
        if class_match:
            return class_match.group(1)
        return None
    
    # Case 2: General method or constructor extraction
    # This pattern captures method/constructor name before the '('
    method_match = re.search(r'(\w+)\s*\(', trimmed_line)
    if method_match:
        return method_match.group(1)

    return None

def extract_methods(diff):
    lines = diff.split('\n')
    methods = set()

    for i, line in enumerate(lines):
        if line.startswith('-'):
            # Look upwards for the function declaration
            for j in range(i, -1, -1):
                if is_function_line(lines[j]):
                    method_name = extract_method_name(lines[j])
                    if method_name:
                        methods.add(method_name)
                    break  # Stop looking once we've found the function declaration

    return methods

def extract_method_implementations(methods, file_content):
    method_implementations = {}

    tree = javalang.parse.parse(file_content)
        
    for method_name in methods:
        method_position = _find_method(tree, method_name)
        if method_position:
            method_body = _find_method_body(method_position, file_content)
            method_implementations[method_name] = method_body

    return method_implementations

def _find_method(tree, method_name: str):
    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        if node.name == method_name:
            return node.position
    return None

def _find_method_body(start_position, content: str) -> str:
    lines = content.split('\n')
    current_line = start_position[0] - 1
    current_column = start_position[1] - 1
    brace_count = 0
    in_string = False
    in_char = False
    in_block_comment = False
    escape_next = False
    method_lines = []

    while current_line < len(lines):
        line = lines[current_line]
        i = current_column if current_line == start_position[0] - 1 else 0
        in_line_comment = False

        while i < len(line):
            char = line[i]

            if escape_next:
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif in_string:
                if char == '"':
                    in_string = False
            elif in_char:
                if char == "'":
                    in_char = False
            elif in_line_comment:
                pass
            elif in_block_comment:
                if char == '*' and i + 1 < len(line) and line[i + 1] == '/':
                    in_block_comment = False
                    i += 1
            else:
                if char == '"':
                    in_string = True
                elif char == "'":
                    in_char = True
                elif char == '/' and i + 1 < len(line):
                    if line[i + 1] == '/':
                        in_line_comment = True
                        i += 1
                    elif line[i + 1] == '*':
                        in_block_comment = True
                        i += 1
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        method_lines.append(line[:i + 1])
                        return '\n'.join(method_lines)

            i += 1

        method_lines.append(line)
        current_line += 1
        current_column = 0

    return '\n'.join(method_lines)

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def process_diff_content(diff_content):
    modified_content = ""

    for line in diff_content.split("\n"):
        if line.startswith("+"):
            continue
        elif line.startswith("-"):
            modified_content += line[1:] + "\n"
        else:
            modified_content += line + "\n"

    return modified_content

def main():
    for file_name in os.listdir(DIFF_PATH):
        if file_name.endswith(".json"):
            file_path = os.path.join(DIFF_PATH, file_name)
            diff_data = load_json(file_path)

            for file_name, diff_content in diff_data.items():
                modified_content = process_diff_content(diff_content)
                methods = extract_methods(diff_content)
                try:
                    method_implementations = extract_method_implementations(methods, modified_content)
                except Exception as e:
                    print(f"Error extracting method implementations for {file_name}: {e}")
                    print('File content:', modified_content)
                    return

                # Save method implementations to a CSV
                df = pd.DataFrame(method_implementations.items(), columns=["Method Name", "Method Implementation"])
                output_file = f"method_implemenations/{file_name}_diff_method_implementations.csv"
                df.to_csv(output_file, index=False)
                print(f"Method implementations saved to {output_file}")


if __name__ == "__main__":
    main()