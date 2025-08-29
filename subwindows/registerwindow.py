import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

class RegisterWindow:  
    def __init__(self, parent, db_handler):
        self.parent = parent
        self.db_handler = db_handler
        self.create_register_window()
    
    def create_register_window(self):
        self.register_window = tk.Toplevel(self.parent)
        self.register_window.title("Register New User")
        self.register_window.geometry("400x550")
        self.register_window.resizable(False, False)
        self.register_window.configure(bg="#2c3e50")
        self.register_window.grab_set()

        main_frame = tk.Frame(self.register_window, bg="#34495e", relief="flat", bd=2)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = tk.Label(main_frame, text="👤 Create New Account", 
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
        self.password_entry.pack(fill="x", pady=(0, 15))
        
        tk.Label(form_frame, text="Confirm Password:", font=("Segoe UI", 10), 
                bg="#34495e", fg="#ecf0f1").pack(anchor="w", pady=(0, 5))
        self.confirm_password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", 11), 
                                             relief="flat", bd=5, bg="#ecf0f1")
        self.confirm_password_entry.pack(fill="x", pady=(0, 20))
        
        btn_frame = tk.Frame(form_frame, bg="#34495e")
        btn_frame.pack(fill="x")
        
        register_btn = tk.Button(btn_frame, text="✅ Create Account", command=self.register_user,
                               font=("Segoe UI", 10, "bold"), bg="#27ae60", fg="white",
                               relief="flat", bd=0, padx=20, pady=8, cursor="hand2")
        register_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = tk.Button(btn_frame, text="❌ Cancel", command=self.register_window.destroy,
                             font=("Segoe UI", 10, "bold"), bg="#e74c3c", fg="white",
                             relief="flat", bd=0, padx=20, pady=8, cursor="hand2")
        cancel_btn.pack(side="left")
    
    def register_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not all([username, password, confirm_password]):
            messagebox.showerror("Error", "Please fill all fields.")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long.")
            return
        
        try:
            self.db_handler.create_user(username, password)
            messagebox.showinfo("Success", "Account created successfully!")
            self.register_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create account: {str(e)}")