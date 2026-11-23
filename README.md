# Browser Engineering

_Inspiration_: Over the past few weeks I've gobbled down a plethora of articles from the future of software engineering to fiction on infinite sets theory proposed by Georg Cantor, to what the typical life after graduation would look like for me as an international student. While on the one hand, I ambled these paths as a way to beguile time and steer my mind away from worry associated with a broken pump back home, my budding cousin, and my sister navigating a new life in a new country, on the other hand, I've noticed and quite recently started enjoying reading again in general. I read this article about writing code and how going through the grunt work of writing code by hand, albeit a bottleneck, was a good bottleneck. The article had started off by mentioning that software solutions were never meant to remove the constraints which surrounded the problems which it was trying to solve, but only to _creatively_ construct solutions that somehow minimized the effects of those constraints.

To be creative means to find association between disconnected facets of information emblazoned across one's minds. This led me down the rabbit hole of reading yet another article that described how writing was essentially thinking. That article referenced an entry in The Economist which had the excerpt, "Real writing is not writing at all. It is thinking; specifically it is thinking: What do i think?". It then went on to make this relevant to programmers and the art of writing code by hand which is slowly being eroded in this age of AI. The main point which he was trying to get across was that when we let AI write our code, we offset a lot of thinking which we could have gotten from writing that code on our own.

# Log Book

Chapter 1: Downloading Web Pages

- Wrote the bare metal implementation of the browser on 11/19/2026: wrote the parsing logic for what the server returns, adjusted the browser for several schemes.
- 11/20/2026: Eliminated close connection from request header, and implemented HTTP/1.1 requests with a headers dictionary, the data and file schemes, entity decoding for `&lt;`, `&gt;` and `&amp;`, and the view-source scheme.
- 11/21/2026: Wrote the redirection logic, reusable socket logic using _scheme, host, port_ as key for same server, implemented browser side caching logic, and finally ended with compressed data by setting the Accept-Encoding header in the browser.

Chapter 2: Drawing to the Screen

- 11/22/2026: Added a GUI with Tkinter that draws the page text onto a canvas, wraps it into lines, and scrolls with the arrow keys, mouse wheel and trackpad. Made newlines in the response start new lines, made the window resizable so the text re-wraps to the new width, and added a scrollbar that shows how far down the page you are.
- 11/22/2026: Rendered emoji as OpenMoji images, added the _about:blank_ URL, and made malformed URLs fall back to a blank page instead of crashing the browser.

Chapter 3: Formatting Text

- 11/22/2026: Changed the lexer to split the response into _Text_ and _Tag_ tokens, laid out whole words instead of single characters by measuring them with Tk fonts, and added bold and italic text with the _b_ and _i_ tags. Split the code into _GUI/_ and _utils/_ folders.
- 11/23/2026: Moved layout into its own _Layout_ class, added text sizes with the _small_ and _big_ tags, lined up words of different sizes on a shared baseline, started new lines on _br_ and new paragraphs on _/p_, and added a font cache so each font is only created once.

NOTE: My browser now opens pages in its own window: it downloads them, lays out the text with bold, italic and different sizes, and lets you scroll. Run it from the project root with `python3 -m GUI.screen_drawer <url>`.
