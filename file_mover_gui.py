#!/usr/bin/env python3
"""
file_mover_gui.py - Graphical interface for moving/copying all files of a
given format from one folder to another.

Packaged into a standalone .exe with PyInstaller (see build.ps1).
"""

import shutil
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def normalize_extensions(raw):
    """Turns 'pdf, .JPG png' into {'.pdf', '.jpg', '.png'}."""
    result = set()
    for part in raw.replace(",", " ").split():
        e = part.strip().lower()
        if not e:
            continue
        if not e.startswith("."):
            e = "." + e
        result.add(e)
    return result


def unique_destination(dest_dir: Path, name: str) -> Path:
    """Finds a free name on conflict: 'image.jpg' -> 'image (1).jpg' ..."""
    target = dest_dir / name
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Mover")
        self.geometry("620x460")
        self.minsize(560, 420)

        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.ext_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.copy_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        # Source
        ttk.Label(frm, text="Source folder:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.source_var).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Browse…",
                   command=lambda: self._pick_dir(self.source_var)).grid(row=0, column=2, **pad)

        # Destination
        ttk.Label(frm, text="Destination folder:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.dest_var).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Browse…",
                   command=lambda: self._pick_dir(self.dest_var)).grid(row=1, column=2, **pad)

        # Extensions
        ttk.Label(frm, text="File extensions:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.ext_var).grid(row=2, column=1, sticky="ew", **pad)
        ttk.Label(frm, text="e.g.  pdf jpg png").grid(row=2, column=2, sticky="w", **pad)

        # Options
        opts = ttk.Frame(frm)
        opts.grid(row=3, column=0, columnspan=3, sticky="w", **pad)
        ttk.Checkbutton(opts, text="Include subfolders",
                        variable=self.recursive_var).pack(side="left", padx=(0, 16))
        ttk.Checkbutton(opts, text="Copy instead of move",
                        variable=self.copy_var).pack(side="left")

        # Actions
        actions = ttk.Frame(frm)
        actions.grid(row=4, column=0, columnspan=3, sticky="w", **pad)
        self.preview_btn = ttk.Button(actions, text="Preview", command=self._preview)
        self.preview_btn.pack(side="left", padx=(0, 8))
        self.run_btn = ttk.Button(actions, text="Start", command=self._run)
        self.run_btn.pack(side="left")

        # Log output
        ttk.Label(frm, text="Log:").grid(row=5, column=0, sticky="w", padx=8)
        self.log = tk.Text(frm, height=10, wrap="none", state="disabled")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=8, pady=(0, 8))
        frm.rowconfigure(6, weight=1)

        self.status = ttk.Label(frm, text="Ready.", anchor="w")
        self.status.grid(row=7, column=0, columnspan=3, sticky="ew", padx=8)

    def _pick_dir(self, var):
        d = filedialog.askdirectory(initialdir=var.get() or None)
        if d:
            var.set(d)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _collect(self):
        """Validates input and collects matching files. Returns (files, source,
        dest, extensions) or None on error (with a message shown)."""
        source = Path(self.source_var.get().strip()).expanduser()
        dest = Path(self.dest_var.get().strip()).expanduser()
        extensions = normalize_extensions(self.ext_var.get())

        if not self.source_var.get().strip() or not source.is_dir():
            messagebox.showerror("Error", "Please choose a valid source folder.")
            return None
        if not self.dest_var.get().strip():
            messagebox.showerror("Error", "Please choose a destination folder.")
            return None
        if not extensions:
            messagebox.showerror("Error", "Please enter at least one file extension.")
            return None

        pattern = "**/*" if self.recursive_var.get() else "*"
        files = [p for p in source.glob(pattern)
                 if p.is_file() and p.suffix.lower() in extensions]
        return files, source, dest.resolve(), extensions

    def _preview(self):
        collected = self._collect()
        if not collected:
            return
        files, source, dest, extensions = collected
        self._clear_log()
        if not files:
            self._log(f"No files with {', '.join(sorted(extensions))} found in {source}.")
            self.status.config(text="0 files found.")
            return
        self._log(f"[Preview] {len(files)} file(s) -> {dest}\n")
        for f in files:
            self._log(f"  {f.name}")
        self.status.config(text=f"Preview: {len(files)} file(s). Nothing changed yet.")

    def _run(self):
        collected = self._collect()
        if not collected:
            return
        files, source, dest, extensions = collected
        if not files:
            messagebox.showinfo("No files",
                                f"No files with {', '.join(sorted(extensions))} found.")
            return

        action = "copied" if self.copy_var.get() else "moved"
        if not messagebox.askyesno("Confirm",
                                    f"{len(files)} file(s) will be {action}:\n\n"
                                    f"{source}\n  ->  {dest}\n\nContinue?"):
            return

        # Lock UI, do the work in a background thread
        self.run_btn.config(state="disabled")
        self.preview_btn.config(state="disabled")
        self._clear_log()
        threading.Thread(target=self._work, args=(files, dest), daemon=True).start()

    def _work(self, files, dest):
        copy = self.copy_var.get()
        done = errors = 0
        try:
            dest.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            self.after(0, lambda: messagebox.showerror("Error", f"Cannot create destination folder:\n{ex}"))
            self.after(0, self._unlock)
            return

        for f in files:
            try:
                target = unique_destination(dest, f.name)
                if copy:
                    shutil.copy2(str(f), str(target))
                else:
                    shutil.move(str(f), str(target))
                done += 1
                self.after(0, self._log, f"  OK: {f.name}  ->  {target.name}")
            except Exception as ex:
                errors += 1
                self.after(0, self._log, f"  ERROR on {f.name}: {ex}")

        verb = "copied" if copy else "moved"
        self.after(0, self._log, f"\nDone. {done} {verb}, {errors} error(s).")
        self.after(0, lambda: self.status.config(text=f"Done: {done} {verb}, {errors} error(s)."))
        self.after(0, self._unlock)

    def _unlock(self):
        self.run_btn.config(state="normal")
        self.preview_btn.config(state="normal")


if __name__ == "__main__":
    App().mainloop()
