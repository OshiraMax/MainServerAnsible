import os
import sys
import pathspec

PROJECT_NAME = 'MainServer'
EXCLUDED_DIRS = {'.git', '.vscode', 'public', 'node_modules', 'assets'}
EXCLUDED_FILES = {'.gitignore', 'package-lock.json', 'inventory','summary.py','README.md'}
READ_CONTENT_DIRS = {'assets'}

def read_gitignore(gitignore_path):
    with open(gitignore_path, 'r') as f:
        spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
    return spec

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"

def generate_tree_view(path, spec):
    tree_view = ''
    for root, dirs, files in os.walk(path, topdown=True):
        dirs[:] = [d for d in dirs if not spec.match_file(os.path.relpath(os.path.join(root, d), path)) and d not in EXCLUDED_DIRS]
        files[:] = [f for f in files if not spec.match_file(os.path.relpath(os.path.join(root, f), path)) and f not in EXCLUDED_FILES]
        level = root.replace(path, '').count(os.sep)
        indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
        tree_view += '{}{}\n'.format(indent, os.path.basename(root) if root != path else PROJECT_NAME)
        subindent = '│   ' * level + '├── '
        for f in files:
            tree_view += '{}{}\n'.format(subindent, f)
    return tree_view

def scan_dir(path, spec, base_path):
    md_content = '# Структура проекта\n\n'
    md_content += '\n' + generate_tree_view(path, spec) + '\n\n'
    md_content += '# Код проекта\n\n'
    for root, dirs, files in os.walk(path, topdown=True):
        dirs[:] = [d for d in dirs if not spec.match_file(os.path.relpath(os.path.join(root, d), path)) and d not in EXCLUDED_DIRS]
        files[:] = [f for f in files if not spec.match_file(os.path.relpath(os.path.join(root, f), path)) and f not in EXCLUDED_FILES]

        relative_root = os.path.relpath(root, base_path)
        depth = relative_root.count(os.sep) if root != base_path else 0
        header_level = '##' + '#' * depth 

        if root != base_path:
            md_content += '{} {}\n\n'.format(header_level, os.path.basename(root))

        for file in sorted(files):
            file_path = os.path.join(root, file)
            md_content += '- **{}**\n\n'.format(file)
            if os.path.basename(root) not in READ_CONTENT_DIRS:
                content = read_file_content(file_path)
                md_content += content + '\n\n'

    return md_content

def generate_md(output_path, project_path='.'):
    gitignore_path = os.path.join(project_path, '.gitignore')
    if os.path.exists(gitignore_path):
        spec = read_gitignore(gitignore_path)
    else:
        spec = pathspec.PathSpec.from_lines('gitwildmatch', [])
    md_content = scan_dir(project_path, spec, project_path)
    with open(output_path, 'w', encoding='utf-8') as md_file:
        md_file.write(md_content)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python summary.py NameFile")
        sys.exit(1)
    
    output_file_name = sys.argv[1] + '.md'
    project_path = '.'
    generate_md(output_file_name, project_path)
