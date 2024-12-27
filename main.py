import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import sqlite3
import io
from io import BytesIO
import os
import logging
import threading


class MainProject:
    def __init__(self, root):
        self.root = root
        self.root.title("EDS data Collection")
        self.root.geometry("778x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#e5e5dc")
        self.create_widget()
        
        #Connect to the database part
        self.db_handler = SQLiteHandler("eds.db")

    def create_widget(self):
        #### First row with four button Finish
        self.add_button = tk.Button(self.root, text="Add Data", command=self.add_data, width=20, height=2, bg="#d9138a", fg="white", font=("Helvetica", 10, "bold"))
        self.add_button.grid(row=0, column=0, padx=10, pady=10)

        self.delete_button = tk.Button(self.root, text="Delete Data", command=self.delete_data, width=20, height=2, bg="#f4081e", fg="white", font=("Helvetica", 10, "bold"))
        self.delete_button.grid(row=0, column=1, padx=10, pady=10)

        self.update_button = tk.Button(self.root, text="Update Data", command=self.update_data, width=20, height=2, bg="#6b7b8c", fg="white", font=("Helvetica", 10, "bold"))
        self.update_button.grid(row=0, column=2, padx=10, pady=10)

        self.query_button = tk.Button(self.root, text="Query All", command=self.query_all, width=20, height=2, bg="#322e2f", fg="white", font=("Helvetica", 10, "bold"))
        self.query_button.grid(row=0, column=3, padx=10, pady=10)
        
        ####Second row with search option
        self.label_searchby = tk.Label(self.root, text="Search by Component :", font=("Arial", 12), bg="#e5e5dc")
        self.label_searchby.grid(row=1, column=0, padx=10, pady=10)

        self.search_textbox = tk.Entry(self.root, font=("Arial", 12), width=20 )
        self.search_textbox.grid(row=1, column=1, padx=10, pady=10)

        self.submit_button = tk.Button(self.root, text="Submit", command=self.submit_search, width=20, height=2, bg="#8BC34A", fg="white", font=("Helvetica", 10, "bold"))
        self.submit_button.grid(row=1, column=2, padx=10, pady=10)
        
        ####Third row with table
        self.treeview = ttk.Treeview(self.root, columns=("Rowid", "Component", "VHX Remark", "EDS Remark", "Remark"), show="headings", height=24)
        self.treeview.heading("Rowid", text="Row ID", anchor="center")
        self.treeview.heading("Component", text="Component", anchor="center")
        self.treeview.heading("VHX Remark", text="VHX Remark", anchor="center")
        self.treeview.heading("EDS Remark", text="EDS Remark", anchor="center")
        self.treeview.heading("Remark", text="Remark", anchor="center")
        
        # Set the column data to be centered as well
        self.treeview.column("Rowid", anchor="center", width=100)  # Example width
        self.treeview.column("Component", anchor="center", width=150)
        self.treeview.column("VHX Remark", anchor="center", width=150)
        self.treeview.column("EDS Remark", anchor="center", width=150)
        self.treeview.column("Remark", anchor="center", width=200)
                
        
        self.treeview.grid(row=2, column=0, columnspan=4, padx=10, pady=10)
        self.populate_treeview()
        # Bind double-click event to the treeview for opening images
        self.treeview.bind("<Double-1>", self.on_double_click)

        #### Fourth row for author information
        self.footer_label = tk.Label(self.root, text="This Program is Written by Aby | github.com/abyshergill", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        self.footer_label.grid(row=3, column=0, columnspan=4, padx=10, pady=10)      
        
####Logic 
########### First Row Logic    
    def add_data(self):
        #self.root.attributes("-disabled", True)
        self.add_popup = tk.Toplevel(self.root)
        self.add_popup.title("Add New Data")
        self.add_popup.configure(bg="#e5e5dc")
        self.add_popup.geometry("475x500")
        self.add_popup.grab_set()
        self.add_popup.resizable(False, False)

        # Get inputs for remark, Text1, and Text2
        self.name_label = tk.Label(self.add_popup, text="Component Name : ", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        self.name_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = tk.Entry(self.add_popup, font=("Helvetica", 12), width=25)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        self.vhx_label = tk.Label(self.add_popup, text="Add VHX Picture Record :", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        self.vhx_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.vhx_button = tk.Button(self.add_popup, text="Choose VHX Image", command=self.choose_vhx, width=20, height=2, bg="#322e2f", fg="white", font=("Helvetica", 8, "bold"))
        self.vhx_button.grid(row=1, column=1, padx=10, pady=10, sticky="e")

        self.eds_label = tk.Label(self.add_popup, text="Add EDS Result Record", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        self.eds_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.eds_button = tk.Button(self.add_popup, text="Choose EDS Image", command=self.choose_eds, width=20, height=2, bg="#322e2f", fg="white", font=("Helvetica", 8, "bold"))
        self.eds_button.grid(row=2, column=1, padx=10, pady=10, sticky="e")
        
        self.remark_label = tk.Label(self.add_popup, text="Remark : ", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        self.remark_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.remark_entry = tk.Entry(self.add_popup, font=("Helvetica", 12), width=25)
        self.remark_entry.grid(row=3, column=1, padx=10, pady=10)

        self.save_button = tk.Button(self.add_popup, text="Save", command=self.save_entry, width=28, height=2, bg="#26495c", fg="white", font=("Helvetica", 10, "bold"))
        self.save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="e")

        # Preview Labels
        self.preview1_label = tk.Label(self.add_popup, text="VHX Image Preview", bg="#d3d3d3")
        self.preview1_label.grid(row=5, column=0, padx=10, pady=10)

        self.preview2_label = tk.Label(self.add_popup, text="EDS Image Preview", bg="#d3d3d3")
        self.preview2_label.grid(row=5, column=1, padx=10, pady=10)

    def choose_vhx(self):
        file_path = filedialog.askopenfile(title="Select VHX Picture", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])

        if file_path:
            self.picture1_path = file_path.name 
            with open(self.picture1_path, 'rb') as file:
                image = Image.open(file)  
                image = image.resize((200, 200)) 
                self.picture1_preview = ImageTk.PhotoImage(image)
                self.preview1_label.config(image=self.picture1_preview)
                self.preview1_label.image = self.picture1_preview  

    def choose_eds(self):
        file_path = filedialog.askopenfile(title="Select EDS picture", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            self.picture2_path = file_path.name
            with open(self.picture2_path, 'rb') as file:
                image = Image.open(file)  
                image = image.resize((200, 200)) 
                self.picture2_preview = ImageTk.PhotoImage(image)
                self.preview2_label.config(image=self.picture2_preview)
                self.preview2_label.image = self.picture2_preview 
                
    def save_entry(self):
        logging.info("Save Button have been clicked")
        name = self.name_entry.get()
        remark = self.remark_entry.get()

        if remark and name and hasattr(self, 'picture1_path') and hasattr(self, 'picture2_path'):
            logging.info("Threading have started")
            # Use thread to make operation little faster
            threading.Thread(target=self.save_entry_to_db, args=(remark, name)).start()
            logging.info("Thread is finished")
        else:
            messagebox.showerror("Error", "Please fill all fields and select both pictures.")  

    def save_entry_to_db(self, remark, name):
        logging.info("Started saving to DB...")
        try:
            # Extract only the file names from the full file paths
            picture1_filename = os.path.basename(self.picture1_path)
            picture2_filename = os.path.basename(self.picture2_path)

            with open(self.picture1_path, "rb") as f1, open(self.picture2_path, "rb") as f2:
                picture1_data = f1.read()
                picture2_data = f2.read()

            self.db_handler.add_entry(name, picture1_filename, picture1_data, picture2_filename, picture2_data, remark)
            self.add_popup.destroy()
            self.root.attributes("-disabled", False)
            self.query_all()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))           

    def populate_treeview(self):
        conn = sqlite3.connect("eds.db")  
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, component, vhx_remark, eds_remark, remark FROM eds")
        rows = cursor.fetchall()
        for row in rows:
            self.treeview.insert("", "end", values=row)
        conn.close()   
   
    def delete_data(self):
        selected_item = self.treeview.selection()

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an entry to delete.")
            return

        rowid = self.treeview.item(selected_item, "values")[0]
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the entry with Row ID {rowid}?")
        if confirm:
            threading.Thread(target=self.db_handler.delete_entry, args=(rowid,)).start()
            self.query_all()
            messagebox.showinfo("Deleted", f"Entry with Row ID {rowid} has been deleted.")
   
    def update_data(self):
        selected_item = self.treeview.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a row to update.")
            return
        
        item_data = self.treeview.item(selected_item, "values")
        rowid, component, vhx_remark, eds_remark, remark = item_data
        self.update_popup(rowid, component, vhx_remark, eds_remark, remark)

    def update_popup(self, rowid, component, vhx_remark, eds_remark, remark):
        update_popup = tk.Toplevel(self.root)
        update_popup.title("Update Entry")
        update_popup.configure(bg="#e5e5dc")
        update_popup.geometry("475x500")
        update_popup.grab_set()
        update_popup.resizable(False, False)

        component_label = tk.Label(update_popup, text="Component Name:", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        component_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        name_entry = tk.Entry(update_popup, font=("Helvetica", 12), width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.insert(0, component)

        def choose_vhx_image():
            file_path = filedialog.askopenfilename(title="Select VHX Picture", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
            if file_path:
                self.picture1_path = file_path  
                image = Image.open(file_path)
                image = image.resize((150, 150))  
                self.picture1_preview = ImageTk.PhotoImage(image)
                vhx_label.config(image=self.picture1_preview) 

        def choose_eds_image():
            file_path = filedialog.askopenfilename(title="Select EDS Picture", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
            if file_path:
                self.picture2_path = file_path  
                image = Image.open(file_path)
                image = image.resize((150, 150)) 
                self.picture2_preview = ImageTk.PhotoImage(image)
                eds_label.config(image=self.picture2_preview)  

        # VHX Remark and Image Selection
        vhx_entry_label = tk.Label(update_popup, text="VHX Remark:", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        vhx_entry_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        vhx_button = tk.Button(update_popup, text="Choose VHX Image", command=choose_vhx_image, width=20, height=2, bg="#322e2f", fg="white", font=("Helvetica", 8, "bold"))
        vhx_button.grid(row=1, column=1, padx=10, pady=10, sticky="e")
        
        # EDS Remark and Image Selection
        eds_entry_label = tk.Label(update_popup, text="EDS Remark:", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        eds_entry_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        eds_button = tk.Button(update_popup, text="Choose EDS Image", command=choose_eds_image, width=20, height=2, bg="#322e2f", fg="white", font=("Helvetica", 8, "bold"))
        eds_button.grid(row=2, column=1, padx=10, pady=10, sticky="e")
        
        # Remark Field
        remark_label = tk.Label(update_popup, text="Remark:", font=("Helvetica", 10, "bold"), bg="#e5e5dc")
        remark_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        remark_entry = tk.Entry(update_popup, font=("Helvetica", 12), width=25)
        remark_entry.grid(row=3, column=1, padx=10, pady=10)
        remark_entry.insert(0, remark)

        # Save Button to update the entry
        save_button = tk.Button(update_popup, text="Save", command=lambda: self.save_update(update_popup, rowid, name_entry, self.picture1_path, self.picture2_path, remark_entry),
                                width=28, height=2, bg="#26495c", fg="white", font=("Helvetica", 10, "bold"))
        save_button.grid(row=5, column=0, columnspan=2, pady=10, sticky="e")

        # Image preview labels
        vhx_label = tk.Label(update_popup, text="VHX Preview", bg="#d3d3d3")
        vhx_label.grid(row=6, column=0, padx=10, pady=10)

        eds_label = tk.Label(update_popup, text="EDS Preview", bg="#d3d3d3")
        eds_label.grid(row=6, column=1, padx=10, pady=10)



        
    def save_update(self, update_popup, rowid, name_entry, vhx_image_path, eds_image_path, remark_text):    
        name = name_entry.get()
        vhx_remark = os.path.basename(vhx_image_path)
        eds_remark = os.path.basename(eds_image_path)
        remark = remark_text.get()

        if not name or not vhx_remark or not eds_remark or not remark:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        vhx_image_data = vhx_image_path
        eds_image_data = eds_image_path
        if vhx_image_data:
            with open(vhx_image_data, "rb") as f1:
                vhx_image_data = f1.read()
        
        if eds_image_data:
            with open(eds_image_data, "rb") as f2:
                eds_image_data = f2.read()

        # Update the database
        try:
            self.db_handler.update_entry(rowid, name, vhx_remark, vhx_image_data, eds_remark, eds_image_data, remark)
            messagebox.showinfo("Success", "Entry updated successfully!")
            update_popup.destroy()

            # Refresh the Treeview
            self.query_all()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
   
    def query_all(self):
        rows = self.db_handler.get_all_entries()
        # This will update all table every time query_all is call
        self.treeview.delete(*self.treeview.get_children())
        for row in rows:
            row_values = (row[0], row[1], row[2], row[4], row[6])  # Only pass required columns
            self.treeview.insert("", "end", values=row_values)

#########  Second Row Logic
    def submit_search(self):
        component_name = self.search_textbox.get()
        if not component_name:
            messagebox.showerror("Error", "Please enter a component name to search.")
            return

        rows = self.db_handler.search_by_component(component_name)
        if rows:
            self.update_treeview(rows)
        else:
            messagebox.showinfo("No Results", "No entries found for the given component.")
            
    def update_treeview(self, rows):
        # Clear the existing data in the Treeview
        for row in self.treeview.get_children():
            self.treeview.delete(row)

        # Insert new rows into the Treeview
        for row in rows:
            row_values = (row[0], row[1], row[2], row[3], row[4])
            self.treeview.insert("", "end", values=row_values)

    def on_double_click(self, event):
        selected_item = self.treeview.selection()  # Get selected row
        if selected_item:
            row_id = self.treeview.item(selected_item[0])["values"][0]  
            self.open_images_window(row_id)

    def open_images_window(self, row_id):
        # Fetch the images from the database using row_id
        vhx_data, eds_data = self.db_handler.get_images_by_rowid(row_id)

        if vhx_data and eds_data:
            # Create a new popup window
            image_window = tk.Toplevel(self.root)
            image_window.title("Image Preview")
            image_window.geometry("656x410")
            image_window.grab_set()
            image_window.resizable(False, False)

            # Open the VHX image using BytesIO to treat the BLOB data as a file
            vhx_image = Image.open(BytesIO(vhx_data))
            vhx_image = vhx_image.resize((300, 300))  
            vhx_image_tk = ImageTk.PhotoImage(vhx_image)
            vhx_label = tk.Label(image_window, image=vhx_image_tk)
            vhx_label.image = vhx_image_tk  
            vhx_label.grid(row=0, column=0, padx=10, pady=10)

            # Open the EDS image using BytesIO to treat the BLOB data as a file
            eds_image = Image.open(BytesIO(eds_data))
            eds_image = eds_image.resize((300, 300))  
            eds_image_tk = ImageTk.PhotoImage(eds_image)
            eds_label = tk.Label(image_window, image=eds_image_tk)
            eds_label.image = eds_image_tk  
            eds_label.grid(row=0, column=1, padx=10, pady=10)

            # Add download buttons for both images
            vhx_download_button = tk.Button(image_window, text="Download VHX Image", command=lambda: self.download_image(vhx_data, "VHX_Image.jpg"),
                                            width=28, height=2, bg="#26495c", fg="white", font=("Helvetica", 10, "bold"))
            vhx_download_button.grid(row=1, column=0, padx=10, pady=10)

            eds_download_button = tk.Button(image_window, text="Download EDS Image", command=lambda: self.download_image(eds_data, "EDS_Image.jpg"),
                                            width=28, height=2, bg="#26495c", fg="white", font=("Helvetica", 10, "bold"))
            eds_download_button.grid(row=1, column=1, padx=10, pady=10)
        else:
            messagebox.showerror("Error", "No images found for this entry.")

    def download_image(self, image_data, default_filename):
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")], initialfile=default_filename)
        if file_path:
            try:
                with open(file_path, "wb") as file:
                    file.write(image_data)
                messagebox.showinfo("Success", "Image downloaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to download image: {e}")

        
#####################################################################################
########  This class will deal with SQLite database

class SQLiteHandler:
    def __init__(self, db_eds):
        self.db_eds = db_eds
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(self.db_eds)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS eds (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT,
            vhx_remark TEXT,
            vhx_data BLOB,
            eds_remark TEXT,
            eds_data BLOB,
            remark TEXT
        )
        """)
        conn.commit()
        conn.close()

    def add_entry(self, component, vhx_remark, vhx_data, eds_remark, eds_data, remark):
        conn = sqlite3.connect(self.db_eds)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO eds (component, vhx_remark, vhx_data, eds_remark, eds_data, remark)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (component, vhx_remark, vhx_data, eds_remark, eds_data, remark))
        conn.commit()
        conn.close()
        
    def update_entry(self, rowid, component, vhx_remark, vhx_data, eds_remark, eds_data, remark):
        """Update the database with the new values."""
        conn = sqlite3.connect(self.db_eds)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE eds
            SET component = ?, vhx_remark = ?, vhx_data = ?, eds_remark = ?, eds_data =?,  remark = ?
            WHERE rowid = ?
        """, (component, vhx_remark, vhx_data, eds_remark, eds_data, remark, rowid))
        conn.commit()
        conn.close()     
    
    def search_by_component(self, component_name):
        """Search for entries in the database by component name."""
        conn = sqlite3.connect(self.db_eds)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rowid, component, vhx_remark, eds_remark, remark
            FROM eds
            WHERE component LIKE ?
        """, ('%' + component_name + '%',))  
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_entries(self):
        conn = sqlite3.connect(self.db_eds)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eds")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_entry(self, rowid):
        conn = sqlite3.connect(self.db_eds)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM eds WHERE rowid = ?", (rowid,))
        conn.commit()
        conn.close()

    def get_images_by_rowid(self, row_id):
        """Fetch the image BLOBs for the given rowid."""
        conn = sqlite3.connect(self.db_eds)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vhx_data, eds_data
            FROM eds
            WHERE rowid = ?
        """, (row_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result  
        return None, None


if __name__ == "__main__":
    logging.basicConfig(
                    filename="app.log",  
                    level=logging.DEBUG,  
                    format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
                    datefmt="%Y-%m-%d %H:%M:%S"  
                    )
    # Disable all logging
    logging.disable(logging.CRITICAL)
    root = tk.Tk()
    app = MainProject(root)
    root.mainloop()