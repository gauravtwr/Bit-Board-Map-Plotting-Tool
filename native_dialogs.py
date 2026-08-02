"""Native OS file/folder pickers, invoked from the local Flask backend.

This web app only ever runs on localhost for the same machine that's using
the browser tab, so it's safe (and much more useful) for the backend to pop
up real Windows file/folder dialogs instead of relying on what a sandboxed
browser page can do.
"""

import tkinter as tk
from tkinter import filedialog

IMAGE_FILETYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp"),
    ("All files", "*.*"),
]


def _with_hidden_root(action):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return action(root)
    finally:
        root.destroy()


def pick_file():
    """Open a native "select image" dialog. Returns a path, or None if cancelled."""
    path = _with_hidden_root(
        lambda root: filedialog.askopenfilename(
            parent=root, title="Select an image", filetypes=IMAGE_FILETYPES
        )
    )
    return path or None


def pick_folder(title="Select a folder"):
    """Open a native "select folder" dialog. Returns a path, or None if cancelled."""
    path = _with_hidden_root(
        lambda root: filedialog.askdirectory(parent=root, title=title)
    )
    return path or None
