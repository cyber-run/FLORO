import customtkinter as ctk
from PIL import Image
from custom_treeview import CustomTreeview
from image_canvas import ImageCanvas


class FrontEnd:
    def __init__(self, master):
        self.master = master
        self.label_image_pixel = None
        self.label_image_info = None
        self.home_button = None
        self.data_button = None
        self.fg_color1 = None
        self.image_canvas = None

        self.create_status_bar()
        self.setup_sidebar()
        self.create_canvas_view()
        self.master.bind("<BackSpace>", self.image_canvas.delete_selected_roi)

    def create_canvas_view(self):
        self.canvas_view_frame = ctk.CTkFrame(
            self.master,
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
        frame_statusbar = ctk.CTkFrame(self.master, corner_radius=0)
        frame_statusbar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.project_name_label = ctk.CTkLabel(frame_statusbar, text="")
        self.project_name_label.pack(side="left", padx=5, anchor="w")

        status = ctk.CTkLabel(frame_statusbar, text="Idle")
        status.pack(side="left", padx=5, anchor="center", expand=True, fill="x")

        self.label_image_info = ctk.CTkLabel(frame_statusbar, text="Image info")
        self.label_image_info.pack(side="right", padx=5, anchor="e")

    def update_image_info(self, image_info):
        self.label_image_info.configure(text=image_info)

    def setup_sidebar(self):
        sidebar_frame = ctk.CTkFrame(
            self.master,
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
            command=lambda: self.master.switch_view("roi")
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
            command=lambda: self.master.switch_view("data")
        )
        self.data_button.pack(side="top", padx=5, pady=5)

    def update_project_name(self, project_name):
        self.project_name_label.configure(text=project_name)

    def switch_view_buttons(self, view):
        if view == "roi":
            self.home_button.configure(fg_color="#27272a")
            self.data_button.configure(fg_color=self.fg_color1)
        elif view == "data":
            self.data_button.configure(fg_color="#27272a")
            self.home_button.configure(fg_color=self.fg_color1)

    def setup_roi_selector(self):
        pass

    def setup_data_view(self):
        pass