import os
import sys
import argparse
import xml.etree.ElementTree as ET
import base64
import calendar
import datetime

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

    def get_decoded_content(self, raw=False):
        """Возвращает содержимое файла, декодированное (или сырое, если raw=True)."""
        if self.is_dir():
            return None
        
        if self.encoding == "base64":
            try:
                decoded_bytes = base64.b64decode(self.content)
                if raw:
                    return decoded_bytes 
                return decoded_bytes.decode('utf-8')
            except Exception as e:
                return f"!! Error decoding base64: {e} !!"
        else:
            if raw:
                return self.content.encode('utf-8')
            return self.content

class VFS:
    def __init__(self, xml_path):
        self.root = VFSNode(name="/", type="dir", content={})
        self.xml_path = xml_path
        self._load_vfs_from_xml()

    def _parse_element(self, element, parent_node):
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
        global VFS_CWD
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
        display_path = VFS_CWD if path == "." else path
        print(f"Directory listing for {display_path}:")
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

def handle_wc(args):
    """Реализует команду wc (word count) с поддержкой флагов -l, -w, -c."""
    global VFS_TREE
    
    # Парсинг аргументов
    show_lines = False
    show_words = False
    show_bytes = False
    file_path = None
    
    for arg in args:
        if arg.startswith('-'):
            for char in arg[1:]:
                if char == 'l':
                    show_lines = True
                elif char == 'w':
                    show_words = True
                elif char == 'c':
                    show_bytes = True
                else:
                    print(f"wc: invalid option -- '{char}'")
                    return
        elif file_path is None:
            file_path = arg
        else:
            # Поддерживается только один файл
            print("wc: only one file argument is supported.")
            return

    if file_path is None:
        print("wc: requires a file path.")
        return

    # Если флаги не заданы, выводим все три показателя
    if not (show_lines or show_words or show_bytes):
        show_lines = show_words = show_bytes = True

    # 2. Доступ к VFS Node и проверки
    node = VFS_TREE.get_node(file_path)
    
    if node is None:
        print(f"wc: {file_path}: No such file or directory")
        return
    
    if node.is_dir():
        print(f"wc: {file_path}: Is a directory")
        return

    # 3. Вычисление метрик
    try:
        content_bytes = node.get_decoded_content(raw=True)
        content_text = content_bytes.decode('utf-8')
        
        # Строки: считаем переносы + 1, если файл не пустой
        lines = content_text.count('\n') + (1 if content_text.strip() else 0)
        words = len(content_text.split())
        bytes_count = len(content_bytes)
        
        # 4. Форматирование вывода
        output_parts = []
        if show_lines:
            output_parts.append(f"{lines:7}")
        if show_words:
            output_parts.append(f"{words:7}")
        if show_bytes:
            output_parts.append(f"{bytes_count:7}")
            
        print(f" {' '.join(output_parts)} {file_path}")
        
    except Exception as e:
        print(f"wc: error processing {file_path}: {e}")
        
def handle_cal(args):
    """Реализует команду cal (calendar)."""
    
    now = datetime.datetime.now()
    month = now.month
    year = now.year

    if len(args) == 1:
        try:
            year = int(args[0])
            print(calendar.calendar(year))
            return
        except ValueError:
            print("cal: invalid argument. Usage: cal [month] [year] or cal [year]")
            return
    elif len(args) == 2:
        try:
            # cal [месяц] [год]
            month = int(args[0])
            year = int(args[1])
            if not (1 <= month <= 12):
                raise ValueError
            print(calendar.month(year, month))
            return
        except ValueError:
            print("cal: invalid arguments. Usage: cal [month] [year]")
            return
    elif len(args) > 2:
        print("cal: too many arguments. Usage: cal [month] [year] or cal [year]")
        return

    print(calendar.month(year, month))

def handle_who(args):
    """Реализует команду who (отображает, кто вошел в систему)."""
    
    current_user = os.getenv('USERNAME') or os.getenv('USER') or 'unknown_user'
    tty = 'pts/0' 
    login_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"{current_user} {tty} {login_time}")

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
        handle_ls(args)
    elif command == "cd":
        handle_cd(args)
    elif command == "wc":
        handle_wc(args)
    elif command == "cal":
        handle_cal(args)
    elif command == "who":
        handle_who(args)
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