import customtkinter as ctk
from PIL import Image
from custom_treeview import CustomTreeview
from image_canvas import ImageCanvas
from CTkMessagebox import CTkMessagebox
from CTkMenuBar import *
import os


class FrontEnd:
    def __init__(self, root):
        self.root = root
        self.label_image_pixel = None
        self.label_image_info = None
        self.home_button = None
        self.data_button = None
        self.fg_color1 = None
        self.image_canvas = None

        self.create_menu()
        self.create_status_bar()
        self.setup_sidebar()
        self.create_canvas_view()
        self.root.bind("<BackSpace>", self.image_canvas._delete_selected_roi)

    def create_menu(self):
        # Create the title menu if windows else create menu bar
        title_menu = CTkTitleMenu(self.root) if os.name == "nt" else CTkMenuBar(self.root)

        file_menu = title_menu.add_cascade(text="File")
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option="Open", command=self.root.menu_open_clicked)
        file_dropdown.add_separator()
        file_dropdown.add_option(option="New Project", command=self.new_project_window)
        file_dropdown.add_separator()
        file_dropdown.add_option(option="Exit", command=self.root.destroy)

    def create_canvas_view(self):
        self.canvas_view_frame = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            border_width=-2,
            border_color="#1c1c1c"
        )
        self.canvas_view_frame.grid(row=0, column=1, sticky="nsew")

        self.image_canvas = ImageCanvas(
            self.canvas_view_frame,
            frontend=self,
            background="black",
            highlightthickness=0
        )
        self.image_canvas.pack(side="left", expand=True, fill="both", padx=5, pady=5)

        self.roi_table_frame = ctk.CTkFrame(self.canvas_view_frame, width=200, fg_color="transparent")
        self.roi_table_frame.pack(side="right", fill="y", padx=5, pady=5)
        self.roi_table_frame.pack_propagate(False)

        columns = ("ID", "Drug Name")
        headings = ("ID", "Drug Name")
        self.roi_table = CustomTreeview(self.roi_table_frame, columns=columns, headings=headings)
        self.roi_table.column("#1", width=40, minwidth=40)
        self.roi_table.pack(fill="both", expand=True)

        ctk.set_default_color_theme("assets/style.json")

        self.extract_button = ctk.CTkButton(
            self.roi_table_frame,
            text="Extract ROIs",
            fg_color="#3F8047",
            hover_color="#2B5530",
        )
        self.extract_button.pack(side="bottom", fill="x", padx=5, pady=5, anchor="s")

    def create_status_bar(self):
        frame_statusbar = ctk.CTkFrame(self.root, corner_radius=0)
        frame_statusbar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.project_name_label = ctk.CTkLabel(frame_statusbar, text="")
        self.project_name_label.pack(side="left", padx=5, anchor="w")

        status = ctk.CTkLabel(frame_statusbar, text="Idle")
        status.pack(side="left", padx=5, anchor="center", expand=True, fill="x")

        self.label_image_info = ctk.CTkLabel(frame_statusbar, text="Image info")
        self.label_image_info.pack(side="right", padx=5, anchor="e")

    def setup_sidebar(self):
        '''
        Create the sidebar with buttons for switching between views.
        '''
        sidebar_frame = ctk.CTkFrame(
            self.root,
            width=30,
            corner_radius=0,
            border_width=-2,
            border_color="#1c1c1c"
        )
        sidebar_frame.grid(row=0, column=0, sticky="nsw")
        sidebar_frame.grid_propagate(False)

        self.fg_color1 = sidebar_frame.cget("fg_color")

        home_icon = ctk.CTkImage(Image.open("assets/track.png"), size=(30, 30))
        data_icon = ctk.CTkImage(Image.open("assets/data.png"), size=(30, 30))

        self.home_button = ctk.CTkButton(
            sidebar_frame,
            text="",
            image=home_icon,
            height=40,
            width=40,
            corner_radius=5,
            fg_color="#27272a",
            hover_color="#1c1c1c",
            command=lambda: self.root.switch_view("roi")
        )
        self.home_button.pack(side="top", padx=5, pady=5)

        self.data_button = ctk.CTkButton(
            sidebar_frame,
            text="",
            image=data_icon,
            height=40,
            width=40,
            corner_radius=5,
            fg_color=self.fg_color1,
            hover_color="#1c1c1c",
            command=lambda: self.root.switch_view("data")
        )
        self.data_button.pack(side="top", padx=5, pady=5)

    def new_project_window(self, event=None):
        '''
        Create a top level window for setting up a new project
        '''
        new_project_window = ctk.CTkToplevel(self.root)
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
            command=lambda: self.root.select_folder(folder_path_entry),
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
            command=lambda: self.root.create_project(
                folder_path_entry.get(),
                project_name_entry.get(),
                new_project_window
            ),
            fg_color="#F9F9FA"
        )
        create_project_button.pack(pady=10)

    def setup_data_view(self):
        pass

    def setup_roi_selector(self):
        pass
    
    def switch_view_buttons(self, view):
        '''
        Highlight the button for the current view and unhighlight the other button.
        '''
        if view == "roi":
            self.home_button.configure(fg_color="#27272a")
            self.data_button.configure(fg_color=self.fg_color1)
        elif view == "data":
            self.data_button.configure(fg_color="#27272a")
            self.home_button.configure(fg_color=self.fg_color1)
    
    def update_project_name(self, project_name):
        '''
        Update the project name label with the given project name.
        '''
        self.project_name_label.configure(text=project_name)
    
    def update_image_info(self, image_info):
        '''
        Update the image info label with the given image info.
        '''
        self.label_image_info.configure(text=image_info)

    def show_message(self, title, message):
        '''
        Show a message box with the given title and message.
        '''
        CTkMessagebox(title=title, message=message)