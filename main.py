import logging
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from subwindows.mainwindow import MainWindow
from settings.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        root = tk.Tk()
        icon_path = os.path.join(os.path.dirname(__file__), "icon", "logo.ico")
        if os.path.exists(icon_path):
             app = MainWindow(root, icon_path)
        else:
             logger.warning(f"Icon file not found at {icon_path}. Skipping icon setting.")
        root.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Application Error", f"Failed to start application: {str(e)}")