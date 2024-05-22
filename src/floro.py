import os
import json
from tkinter import filedialog
from PIL import Image
import customtkinter as ctk
from front_end import FrontEnd
from db_manager import DatabaseManager

Image.MAX_IMAGE_PIXELS = None

class Application(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color="#151518")

        self.configure_root()

        self.frontend = FrontEnd(self)
        self.db_manager = DatabaseManager()

        self.current_view = "roi"
        self.pil_image = None

        self.bind_events()

    def configure_root(self):
        self.title("FLORO")
        self.geometry("1200x800")
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

    def bind_events(self):
        self.bind_all("<Control-o>", self.menu_open_clicked)
        self.bind_all("<Control-n>", self.frontend.new_project_window)

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
            self.db_manager.create_database(folder_path)
            self.load_project()
            self.display_first_image()
        else:
            self.frontend.show_message("Error", "Please enter a folder path and project name.")

    def display_first_image(self):
        image_paths = self.db_manager.get_image_paths_from_database()
        if image_paths:
            first_image_path = image_paths[0]
            self.set_image(first_image_path)
        else:
            self.frontend.show_message("Error", "No images found in the selected folder.")

    def load_project(self):
        try:
            with open("project_data.json", "r") as file:
                project_data = json.load(file)
                project_name = project_data["project_name"]
                self.frontend.update_project_name(project_name)
        except FileNotFoundError:
            pass

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

    def add_roi(self, roi_points):
        '''
        Save the ROI data to the database and update the ROI table.
        '''
        print(f"Database path: {self.db_manager.db_path}")  # Print the database path

        if roi_points:
            # Assign anonymous drug name for initialization
            drug_name = "Drug X"
            # Save the ROI data to the database
            roi_id = self.db_manager.save_roi(drug_name, str(roi_points))
            # Insert the ROI data into the table
            self.frontend.roi_table.insert(parent="", index="end", values=(roi_id, drug_name))
        else:
            print("No ROI points provided.")

    def update_drug_name(self, roi_id, new_drug_name):
        '''
        Update the drug name in the database.
        '''
        self.db_manager.update_drug_name(roi_id, new_drug_name)

    def delete_roi(self, roi_points):
        """
        Delete the ROI data from the database and update the table.
        
        Args:
            roi_points (list): List of points defining the ROI to delete.
        """
        roi_id = self.db_manager.delete_roi(roi_points)

        print(f"Deleted ROI with ID: {roi_id}")  # Print the ID of the deleted ROI

        # Delete from Treeview
        # self.frontend.roi_table.delete(str(roi_id))

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("assets/style.json")

    app = Application()
    app.mainloop()
