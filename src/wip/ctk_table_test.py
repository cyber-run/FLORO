import customtkinter
from CTkTable import *

root = customtkinter.CTk()

row_nums = []
deleted_values = []

def show(cell):
    if cell["row"] not in row_nums:
        table.select_row(cell["row"])
        row_nums.append(cell["row"])
        deleted_values.append(table.get_row(cell["row"]))
    else:
        table.deselect_row(cell["row"])
        row_nums.remove(cell["row"])
        deleted_values.remove(table.get_row(cell["row"]))

def delete():
    global row_nums
    if len(row_nums) == 0:
        return
    else:
        table.delete_rows(row_nums)
        row_nums = []
    print(deleted_values)
    
value = [["A","B","C","D","E"],[1,2,3,4,5],[0,0,0,0,0],[1,2,0,0,0],[1,2,3,4,5]]

table = CTkTable(master=root, row=5, column=5, values=value, command=show, corner_radius=5)
table.pack(expand=True, fill="both", padx=20, pady=20)
    
btn = customtkinter.CTkButton(root, text='Delete', width=150, command=delete)
btn.pack(expand=True,pady=5, padx=5)
root.mainloop()