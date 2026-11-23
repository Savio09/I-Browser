import tkinter
import tkinter.font

from utils.text import Text

HSTEP, VSTEP = 13, 18
# invisible "show this as emoji" marker that follows some emoji
VARIATION_SELECTOR = "\ufe0f"

# fonts already made, keyed by (size, weight, style).
# each value is (font, label); the label makes font.metrics() much faster.
FONTS = {}


def get_font(size, weight, style):
    """Return the font for this size/weight/style, making it only the first time."""
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Layout:
    """Places each word of a page; the result is in display_list.

    display_list holds (x, y, word, font). draw() uses the font stored with
    each word, so the widths measured here match what appears on screen.
    """

    def __init__(self, tokens, width):
        self.display_list = []
        # lines wrap before they reach this width (the space left for text)
        self.width = width
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        # words on the current line, as (x, word, font). They get their y,
        # and go into display_list, when flush() ends the line.
        self.line = []
        for tok in tokens:
            self.token(tok)
        # place whatever is left on the last line
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        word = word.replace(VARIATION_SELECTOR, "")
        if not word:
            return
        w = font.measure(word)
        # the word doesn't fit: finish this line, so the word starts the next
        if self.cursor_x + w >= self.width - HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y += 1.5 * (max_ascent + max_descent)
        self.cursor_x = HSTEP
        self.line = []
