# PcOrganiser

A small tool to **move** or **copy** all files of a given format from one
folder into another. Comes as both a graphical app (`.exe`) and a command-line
script. Pure Python, no third-party packages needed to run (Python 3.7+).

## Graphical app (recommended)

Run `dist/Datei-Verschieber.exe` (double-click). Pick a source folder, a
destination folder, enter one or more extensions (e.g. `pdf jpg png`), and hit
**Preview** or **Start**.

Source: [file_mover_gui.py](file_mover_gui.py)

## Command-line tool

```bash
python move_files.py -s <SOURCE> -d <DEST> -e <EXT...> [options]
```

### Options

| Option                | Description                                          |
|-----------------------|------------------------------------------------------|
| `-s`, `--source`      | Source folder (required)                             |
| `-d`, `--destination` | Destination folder, created if needed (required)     |
| `-e`, `--ext`         | One or more extensions, e.g. `pdf jpg png` (required)|
| `-r`, `--recursive`   | Also search subfolders                               |
| `--copy`              | Copy instead of move                                 |
| `--dry-run`           | Only show what would happen (change nothing)         |

### Examples

```bash
# Move all PDFs from Downloads into Documents
python move_files.py -s ~/Downloads -d ~/Documents -e pdf

# Multiple formats, including subfolders, preview only
python move_files.py -s ./source -d ./dest -e jpg png gif --recursive --dry-run

# Copy instead of move
python move_files.py -s ./source -d ./dest -e txt --copy
```

## Building the .exe

Requires [PyInstaller](https://pyinstaller.org):

```powershell
py -m pip install --user pyinstaller
./build.ps1
```

The resulting executable lands in `dist/`.

## Notes

- If a file of the same name already exists in the destination, it is renamed
  automatically: `image.jpg` → `image (1).jpg`, `image (2).jpg`, …
- Extensions are case-insensitive (`PDF` = `pdf`) and work with or without a
  leading dot (`pdf` = `.pdf`).
- Use `--dry-run` (CLI) or **Preview** (GUI) to safely check which files would
  be affected before making changes.
