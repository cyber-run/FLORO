import threading, cProfile, cv2, os, pstats, sys
from custom_widgets import create_range_box
from PIL import Image, ImageTk
from tkinter import filedialog
import customtkinter as ctk
import tkinter as tk
import numpy as np


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

Image.MAX_IMAGE_PIXELS = None  # Disable the warning for large image files


class Application(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color="#151518")

        # Setup root window
        self.geometry("1200x800")
        self.title("Python Image Viewer")

        self.current_view = "roi"

        self.pr = cProfile.Profile()

        # Setup image and ROI variables
        self.pil_image = None
        self.roi_start = None
        self.roi_end = None
        self.is_drawing_roi = False

        # Initial values
        self.threshold_value = 16
        self.kernel_size_value = 3

        # Initialise widgets and bindings
        self.create_menu()
        self.create_status_bar()
        self.bind_events()
        self.setup_sidebar()
        self.create_widgets()


        # Init/reset transformation matrix
        self.reset_transform()
    
    def write_img(self, img):
        """Write the image to a file."""
        filename = filedialog.asksaveasfilename(
            filetypes=[("PNG", ".png"), ("JPEG", ".jpg"), ("Tiff", ".tif")],
            initialdir=os.getcwd()
        )
        if filename:
            img.save(filename)
    
    def create_widgets(self):
        """Create the status bar and canvas widgets."""
        self.canvas = ctk.CTkCanvas(self, background="black")
        self.canvas.pack(side="right", expand=True, fill="both")


    def create_menu(self):
        """Create the menu bar and bind menu items to their respective functions."""
        self.menu_bar = tk.Menu(self)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        self.file_menu.add_command(label="Open", command=self.menu_open_clicked, accelerator="Ctrl+O")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.destroy)

        self.bind_all("<Control-o>", self.menu_open_clicked)
        self.configure(menu=self.menu_bar)


    def create_status_bar(self):
        """Create the status bar with image information and pixel coordinates."""
        self.frame_statusbar = ctk.CTkFrame(self, corner_radius=0)
        self.frame_statusbar.pack(side="bottom", fill="x")

        self.label_image_pixel = ctk.CTkLabel(self.frame_statusbar, text="(x, y)")
        self.label_image_pixel.pack(side="left", padx=5, anchor="w")

        self.status = ctk.CTkLabel(self.frame_statusbar, text="Idle")
        self.status.pack(side="left", padx=5, anchor="center", expand=True, fill="x")

        self.label_image_info = ctk.CTkLabel(self.frame_statusbar, text="Image info")
        self.label_image_info.pack(side="right", padx=5, anchor="e")

    def bind_events(self):
        """Bind mouse events to their respective functions."""
        self.bind("<Button-1>", self.mouse_down_left)
        self.bind("<B1-Motion>", self.mouse_move_left)
        self.bind("<Motion>", self.mouse_move)
        self.bind("<Double-Button-1>", self.mouse_double_click_left)
        self.bind("<ButtonRelease-1>", self.mouse_up_left)
        self.bind("<MouseWheel>", self.mouse_wheel)

    def menu_open_clicked(self, event=None):
        """Open an image file and set it as the current image."""
        filename = filedialog.askopenfilename(
            filetypes=[("Image file", ".bmp .png .jpg .tif"), ("Bitmap", ".bmp"), ("PNG", ".png"), ("JPEG", ".jpg"),
                       ("Tiff", ".tif")],
            initialdir=os.getcwd()
        )
        self.set_image(filename)

    def set_image(self, filename):
        """Load an image file and display it on the canvas."""
        if not filename:
            return
        self.pil_image = Image.open(filename)
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.draw_image()

        self.title(f"FLORO - {os.path.basename(filename)}")
        self.label_image_info.configure(text=f"{self.pil_image.format}: {self.pil_image.width}x{self.pil_image.height} {self.pil_image.mode}")
        os.chdir(os.path.dirname(filename))

    def mouse_down_left(self, event):
        """Handle left mouse button press event."""
        self.__old_event = event
        if event.state & 0x0004:  # Check if Ctrl key is pressed
            self.roi_start = self.to_image_point(event.x, event.y)
            self.roi_end = None
            self.is_drawing_roi = True
        else:
            self.is_drawing_roi = False

    def mouse_move_left(self, event):
        """Handle left mouse button drag event."""
        if self.pil_image is None:
            return
        if self.is_drawing_roi:
            self.roi_end = self.to_image_point(event.x, event.y)
            self.draw_image()
        else:
            self.translate(event.x - self.__old_event.x, event.y - self.__old_event.y)
            self.draw_image()
        self.__old_event = event

    def mouse_up_left(self, event):
        """Handle left mouse button release event for ending ROI drawing."""
        if self.is_drawing_roi:
            self.roi_end = self.to_image_point(event.x, event.y)
            self.is_drawing_roi = False
            self.draw_image()

    def mouse_move(self, event):
        """Handle mouse move event and update the status bar with the current pixel coordinates."""
        if self.pil_image is None:
            return

        image_point = self.to_image_point(event.x, event.y)
        if len(image_point) > 0:
            self.label_image_pixel.configure(text=f"({image_point[0]:.2f}, {image_point[1]:.2f})")
        else:
            self.label_image_pixel.configure(text="(--, --)")

    def mouse_double_click_left(self, event):
        """Handle left mouse button double-click event and fit the image to the canvas."""
        if self.pil_image is None:
            return
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.draw_image()

    def mouse_wheel(self, event):
        """Handle mouse wheel event for zooming the image."""
        if self.pil_image is None:
            return

        if event.delta < 0:
            self.scale_at(1.25, event.x, event.y)
        else:
            self.scale_at(0.8, event.x, event.y)
        self.draw_image()

    def reset_transform(self):
        """Reset the affine transformation matrix to the identity matrix."""
        self.mat_affine = np.eye(3)

    def translate(self, offset_x, offset_y):
        """Apply translation to the affine transformation matrix."""
        mat = np.eye(3)
        mat[0, 2] = float(offset_x)
        mat[1, 2] = float(offset_y)

        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale(self, scale: float):
        """Apply scaling to the affine transformation matrix."""
        mat = np.eye(3)
        mat[0, 0] = scale
        mat[1, 1] = scale

        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale_at(self, scale: float, cx: float, cy: float):
        """Apply scaling centered at a specific point."""
        self.translate(-cx, -cy)
        self.scale(scale)
        self.translate(cx, cy)

    def zoom_fit(self, image_width, image_height):
        """Fit the image to the canvas while maintaining the aspect ratio."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if (image_width * image_height <= 0) or (canvas_width * canvas_height <= 0):
            return

        self.reset_transform()

        scale = 1.0
        offsetx = 0.0
        offsety = 0.0

        if (canvas_width * image_height) > (image_width * canvas_height):
            scale = canvas_height / image_height
            offsetx = (canvas_width - image_width * scale) / 2
        else:
            scale = canvas_width / image_width
            offsety = (canvas_height - image_height * scale) / 2

        self.scale(scale)
        self.translate(offsetx, offsety)

    def to_image_point(self, x, y):
        """Convert canvas coordinates to image coordinates."""
        if self.pil_image is None:
            return np.array([])
        mat_inv = np.linalg.inv(self.mat_affine)
        image_point = np.dot(mat_inv, (x, y, 1.))
        if (
            image_point[0] < 0
            or image_point[1] < 0
            or image_point[0] > self.pil_image.width
            or image_point[1] > self.pil_image.height
        ):
            return np.array([])

        return image_point

    def to_canvas_point(self, x, y):
        """Convert image coordinates to canvas coordinates."""
        canvas_point = np.dot(self.mat_affine, (x, y, 1.))
        return canvas_point[:2]

    def draw_image(self):
        """Draw the image and ROI rectangle on the canvas."""
        self.canvas.delete("all")

        if self.pil_image is None:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        mat_inv = np.linalg.inv(self.mat_affine)

        affine_inv = (
            mat_inv[0, 0],
            mat_inv[0, 1],
            mat_inv[0, 2],
            mat_inv[1, 0],
            mat_inv[1, 1],
            mat_inv[1, 2],
        )

        dst = self.pil_image.transform(
            (canvas_width, canvas_height),
            Image.AFFINE,
            affine_inv,
            Image.NEAREST,
        )

        im = ImageTk.PhotoImage(image=dst)

        self.canvas.create_image(0, 0, anchor="nw", image=im)
        self.image = im

        if self.roi_start is not None and self.roi_end is not None:
            roi_start_canvas = self.to_canvas_point(self.roi_start[0], self.roi_start[1])
            roi_end_canvas = self.to_canvas_point(self.roi_end[0], self.roi_end[1])
            self.canvas.create_rectangle(
                roi_start_canvas[0],
                roi_start_canvas[1],
                roi_end_canvas[0],
                roi_end_canvas[1],
                outline="red",
                width=2,
            )

    def setup_roi_selector(self):
        pass

    def setup_data_view(self):
        pass

    def switch_view(self, view):
        '''
        Switch between the roi view and data analysis view
        '''
        if view == "roi" and self.current_view != "roi":
            # Destroy the existing widgets in the data view if they exist
            self.current_view = "roi"


            # Set up the roi view
            self.setup_roi_selector()
            self.home_button.configure(fg_color="#27272a")
            self.data_button.configure(fg_color=self.fg_color1)
            
        elif view == "data" and self.current_view != "data":
            self.current_view = "data"

            # Destroy existing widgets in the roi view if they exist
            self.canvas.pack_forget()

            # Set up the data analysis view
            self.setup_data_view()
            self.data_button.configure(fg_color="#27272a")
            self.home_button.configure(fg_color=self.fg_color1)

    def setup_sidebar(self):
        '''
        Set up the sidebar with buttons for switching between views
        '''
        self.sidebar_frame = ctk.CTkFrame(self, width=50, corner_radius=0, border_width=-2, border_color="#1c1c1c")
        self.sidebar_frame.pack(side="left", fill="y")
        self.fg_color1 = self.sidebar_frame.cget("fg_color")

        # Load icons
        home_icon = ctk.CTkImage(Image.open("assets/track.png"), size=(30, 30))
        data_icon = ctk.CTkImage(Image.open("assets/data.png"), size=(30, 30))

        self.home_button = ctk.CTkButton(
            self.sidebar_frame,
            text="",
            image=home_icon,
            height=40,
            width=40,
            corner_radius=5,
            fg_color="#27272a",
            hover_color="#1c1c1c",
            command=lambda: self.switch_view("roi")  # Switch to roi view when clicked
        )
        self.home_button.pack(side="top", padx=5, pady=5)

        self.data_button = ctk.CTkButton(
            self.sidebar_frame,
            text="",
            image=data_icon,
            height=40,
            width=40,
            corner_radius=5,
            fg_color=self.fg_color1,
            hover_color="#1c1c1c",
            command=lambda: self.switch_view("data")  # Switch to data analysis view when clicked
        )
        self.data_button.pack(side="top", padx=5, pady=5)


if __name__ == "__main__":
    # Set the theme of customtkinter
    ctk.set_appearance_mode("Dark")  # Options: "Light", "Dark", "System"
    ctk.set_default_color_theme("assets/style.json")  # Options include: "blue", "dark-blue", "green"

    app = Application()
    app.mainloop()
