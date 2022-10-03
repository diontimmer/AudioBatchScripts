pyinstaller --noconfirm --onefile --windowed --icon "%~dp0data/dtico.ico" --add-data "%~dp0data;data" --clean --distpath "%~dp0/binaries"  "%~dp0ABS.py"
