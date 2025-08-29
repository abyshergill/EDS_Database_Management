import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import threading
import io
from io import BytesIO
import os
import threading
import json

from subwindows.registerwindow import RegisterWindow

class LoginWindow:
    def __init__(self, parent, db_handler, on_success):
        self.parent = parent
        self.db_handler = db_handler
        self.on_success = on_success
        self.current_user = None
        self.create_login_window()
    
    def create_login_window(self):
        self.login_window = tk.Toplevel(self.parent)
        self.login_window.title("EDS Data Collection - Login")
        self.login_window.geometry("400x400")
        self.login_window.resizable(False, False)
        self.login_window.configure(bg="#2c3e50")
        self.login_window.grab_set()
        
        # ==> This will make sure your login window will appear at center 
        screen_width = self.login_window.winfo_screenwidth()
        screen_height = self.login_window.winfo_screenheight()

        window_width = 400
        window_height = 400

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.login_window.geometry(f'{window_width}x{window_height}+{x}+{y}')

        self.login_window.transient(self.parent)
        #====================================================

        main_frame = tk.Frame(self.login_window, bg="#34495e", relief="flat", bd=2)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        title_label = tk.Label(main_frame, text="🔐 User Authentication", 
                              font=("Segoe UI", 16, "bold"), 
                              bg="#34495e", fg="#ecf0f1")
        title_label.pack(pady=(20, 30))
    
        form_frame = tk.Frame(main_frame, bg="#34495e")
        form_frame.pack(expand=True, fill="x", padx=20)
        
        tk.Label(form_frame, text="Username:", font=("Segoe UI", 10), 
                bg="#34495e", fg="#ecf0f1").pack(anchor="w", pady=(0, 5))
        self.username_entry = tk.Entry(form_frame, font=("Segoe UI", 11), 
                                      relief="flat", bd=5, bg="#ecf0f1")
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        tk.Label(form_frame, text="Password:", font=("Segoe UI", 10), 
                bg="#34495e", fg="#ecf0f1").pack(anchor="w", pady=(0, 5))
        self.password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", 11), 
                                      relief="flat", bd=5, bg="#ecf0f1")
        self.password_entry.pack(fill="x", pady=(0, 20))
        
        btn_frame = tk.Frame(form_frame, bg="#34495e")
        btn_frame.pack(fill="x")
        
        login_btn = tk.Button(btn_frame, text="🔑 Login", command=self.authenticate,
                             font=("Segoe UI", 10, "bold"), bg="#27ae60", fg="white",
                             relief="flat", bd=0, padx=20, pady=8, cursor="hand2")
        login_btn.pack(side="left", padx=(0, 10))
        
        register_btn = tk.Button(btn_frame, text="👤 Register", command=self.show_register,
                               font=("Segoe UI", 10, "bold"), bg="#3498db", fg="white",
                               relief="flat", bd=0, padx=20, pady=8, cursor="hand2")
        register_btn.pack(side="left")
        
        self.login_window.bind('<Return>', lambda event: self.authenticate())
        self.username_entry.focus()
    
    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return
        
        if self.db_handler.verify_user(username, password):
            self.current_user = username
            self.login_window.destroy()
            self.on_success(username)
        else:
            messagebox.showerror("Authentication Failed", "Invalid username or password.")
            self.password_entry.delete(0, tk.END)
    
    def show_register(self):
        RegisterWindow(self.login_window, self.db_handler)

