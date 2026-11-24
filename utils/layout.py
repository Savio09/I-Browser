import tkinter
import tkinter.font

from utils.text import Text

HSTEP, VSTEP = 13, 18
# invisible "show this as emoji" marker that follows some emoji
VARIATION_SELECTOR = "\ufe0f"

# fonts already made, keyed by (size, weight, style).
# each value is (font, label); the label makes font.metrics() much faster.
FONTS = {}


def get_font(size, weight, style, family=None):
    """Return the font for this size/weight/style, making it only the first time."""
    key = (size, weight, style, family)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style, family=family)
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
        self.line = []
        self.center = False
        self.sup = False
        self.abbr = False
        self.pre = False
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            if self.pre:
                self.pre_text(tok.text)
            else:
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
        elif tok.tag == 'h1 class="title"':
            self.flush()
            self.center = True
        elif tok.tag == "/h1":
            self.flush()
            self.center = False
        elif tok.tag == "sup":
            self.sup = True
        elif tok.tag == "/sup":
            self.sup = False
        elif tok.tag == "abbr":
            self.abbr = True
        elif tok.tag == "/abbr":
            self.abbr = False
        elif tok.tag == "pre":
            self.flush()
            self.pre = True
        elif tok.tag == "/pre":
            self.flush()
            self.pre = False

    def pre_text(self, text):
        """
        Preserve whitespace and line breaks for <pre> text. Each line is treated as a separate word, and the cursor is moved down after each line.
        """
        font = get_font(self.size, self.weight, self.style, "Courier New")
        pieces = text.split("\n")
        for i in range(len(pieces)):
            line = pieces[i]
            if line:
                self.line.append((self.cursor_x, line, font, self.sup))
                self.cursor_x += font.measure(line)
            if self.line:
                self.flush()
            else:
                self.cursor_y += 1.5 * font.metrics("linespace")
        print(pieces)

    def abbr_word(self, word):
        """Place one word from inside <abbr> in small caps.

        Lower-case letters become capitals in a smaller, bold font; every
        other character keeps the normal font. One word can need both fonts,
        so the word is split into pieces, and each piece goes into self.line
        as its own entry, right after the piece before it.
        """
        size = self.size // 2 if self.sup else self.size
        normal_font = get_font(size, self.weight, self.style)
        small_caps_font = get_font(size - 2, "bold", self.style)

        # 1. group neighbouring characters of the same kind into pieces:
        #    "Css3" -> [["C", False], ["ss", True], ["3", False]]
        pieces = []
        for c in word:
            if pieces and pieces[-1][1] == c.islower():
                # same kind as the character before: add it to that piece
                pieces[-1][0] += c
            else:
                # the kind changed (or this is the first character): new piece
                pieces.append([c, c.islower()])

        # 2. give each piece the text and font it's drawn with.
        #    upper() returns a new string, so keep its result.
        placed = []
        for text, is_lower in pieces:
            if is_lower:
                placed.append((text.upper(), small_caps_font))
            else:
                placed.append((text, normal_font))

        # 3. wrap check for the whole word at once, so its pieces never end up
        #    on different lines
        total_width = sum(font.measure(text) for text, font in placed)
        if self.cursor_x + total_width >= self.width - HSTEP:
            self.flush()

        # 4. put the pieces side by side: move past each one, with no space
        for text, font in placed:
            self.line.append((self.cursor_x, text, font, self.sup))
            self.cursor_x += font.measure(text)
        # 5. add a space after the whole word, so the next word doesn't touch it
        self.cursor_x += normal_font.measure(" ")

    def word(self, word):
        size = self.size // 2 if self.sup else self.size
        font = get_font(size, self.weight, self.style)
        word = word.replace(VARIATION_SELECTOR, "")
        if not word:
            return
        if self.abbr:
            self.abbr_word(word)
            return
        w = font.measure(word)
        # the word doesn't fit: finish this line, so the word starts the next
        if self.cursor_x + w >= self.width - HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font, self.sup))
        self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font, sup in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        offset = 0

        if self.center:
            last_x, last_word, last_font, _ = self.line[-1]
            line_width = last_x + last_font.measure(last_word) - HSTEP
            offset = max(0, (self.width - 2 * HSTEP - line_width) / 2)

        for x, word, font, sup in self.line:

            if sup:
                # top of the superscript level with the top of the normal text
                y = baseline - max_ascent
            else:
                # bottom of the word on the baseline
                y = baseline - font.metrics("ascent")
            self.display_list.append((x + offset, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y += 1.5 * (max_ascent + max_descent)
        self.cursor_x = HSTEP
        self.line = []
