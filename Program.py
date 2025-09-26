import os
import sys
import argparse
import xml.etree.ElementTree as ET
import base64

VFS_NAME = "vfs"
VFS_ROOT_PATH = "" 
VFS_CWD = "/"      
VFS_TREE = None    

# --- VFS Структуры Данных ---

class VFSNode:
    """Базовый узел VFS: может быть Файлом или Директорией."""
    def __init__(self, name, type="dir", content=None, encoding=None):
        self.name = name
        self.type = type 
        self.content = content 
        self.encoding = encoding

    def is_dir(self):
        return self.type == "dir"

    def is_file(self):
        return self.type == "file"

    def get_decoded_content(self):
        """Возвращает содержимое файла, декодированное при необходимости."""
        if self.is_dir():
            return None
        
        if self.encoding == "base64":
            try:
                return base64.b64decode(self.content).decode('utf-8')
            except Exception as e:
                return f"!! Error decoding base64: {e} !!"
        else:
            return self.content

class VFS:
    """Управление виртуальной файловой системой."""
    def __init__(self, xml_path):
        self.root = VFSNode(name="/", type="dir", content={})
        self.xml_path = xml_path
        self._load_vfs_from_xml()

    def _parse_element(self, element, parent_node):
        """Рекурсивно парсит XML-элементы и строит VFS-дерево."""
        for child_element in element:
            name = child_element.attrib.get('name')
            node_type = child_element.tag
            
            if not name:
                print(f"Warning: Skipping VFS node with no 'name' attribute in {node_type} element.", file=sys.stderr)
                continue

            if node_type == "dir":
                new_node = VFSNode(name=name, type="dir", content={})
                parent_node.content[name] = new_node
                self._parse_element(child_element, new_node)
            
            elif node_type == "file":
                encoding = child_element.attrib.get('encoding')
                content = child_element.text.strip() if child_element.text else ""
                
                new_node = VFSNode(name=name, type="file", content=content, encoding=encoding)
                parent_node.content[name] = new_node
            
    def _load_vfs_from_xml(self):
        """Загружает VFS из XML-файла. Гарантирует создание корня."""
        
        try:
            tree = ET.parse(self.xml_path)
            xml_root = tree.getroot()
            
            if xml_root.tag != "vfs":
                raise ValueError(f"Root tag must be 'vfs', found '{xml_root.tag}'")
            
            self.root = VFSNode(name="/", type="dir", content={}) 
            self._parse_element(xml_root, self.root)
            print("VFS loaded successfully from XML.")
            
        except FileNotFoundError:
            print(f"Error: VFS XML file not found at '{self.xml_path}'. Initializing minimal VFS.", file=sys.stderr)
            self.root = VFSNode(name="/", type="dir", content={})
        except ET.ParseError as e:
            print(f"Error: Failed to parse XML file: {e}. Initializing minimal VFS.", file=sys.stderr)
            self.root = VFSNode(name="/", type="dir", content={})
        except Exception as e:
            print(f"An unexpected error occurred during VFS loading: {e}. Initializing minimal VFS.", file=sys.stderr)
            self.root = VFSNode(name="/", type="dir", content={})


    def get_node(self, path):
        """Находит узел VFS по абсолютному или относительному пути."""
        global VFS_CWD

        # Спасибо пайтон
        path_unix_style = path.replace('\\', '/')
        
        current_path = os.path.normpath(os.path.join(VFS_CWD, path_unix_style))
        
        current_path = current_path.replace('\\', '/')
        
        if current_path == "/":
            return self.root
        
        parts = current_path.strip("/").split("/")
        
        current_node = self.root
        for part in parts:
            if part == "" or not current_node.is_dir():
                continue 
            
            if part not in current_node.content:
                return None
            
            current_node = current_node.content[part]
            
        return current_node


# --- Обработчики Команд ---

def handle_exit():
    print("Exiting shell...")
    sys.exit(0)

def handle_ls(args):
    """Обновленная команда ls для работы с VFS."""
    global VFS_TREE
    
    path = args[0] if args else "."
    
    node = VFS_TREE.get_node(path) 
    
    if node is None:
        print(f"ls: cannot access '{path}': No such file or directory")
        return
        
    if node.is_file():
        print(f"--- {node.name} (FILE) ---")
        print(node.get_decoded_content())
        print("--------------------")
    elif node.is_dir():
        print(f"Directory listing for {path}:")
        if not node.content:
            print("  (empty)")
        else:
            for name, child in node.content.items():
                type_str = "DIR" if child.is_dir() else "FILE"
                print(f"  [{type_str}] {name}")

def handle_cd(args):
    """Обновленная команда cd для работы с VFS."""
    global VFS_CWD
    
    if not args:
        target_path = "/"
    else:
        target_path = args[0]
        
    node = VFS_TREE.get_node(target_path)
    
    if node is None:
        print(f"cd: {target_path}: No such file or directory")
    elif not node.is_dir():
        print(f"cd: {target_path}: Not a directory")
    else:
        new_cwd = os.path.normpath(os.path.join(VFS_CWD, target_path)).replace('\\', '/')
        VFS_CWD = "/" + new_cwd.lstrip("/") 
        print(f"Changed directory to: {VFS_CWD}")

def parse_and_execute(command_line):
    expanded_line = os.path.expandvars(command_line)
    parts = expanded_line.split()
    if not parts:
        return
        
    command = parts[0]
    args = parts[1:]
    
    if command == "exit":
        handle_exit()
    elif command == "ls":
        if VFS_TREE is None: 
             print("shell: VFS is not initialized.")
        else:
            handle_ls(args)
    elif command == "cd":
        if VFS_TREE is None: 
             print("shell: VFS is not initialized.")
        else:
            handle_cd(args)
    else:
        print(f"shell: command not found: {command}")

def execute_script(script_path):
    try:
        with open(script_path, 'r') as f:
            for line in f:
                if line.strip().startswith('#') or not line.strip():
                    continue

                print(f"{VFS_NAME}:{VFS_CWD}> {line.strip()}")
                parse_and_execute(line.strip())
                
    except FileNotFoundError:
        print(f"shell: script not found: {script_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"shell: error executing script: {e}", file=sys.stderr)
        sys.exit(1)


def repl_loop():
    print("=== VFS started successfully ===")
    print(f"VFS path set to: {VFS_ROOT_PATH}")
    print("Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input(f"{VFS_NAME}:{VFS_CWD}> ") 
            if not user_input.strip():
                continue
            parse_and_execute(user_input)
            
        except (EOFError, KeyboardInterrupt):
            print("\nExiting shell...")
            sys.exit(0)


def main():
    global VFS_ROOT_PATH, VFS_TREE
    
    parser = argparse.ArgumentParser(description="VFS Shell Emulator")
    parser.add_argument(
        '-v', '--vfs-path',
        type=str,
        default=os.path.join(os.getcwd(), 'vfs_test.xml'),
        help="Path to the physical location of the VFS XML file."
    )
    parser.add_argument(
        '-s', '--script',
        type=str,
        help="Path to the startup script to execute."
    )
    
    args = parser.parse_args()
    
    print("--- Debug Information ---")
    print(f"VFS XML Path: {args.vfs_path}")
    print(f"Script Path: {args.script}")
    print("-------------------------")
    
    VFS_ROOT_PATH = args.vfs_path
    
    VFS_TREE = VFS(VFS_ROOT_PATH)
    
    if args.script:
        execute_script(args.script)
    else:
        repl_loop()

if __name__ == "__main__":
    main()