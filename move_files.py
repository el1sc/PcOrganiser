#!/usr/bin/env python3
"""
move_files.py - Moves (or copies) all files of a given file format from a
source folder into a destination folder.

Examples:
    # Move all .pdf files from Downloads into Documents
    python move_files.py -s ~/Downloads -d ~/Documents -e pdf

    # Multiple formats, including subfolders, just preview (no real move)
    python move_files.py -s ./source -d ./dest -e jpg png gif --recursive --dry-run

    # Copy instead of move
    python move_files.py -s ./source -d ./dest -e txt --copy
"""

import argparse
import shutil
import sys
from pathlib import Path


def normalize_extensions(exts):
    """Ensures a uniform format: '.pdf' (lowercase, with dot)."""
    normalized = set()
    for e in exts:
        e = e.strip().lower()
        if not e:
            continue
        if not e.startswith("."):
            e = "." + e
        normalized.add(e)
    return normalized


def unique_destination(dest_dir: Path, name: str) -> Path:
    """Finds a free filename if the target already exists.
    'image.jpg' becomes 'image (1).jpg', 'image (2).jpg', ... on conflict.
    """
    target = dest_dir / name
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def main():
    parser = argparse.ArgumentParser(
        description="Moves or copies all files of a given format from a source "
                    "into a destination folder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-s", "--source", required=True,
                        help="Source folder")
    parser.add_argument("-d", "--destination", required=True,
                        help="Destination folder (created if needed)")
    parser.add_argument("-e", "--ext", "--extensions", nargs="+", required=True,
                        dest="extensions",
                        help="One or more file extensions, e.g. pdf jpg png")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Also search subfolders")
    parser.add_argument("--copy", action="store_true",
                        help="Copy instead of move")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only show what would happen (change nothing)")

    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    dest = Path(args.destination).expanduser().resolve()
    extensions = normalize_extensions(args.extensions)

    if not source.is_dir():
        print(f"Error: source folder does not exist: {source}", file=sys.stderr)
        sys.exit(1)

    if not extensions:
        print("Error: no valid file extension given.", file=sys.stderr)
        sys.exit(1)

    # Collect files
    pattern = "**/*" if args.recursive else "*"
    files = [
        p for p in source.glob(pattern)
        if p.is_file() and p.suffix.lower() in extensions
    ]

    if not files:
        print(f"No files with extension {', '.join(sorted(extensions))} "
              f"found in {source}.")
        return

    action = "Copying" if args.copy else "Moving"
    print(f"{action}: {len(files)} file(s) -> {dest}")
    if args.dry_run:
        print("[DRY-RUN] No changes will be made.\n")

    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    done = 0
    errors = 0
    for f in files:
        target = unique_destination(dest, f.name) if not args.dry_run else dest / f.name
        try:
            if args.dry_run:
                print(f"  {f}  ->  {target}")
            else:
                if args.copy:
                    shutil.copy2(str(f), str(target))
                else:
                    shutil.move(str(f), str(target))
                print(f"  OK: {f.name}  ->  {target}")
            done += 1
        except Exception as ex:
            errors += 1
            print(f"  ERROR on {f.name}: {ex}", file=sys.stderr)

    print(f"\nDone. {done} processed, {errors} error(s).")


if __name__ == "__main__":
    main()
