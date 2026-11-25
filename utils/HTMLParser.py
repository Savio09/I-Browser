from tag import Element
from Text import Text


class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        """Split HTML into a list of tokens: Text for page text, Tag for tags."""
        in_tag = False
        text = ""

        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()
    
    def add_text(self, text):
        parent = self.unfinished[-1]
        node = 

    def finish(self):
        pass