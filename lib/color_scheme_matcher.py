"""
Color Scheme Matcher (for sublime text)
Licensed under MIT
Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>
"""

from .rgba import RGBA
import sublime
import re
from plistlib import readPlistFromBytes
from os import path


def sublime_format_path(pth):
    m = re.match(r"^([A-Za-z]{1}):(?:/|\\)(.*)", pth)
    if sublime.platform() == "windows" and m != None:
        pth = m.group(1) + "/" + m.group(2)
    return pth.replace("\\", "/")


class ColorSchemeMatcher(object):
    def __init__(self, scheme_file, strip_trans=False):
        self.color_scheme = path.normpath(scheme_file)
        self.scheme_file = path.basename(self.color_scheme)
        self.plist_file = readPlistFromBytes(sublime.load_binary_resource(sublime_format_path(self.color_scheme)))
        self.scheme_file = scheme_file
        self.strip_trans = strip_trans
        self.matched = {}

        self.parse_scheme()

    def parse_scheme(self):
        color_settings = self.plist_file["settings"][0]["settings"]

        # Get general theme colors from color scheme file
        self.bground = self.strip_transparency(color_settings.get("background", '#FFFFFF'), simple_strip=True)
        self.fground = self.strip_transparency(color_settings.get("foreground", '#000000'))
        self.sbground = self.strip_transparency(color_settings.get("selection", self.fground))
        self.sfground = self.strip_transparency(color_settings.get("selectionForeground", None))
        self.gbground = self.strip_transparency(color_settings.get("gutter", self.bground))
        self.gfground = self.strip_transparency(color_settings.get("gutterForeground", self.fground))

        # Create scope colors mapping from color scheme file
        self.colors = {}
        for item in self.plist_file["settings"]:
            name = item.get('name', None)
            scope = item.get('scope', None)
            color = None
            style = []
            if 'settings' in item:
                color = item['settings'].get('foreground', None)
                bgcolor = item['settings'].get('background', None)
                if 'fontStyle' in item['settings']:
                    for s in item['settings']['fontStyle'].split(' '):
                        if s == "bold" or s == "italic":  # or s == "underline":
                            style.append(s)

            if scope != None and name != None and (color != None or bgcolor != None):
                self.colors[scope] = {
                    "name": name,
                    "color": self.strip_transparency(color),
                    "bgcolor": self.strip_transparency(bgcolor),
                    "style": style
                }

    def strip_transparency(self, color, simple_strip=False):
        if color is None:
            return color
        elif not self.strip_trans:
            return color.replace(" ", "")
        ba = "AA"
        rgba = RGBA(color.replace(" ", ""))
        if not simple_strip:
            rgba.apply_alpha(self.bground + ba if self.bground != "" else "#FFFFFF%s" % ba)
        return rgba.get_rgb()

    def guess_color(self, view, pt, scope_key):
        color = self.fground
        bgcolor = self.bground
        style = set([])
        color_selector = "foreground"
        style_selectors = {"bold": "", "italic": ""}
        bg_selector = "background"
        if scope_key in self.matched:
            color = self.matched[scope_key]["color"]
            style = self.matched[scope_key]["style"]
            bgcolor = self.matched[scope_key]["bgcolor"]
            selectors = self.matched[scope_key]["selectors"]
            color_selector, bg_selector, style_selectors = selectors["color"], selectors["background"], selectors["style"]
        else:
            best_match_bg = 0
            best_match_fg = 0
            best_match_style = 0
            for key in self.colors:
                match = view.score_selector(pt, key)
                if self.colors[key]["color"] is not None and match > best_match_fg:
                    best_match_fg = match
                    color = self.colors[key]["color"]
                    color_selector = self.colors[key]["name"]
                if self.colors[key]["style"] is not None and match > best_match_style:
                    best_match_style = match
                    for s in self.colors[key]["style"]:
                        style.add(s)
                        if s == "bold":
                            style_selectors["bold"] = self.colors[key]["name"]
                        elif s == "italic":
                            style_selectors["italic"] = self.colors[key]["name"]
                if self.colors[key]["bgcolor"] is not None and match > best_match_bg:
                    best_match_bg = match
                    bgcolor = self.colors[key]["bgcolor"]
                    bg_selector = self.colors[key]["name"]
            self.matched[scope_key] = {
                "color": color, "bgcolor": bgcolor,
                "style": style, "selectors": {
                    "color": color_selector,
                    "background": bg_selector,
                    "style": style_selectors
                }
            }
        if len(style) == 0:
            style = "normal"
        else:
            style = ' '.join(style)
        return color, style, bgcolor, color_selector, bg_selector, style_selectors
