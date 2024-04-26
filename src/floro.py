import threading
import cProfile
import os
from CTkTable import *
from CTkMenuBar import *
from PIL import Image
from tkinter import filedialog
import customtkinter as ctk
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

    def create_canvas_view(self):
        # Create canvas view frame
        self.canvas_view_frame = ctk.CTkFrame(self.master, corner_radius=0, border_width=-2, border_color="#1c1c1c")
        self.canvas_view_frame.grid(row=0, column=1, sticky="nsew")

        self.image_canvas = ImageCanvas(self.canvas_view_frame, frontend=self, background="black", highlightthickness=0)
        self.image_canvas.pack(side="top", expand=True, fill="both", padx=5, pady=5)

    def create_status_bar(self):
        frame_statusbar = ctk.CTkFrame(self.master, corner_radius=0)
        frame_statusbar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.label_image_pixel = ctk.CTkLabel(frame_statusbar, text="(x, y)")
        self.label_image_pixel.pack(side="left", padx=5, anchor="w")

        status = ctk.CTkLabel(frame_statusbar, text="Idle")
        status.pack(side="left", padx=5, anchor="center", expand=True, fill="x")

        self.label_image_info = ctk.CTkLabel(frame_statusbar, text="Image info")
        self.label_image_info.pack(side="right", padx=5, anchor="e")

    def setup_sidebar(self):
        sidebar_frame = ctk.CTkFrame(self.master, width=30, corner_radius=0, border_width=-2, border_color="#1c1c1c")
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

    def update_image_info(self, image_info):
        self.label_image_info.configure(text=image_info)

    def update_pixel_coordinates(self, coordinates):
        self.label_image_pixel.configure(text=coordinates)

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


class Application(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color="#151518")

        self.geometry("1200x800")
        self.title("FLORO")

        self.current_view = "roi"
        self.pil_image = None

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self.frontend = FrontEnd(self)

        self.create_menu()
        self.bind_events()

    def write_img(self, img):
        filename = filedialog.asksaveasfilename(
            filetypes=[("PNG", ".png"), ("JPEG", ".jpg"), ("Tiff", ".tif")],
            initialdir=os.getcwd()
        )
        if filename:
            img.save(filename)

    def create_menu(self):
        if os.name == "nt":
            title_menu = CTkTitleMenu(self)
        else:
            title_menu = CTkMenuBar(self)

        file_menu = title_menu.add_cascade(text="File")
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option="Open", command=self.menu_open_clicked)
        file_dropdown.add_separator()
        file_dropdown.add_option(option="Exit", command=self.destroy)

        self.bind_all("<Control-o>", self.menu_open_clicked)

    def bind_events(self):
        pass

    def menu_open_clicked(self, event=None):
        filename = filedialog.askopenfilename(
            filetypes=[("Image file", ".bmp .png .jpg .tif"), ("Bitmap", ".bmp"), ("PNG", ".png"), ("JPEG", ".jpg"),
                       ("Tiff", ".tif")],
            initialdir=os.getcwd()
        )
        self.set_image(filename)

    def set_image(self, filename):
        if not filename:
            return
        self.pil_image = Image.open(filename)
        self.frontend.image_canvas.set_image(self.pil_image)

        self.title(f"FLORO - {os.path.basename(filename)}")
        self.frontend.update_image_info(f"{self.pil_image.format}: {self.pil_image.width}x{self.pil_image.height} {self.pil_image.mode}")
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