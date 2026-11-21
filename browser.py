import socket

# open connections kept alive between requests, keyed by (scheme, host, port)
open_sockets = {}


class URL:
    def __init__(self, url):
        if url.startswith("view-source:"):
            self.scheme = "view-source"
            # recursively parse the URL after "view-source:"
            self.view_source_url = URL(url[len("view-source:") :])
        elif "://" not in url:
            self.scheme, url = url.split(":", 1)
            assert self.scheme in ["data"]
            if self.scheme == "data":
                self.media_type, self.payload = url.split(",", 1)
        else:
            self.scheme, url = url.split("://", 1)
            assert self.scheme in ["http", "https", "file"]
            if self.scheme == "https":
                self.port = 443
            elif self.scheme == "http":
                self.port = 80
            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
            self.path = "/" + url

    def request(self):
        if self.scheme == "file":
            with open(self.path, "r", encoding="utf-8") as file:
                return file.read()
        if self.scheme == "data":
            return self.payload
        if self.scheme == "view-source":
            return self.view_source_url.request()
        key = (self.scheme, self.host, self.port)
        if key in open_sockets:
            # same server as an earlier request: reuse its connection
            s = open_sockets[key]
        else:
            s = socket.socket(
                family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
            )
            s.connect((self.host, self.port))
            if self.scheme == "https":
                import ssl

                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            open_sockets[key] = s
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request_headers = {
            "Host": self.host,
            "User-Agent": "Browser/0.1",
            "Connection": "keep-alive",
        }

        for request_header, value in request_headers.items():
            request += "{}: {}\r\n".format(request_header, value)
        request += "\r\n"
        s.send(request.encode("utf-8"))

        # binary mode, so read(n) counts bytes like Content-Length does
        response = s.makefile("rb")
        # split the response into pieces starting with the status line
        statusline = response.readline().decode("utf-8")
        version, status, explanation = statusline.split(" ", 2)

        # now comes the headers for the host.
        response_headers = {}
        while True:
            line = response.readline().decode("utf-8")
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        print("Response headers:", response_headers)
        assert "content-length" in response_headers
        content_length = int(response_headers["content-length"])
        # read exactly the body's bytes, then turn them into text for show()
        content = response.read(content_length).decode("utf-8")
        return content


def show(body):
    in_tag = False
    i = 0
    entity_map = {"&lt;": "<", "&gt;": ">", "&amp;": "&"}
    while i < len(body):
        c = body[i]
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            matched = False
            if c == "&":
                for entity, char in entity_map.items():
                    if body[i : i + len(entity)] == entity:
                        print(char, end="")
                        i += len(entity)  # jump past the whole entity
                        matched = True
                        break
            if matched:
                continue  # i already moved; skip the i += 1 below
            print(c, end="")
        i += 1


def load(url):
    body = url.request()
    if url.scheme == "view-source":
        print(body)
    else:
        show(body)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        load(URL("file:///Users/fdeclan/Public/browser_from_scratch/this.txt"))
    else:
        load(URL(sys.argv[1]))
