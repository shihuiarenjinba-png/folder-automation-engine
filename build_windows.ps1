$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'build dependency installation failed.' }

python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'unit/UI language tests failed.' }

python -m PyInstaller --clean --noconfirm --onefile --windowed --name FolderAutomationEngine desktop_app.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

Write-Host 'Built FolderAutomationEngine.exe after unit/UI language tests passed.'
Write-Host 'Before sale: complete SALES_RELEASE_CHECKLIST.md and real Windows smoke tests.'
