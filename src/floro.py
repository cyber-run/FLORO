from custom_widgets import create_range_box
import threading, cProfile, cv2, os, pstats, sys
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
        self.create_widgets()
        self.create_status_bar()
        self.bind_events()

        # Init/reset transformation matrix
        self.reset_transform()

    def update_threshold(self, entry, delta, limit):
        """Update the threshold value from entry with delta and enforce limits."""
        current_value = int(entry.get())
        new_value = current_value + delta
        if delta > 0:
            new_value = min(limit, new_value)  # Increment
        else:
            new_value = max(0, new_value)  # Decrement, ensuring it does not go below 0
        entry.delete(0, 'end')
        entry.insert(0, str(new_value))
        self.threshold_value = new_value
        # self.update_image()

    def update_kernel_size(self, entry, delta, limit):
        """Update the kernel size value from entry with delta and enforce limits."""
        current_value = int(entry.get())
        new_value = current_value + delta
        if delta > 0:
            new_value = min(limit, new_value)  # Increment
        else:
            new_value = max(1, new_value)  # Decrement, ensuring it does not go below 1
        entry.delete(0, 'end')
        entry.insert(0, str(new_value))
        self.kernel_size_value = new_value
        # self.update_image()

    def process_roi_threaded(self):
        """Start the ROI processing in a separate thread."""
        thread = threading.Thread(target=self.process_roi)
        thread.start()

    def process_roi(self):
        """Process the selected ROI with the current threshold and kernel size, when the button is pressed."""
        if self.pil_image is None or self.roi_start is None or self.roi_end is None:
            ctk.CTkMessageBox.show_info("Process ROI", "No ROI defined or image loaded.")
            return

        self.status.configure(text="Processing ROI...")  # Assume there's a method to update a status bar

        self.pr.enable()    # Enable profiler

        processed_image = self._process_roi()  # Refactor the processing into a private method
        if processed_image:
            self.pil_image = processed_image
            self.draw_image()
        self.status.configure(text="ROI Processing Completed.")  # Update status bar

        self.pr.disable()
        ps = pstats.Stats(self.pr, stream=sys.stdout)
        ps.print_stats()

    def _process_roi(self):
        """Process the selected ROI with the current threshold and kernel size using watershed segmentation."""
        if self.pil_image is None or self.roi_start is None or self.roi_end is None:
            return None

        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(self.pil_image), cv2.COLOR_RGB2BGR)

        # Extract the ROI coordinates
        x1, y1 = int(self.roi_start[0]), int(self.roi_start[1])
        x2, y2 = int(self.roi_end[0]), int(self.roi_end[1])

        # Ensure the coordinates are within the image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(cv_image.shape[1], x2), min(cv_image.shape[0], y2)

        # Extract the ROI from the image
        roi = cv_image[y1:y2, x1:x2]

        # Convert cv roi to PIL format
        # roi = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
        # self.write_img(roi)

        # Convert ROI to grayscale and apply threshold
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Noise removal using morphological opening
        kernel = np.ones((3,3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

        # Sure background area (dilate to increase the object boundary to background)
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        # Finding sure foreground area using distance transform
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        ret, sure_fg = cv2.threshold(dist_transform, 0.7*dist_transform.max(), 255, 0)

        # Finding unknown region
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)

        # Marker labelling
        ret, markers = cv2.connectedComponents(sure_fg)

        # Add one to all labels so that sure background is not 0, but 1
        markers = markers + 1

        # Now, mark the region of unknown with zero
        markers[unknown == 255] = 0

        # Apply watershed
        markers = cv2.watershed(roi, markers)
        roi[markers == -1] = [0, 0, 255]  # Mark watershed boundary in red

        # Replace the ROI in the original image with the processed ROI
        cv_image[y1:y2, x1:x2] = roi

        # Convert the processed image back to PIL format
        processed_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

        # Return the processed image
        return processed_image
    
    def write_img(self, img):
        """Write the image to a file."""
        filename = filedialog.asksaveasfilename(
            filetypes=[("PNG", ".png"), ("JPEG", ".jpg"), ("Tiff", ".tif")],
            initialdir=os.getcwd()
        )
        if filename:
            img.save(filename)

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

    def create_widgets(self):
        """Create the status bar and canvas widgets."""
        self.canvas = ctk.CTkCanvas(self, background="black")
        self.canvas.pack(expand=True, fill="both")

        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(side="top", pady=10)

        self.threshold_entry, self.threshold_frame = create_range_box(self.control_frame, "Threshold", 0, 255, self.threshold_value, self.update_threshold)
        self.threshold_frame.pack(side="left", padx=20, pady=10)

        self.kernel_size_entry, self.kernel_frame = create_range_box(self.control_frame, "Kernel Size", 1, 10, self.kernel_size_value, self.update_kernel_size)
        self.kernel_frame.pack(side="left", padx=20, pady=10)

        self.process_button = ctk.CTkButton(self.control_frame, text="Process ROI", command=self.process_roi_threaded)
        self.process_button.pack(side="left", padx=20, pady=(28, 0))

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


if __name__ == "__main__":
    # Set the theme of customtkinter
    ctk.set_appearance_mode("Dark")  # Options: "Light", "Dark", "System"
    ctk.set_default_color_theme("assets/style.json")  # Options include: "blue", "dark-blue", "green"

    app = Application()
    # Run c profile
    # cProfile.run("app.mainloop()", sort="cumulative")
    app.mainloop()
