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
        # current canvas size; starts at the defaults, updated on resize
        self.width, self.height = WIDTH, HEIGHT
        # page text and its laid-out characters; empty until load() runs
        self.text = ""
        self.display_list = []
        self.window = tk.Tk()
        self.canvas = tk.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        # mouse wheel on macOS and Windows (and Linux with Tk 9)
        self.window.bind("<MouseWheel>", self.on_mouse_wheel)
        # trackpad two-finger scrolling (Tk 9 and later, macOS and Windows)
        self.window.bind("<TouchpadScroll>", self.on_touchpad_scroll)
        # mouse wheel on Linux with Tk 8.6, which reports it as buttons 4 and 5
        self.window.bind("<Button-4>", self.scroll_up)
        self.window.bind("<Button-5>", self.scroll_down)
        self.canvas.bind("<Configure>", self.on_resize)

    def draw(self):
        for x, y, c in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scroll_by(self, amount):
        # positive amount scrolls down the page, negative scrolls up
        self.scroll = max(0, self.scroll + amount)  # never above the top
        self.canvas.delete("all")
        self.draw()

    def scroll_down(self, event):
        self.scroll_by(SCROLL_STEP)

    def scroll_up(self, event):
        self.scroll_by(-SCROLL_STEP)

    def on_mouse_wheel(self, event):
        self.scroll_by(-event.delta * SCROLL_STEP / 120)

    def on_touchpad_scroll(self, event):
        low = event.delta & 0xFFFF
        delta_y = low - 0x10000 if low >= 0x8000 else low
        self.scroll_by(-delta_y)

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self.display_list = layout(self.text, self.width)
        self.canvas.delete("all")
        self.draw()

    def load(self, url):
        # fetch the page with browser.py, strip the tags, then draw the text
        body = url.request()
        # keep the text so it can be laid out again when the window is resized
        self.text = lex(body)
        self.display_list = layout(self.text, self.width)
        self.draw()


def layout(text, width):
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

        if cursor_x >= width - HSTEP:
            cursor_x = HSTEP
            cursor_y += VSTEP
    return display_list


if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tk.mainloop()
