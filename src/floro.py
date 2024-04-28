import os
import json
import sqlite3
from tkinter import filedialog
from PIL import Image
from CTkMenuBar import *
from CTkMessagebox import *
import customtkinter as ctk
from front_end import FrontEnd

Image.MAX_IMAGE_PIXELS = None


class Application(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color="#151518")

        self.configure_root()
        self.create_menu()
        self.bind_events()

        self.frontend = FrontEnd(self)

        self.current_view = "roi"
        self.pil_image = None

    def configure_root(self):
        self.title("FLORO")
        self.geometry("1200x800")
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

    def create_menu(self):
        title_menu = CTkTitleMenu(self) if os.name == "nt" else CTkMenuBar(self)

        file_menu = title_menu.add_cascade(text="File")
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option="Open", command=self.menu_open_clicked)
        file_dropdown.add_separator()
        file_dropdown.add_option(option="New Project", command=self.menu_new_project_clicked)
        file_dropdown.add_separator()
        file_dropdown.add_option(option="Exit", command=self.destroy)

    def bind_events(self):
        self.bind_all("<Control-o>", self.menu_open_clicked)
        self.bind_all("<Control-n>", lambda event: self.menu_new_project_clicked())

    def menu_open_clicked(self, event=None):
        filetypes = [
            ("Image file", ".bmp .png .jpg .tif"),
            ("Bitmap", ".bmp"),
            ("PNG", ".png"),
            ("JPEG", ".jpg"),
            ("Tiff", ".tif")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes, initialdir=os.getcwd())
        self.set_image(filename)

    def menu_new_project_clicked(self):
        new_project_window = ctk.CTkToplevel(self)
        new_project_window.title("New Project")
        new_project_window.geometry("400x250")
        new_project_window.attributes("-topmost", True)

        folder_path_label = ctk.CTkLabel(new_project_window, text="Folder Path:")
        folder_path_label.pack(pady=10)

        folder_path_entry = ctk.CTkEntry(new_project_window, width=300)
        folder_path_entry.pack()

        select_folder_button = ctk.CTkButton(
            new_project_window,
            text="Select Folder",
            command=lambda: self.select_folder(folder_path_entry),
            fg_color="#F9F9FA"
        )
        select_folder_button.pack(pady=10)

        project_name_label = ctk.CTkLabel(new_project_window, text="Project Name:")
        project_name_label.pack(pady=10)

        project_name_entry = ctk.CTkEntry(new_project_window, width=300)
        project_name_entry.pack()

        create_project_button = ctk.CTkButton(
            new_project_window,
            text="Create Project",
            command=lambda: self.create_project(
                folder_path_entry.get(),
                project_name_entry.get(),
                new_project_window
            ),
            fg_color="#F9F9FA"
        )
        create_project_button.pack(pady=10)

    def select_folder(self, folder_path_entry):
        folder_path = filedialog.askdirectory()
        folder_path_entry.delete(0, ctk.END)
        folder_path_entry.insert(0, folder_path)

    def create_project(self, folder_path, project_name, new_project_window):
        if folder_path and project_name:
            project_data = {
                "folder_path": folder_path,
                "project_name": project_name
            }
            with open("project_data.json", "w") as file:
                json.dump(project_data, file)
            new_project_window.destroy()
            self.create_database(folder_path)
            self.load_project()
            self.display_first_image()
        else:
            CTkMessagebox(title="Error", message="Please provide a folder path and project name.")

    def create_database(self, folder_path):
        conn = sqlite3.connect("project.sqlite3")
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS images")
        cursor.execute("DROP TABLE IF EXISTS roi_table")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                image_id INTEGER PRIMARY KEY,
                image_path TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roi_table (
                roi_id INTEGER PRIMARY KEY,
                drug_name TEXT,
                roi_points TEXT
            )
        """)

        image_paths = self.get_image_paths(folder_path)
        for image_path in image_paths:
            cursor.execute("INSERT INTO images (image_path) VALUES (?)", (image_path,))

        conn.commit()
        conn.close()

    def save_roi(self, roi_id, drug_name, roi_points):
        conn = sqlite3.connect("project.sqlite3")
        cursor = conn.cursor()

        roi_points_str = str(roi_points)
        cursor.execute(
            "INSERT INTO roi_table (roi_id, drug_name, roi_points) VALUES (?, ?, ?)",
            (roi_id, drug_name, roi_points_str)
        )

        conn.commit()
        conn.close()

    def get_roi_data(self, roi_id):
        conn = sqlite3.connect("project.sqlite3")
        cursor = conn.cursor()

        cursor.execute("SELECT drug_name, roi_points FROM roi_table WHERE roi_id = ?", (roi_id,))
        result = cursor.fetchone()

        if result:
            drug_name, roi_points_str = result
            roi_points = eval(roi_points_str)
            return drug_name, roi_points
        else:
            return None, None

    def display_first_image(self):
        image_paths = self.get_image_paths_from_database()
        if image_paths:
            first_image_path = image_paths[0]
            self.set_image(first_image_path)
        else:
            CTkMessagebox(title="Error", message="No images found in the folder.")

    def get_image_paths(self, folder_path):
        image_extensions = [".bmp", ".png", ".jpg", ".tif"]
        image_paths = [
            os.path.join(folder_path, filename)
            for filename in os.listdir(folder_path)
            if os.path.splitext(filename)[1].lower() in image_extensions
        ]
        return image_paths

    def load_project(self):
        try:
            with open("project_data.json", "r") as file:
                project_data = json.load(file)
                project_name = project_data["project_name"]
                self.frontend.update_project_name(project_name)
        except FileNotFoundError:
            pass

    def get_image_paths_from_database(self):
        conn = sqlite3.connect("project.sqlite3")
        cursor = conn.cursor()

        cursor.execute("SELECT image_path FROM images")
        image_paths = [row[0] for row in cursor.fetchall()]

        conn.close()
        return image_paths

    def set_image(self, filename):
        if not filename:
            return
        self.pil_image = Image.open(filename)
        self.frontend.image_canvas.set_image(self.pil_image)

        image_info = f"{self.pil_image.format}: {self.pil_image.width}x{self.pil_image.height} {self.pil_image.mode}"
        self.frontend.update_image_info(image_info)
        os.chdir(os.path.dirname(filename))

    def switch_view(self, view):
        if view == "roi" and self.current_view != "roi":
            self.current_view = "roi"
            self.frontend.canvas_view_frame.grid(row=0, column=1, sticky="nsew")
            self.frontend.setup_roi_selector()
            self.frontend.switch_view_buttons("roi")
        elif view == "data" and self.current_view != "data":
            self.current_view = "data"
            self.frontend.canvas_view_frame.grid_forget()
            self.frontend.setup_data_view()
            self.frontend.switch_view_buttons("data")


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("assets/style.json")

    app = Application()
    app.mainloop()