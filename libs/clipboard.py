#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
import contextlib
from email.message import EmailMessage
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

try:
    import xerox  # NOTE use https://github.com/clach04/xerox/  -- python -m pip install git+https://github.com/clach04/xerox.git
except ImportError:
    xerox = None

is_android = "getandroidapilevel" in dir(sys)
is_pygamece = getattr(pygame, "IS_CE", False)

def clipboard_init():
    if is_android:
        return
    if not is_pygamece and "scrap" in dir(pygame) and "init" in dir(pygame.scrap):
        # pygame
        pygame.scrap.init()
        pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)

def parse_content_type(header_value: str) -> dict[str, object]:
    """Parse a MIME / Content-Type string like 'text/plain;charset=utf-8'."""
    msg = EmailMessage()
    msg["Content-Type"] = header_value.strip()

    content_type = msg.get_content_type()  # e.g. 'text/plain' (lowercased)
    maintype, _, subtype = content_type.partition("/")
    params = {
        key.lower(): value
        for key, value in msg.get_params(header="Content-Type", unquote=True)
        if key.lower() != content_type
    }

    return {
        "mime_type": content_type,
        "maintype": maintype,
        "subtype": subtype,
        "params": params,
    }

def clipboard_set_text(text):
    if xerox:
        xerox.copy(text)
    elif is_pygamece:
        pygame.scrap.put_text(text)
    else:
        if "scrap" in dir(pygame) and "put" in dir(pygame.scrap):
            pygame.scrap.put("text/plain;charset=utf-8", text.encode("utf-8"))

def clipboard_get_text():
    clipboard_text = ""
    if xerox:
        clipboard_text = xerox.paste() or ""
    elif is_pygamece:
        # pygame-ce
        clipboard_text = pygame.scrap.get_text() or ""
    else:
        # pygame
        for t in pygame.scrap.get_types():
            if "text/plain" in t and pygame.scrap.get(t) != None:
                parsed_content = parse_content_type(t)
                if "charset" in dict(parsed_content["params"]):
                    charset = parsed_content["params"]["charset"]
                else:
                    charset = "utf-8"
                clipboard_text = pygame.scrap.get(t).decode(charset, "ignore")
                break
        if clipboard_text.endswith('\x00'):
            clipboard_text = clipboard_text[:-1]

    return clipboard_text


