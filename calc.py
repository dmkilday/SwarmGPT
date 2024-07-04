import tkinter as tk

# Create the main application window
root = tk.Tk()
root.title("Python Calculator")

# Function to update the input field whenever a number is pressed
def press(num):
    current = entry.get()
    entry.delete(0, tk.END)
    entry.insert(0, str(current) + str(num))

# Function to evaluate the final expression
def equalpress():
    try:
        total = str(eval(entry.get()))
        entry.delete(0, tk.END)
        entry.insert(0, total)
    except:
        entry.delete(0, tk.END)
        entry.insert(0, "Error")

# Function to clear the input field
def clear():
    entry.delete(0, tk.END)

# Create the text entry box for showing the expression.
entry = tk.Entry(root)
entry.grid(row=0, column=0, columnspan=4, ipady=20)

# Create the calculator buttons
buttons = [
    '7', '8', '9', '/',
    '4', '5', '6', '*',
    '1', '2', '3', '-',
    'C', '0', '=', '+',
]

row_val, col_val = 1, 0
for button in buttons:
    action = lambda x=button: press(x) if x not in ['C', '='] else equalpress() if x == '=' else clear()
    tk.Button(root, text=button, command=action, height=3, width=9).grid(row=row_val, column=col_val)
    col_val += 1
    if col_val > 3:
        col_val = 0
        row_val += 1

# Start the GUI event loop
root.mainloop()