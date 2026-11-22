import socket
import time

# open connections kept alive between requests, keyed by (scheme, host, port)
open_sockets = {}
# how many redirects in a row one page load may follow
MAX_REDIRECTS = 5
# saved responses, keyed by (scheme, host, port, path).
# each value is (content, expires_at); expires_at is None for "never expires"
BROWSER_CACHE = {}


def cache_policy(status, response_headers):
    """Decide whether a response may be cached, and for how long.

    Returns (should_cache, max_age), where max_age is in seconds,
    or None when the response doesn't say how long it stays fresh.
    """
    # only 200 responses are cached (our browser only sends GET requests)
    if status != 200:
        return False, None
    if "cache-control" not in response_headers:
        return True, None
    max_age = None
    for directive in response_headers["cache-control"].split(","):
        directive = directive.strip().casefold()
        if directive.startswith("max-age="):
            value = directive[len("max-age=") :]
            if not value.isdigit():
                return False, None
            max_age = int(value)
        else:
            # no-store, or any directive we don't support: don't cache
            return False, None
    return True, max_age


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

    def request(self, redirects_left=MAX_REDIRECTS):
        if self.scheme == "file":
            with open(self.path, "r", encoding="utf-8") as file:
                return file.read()
        if self.scheme == "data":
            return self.payload
        if self.scheme == "view-source":
            return self.view_source_url.request()

        cache_key = (self.scheme, self.host, self.port, self.path)
        if cache_key in BROWSER_CACHE:
            content, expires_at = BROWSER_CACHE[cache_key]
            if expires_at is None or time.time() < expires_at:
                # fresh copy saved: no need to contact the server at all
                return content
            # expired: forget it and fetch a new copy below
            del BROWSER_CACHE[cache_key]

        socket_key = (self.scheme, self.host, self.port)
        if socket_key in open_sockets:
            # same server as an earlier request: reuse its connection
            s = open_sockets[socket_key]
        else:
            s = socket.socket(
                family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
            )
            s.connect((self.host, self.port))
            if self.scheme == "https":
                import ssl

                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            open_sockets[socket_key] = s
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
            print(line)
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        print("Response headers:", response_headers)
        assert "content-length" in response_headers
        content_length = int(response_headers["content-length"])
        # read exactly the body's bytes, then turn them into text for show().
        # this also runs for redirects, so no leftover bytes stay in the
        # kept-alive socket to confuse the next request.
        content = response.read(content_length).decode("utf-8")

        if 300 <= int(status) < 400 and "location" in response_headers:
            assert redirects_left > 0, "too many redirects in a row"
            new_location = response_headers["location"]
            if new_location.startswith("/"):
                # same scheme, host and port as this request
                new_location = "{}://{}:{}{}".format(
                    self.scheme, self.host, self.port, new_location
                )
            # follow the redirect, with one fewer left for the rest of the chain
            return URL(new_location).request(redirects_left - 1)

        should_cache, max_age = cache_policy(int(status), response_headers)
        if should_cache:
            expires_at = None if max_age is None else time.time() + max_age
            BROWSER_CACHE[cache_key] = (content, expires_at)

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
    print(
        url.scheme,
        url.host if hasattr(url, "host") else "",
        url.path if hasattr(url, "path") else "",
        url.media_type if hasattr(url, "media_type") else "",
        url.payload if hasattr(url, "payload") else "",
        url.view_source_url if hasattr(url, "view_source_url") else "",
        url.port if hasattr(url, "port") else "",
    )
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
