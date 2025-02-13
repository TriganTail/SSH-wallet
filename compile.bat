@echo off
:: Проверка наличия PyInstaller
where pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo PyInstaller is not installed. Installing...
    pip install pyinstaller
)

:: Создание папки build_exe_files, если её нет
if not exist build_exe_files (
    mkdir build_exe_files
)

:: Компиляция программы
echo Compiling the program...
pyinstaller --noconfirm ^
            --onefile ^
            --windowed ^
            --icon=favicon.ico ^
            --add-data "api-ms-win-core-path-l1-1-0.dll;." ^
            --distpath build_exe_files ^
            --name=ssh-wallet ^
            index.py

:: Проверка успешности компиляции
if %ERRORLEVEL% equ 0 (
    echo Compilation completed successfully!
    echo The executable file is located in the folder build_exe_files\ssh-wallet.exe
) else (
    echo An error occurred during compilation.
)

pause