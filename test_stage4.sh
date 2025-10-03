# 1. Тестирование wc (word count)
# Переходим в директорию с файлами
cd /home/user

# wc 1.1: Режим по умолчанию (все: -l -w -c)
ls docs/notes.txt
wc docs/notes.txt

# wc 1.2: Только строки (-l)
wc -l docs/notes.txt

# wc 1.3: Только слова (-w)
wc -w docs/notes.txt

# wc 1.4: Только байты (-c) - Тест base64-файла для проверки байтов
wc -c profile.bin

# wc 1.5: Комбинированные флаги (-lw)
wc -lw report.log

# wc 1.6: Обработка ошибки: wc на директории
wc docs

# wc 1.7: Обработка ошибки: wc несуществующего файла
wc non_existent_file.txt

# wc 1.8: Обработка ошибки: неверный флаг
wc -z docs/notes.txt

# 2. Тестирование cal (calendar)
cal
cal 12 2025
cal 2026
cal 15 2025

# 3. Тестирование who
who

# 4. Проверка старых команд
ls
cd docs
ls .
cd ../..