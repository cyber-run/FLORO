from PIL import Image, ImageTk
import customtkinter as ctk
import numpy as np


class ImageCanvas(ctk.CTkCanvas):
    '''
    Custom Canvas widget to display an image and draw ROIs on it.
    '''
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

        self._bind_events()

    def set_image(self, pil_image):
        '''
        Set the image to be displayed on the canvas.
        '''
        self.pil_image = pil_image
        self._zoom_fit(self.pil_image.width, self.pil_image.height)
        self._draw_image()

    def _bind_events(self):
        '''
        Bind ui input events to functions
        '''
        self.bind("<Button-1>", self._mouse_down_left)
        self.bind("<B1-Motion>", self._mouse_move_left)
        self.bind("<ButtonRelease-1>", self._mouse_up_left)
        self.bind("<Double-Button-1>", self._mouse_double_left)
        self.bind("<MouseWheel>", self._mouse_wheel)

    def _delete_selected_roi(self, _):
        '''
        Delete the selected ROI on Backspace key press.
        '''
        if self.selected_roi_index is not None and self.selected_roi_index < len(self.rois):
            print(f"Deleting ROI: {self.current_roi}")
            self.master.master.delete_roi(self.current_roi)
            del self.rois[self.selected_roi_index]  # Remove the ROI from the rois list
            self.selected_roi_index = None
            self._draw_image()

    def _draw_image(self):
        '''
        Draw the image on the canvas and the ROIs on the image.
        '''
        # Check if an image is loaded
        if self.pil_image is None:
            return
        
        # Delete all items on curr canvas to be redrawn on transformed
        self.delete("all")

        # Get the canvas size
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

        # Transform the image
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

        # Display the tranformed image
        self.image = ImageTk.PhotoImage(image=dst)
        self.create_image(0, 0, anchor="nw", image=self.image)

        # Redraw the ROIs for transformed image
        self._draw_all_rois()

    def _draw_all_rois(self):
        '''
        Draw all the ROIs on the canvas.
        '''
        for index, roi in enumerate(self.rois):
            if roi["start"] is not None and roi["end"] is not None and len(roi["start"]) > 0 and len(roi["end"]) > 0:
                x1 = max(0, min(roi["start"][0], self.pil_image.width))
                y1 = max(0, min(roi["start"][1], self.pil_image.height))
                x2 = max(0, min(roi["end"][0], self.pil_image.width))
                y2 = max(0, min(roi["end"][1], self.pil_image.height))

                roi_start_canvas = self._to_canvas_point(x1, y1)
                roi_end_canvas = self._to_canvas_point(x2, y2)

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

                self.tag_bind(f"roi_{index}", "<Enter>", lambda event, i=index: self._on_roi_hover(i))
                self.tag_bind(f"roi_{index}", "<Leave>", lambda event, i=index: self._on_roi_leave(i))
                self.tag_bind(f"roi_{index}", "<Button-1>", lambda event, i=index: self._on_roi_click(i))

    def _draw_current_roi(self):
        '''
        Draw the current ROI being drawn on the canvas.
        '''
        # Check if the current ROI is not None
        if self.current_roi is not None:
            start_x, start_y = self.current_roi["start"][:2]
            end_x, end_y = self.current_roi["end"][:2]

            x1 = max(0, min(start_x, self.pil_image.width))
            y1 = max(0, min(start_y, self.pil_image.height))
            x2 = max(0, min(end_x, self.pil_image.width))
            y2 = max(0, min(end_y, self.pil_image.height))

            roi_start_canvas = self._to_canvas_point(x1, y1)
            roi_end_canvas = self._to_canvas_point(x2, y2)
            self.create_rectangle(
                roi_start_canvas[0],
                roi_start_canvas[1],
                roi_end_canvas[0],
                roi_end_canvas[1],
                outline=self.roi_colour,
                width=2,
                tags="current_roi"
            )

    def _on_roi_hover(self, index):
        '''
        Change the colour of the ROI to the hover colour if the ROI is not selected.
        '''
        self.itemconfig(f"roi_{index}", outline=self.hover_colour)

    def _on_roi_leave(self, index):
        '''
        Change the colour of the ROI back to the ROI colour if the ROI is not selected.
        '''
        if index != self.selected_roi_index:
            self.itemconfig(f"roi_{index}", outline=self.roi_colour)

    def _on_roi_click(self, index):
        '''
        Change the colour of the selected ROI to the selected colour and 
        change the colour of the previously selected ROI to the ROI colour.
        '''
        if self.selected_roi_index is not None:
            self.itemconfig(f"roi_{self.selected_roi_index}", outline=self.roi_colour)
        self.selected_roi_index = index
        self.itemconfig(f"roi_{index}", outline=self.selected_colour)

    def _mouse_down_left(self, event):
        '''
        If the Ctrl key is pressed, start the ROI drawing process.
        '''
        # Capture and save current mouse position (event) for translation
        self.__old_event = event

        # Check if Ctrl key is pressed
        if event.state & 0x0004:

            # Get the start point of the ROI being drawn (current x,y position of the mouse)
            start_point = self._to_image_point(event.x, event.y)

            # If the start point is valid, start the ROI drawing process
            if len(start_point) > 0:
                self.current_roi = {"start": self._to_image_point(event.x, event.y), "end": None}
                self.is_drawing_roi = True
        else:
            self.is_drawing_roi = False

    def _mouse_move_left(self, event):
        '''
        If the Ctrl key is pressed, draw the ROI being drawn on the canvas.
        Else translate the image.
        '''
        # Check if an image is loaded
        if self.pil_image is None:
            return
        # Check if the Ctrl key is pressed
        if self.is_drawing_roi:
            # Get current end point of the ROI being drawn (current x,y position of the mouse)
            end_point = self._to_image_point(event.x, event.y)
            # If the end point is valid, update the current ROI being drawn
            if len(end_point) > 0:
                # Update the end point of the current ROI being drawn
                self.current_roi["end"] = self._to_image_point(event.x, event.y)
                # Redraw the image
                self._draw_image()
                self._draw_current_roi()  # Add this line to draw the current ROI being drawn
        else:
            try:
                # Translate the image
                self._translate(event.x - self.__old_event.x, event.y - self.__old_event.y)
                self._draw_image()
            except AttributeError:
                pass
        self.__old_event = event

    def _mouse_up_left(self, event):
        '''
        If the Ctrl key is pressed, stop ROI drawing process.
        '''
        if self.is_drawing_roi:
            end_point = self._to_image_point(event.x, event.y)
            if len(end_point) > 0:
                self.current_roi["end"] = end_point
                self.rois.append(self.current_roi)
                self._draw_image()

            # Save current ROI to the database
            self.master.master.add_roi(self.current_roi)
            self.is_drawing_roi = False

    def _mouse_double_left(self, _):
        '''
        Reset the zoom and pan of the image on double click.
        '''
        if self.pil_image is None:
            return
        self._zoom_fit(self.pil_image.width, self.pil_image.height)
        self._draw_image()

    def _mouse_wheel(self, event):
        '''
        Zoom in or out the image.
        '''
        if self.pil_image is None:
            return

        if event.delta < 0:
            self._scale_at(1.25, event.x, event.y)
        else:
            self._scale_at(0.8, event.x, event.y)
        self._draw_image()

    def _translate(self, offset_x, offset_y):
        '''
        Translate the image.
        '''
        mat = np.eye(3)
        mat[0, 2] = float(offset_x)
        mat[1, 2] = float(offset_y)

        self.mat_affine = np.dot(mat, self.mat_affine)

    def _scale(self, scale: float):
        '''
        Scale the image.
        '''
        mat = np.eye(3)
        mat[0, 0] = scale
        mat[1, 1] = scale

        self.mat_affine = np.dot(mat, self.mat_affine)

    def _scale_at(self, scale: float, cx: float, cy: float):
        '''
        Scale the image at a specific point.
        '''
        self._translate(-cx, -cy)
        self._scale(scale)
        self._translate(cx, cy)

    def _zoom_fit(self, image_width, image_height):
        '''
        Zoom the image to fit the canvas size. (called on image load and double click)
        '''
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

        if (image_width * image_height <= 0) or (canvas_width * canvas_height <= 0):
            return

        # Reset the affine matrix and transform values
        self.mat_affine = np.eye(3)        
        scale = 1.0
        offsetx = 0.0
        offsety = 0.0

        if (canvas_width * image_height) > (image_width * canvas_height):
            scale = canvas_height / image_height
            offsetx = (canvas_width - image_width * scale) / 2
        else:
            scale = canvas_width / image_width
            offsety = (canvas_height - image_height * scale) / 2

        self._scale(scale)
        self._translate(offsetx, offsety)

    def _to_image_point(self, x, y):
        '''
        Convert canvas point to image point.
        '''
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

    def _to_canvas_point(self, x, y):
        '''
        Convert image point to canvas point.
        '''
        canvas_point = np.dot(self.mat_affine, (x, y, 1.))
        return canvas_point[:2] 