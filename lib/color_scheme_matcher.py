"""
Color Scheme Matcher (for sublime text)
Licensed under MIT
Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>
"""
from __future__ import absolute_import
import sublime
import re
ST3 = int(sublime.version()) >= 3000
if not ST3:
    from plistlib import readPlist
else:
    from plistlib import readPlistFromBytes
from .rgba import RGBA
from os import path


def sublime_format_path(pth):
    m = re.match(r"^([A-Za-z]{1}):(?:/|\\)(.*)", pth)
    if sublime.platform() == "windows" and m is not None:
        pth = m.group(1) + "/" + m.group(2)
    return pth.replace("\\", "/")


class ColorSchemeMatcher(object):
    def __init__(self, scheme_file, strip_trans=False, ignore_gutter=False, track_dark_background=False, filter=None):
        if filter is None:
            filter = self.filter
        self.color_scheme = path.normpath(scheme_file)
        self.scheme_file = path.basename(self.color_scheme)
        if ST3:
            self.plist_file = filter(readPlistFromBytes(sublime.load_binary_resource(sublime_format_path(self.color_scheme))))
        else:
            self.plist_file = filter(readPlist(sublime.packages_path() + self.color_scheme.replace('Packages', '')))
        self.scheme_file = scheme_file
        self.strip_trans = strip_trans
        self.ignore_gutter = ignore_gutter
        self.track_dark_background = track_dark_background
        self.dark_lumens = None
        self.matched = {}

        self.parse_scheme()

    def filter(self, plist):
        return plist

    def parse_scheme(self):
        color_settings = self.plist_file["settings"][0]["settings"]

        # Get general theme colors from color scheme file
        self.bground = self.strip_color(color_settings.get("background", '#FFFFFF'), simple_strip=True)
        self.fground = self.strip_color(color_settings.get("foreground", '#000000'))
        self.sbground = self.strip_color(color_settings.get("selection", self.fground))
        self.sfground = self.strip_color(color_settings.get("selectionForeground", None))
        self.gbground = self.strip_color(color_settings.get("gutter", self.bground)) if not self.ignore_gutter else self.bground
        self.gfground = self.strip_color(color_settings.get("gutterForeground", self.fground)) if not self.ignore_gutter else self.fground

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

            if scope is not None and name is not None and (color is not None or bgcolor is not None):
                self.colors[scope] = {
                    "name": name,
                    "color": self.strip_color(color),
                    "bgcolor": self.strip_color(bgcolor),
                    "style": style
                }

    def strip_color(self, color, simple_strip=False):
        if color is None or color.strip() == "":
            return None
        elif not self.strip_trans:
            return color.replace(" ", "")
        rgba = RGBA(color.replace(" ", ""))
        if not simple_strip:
            rgba.apply_alpha(self.bground if self.bground != "" else "#FFFFFF")
        if self.track_dark_background:
            lumens = rgba.luminance()
            if self.dark_lumens is None or lumens < self.dark_lumens:
                self.dark_lumens = lumens
        return rgba.get_rgb()

    def get_general_colors(self):
        return self.bground, self.fground, self.sbground, self.sfground, self.gbground, self.gfground

    def get_darkest_lumen(self):
        return self.dark_lumens

    def get_plist_file(self):
        return self.plist_file

    def get_scheme_file(self):
        return self.scheme_file

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

    def shift_background_brightness(self, lumens_limit):
        dlumen = self.get_darkest_lumen()
        if dlumen is not None and dlumen < lumens_limit:
            factor = 1 + ((lumens_limit - dlumen) / 255.0)
            for k, v in self.colors.items():
                fg, bg = v["color"], v["bgcolor"]
                if fg is not None:
                    self.colors[k]["color"] = self.apply_brightness(fg, factor)
                if bg is not None:
                    self.colors[k]["bgcolor"] = self.apply_brightness(bg, factor)
            self.bground = self.apply_brightness(self.bground, factor)
            self.fground = self.apply_brightness(self.fground, factor)
            self.sbground = self.apply_brightness(self.sbground, factor)
            if self.sfground is not None:
                self.sfground = self.apply_brightness(self.sfground, factor)
            self.gbground = self.apply_brightness(self.gbground, factor)
            self.gfground = self.apply_brightness(self.gfground, factor)

    def apply_brightness(self, color, shift_factor):
        rgba = RGBA(color)
        if shift_factor is not None:
            rgba.brightness(shift_factor)
        return rgba.get_rgb()
