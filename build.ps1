# Builds the standalone Windows executable for the GUI app.
# Requires PyInstaller:  py -m pip install --user pyinstaller
py -m PyInstaller --onefile --windowed --name "Datei-Verschieber" `
    --distpath dist --workpath build --specpath build file_mover_gui.py
