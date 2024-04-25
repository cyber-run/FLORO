import cv2
import numpy as np
import customtkinter as ctk
from tkinter import Tk, PhotoImage
from PIL import Image, ImageTk

class ImageProcessorGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Processing GUI with customtkinter")

        # Set the theme of customtkinter
        ctk.set_appearance_mode("Dark")  # Options: "Light", "Dark", "System"
        ctk.set_default_color_theme("assets/style.json")  # Options include: "blue", "dark-blue", "green"

        # Load and resize the image
        self.image_path = 'assets/array.jpg'
        self.img = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)

        # Initial values
        self.threshold_value = 16
        self.kernel_size_value = 3

        self.control_frame = ctk.CTkFrame(master)
        self.control_frame.pack(side="top", pady=10)

        # Custom slider for Threshold
        self.threshold_entry, self.threshold_frame = self.RangeBox(self.control_frame, "Threshold", 0, 255, self.threshold_value, self.update_threshold)
        self.threshold_frame.pack(side="left", padx=20, pady=10)

        # Custom slider for Kernel Size
        self.kernel_size_entry, self.kernel_frame = self.RangeBox(self.control_frame, "Kernel Size", 1, 10, self.kernel_size_value, self.update_kernel_size)
        self.kernel_frame.pack(side="left", padx=20, pady=10)

        # Update button
        self.update_button = ctk.CTkButton(self.control_frame, text="Update Image", command=self.update_image)
        self.update_button.pack(side="left",padx=20, pady=(28,0))

        # Initialize the image processing to display initial image
        self.update_image()

    def RangeBox(self, master, label, from_, to_, initial, command):
        """Create a increment range box widget with text entry and +/- buttons."""
        frame = ctk.CTkFrame(master, fg_color="transparent")

        ctk.CTkLabel(frame, text=label).pack(side="top")

        decrement_button = ctk.CTkButton(frame, text="-", width=30, command=lambda: command(entry, -1, from_))
        decrement_button.pack(side="left")

        entry = ctk.CTkEntry(frame, width=120)
        entry.insert(0, str(initial))
        entry.pack(side="left", padx=(10, 0))

        increment_button = ctk.CTkButton(frame, text="+", width=30, command=lambda: command(entry, 1, to_))
        increment_button.pack(side="left", padx=(10, 0))

        return entry, frame

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

    def process_image(self) -> PhotoImage:
        """Apply thresholding and morphological operations to the image, resizing for display."""
        _, thresh = cv2.threshold(self.img, self.threshold_value, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.kernel_size_value, self.kernel_size_value))
        processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        pil_image = Image.fromarray(cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB))
        return ImageTk.PhotoImage(pil_image)

    def update_image(self):
        """Update the image display based on the current settings."""
        self.display_image = self.process_image()
        self.image_label.configure(image=self.display_image)

# Main application
root = ctk.CTk(fg_color="#151518")
app = ImageProcessorGUI(root)
root.mainloop()
