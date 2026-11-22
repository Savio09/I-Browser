import tkinter as tk

from browser import URL, lex

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
# a newline moves down more than a normal line, to suggest paragraph breaks
NEWLINE_STEP = int(VSTEP * 1.5)
SCROLL_STEP = 100


class Browser:
    def __init__(self):
        self.scroll = 0
        self.window = tk.Tk()
        self.canvas = tk.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)

    def draw(self):
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scroll_down(self, event):
        self.scroll += SCROLL_STEP
        self.canvas.delete("all")
        self.draw()

    def scroll_up(self, event):
        self.scroll -= SCROLL_STEP
        if self.scroll < 0:
            self.scroll = 0
        self.canvas.delete("all")
        self.draw()

    def load(self, url):
        # fetch the page with browser.py, strip the tags, then draw the text
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()


def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == "\n":
            # end the current line: back to the left edge, one step down
            cursor_x = HSTEP
            cursor_y += NEWLINE_STEP
            continue  # nothing to draw, and don't move cursor_x forward
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP

        if cursor_x >= WIDTH - HSTEP:
            cursor_x = HSTEP
            cursor_y += VSTEP
    return display_list


if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tk.mainloop()
