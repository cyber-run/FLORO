import tkinter as tk
from tkinter import ttk
import sv_ttk


class CustomTreeview(ttk.Treeview):
    def __init__(self, parent, columns, headings, data=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.columns = columns
        self.headings = headings
        self.data = data

        self.configure_treeview()
        self.create_columns()
        self.create_headings()
        if self.data:
            self.insert_data()

        self.bind("<BackSpace>", self.delete_selected_row)
        self.bind("<Double-1>", self.on_double_click)

        # Set the theme to "Sun Valley"
        sv_ttk.set_theme("dark")

    def configure_treeview(self):
        self.pack(expand=True, fill="both")
        self["columns"] = self.columns
        self["show"] = "headings"  # Hide the first empty column

    def create_columns(self):
        for column in self.columns:
            self.column(column, width=150, minwidth=150, anchor="center")

    def create_headings(self):
        for column, heading in zip(self.columns, self.headings):
            self.heading(column, text=heading, anchor="center")

    def insert_data(self):
        for row in self.data:
            self.insert(parent="", index="end", values=row)

    def delete_selected_row(self, event):
        selected_item = self.selection()
        if selected_item:
            roi_id = self.set(selected_item, "#1")
            self.master.master.master.delete_roi(int(roi_id))

    def on_double_click(self, event):
        region = self.identify("region", event.x, event.y)
        if region == "cell":
            column = self.identify_column(event.x)
            if column == "#2":  # Assuming "Name" is the second column
                item = self.identify_row(event.y)
                self.edit_cell(item, column)

    def edit_cell(self, item, column):
        # Create an entry widget to edit the cell
        entry = ttk.Entry(self, style="Custom.TEntry")
        entry.place(x=self.bbox(item, column)[0], y=self.bbox(item, column)[1],
                    width=self.column(column, "width"), height=self.bbox(item, column)[3])

        # Set the initial value of the entry widget
        entry.insert(0, self.set(item, column))

        # Bind the entry widget to handle the editing process
        entry.bind("<FocusOut>", lambda e: self.update_cell(item, column, entry))
        entry.bind("<Return>", lambda e: self.update_cell(item, column, entry))

        entry.focus_set()

    def update_cell(self, item, column, entry):
        # Get the new value from the entry widget
        new_value = entry.get()

        # Update the cell value in the treeview
        self.set(item, column, new_value)

        # Destroy the entry widget
        entry.destroy()

        # Redraw the treeview to ensure the cell returns to normal appearance
        self.update()

        # Set focus back to the treeview
        self.focus_set()

        # Call the method in the Application class to update the drug name in the database
        if column == "#2":  # Assuming "Drug Name" is the second column
            roi_id = self.set(item, "#1")  # Get the ROI ID from the first column
            self.master.master.master.update_drug_name(roi_id, new_value)

if __name__ == "__main__":
    # Create the main window
    window = tk.Tk()
    window.title("Treeview with Sun Valley Theme")

    # Define the columns and headings
    columns = ("ID", "Name", "No. of wells")
    headings = ("ID", "Name", "No. of wells")

    # Sample data
    data = [
        (1, "John", 5),
        (2, "Emily", 3),
        (3, "Michael", 7)
    ]

    # Create a CustomTreeview widget
    treeview = CustomTreeview(window, columns, headings, data)

    # Apply custom style to the entry widget
    style = ttk.Style(window)
    style.configure("Custom.TEntry", fieldbackground="white", bordercolor="gray", borderwidth=1)

    # Set the row height using the style
    style.configure("Treeview", rowheight=30)

    # Start the main event loop
    window.mainloop()