import os
import sys

VFS_NAME = "vfs"

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

def repl_loop(): # Главная функция
    print("=== VFS started successfully ===")
    print("Type 'exit' to quit.")
    while True:
        try:
            # Чтение ввода пользователя
            user_input = input(f"{VFS_NAME}> ")
            
            # Пропуск пустых строк
            if not user_input.strip():
                continue
            
            # Выполнение команды
            parse_and_execute(user_input)
            
        except (EOFError, KeyboardInterrupt):
            # Обработка Ctrl+D или Ctrl+C для выхода
            print("\nExiting shell...")
            sys.exit(0)

if __name__ == "__main__":
    repl_loop()