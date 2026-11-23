import tkinter as tk
import tkinter.font

window = tk.Tk()
bi_times = tk.font.Font(family="Times", size=16, weight="bold", slant="italic")

canvas = tk.Canvas(
    window,
    width=800,
    height=600,
    highlightthickness=0,
)
canvas.pack(fill=tk.BOTH, expand=True)

font1 = tk.font.Font(family="Times", size=16)
font2 = tk.font.Font(family="Times", size=16, slant="italic")


x, y = 200, 200

canvas.create_text(x, y, text="Hello, ", font=bi_times)
x += font1.measure("Hello, ")
canvas.create_text(x, y, text="Overlapping", font=font2)

tk.mainloop()
