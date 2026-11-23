import functools
import os
import tkinter as tk
import tkinter.font

from browser import URL, lex
from utils.text import Text

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
SCROLLBAR_WIDTH = 10

# the openmoji folder is in the project root, one folder up from GUI/
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMOJI_DIR = os.path.join(PROJECT_DIR, "openmoji")
VARIATION_SELECTOR = "\ufe0f"


@functools.lru_cache(maxsize=None)
def emoji_path(word):
    """Path of the emoji image if word is a single emoji character, else None.

    Cached, because it's asked again for the same words on every redraw.
    """
    # only a one-character word can be an emoji image, and plain ASCII is
    # never an emoji (OpenMoji even has an image for "-")
    if len(word) != 1 or ord(word) < 128:
        return None
    path = os.path.join(EMOJI_DIR, f"{ord(word):04X}.png")
    return path if os.path.exists(path) else None


class Browser:
    def __init__(self):
        self.scroll = 0
        # current canvas size; starts at the defaults, updated on resize
        self.width, self.height = WIDTH, HEIGHT
        # the page's tokens (from lex) and its laid-out words; empty until load()
        self.tokens = []
        self.display_list = []
        # loaded emoji images, by file path. Keeping them here also keeps them
        # alive: Tk deletes an image once Python no longer references it.
        self.images = {}
        self.window = tk.Tk()
        self.canvas = tk.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.on_mouse_wheel)
        self.window.bind("<TouchpadScroll>", self.on_touchpad_scroll)
        self.window.bind("<Button-4>", self.scroll_up)
        self.window.bind("<Button-5>", self.scroll_down)
        self.canvas.bind("<Configure>", self.on_resize)

    def doc_height(self):
        """Height of the whole page: down to the bottom of its last line."""
        if not self.display_list:
            return 0
        # the last word's top, plus the height of a line in its font
        _, y, _, font = self.display_list[-1]
        return y + font.metrics("linespace")

    def clamp_scroll(self):
        # furthest down you can go: the last line just reaches the bottom edge.
        # if the page is shorter than the window, that's 0 (no scrolling at all).
        max_scroll = max(0, self.doc_height() - self.height)
        self.scroll = min(max(0, self.scroll), max_scroll)

    def draw(self):
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            # skip words below or above the visible part of the page
            if y > self.scroll + self.height:
                continue
            if y + font.metrics("linespace") < self.scroll:
                continue
            path = emoji_path(word)
            if path:
                self.canvas.create_image(
                    x, y - self.scroll, image=self.get_image(path), anchor="nw"
                )
            else:
                self.canvas.create_text(
                    x, y - self.scroll, text=word, font=font, anchor="nw"
                )
        self.draw_scrollbar()

    def get_image(self, path):
        # load each emoji from disk only once, then reuse it
        if path not in self.images:
            self.images[path] = tk.PhotoImage(file=path)
        return self.images[path]

    def draw_scrollbar(self):
        doc_height = self.doc_height()
        if doc_height <= self.height:
            return  # the whole page fits on screen: no scrollbar
        # the bar is to the window what the visible part is to the whole page:
        # its top/bottom are the visible part's top/bottom, scaled down by
        # (window height / page height)
        top = self.scroll / doc_height * self.height
        bottom = (self.scroll + self.height) / doc_height * self.height
        self.canvas.create_rectangle(
            self.width - SCROLLBAR_WIDTH,
            top,
            self.width,
            bottom,
            fill="blue",
            outline="",
        )

    def scroll_by(self, amount):
        # positive amount scrolls down the page, negative scrolls up
        self.scroll += amount
        self.clamp_scroll()  # never above the top or past the last line
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
        # leave room at the right edge for the scrollbar
        self.display_list = layout(self.tokens, self.width - SCROLLBAR_WIDTH)
        # a taller window or a re-wrapped page can move the bottom limit
        self.clamp_scroll()
        self.draw()

    def load(self, url):
        body = url.request()
        self.tokens = lex(body)
        self.display_list = layout(self.tokens, self.width - SCROLLBAR_WIDTH)
        self.draw()


def layout(tokens, width):
    """Place each word of the page; return a list of (x, y, word, font).

    draw() uses the font stored with each word, so the widths measured here
    match what appears on screen.
    """
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    weight, style = "normal", "roman"
    for tok in tokens:
        if not isinstance(tok, Text):
            if tok.tag == "i":
                style = "italic"
            elif tok.tag == "/i":
                style = "roman"
            elif tok.tag == "b":
                weight = "bold"
            elif tok.tag == "/b":
                weight = "normal"
        else:
            for word in tok.text.split():
                font = tk.font.Font(size=16, weight=weight, slant=style)
                word = word.replace(VARIATION_SELECTOR, "")
                if not word:
                    continue
                w = font.measure(word)
                if cursor_x + w >= width - HSTEP:
                    cursor_x = HSTEP
                    cursor_y += font.metrics("linespace") * 1.5
                display_list.append((cursor_x, cursor_y, word, font))
                cursor_x += w + font.measure(" ")
    return display_list


if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tk.mainloop()
