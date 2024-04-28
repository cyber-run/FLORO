from PIL import Image, ImageTk
import customtkinter as ctk
import numpy as np


class ImageCanvas(ctk.CTkCanvas):
    def __init__(self, master, frontend, **kwargs):
        super().__init__(master, **kwargs)
        self.frontend = frontend
        self.pil_image = None
        self.rois = []
        self.current_roi = None
        self.is_drawing_roi = False
        self.mat_affine = np.eye(3)
        self.selected_roi_index = None

        self.roi_colour = "#223BC9"
        self.hover_colour = "#067FD0"
        self.selected_colour = "#E63B60"

        self.bind("<Button-1>", self.mouse_down_left)
        self.bind("<B1-Motion>", self.mouse_move_left)
        self.bind("<Double-Button-1>", self.mouse_double_click_left)
        self.bind("<ButtonRelease-1>", self.mouse_up_left)
        self.bind("<MouseWheel>", self.mouse_wheel)
        self.bind("<BackSpace>", self.delete_selected_roi)

    def set_image(self, pil_image):
        self.pil_image = pil_image
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.draw_image()

    def mouse_down_left(self, event):
        self.__old_event = event
        if event.state & 0x0004:  # Check if Ctrl key is pressed
            start_point = self.to_image_point(event.x, event.y)
            if len(start_point) > 0:
                self.current_roi = {"start": self.to_image_point(event.x, event.y), "end": None}
                self.is_drawing_roi = True
        else:
            self.is_drawing_roi = False

    def mouse_move_left(self, event):
        if self.pil_image is None:
            return
        if self.is_drawing_roi:
            end_point = self.to_image_point(event.x, event.y)
            if len(end_point) > 0:
                self.current_roi["end"] = self.to_image_point(event.x, event.y)
                self.draw_image()
                self.draw_current_roi()  # Add this line to draw the current ROI being drawn
        else:
            try:
                self.translate(event.x - self.__old_event.x, event.y - self.__old_event.y)
                self.draw_image()
            except AttributeError:
                pass
        self.__old_event = event

    def mouse_up_left(self, event):
        if self.is_drawing_roi:
            end_point = self.to_image_point(event.x, event.y)
            if len(end_point) > 0:
                self.current_roi["end"] = end_point
                self.rois.append(self.current_roi)
                self.update_roi_table()
            self.is_drawing_roi = False
            self.draw_image()

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
        self.delete("current_roi")  # Add this line to remove the previous current ROI

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

        for index, roi in enumerate(self.rois):
            if roi["start"] is not None and roi["end"] is not None and len(roi["start"]) > 0 and len(roi["end"]) > 0:
                x1 = max(0, min(roi["start"][0], self.pil_image.width))
                y1 = max(0, min(roi["start"][1], self.pil_image.height))
                x2 = max(0, min(roi["end"][0], self.pil_image.width))
                y2 = max(0, min(roi["end"][1], self.pil_image.height))

                roi_start_canvas = self.to_canvas_point(x1, y1)
                roi_end_canvas = self.to_canvas_point(x2, y2)

                color = self.selected_colour if index == self.selected_roi_index else self.roi_colour
                self.create_rectangle(
                    roi_start_canvas[0],
                    roi_start_canvas[1],
                    roi_end_canvas[0],
                    roi_end_canvas[1],
                    outline=color,
                    width=2,
                    tags=f"roi_{index}"
                )

                self.tag_bind(f"roi_{index}", "<Enter>", lambda event, i=index: self.on_roi_hover(i))
                self.tag_bind(f"roi_{index}", "<Leave>", lambda event, i=index: self.on_roi_leave(i))
                self.tag_bind(f"roi_{index}", "<Button-1>", lambda event, i=index: self.on_roi_click(i))

    def update_roi_table(self):
        self.frontend.roi_table.delete(*self.frontend.roi_table.get_children())
        for index, roi in enumerate(self.rois, start=1):
            if roi["start"] is not None and roi["end"] is not None and len(roi["start"]) >= 2 and len(roi["end"]) >= 2:
                start_x, start_y = roi["start"][:2]
                end_x, end_y = roi["end"][:2]
                self.frontend.roi_table.insert(parent="", index="end", values=(index, f"({start_x:.2f}, {start_y:.2f})"))

    def draw_current_roi(self):
        if self.current_roi is not None:
            start_x, start_y = self.current_roi["start"][:2]
            end_x, end_y = self.current_roi["end"][:2]

            x1 = max(0, min(start_x, self.pil_image.width))
            y1 = max(0, min(start_y, self.pil_image.height))
            x2 = max(0, min(end_x, self.pil_image.width))
            y2 = max(0, min(end_y, self.pil_image.height))

            roi_start_canvas = self.to_canvas_point(x1, y1)
            roi_end_canvas = self.to_canvas_point(x2, y2)
            self.create_rectangle(
                roi_start_canvas[0],
                roi_start_canvas[1],
                roi_end_canvas[0],
                roi_end_canvas[1],
                outline=self.roi_colour,
                width=2,
                tags="current_roi"
            )

    def on_roi_hover(self, index):
        self.itemconfig(f"roi_{index}", outline=self.hover_colour)

    def on_roi_leave(self, index):
        if index != self.selected_roi_index:
            self.itemconfig(f"roi_{index}", outline=self.roi_colour)

    def on_roi_click(self, index):
        if self.selected_roi_index is not None:
            self.itemconfig(f"roi_{self.selected_roi_index}", outline=self.roi_colour)
        self.selected_roi_index = index
        self.itemconfig(f"roi_{index}", outline=self.selected_colour)

    def delete_selected_roi(self, event):
        if self.selected_roi_index is not None and self.selected_roi_index < len(self.rois):
            self.rois.pop(self.selected_roi_index)
            self.selected_roi_index = None
            self.draw_image()
            self.update_roi_table()