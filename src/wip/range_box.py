from typing import Tuple
import customtkinter as ctk

def update_entry(entry: ctk.CTkEntry, delta: int, boundary: int) -> None:
    """Update the entry based on the delta and boundary constraints."""
    current_value = int(entry.get())
    new_value = current_value + delta
    if (delta > 0 and new_value <= boundary) or (delta < 0 and new_value >= boundary):
        entry.delete(0, "end")
        entry.insert(0, str(new_value))

def create_range_box(master: ctk.CTk, label: str, from_: int, to_: int, initial: int, command) -> Tuple[ctk.CTkEntry, ctk.CTkFrame]:
    """Create a increment range box widget with text entry and +/- buttons.

    Args:
        master (ctk.CTk): The parent widget.
        label (str): The label text for the widget.
        from_ (int): The minimum value allowed.
        to_ (int): The maximum value allowed.
        initial (int): The initial value.
        command (function): The command to execute on button press.

    Returns:
        Tuple[ctk.CTkEntry, ctk.CTkFrame]: A tuple containing the entry and the frame widgets.
    """
    frame = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(frame, text=label).pack(side="top")

    decrement_button = ctk.CTkButton(frame, text="-", width=30, command=lambda: update_entry(entry, -1, from_))
    decrement_button.pack(side="left")

    entry = ctk.CTkEntry(frame, width=120)
    entry.insert(0, str(initial))
    entry.pack(side="left", padx=(10, 0))

    increment_button = ctk.CTkButton(frame, text="+", width=30, command=lambda: update_entry(entry, 1, to_))
    increment_button.pack(side="left", padx=(10, 0))

    return entry, frame
