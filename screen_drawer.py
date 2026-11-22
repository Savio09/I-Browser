import tkinter as tk

from browser import URL, lex

WIDTH, HEIGHT = 800, 600


class Browser:
    def __init__(self):
        self.window = tk.Tk()
        self.canvas = tk.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

    def load(self, url):
        # fetch the page with browser.py, strip the tags, then draw the text
        body = url.request()
        text = lex(body)
        for c in text:
            self.canvas.create_text(100, 100, text=c)


if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tk.mainloop()
