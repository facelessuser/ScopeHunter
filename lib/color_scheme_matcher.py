"""
Color Scheme Matcher (for sublime text).

Licensed under MIT
Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
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
from collections import namedtuple


class SchemeColors(
    namedtuple(
        'SchemeColors',
        ['fg', 'fg_simulated', 'bg', "bg_simulated", "style", "fg_selector", "bg_selector", "style_selectors"],
        verbose=False
    )
):

    """SchemeColors."""

    pass


class SchemeSelectors(namedtuple('SchemeSelectors', ['name', 'scope'], verbose=False)):

    """SchemeSelectors."""

    pass


def sublime_format_path(pth):
    """Format path for sublime internal use."""

    m = re.match(r"^([A-Za-z]{1}):(?:/|\\)(.*)", pth)
    if sublime.platform() == "windows" and m is not None:
        pth = m.group(1) + "/" + m.group(2)
    return pth.replace("\\", "/")


class ColorSchemeMatcher(object):

    """Determine color scheme colors and style for text in a Sublime view buffer."""

    def __init__(self, scheme_file, ignore_gutter=False, track_dark_background=False, filter=None):
        """Initialize."""
        if filter is None:
            filter = self.filter
        self.color_scheme = path.normpath(scheme_file)
        self.scheme_file = path.basename(self.color_scheme)
        if ST3:
            self.plist_file = filter(
                readPlistFromBytes(sublime.load_binary_resource(sublime_format_path(self.color_scheme)))
            )
        else:
            self.plist_file = filter(
                readPlist(sublime.packages_path() + self.color_scheme.replace('Packages', ''))
            )
        self.scheme_file = scheme_file
        self.ignore_gutter = ignore_gutter
        self.track_dark_background = track_dark_background
        self.dark_lumens = None
        self.lumens = None
        self.matched = {}
        self.is_dark_theme = False

        self.parse_scheme()

    def filter(self, plist):
        """Dummy filter call that does nothing."""

        return plist

    def parse_scheme(self):
        """Parse the color scheme."""

        color_settings = self.plist_file["settings"][0]["settings"]

        # Get general theme colors from color scheme file
        self.bground, self.bground_sim = self.strip_color(
            color_settings.get("background", '#FFFFFF'), simple_strip=True, bg=True
        )
        if self.lumens <= 127:
            self.is_dark_theme = True
        self.fground, self.fground_sim = self.strip_color(color_settings.get("foreground", '#000000'))
        self.sbground = self.strip_color(color_settings.get("selection", self.fground), bg=True)[0]
        self.sbground_sim = self.strip_color(color_settings.get("selection", self.fground_sim), bg=True)[1]
        self.sfground, self.sfground_sim = self.strip_color(color_settings.get("selectionForeground", None))
        if not self.ignore_gutter:
            self.gbground = self.strip_color(color_settings.get("gutter", self.bground), bg=True)[0]
        else:
            self.gbground = self.bground
        if not self.ignore_gutter:
            self.gbground_sim = self.strip_color(color_settings.get("gutter", self.bground_sim), bg=True)[1]
        else:
            self.gbground_sim = self.bground_sim
        if not self.ignore_gutter:
            self.gfground = self.strip_color(color_settings.get("gutterForeground", self.fground))[0]
        else:
            self.gfground = self.fground
        if not self.ignore_gutter:
            self.gfground_sim = self.strip_color(color_settings.get("gutterForeground", self.fground_sim))[1]
        else:
            self.gfground_sim = self.fground_sim

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
                fg, fg_sim = self.strip_color(color)
                bg, bg_sim = self.strip_color(bgcolor, bg=True)
                self.colors[scope] = {
                    "name": name,
                    "scope": scope,
                    "color": fg,
                    "color_simulated": fg_sim,
                    "bgcolor": bg,
                    "bgcolor_simulated": bg_sim,
                    "style": style
                }

    def strip_color(self, color, simple_strip=False, bg=False):
        """
        Strip transparency from the color value.

        Transparency can be stripped in one of two ways:
            - Simply mask off the alpha channel.
            - Apply the alpha channel to the color essential getting the color seen by the eye.
        """

        if color is None or color.strip() == "":
            return None, None

        rgba = RGBA(color.replace(" ", ""))
        if not simple_strip:
            rgba.apply_alpha(self.bground_sim if self.bground_sim != "" else "#FFFFFF")

        self.lumens = rgba.luminance()
        if self.track_dark_background and bg:
            if self.dark_lumens is None or self.lumens < self.dark_lumens:
                self.dark_lumens = self.lumens

        return color, rgba.get_rgb()

    def get_general_colors(self, simulate_transparency=False):
        """
        Get the core colors (background, foreground) for the view and gutter.

        Get the visible look of the color by simulated transparency if requrested.
        """
        if simulate_transparency:
            return (
                self.bground_sim, self.fground_sim, self.sbground_sim,
                self.sfground_sim, self.gbground_sim, self.gfground_sim
            )
        else:
            return self.bground, self.fground, self.sbground, self.sfground, self.gbground, self.gfground

    def get_darkest_lumen(self):
        """Get the darkest background lumen found."""

        return self.dark_lumens

    def get_plist_file(self):
        """Get the plist file used during the process."""

        return self.plist_file

    def get_scheme_file(self):
        """Get the scheme file used during the process."""

        return self.scheme_file

    def guess_color(self, view, pt, scope_key):
        """Guess the colors and style of the text for the given Sublime view pt."""

        color = self.fground
        color_sim = self.fground_sim
        bgcolor = self.bground
        bgcolor_sim = self.bground_sim
        style = set([])
        color_selector = SchemeSelectors("foreground", "foreground")
        bg_selector = SchemeSelectors("background", "background")
        style_selectors = {"bold": SchemeSelectors("", ""), "italic": SchemeSelectors("", "")}
        if scope_key in self.matched:
            color = self.matched[scope_key]["color"]
            color_sim = self.matched[scope_key]["color_simulated"]
            style = self.matched[scope_key]["style"]
            bgcolor = self.matched[scope_key]["bgcolor"]
            bgcolor_sim = self.matched[scope_key]["bgcolor_simulated"]
            selectors = self.matched[scope_key]["selectors"]
            color_selector = selectors["color"]
            bg_selector = selectors["background"]
            style_selectors = selectors["style"]
        else:
            best_match_bg = 0
            best_match_fg = 0
            best_match_style = 0
            for key in self.colors:
                match = view.score_selector(pt, key)
                if self.colors[key]["color"] is not None and match > best_match_fg:
                    best_match_fg = match
                    color = self.colors[key]["color"]
                    color_sim = self.colors[key]["color_simulated"]
                    color_selector = SchemeSelectors(self.colors[key]["name"], self.colors[key]["scope"])
                if self.colors[key]["style"] is not None and match > best_match_style:
                    best_match_style = match
                    for s in self.colors[key]["style"]:
                        style.add(s)
                        if s == "bold":
                            style_selectors["bold"] = SchemeSelectors(
                                self.colors[key]["name"], self.colors[key]["scope"]
                            )
                        elif s == "italic":
                            style_selectors["italic"] = SchemeSelectors(
                                self.colors[key]["name"], self.colors[key]["scope"]
                            )
                if self.colors[key]["bgcolor"] is not None and match > best_match_bg:
                    best_match_bg = match
                    bgcolor = self.colors[key]["bgcolor"]
                    bgcolor_sim = self.colors[key]["bgcolor_simulated"]
                    bg_selector = SchemeSelectors(self.colors[key]["name"], self.colors[key]["scope"])
            self.matched[scope_key] = {
                "color": color,
                "bgcolor": bgcolor,
                "color_simulated": color_sim,
                "bgcolor_simulated": bgcolor_sim,
                "style": style,
                "selectors": {
                    "color": color_selector,
                    "background": bg_selector,
                    "style": style_selectors
                }
            }
        if len(style) == 0:
            style = "normal"
        else:
            style = ' '.join(style)
        return SchemeColors(
            color, color_sim, bgcolor, bgcolor_sim, style,
            color_selector, bg_selector, style_selectors
        )

    def shift_background_brightness(self, lumens_limit):
        """Shift background color brightness if below lumens limit."""

        dlumen = self.get_darkest_lumen()
        if dlumen is not None and dlumen < lumens_limit:
            factor = 1 + ((lumens_limit - dlumen) / 255.0)
            for k, v in self.colors.items():
                fg, bg = v["color"], v["bgcolor"]
                fg_sim, bg_sim = v["color_simulated"], v["bgcolor_simulated"]
                if fg is not None:
                    self.colors[k]["color"] = self.apply_brightness(fg, factor)
                    self.colors[k]["color_simulated"] = self.apply_brightness(fg_sim, factor)
                if bg is not None:
                    self.colors[k]["bgcolor"] = self.apply_brightness(bg, factor)
                    self.colors[k]["bgcolor_simulated"] = self.apply_brightness(bg_sim, factor)
            self.bground = self.apply_brightness(self.bground, factor)
            self.bground_sim = self.apply_brightness(self.bground_sim, factor)
            self.fground = self.apply_brightness(self.fground, factor)
            self.fground_sim = self.apply_brightness(self.fground_sim, factor)
            self.sbground = self.apply_brightness(self.sbground, factor)
            self.sbground_sim = self.apply_brightness(self.sbground_sim, factor)
            if self.sfground is not None:
                self.sfground = self.apply_brightness(self.sfground, factor)
                self.sfground_sim = self.apply_brightness(self.sfground_sim, factor)

            self.gbground = self.apply_brightness(self.gbground, factor)
            self.gbground_sim = self.apply_brightness(self.gbground_sim, factor)
            self.gfground = self.apply_brightness(self.gfground, factor)
            self.gfground_sim = self.apply_brightness(self.gfground_sim, factor)

    def apply_brightness(self, color, shift_factor):
        """Apply the brightness to the given color using the shift_factor."""

        rgba = RGBA(color)
        if shift_factor is not None:
            rgba.brightness(shift_factor)
        return rgba.get_rgb()
