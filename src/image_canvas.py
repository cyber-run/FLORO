from PIL import Image, ImageTk
import customtkinter as ctk
import numpy as np


class ImageCanvas(ctk.CTkCanvas):
    def __init__(self, master, frontend, **kwargs):
        super().__init__(master, **kwargs)
        self.frontend = frontend
        self.pil_image = None
        self.roi_start = None
        self.roi_end = None
        self.is_drawing_roi = False
        self.mat_affine = np.eye(3)

        self.bind("<Button-1>", self.mouse_down_left)
        self.bind("<B1-Motion>", self.mouse_move_left)
        self.bind("<Motion>", self.mouse_move)
        self.bind("<Double-Button-1>", self.mouse_double_click_left)
        self.bind("<ButtonRelease-1>", self.mouse_up_left)
        self.bind("<MouseWheel>", self.mouse_wheel)

    def set_image(self, pil_image):
        self.pil_image = pil_image
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.draw_image()

    def mouse_down_left(self, event):
        self.__old_event = event
        if event.state & 0x0004:  # Check if Ctrl key is pressed
            self.roi_start = self.to_image_point(event.x, event.y)
            self.roi_end = None
            self.is_drawing_roi = True
        else:
            self.is_drawing_roi = False

    def mouse_move_left(self, event):
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
        if self.is_drawing_roi:
            self.roi_end = self.to_image_point(event.x, event.y)
            self.is_drawing_roi = False
            self.draw_image()


    def mouse_move(self, event):
        if self.pil_image is None:
            return

        image_point = self.to_image_point(event.x, event.y)
        if len(image_point) > 0:
            self.frontend.update_pixel_coordinates(f"({image_point[0]:.2f}, {image_point[1]:.2f})")
        else:
            self.frontend.update_pixel_coordinates("(--, --)")

    def mouse_double_click_left(self, event):
        if self.pil_image is None:
            return
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.draw_image()

    def mouse_wheel(self, event):
        if self.pil_image is None:
            return

        if event.delta < 0:
            self.scale_at(1.25, event.x, event.y)
        else:
            self.scale_at(0.8, event.x, event.y)
        self.draw_image()

    def reset_transform(self):
        self.mat_affine = np.eye(3)

    def translate(self, offset_x, offset_y):
        mat = np.eye(3)
        mat[0, 2] = float(offset_x)
        mat[1, 2] = float(offset_y)

        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale(self, scale: float):
        mat = np.eye(3)
        mat[0, 0] = scale
        mat[1, 1] = scale

        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale_at(self, scale: float, cx: float, cy: float):
        self.translate(-cx, -cy)
        self.scale(scale)
        self.translate(cx, cy)

    def zoom_fit(self, image_width, image_height):
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

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
        canvas_point = np.dot(self.mat_affine, (x, y, 1.))
        return canvas_point[:2]

    def draw_image(self):
        self.delete("all")

        if self.pil_image is None:
            return

        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

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

        self.image = ImageTk.PhotoImage(image=dst)
        self.create_image(0, 0, anchor="nw", image=self.image)

        if self.roi_start is not None and self.roi_end is not None and len(self.roi_start) > 0 and len(self.roi_end) > 0:
            # Clamp ROI coordinates to image boundaries
            x1 = max(0, min(self.roi_start[0], self.pil_image.width))
            y1 = max(0, min(self.roi_start[1], self.pil_image.height))
            x2 = max(0, min(self.roi_end[0], self.pil_image.width))
            y2 = max(0, min(self.roi_end[1], self.pil_image.height))

            roi_start_canvas = self.to_canvas_point(x1, y1)
            roi_end_canvas = self.to_canvas_point(x2, y2)
            self.create_rectangle(
                roi_start_canvas[0],
                roi_start_canvas[1],
                roi_end_canvas[0],
                roi_end_canvas[1],
                outline="red",
                width=2,
            )
