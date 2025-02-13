#!/bin/bash

# Проверка наличия PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller is not installed. Installing..."
    pip install pyinstaller
fi

# Создание папки build_exe_files, если её нет
if [ ! -d "build_exe_files" ]; then
    mkdir build_exe_files
fi

# Компиляция программы
echo "Compiling the program..."
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --icon=favicon.ico \
            --add-data "api-ms-win-core-path-l1-1-0.dll:." \
            --distpath build_exe_files \
            --name=ssh-wallet \
            index.py

# Проверка успешности компиляции
if [ $? -eq 0 ]; then
    echo "Compilation completed successfully!"
    echo "The executable file is located in the folder build_exe_files/ssh-wallet"
else
    echo "An error occurred during compilation."
fi