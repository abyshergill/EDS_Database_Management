import logging
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io
from io import BytesIO
import os
import threading
from datetime import datetime

from settings.configmanager import ConfigManager 
from subwindows.loginwindow import LoginWindow
from db.databasehandler import DatabaseHandler

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, root, icon_path):
        self.root = root
        self.root.iconbitmap(icon_path)
        self.config_manager = ConfigManager()
        self.current_user = None
        self.setup_ui()  
        self.db_handler = DatabaseHandler(self.config_manager)
        self.show_login()
        
    def setup_ui(self):
        self.root.title("🔬 EDS Data Collection System")
        window_size = self.config_manager.get("ui.window_size", "900x750")
        self.root.geometry(window_size)
        self.root.resizable(True, True)
        self.root.configure(bg="#ecf0f1")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure("Treeview", background="#ffffff", foreground="#2c3e50", 
                           rowheight=25, fieldbackground="#ffffff")
        self.style.configure("Treeview.Heading", background="#3498db", foreground="white", 
                           font=("Segoe UI", 10, "bold"))
        
    def show_login(self):
        #self.root.withdraw()   #==> Issue 0 Hide main window As of now it is not working future i will fix this
        LoginWindow(self.root, self.db_handler, self.on_login_success)

    def on_login_success(self, username):
        self.current_user = username
        #self.root.deiconify()  #==> Issue 0 Show main window As of now it is not working future i will fix this
        self.create_widgets()
        self.update_user_info()
    
    def update_user_info(self):
        if hasattr(self, 'user_label'):
            self.user_label.config(text=f"👤 Logged in as: {self.current_user}")
    
    def create_widgets(self):
        main_container = tk.Frame(self.root, bg="#ecf0f1")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = tk.Frame(main_container, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🔬 EDS Data Collection System", 
                             font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="#ecf0f1")
        title_label.pack(side="left", padx=20, pady=20)
        
        self.user_label = tk.Label(header_frame, text=f"👤 Logged in as: {self.current_user}", 
                                  font=("Segoe UI", 10), bg="#2c3e50", fg="#ecf0f1")
        self.user_label.pack(side="right", padx=20, pady=20)
        
        button_frame = tk.Frame(main_container, bg="#ecf0f1")
        button_frame.pack(fill="x", pady=(0, 10))
        
        buttons = [
            ("➕ Add Data", self.add_data, "#27ae60"),
            ("🗑️ Delete Data", self.delete_data, "#e74c3c"),
            ("✏️ Update Data", self.update_data, "#f39c12"),
            ("📋 Query All", self.query_all, "#3498db")
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=command, 
                           width=18, height=2, bg=color, fg="white", 
                           font=("Segoe UI", 10, "bold"), relief="flat", 
                           cursor="hand2", bd=0)
            btn.grid(row=0, column=i, padx=5, pady=5)
        
        search_frame = tk.LabelFrame(main_container, text="🔍 Search Options", 
                                   font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                   fg="#2c3e50", relief="groove", bd=2)
        search_frame.pack(fill="x", pady=(0, 10))
        
        search_inner = tk.Frame(search_frame, bg="#ecf0f1")
        search_inner.pack(fill="x", padx=10, pady=10)
        
        tk.Label(search_inner, text="Search by Component:", 
                font=("Segoe UI", 10), bg="#ecf0f1", fg="#2c3e50").pack(side="left", padx=(0, 10))
        
        self.search_textbox = tk.Entry(search_inner, font=("Segoe UI", 11), 
                                     width=30, relief="groove", bd=2)
        self.search_textbox.pack(side="left", padx=(0, 10))
        
        search_btn = tk.Button(search_inner, text="🔍 Search", command=self.submit_search,
                             bg="#9b59b6", fg="white", font=("Segoe UI", 10, "bold"),
                             relief="flat", cursor="hand2", padx=20, bd=0)
        search_btn.pack(side="left", padx=5)
        
        clear_btn = tk.Button(search_inner, text="🔄 Clear", command=self.clear_search,
                            bg="#95a5a6", fg="white", font=("Segoe UI", 10, "bold"),
                            relief="flat", cursor="hand2", padx=20, bd=0)
        clear_btn.pack(side="left", padx=5)
        
        table_frame = tk.LabelFrame(main_container, text="📊 Data Records", 
                                  font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                  fg="#2c3e50", relief="groove", bd=2)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        tree_container = tk.Frame(table_frame, bg="#ffffff")
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Rowid", "Component", "VHX Remark", "EDS Remark", "Remark", "Created By", "Date")
        self.treeview = ttk.Treeview(tree_container, columns=columns, show="headings", height=20)
        
        column_configs = [
            ("Rowid", 80, "center"),
            ("Component", 150, "center"),
            ("VHX Remark", 120, "center"),
            ("EDS Remark", 120, "center"),
            ("Remark", 200, "center"),
            ("Created By", 100, "center"),
            ("Date", 120, "center")
        ]
        
        for col, width, anchor in column_configs:
            self.treeview.heading(col, text=col, anchor="center")
            self.treeview.column(col, anchor=anchor, width=width, minwidth=50)
        
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.treeview.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.treeview.xview)
        self.treeview.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.treeview.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        self.treeview.bind("<Double-1>", self.on_double_click)
        
        footer_frame = tk.Frame(main_container, bg="#34495e", height=40)
        footer_frame.pack(fill="x")
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(footer_frame, 
                               text="💻 Enhanced EDS Data Collection System | Developed by Aby | github.com/abyshergill", 
                               font=("Segoe UI", 9), bg="#34495e", fg="#ecf0f1")
        footer_label.pack(expand=True)
        
        self.populate_treeview()

    def add_data(self):
        self.add_popup = tk.Toplevel(self.root)
        self.add_popup.title("➕ Add New Data Entry")
        self.add_popup.configure(bg="#ecf0f1")
        self.add_popup.geometry("650x650")
        self.add_popup.grab_set()
        self.add_popup.resizable(False, False)
        
        main_frame = tk.Frame(self.add_popup, bg="#ecf0f1")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = tk.Label(main_frame, text="📝 Add New Entry", 
                             font=("Segoe UI", 16, "bold"), bg="#ecf0f1", fg="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        form_frame = tk.LabelFrame(main_frame, text="Entry Details", 
                                 font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                 fg="#2c3e50", relief="groove", bd=2)
        form_frame.pack(fill="x", pady=(0, 20))
        
        form_inner = tk.Frame(form_frame, bg="#ecf0f1")
        form_inner.pack(fill="x", padx=15, pady=15)

        tk.Label(form_inner, text="Component Name:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(form_inner, font=("Segoe UI", 11), width=35, 
                                  relief="groove", bd=2)
        self.name_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        tk.Label(form_inner, text="VHX Image:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=1, column=0, sticky="w", pady=5)
        vhx_frame = tk.Frame(form_inner, bg="#ecf0f1")
        vhx_frame.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        self.vhx_button = tk.Button(vhx_frame, text="📷 Choose VHX Image", 
                                   command=self.choose_vhx, bg="#3498db", fg="white", 
                                   font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2")
        self.vhx_button.pack(side="left")
        
        tk.Label(form_inner, text="EDS Image:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=2, column=0, sticky="w", pady=5)
        eds_frame = tk.Frame(form_inner, bg="#ecf0f1")
        eds_frame.grid(row=2, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        self.eds_button = tk.Button(eds_frame, text="📊 Choose EDS Image", 
                                   command=self.choose_eds, bg="#e67e22", fg="white", 
                                   font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2")
        self.eds_button.pack(side="left")
        
        tk.Label(form_inner, text="Remark:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=3, column=0, sticky="nw", pady=5)
        self.remark_text = tk.Text(form_inner, font=("Segoe UI", 10), width=35, height=4, 
                                  relief="groove", bd=2, wrap="word")
        self.remark_text.grid(row=3, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        form_inner.columnconfigure(1, weight=1)
        
        preview_frame = tk.LabelFrame(main_frame, text="Image Preview", 
                                    font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                    fg="#2c3e50", relief="groove", bd=2)
        preview_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        preview_inner = tk.Frame(preview_frame, bg="#ecf0f1")
        preview_inner.pack(fill="both", expand=True, padx=10, pady=10)

        self.preview1_label = tk.Label(preview_inner, text="VHX Image Preview", 
                                      bg="#bdc3c7")
        self.preview1_label.pack(side="left", padx=(0, 10))
        
        self.preview2_label = tk.Label(preview_inner, text="EDS Image Preview", 
                                      bg="#bdc3c7")
        self.preview2_label.pack(side="right")
        
        button_frame = tk.Frame(main_frame, bg="#ecf0f1")
        button_frame.pack(fill="x")
        
        save_btn = tk.Button(button_frame, text="💾 Save Entry", command=self.save_entry,
                           bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"),
                           relief="flat", cursor="hand2", padx=30, pady=10)
        save_btn.pack(side="right", padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                             command=self.add_popup.destroy,
                             bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
                             relief="flat", cursor="hand2", padx=30, pady=10)
        cancel_btn.pack(side="right")

    def choose_vhx(self):
        file_path = filedialog.askopenfilename(title="Select VHX Picture", 
                                             filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            self.picture1_path = file_path 
            try:
                with open(self.picture1_path, 'rb') as file:
                    image = Image.open(file)  
                    image = image.resize((250, 200)) 
                    self.picture1_preview = ImageTk.PhotoImage(image)
                    self.preview1_label.config(image=self.picture1_preview, text="")
                    self.preview1_label.image = self.picture1_preview
                    self.vhx_button.config(text="✅ VHX Image Selected", bg="#27ae60")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")


    def choose_eds(self):
        file_path = filedialog.askopenfilename(title="Select EDS Picture", 
                                             filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            self.picture2_path = file_path
            try:
                with open(self.picture2_path, 'rb') as file:
                    image = Image.open(file)  
                    image = image.resize((250, 200)) 

                    self.picture2_preview = ImageTk.PhotoImage(image)
                    self.preview2_label.config(image=self.picture2_preview, text="")
                    self.preview2_label.image = self.picture2_preview
                    self.eds_button.config(text="✅ EDS Image Selected", bg="#27ae60")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                
    def save_entry(self):
        logger.info("Save Button clicked")
        name = self.name_entry.get()
        remark = self.remark_text.get("1.0", tk.END).strip()

        if not all([name, remark, hasattr(self, 'picture1_path'), hasattr(self, 'picture2_path')]):
            messagebox.showerror("Error", "Please fill all fields and select both images.")
            return
            
        threading.Thread(target=self.save_entry_to_db, args=(name, remark)).start()

    def save_entry_to_db(self, name, remark):
        logger.info("Started saving to DB...")
        try:
            picture1_filename = os.path.basename(self.picture1_path)
            picture2_filename = os.path.basename(self.picture2_path)

            with open(self.picture1_path, "rb") as f1, open(self.picture2_path, "rb") as f2:
                picture1_data = f1.read()
                picture2_data = f2.read()

            self.db_handler.add_entry(name, picture1_filename, picture1_data, 
                                    picture2_filename, picture2_data, remark, self.current_user)
            
            self.root.after(0, lambda: [
                self.add_popup.destroy(),
                self.query_all(),
                messagebox.showinfo("Success", "Entry saved successfully!")
            ])
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Database Error", str(e)))

    def populate_treeview(self):
        try:
            rows = self.db_handler.get_all_entries()
            self.treeview.delete(*self.treeview.get_children())
            for row in rows:
                #==>  For My refference Format: rowid, component, vhx_remark, eds_remark, remark, created_by, created_date
                display_row = (row[0], row[1], row[2], row[4], row[6], row[7], 
                             row[8].split()[0] if row[8] else "N/A")  # Show only date part
                self.treeview.insert("", "end", values=display_row)
        except Exception as e:
            logger.error(f"Error populating treeview: {e}")
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def delete_data(self):
        selected_item = self.treeview.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an entry to delete.")
            return

        rowid = self.treeview.item(selected_item, "values")[0]
        component = self.treeview.item(selected_item, "values")[1]
        
        confirm = messagebox.askyesno("Confirm Deletion", 
                                    f"Are you sure you want to delete the entry:\n\n"
                                    f"Component: {component}\nRow ID: {rowid}?")
        if confirm:
            try:
                self.db_handler.delete_entry(rowid)
                self.query_all()
                messagebox.showinfo("Success", f"Entry '{component}' has been deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete entry: {str(e)}")

    def update_data(self):
        selected_item = self.treeview.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a row to update.")
            return
        
        item_data = self.treeview.item(selected_item, "values")
        rowid = item_data[0]
        
        full_data = self.db_handler.get_entry_by_id(rowid)
        if full_data:
            self.update_popup(full_data)
        else:
            messagebox.showerror("Error", "Could not retrieve entry data.")

    def update_popup(self, entry_data):
        rowid, component, vhx_remark, vhx_data, eds_remark, eds_data, remark, created_by, created_date = entry_data
        
        update_popup = tk.Toplevel(self.root)
        update_popup.title("✏️ Update Entry")
        update_popup.configure(bg="#ecf0f1")
        update_popup.geometry("600x650")
        update_popup.grab_set()
        update_popup.resizable(False, False)

        main_frame = tk.Frame(update_popup, bg="#ecf0f1")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = tk.Label(main_frame, text=f"📝 Update Entry (ID: {rowid})", 
                             font=("Segoe UI", 16, "bold"), bg="#ecf0f1", fg="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        form_frame = tk.LabelFrame(main_frame, text="Entry Details", 
                                 font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                 fg="#2c3e50", relief="groove", bd=2)
        form_frame.pack(fill="x", pady=(0, 20))
        
        form_inner = tk.Frame(form_frame, bg="#ecf0f1")
        form_inner.pack(fill="x", padx=15, pady=15)
        
        tk.Label(form_inner, text="Component Name:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, sticky="w", pady=5)
        name_entry = tk.Entry(form_inner, font=("Segoe UI", 11), width=35, 
                             relief="groove", bd=2)
        name_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")
        name_entry.insert(0, component)
        
        tk.Label(form_inner, text="VHX Image:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=1, column=0, sticky="w", pady=5)
        vhx_frame = tk.Frame(form_inner, bg="#ecf0f1")
        vhx_frame.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        self.update_vhx_data = vhx_data
        self.update_vhx_filename = vhx_remark
        
        def choose_vhx_update():
            file_path = filedialog.askopenfilename(title="Select New VHX Picture", 
                                                 filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
            if file_path:
                try:
                    with open(file_path, 'rb') as f:
                        self.update_vhx_data = f.read()
                    self.update_vhx_filename = os.path.basename(file_path)
                    
                    image = Image.open(file_path)
                    image = image.resize((150, 150))
                    photo = ImageTk.PhotoImage(image)
                    vhx_preview.config(image=photo, text="")
                    vhx_preview.image = photo
                    vhx_button.config(text="✅ New VHX Selected", bg="#27ae60")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load image: {str(e)}")
        
        vhx_button = tk.Button(vhx_frame, text="📷 Change VHX Image", 
                              command=choose_vhx_update, bg="#3498db", fg="white", 
                              font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2")
        vhx_button.pack(side="left")
        
        tk.Label(form_inner, text="EDS Image:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=2, column=0, sticky="w", pady=5)
        eds_frame = tk.Frame(form_inner, bg="#ecf0f1")
        eds_frame.grid(row=2, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        self.update_eds_data = eds_data
        self.update_eds_filename = eds_remark
        
        def choose_eds_update():
            file_path = filedialog.askopenfilename(title="Select New EDS Picture", 
                                                 filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
            if file_path:
                try:
                    with open(file_path, 'rb') as f:
                        self.update_eds_data = f.read()
                    self.update_eds_filename = os.path.basename(file_path)
                    
                    image = Image.open(file_path)
                    image = image.resize((150, 150))
                    photo = ImageTk.PhotoImage(image)
                    eds_preview.config(image=photo, text="")
                    eds_preview.image = photo
                    eds_button.config(text="✅ New EDS Selected", bg="#27ae60")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load image: {str(e)}")
        
        eds_button = tk.Button(eds_frame, text="📊 Change EDS Image", 
                              command=choose_eds_update, bg="#e67e22", fg="white", 
                              font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2")
        eds_button.pack(side="left")
        
        tk.Label(form_inner, text="Remark:", font=("Segoe UI", 10, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").grid(row=3, column=0, sticky="nw", pady=5)
        remark_text = tk.Text(form_inner, font=("Segoe UI", 10), width=35, height=4, 
                             relief="groove", bd=2, wrap="word")
        remark_text.grid(row=3, column=1, padx=(10, 0), pady=5, sticky="ew")
        remark_text.insert("1.0", remark)
        
        form_inner.columnconfigure(1, weight=1)
        
        preview_frame = tk.LabelFrame(main_frame, text="Current Images", 
                                    font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                    fg="#2c3e50", relief="groove", bd=2)
        preview_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        preview_inner = tk.Frame(preview_frame, bg="#ecf0f1")
        preview_inner.pack(fill="both", expand=True, padx=10, pady=10)
        
        vhx_preview = tk.Label(preview_inner, bg="#bdc3c7", width=250, height=200)
        vhx_preview.pack(side="left", padx=(0, 10))
        
        eds_preview = tk.Label(preview_inner, bg="#bdc3c7", width=250, height=200)
        eds_preview.pack(side="right")
        
        try:
            if vhx_data:
                vhx_image = Image.open(BytesIO(vhx_data))
                vhx_image = vhx_image.resize((300, 300))
                vhx_photo = ImageTk.PhotoImage(vhx_image)
                vhx_preview.config(image=vhx_photo, text="")
                vhx_preview.image = vhx_photo
            
            if eds_data:
                eds_image = Image.open(BytesIO(eds_data))
                eds_image = eds_image.resize((150, 150))
                eds_photo = ImageTk.PhotoImage(eds_image)
                eds_preview.config(image=eds_photo, text="")
                eds_preview.image = eds_photo
        except Exception as e:
            logger.error(f"Error loading preview images: {e}")
        
        def save_update():
            new_name = name_entry.get()
            new_remark = remark_text.get("1.0", tk.END).strip()
            
            if not new_name or not new_remark:
                messagebox.showerror("Error", "Please fill in all fields.")
                return
            
            try:
                self.db_handler.update_entry(rowid, new_name, self.update_vhx_filename, 
                                           self.update_vhx_data, self.update_eds_filename, 
                                           self.update_eds_data, new_remark)
                messagebox.showinfo("Success", "Entry updated successfully!")
                update_popup.destroy()
                self.query_all()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update entry: {str(e)}")

        button_frame = tk.Frame(main_frame, bg="#ecf0f1")
        button_frame.pack(fill="x")
        
        save_btn = tk.Button(button_frame, text="💾 Save Changes", command=save_update,
                           bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"),
                           relief="flat", cursor="hand2", padx=30, pady=10)
        save_btn.pack(side="right", padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                             command=update_popup.destroy,
                             bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
                             relief="flat", cursor="hand2", padx=30, pady=10)
        cancel_btn.pack(side="right")

    def query_all(self):
        self.populate_treeview()

    def submit_search(self):
        component_name = self.search_textbox.get().strip()
        if not component_name:
            messagebox.showwarning("Warning", "Please enter a component name to search.")
            return

        try:
            rows = self.db_handler.search_by_component(component_name)
            if rows:
                self.update_treeview(rows)
            else:
                messagebox.showinfo("No Results", f"No entries found for component '{component_name}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def clear_search(self):
        self.search_textbox.delete(0, tk.END)
        self.query_all()
            
    def update_treeview(self, rows):
        self.treeview.delete(*self.treeview.get_children())
        for row in rows:
            display_row = (row[0], row[1], row[2], row[3], row[4], row[5] if len(row) > 5 else "N/A", 
                          row[6].split()[0] if len(row) > 6 and row[6] else "N/A")
            self.treeview.insert("", "end", values=display_row)

    def on_double_click(self, event):
        selected_item = self.treeview.selection()
        if selected_item:
            row_id = self.treeview.item(selected_item[0])["values"][0]
            self.open_images_window(row_id)

    def open_images_window(self, row_id):
        try:
            vhx_data, eds_data = self.db_handler.get_images_by_rowid(row_id)

            if not vhx_data or not eds_data:
                messagebox.showerror("Error", "No images found for this entry.")
                return

            image_window = tk.Toplevel(self.root)
            image_window.title(f"📷 Image Preview - Entry ID: {row_id}")
            image_window.geometry("700x500")
            image_window.grab_set()
            image_window.resizable(False, False)
            image_window.configure(bg="#ecf0f1")

            main_frame = tk.Frame(image_window, bg="#ecf0f1")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            title_label = tk.Label(main_frame, text=f"📷 Image Preview - Entry ID: {row_id}", 
                                 font=("Segoe UI", 14, "bold"), bg="#ecf0f1", fg="#2c3e50")
            title_label.pack(pady=(0, 20))

            images_frame = tk.Frame(main_frame, bg="#ecf0f1")
            images_frame.pack(expand=True, fill="both", pady=(0, 20))

            vhx_frame = tk.LabelFrame(images_frame, text="VHX Image", 
                                    font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                    fg="#2c3e50", relief="groove", bd=2)
            vhx_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

            vhx_image = Image.open(BytesIO(vhx_data))
            vhx_image = vhx_image.resize((300, 300))
            vhx_image_tk = ImageTk.PhotoImage(vhx_image)
            vhx_label = tk.Label(vhx_frame, image=vhx_image_tk, bg="#ffffff")
            vhx_label.image = vhx_image_tk
            vhx_label.pack(padx=10, pady=10)

            eds_frame = tk.LabelFrame(images_frame, text="EDS Image", 
                                    font=("Segoe UI", 10, "bold"), bg="#ecf0f1", 
                                    fg="#2c3e50", relief="groove", bd=2)
            eds_frame.pack(side="left", fill="both", expand=True)

            eds_image = Image.open(BytesIO(eds_data))
            eds_image = eds_image.resize((300, 300))
            eds_image_tk = ImageTk.PhotoImage(eds_image)
            eds_label = tk.Label(eds_frame, image=eds_image_tk, bg="#ffffff")
            eds_label.image = eds_image_tk
            eds_label.pack(padx=10, pady=10)

            button_frame = tk.Frame(main_frame, bg="#ecf0f1")
            button_frame.pack(fill="x")

            vhx_btn = tk.Button(button_frame, text="💾 Download VHX", 
                               command=lambda: self.download_image(vhx_data, f"VHX_Entry_{row_id}.jpg"),
                               bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
                               relief="flat", cursor="hand2", padx=20, pady=8)
            vhx_btn.pack(side="left", padx=(0, 10))

            eds_btn = tk.Button(button_frame, text="💾 Download EDS", 
                               command=lambda: self.download_image(eds_data, f"EDS_Entry_{row_id}.jpg"),
                               bg="#e67e22", fg="white", font=("Segoe UI", 10, "bold"),
                               relief="flat", cursor="hand2", padx=20, pady=8)
            eds_btn.pack(side="left", padx=(0, 10))

            close_btn = tk.Button(button_frame, text="✖️ Close", 
                                command=image_window.destroy,
                                bg="#95a5a6", fg="white", font=("Segoe UI", 10, "bold"),
                                relief="flat", cursor="hand2", padx=20, pady=8)
            close_btn.pack(side="right")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open images: {str(e)}")

    def download_image(self, image_data, default_filename):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All Files", "*.*")],
                initialfile=default_filename
            )
            
            if file_path:
                with open(file_path, "wb") as file:
                    file.write(image_data)
                messagebox.showinfo("Success", "Image downloaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download image: {str(e)}")

