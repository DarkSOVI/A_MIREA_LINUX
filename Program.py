import os
import sys
import argparse

VFS_NAME = "vfs"
VFS_ROOT = ""

def handle_exit():
    print("Exiting shell...")
    sys.exit(0)

def handle_ls(args):
    print(f"ls called with arguments: {args}")

def handle_cd(args):
    print(f"cd called with arguments: {args}")

def parse_and_execute(command_line):
    # Раскрытие переменных окружения
    expanded_line = os.path.expandvars(command_line)
    
    # Разделение строки на команду и аргументы
    parts = expanded_line.split()
    if not parts:
        return
        
    command = parts[0]
    args = parts[1:]
    
    # Вызов обработчиков команд-заглушек
    if command == "exit":
        handle_exit()
    elif command == "ls":
        handle_ls(args)
    elif command == "cd":
        handle_cd(args)
    else:
        # Обработка ошибки: команда не найдена
        print(f"shell: command not found: {command}")

def execute_script(script_path):
    try:
        with open(script_path, 'r') as f:
            for line in f:
                # Пропускаем комментарии (строки, начинающиеся с #) и пустые строки
                if line.strip().startswith('#') or not line.strip():
                    continue

                # Имитируем ввод пользователя
                print(f"{VFS_NAME}> {line.strip()}")
                parse_and_execute(line.strip())
                
    except FileNotFoundError:
        print(f"shell: script not found: {script_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"shell: error executing script: {e}", file=sys.stderr)
        sys.exit(1)


def repl_loop(): # Основной цикл
    print("=== VFS started successfully ===")
    print(f"VFS path set to: {VFS_ROOT}")
    print("Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input(f"{VFS_NAME}> ")
            if not user_input.strip():
                continue
            parse_and_execute(user_input)
            
        except (EOFError, KeyboardInterrupt):
            print("\nExiting shell...")
            sys.exit(0)


def main():
    global VFS_ROOT # Основная точка входа в приложение
    
    parser = argparse.ArgumentParser(description="VFS Shell Emulator")
    parser.add_argument(
        '-v', '--vfs-path',
        type=str,
        default=os.path.join(os.getcwd(), 'vfs'),
        help="Path to the physical location of the VFS."
    )
    parser.add_argument(
        '-s', '--script',
        type=str,
        help="Path to the startup script to execute."
    )
    
    args = parser.parse_args()
    
    # Отладочный вывод заданных параметров
    print("--- Debug Information ---")
    print(f"VFS Path: {args.vfs_path}")
    print(f"Script Path: {args.script}")
    print("-------------------------")
    
    VFS_ROOT = args.vfs_path
    
    if args.script:
        execute_script(args.script)
    else:
        repl_loop()

if __name__ == "__main__":
    main()