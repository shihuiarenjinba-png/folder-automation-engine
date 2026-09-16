$ErrorActionPreference = 'Stop'
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
python -m PyInstaller --clean --noconfirm --onefile --windowed --name FolderAutomationEngine desktop_app.py
