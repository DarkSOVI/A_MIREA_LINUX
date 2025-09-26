#!/bin/bash

echo "--- Running VFS Shell Emulator ---"
python Program.py -v vfs_test.xml -s test_stage3.sh

# Запуск интерактивного режима для дополнительного тестирования
echo -e "\n--- Running Interactive Mode (Ctrl+C to quit) ---"
python Program.py -v vfs_test.xml