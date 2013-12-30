"""
Scope Hunter
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
"""

import sublime
import sublime_plugin
from time import time, sleep
import thread
try:
    from ScopeHunterLib.color_scheme_matcher import ColorSchemeMatcher
except:
    ColorSchemeMatcher = None


def log(msg):
    print("ScopeHunter: %s" % msg)


def underline(regions):
    """
    Convert to empty regions
    """

    new_regions = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            new_regions.append(sublime.Region(start))
            start += 1
    return new_regions


class ScopeThreadManager(object):
    @classmethod
    def load(cls):
        cls.wait_time = 0.12
        cls.time = time()
        cls.modified = False
        cls.ignore_all = False
        cls.instant_scoper = False

    @classmethod
    def is_enabled(cls, view):
        return not view.settings().get("is_widget") and not cls.ignore_all

ScopeThreadManager.load()


class GetSelectionScope(object):
    def get_scope(self, pt):
        global initialized
        if self.rowcol or self.points or self.highlight_extent:
            pts = self.view.extract_scope(pt)
            # Scale back the extent by one for true points included
            if pts.size() < self.highlight_max_size:
                self.extents.append(sublime.Region(pts.begin(), pts.end()))
            if self.points:
                self.scope_bfr.append("%-25s (%d, %d)" % ("Scope Extent pts:", pts.begin(), pts.end()))
            if self.rowcol:
                row1, col1 = self.view.rowcol(pts.begin())
                row2, col2 = self.view.rowcol(pts.end())
                self.scope_bfr.append(
                    "%-25s (line: %d char: %d, line: %d char: %d)" % ("Scope Extent row/col:", row1 + 1, col1 + 1, row2 + 1, col2 + 1)
                )
        scope = self.view.scope_name(pt)

        if self.clipboard:
            self.clips.append(scope)

        if self.first and self.show_statusbar:
            self.status = scope
            self.first = False

        self.scope_bfr.append("%-25s %s" % ("Scope:", self.view.scope_name(pt)))

        if not initialized:
            init_color_scheme()
            initialized = True

        if self.show_selectors and scheme_matcher is not None:
            try:
                color, style, bgcolor, color_selector, bg_selector, style_selectors = scheme_matcher.guess_color(self.view, pt, scope)
                scheme_file = scheme_matcher.color_scheme
                self.scope_bfr.append("%-25s %s" % ("Scheme File:", scheme_file))
                self.scope_bfr.append("%-25s %s" % ("foreground:", color))
                self.scope_bfr.append("%-25s %s" % ("foreground selector:", color_selector))
                self.scope_bfr.append("%-25s %s" % ("background:", bgcolor))
                self.scope_bfr.append("%-25s %s" % ("background selector:", bg_selector))
                self.scope_bfr.append("%-25s %s" % ("style:", style))
                if style_selectors["bold"] != "":
                    self.scope_bfr.append("%-25s %s" % ("bold selector:", style_selectors["bold"]))
                if style_selectors["italic"] != "":
                    self.scope_bfr.append("%-25s %s" % ("italic selector:", style_selectors["italic"]))
            except Exception as e:
                log("Evaluating theme failed!  Ignoring theme related info.\n%s" % str(e))
                self.show_selectors = False

        # Divider
        self.scope_bfr.append("")

    def run(self, v):
        self.view = v
        self.window = self.view.window()
        view = self.window.get_output_panel('scope_viewer')
        self.scope_bfr = []
        self.clips = []
        self.status = ""
        self.show_statusbar = bool(sh_settings.get("show_statusbar", False))
        self.show_panel = bool(sh_settings.get("show_panel", False))
        self.clipboard = bool(sh_settings.get("clipboard", False))
        self.multiselect = bool(sh_settings.get("multiselect", False))
        self.rowcol = bool(sh_settings.get("extent_line_char", False))
        self.points = bool(sh_settings.get("extent_points", False))
        self.console_log = bool(sh_settings.get("console_log", False))
        self.highlight_extent = bool(sh_settings.get("highlight_extent", False))
        self.highlight_scope = sh_settings.get("highlight_scope", 'invalid')
        self.highlight_style = sh_settings.get("highlight_style", 'underline')
        self.highlight_max_size = int(sh_settings.get("highlight_max_size", 100))
        self.show_selectors = bool(sh_settings.get("show_color_scheme_info", False))
        self.first = True
        self.extents = []

        # Get scope info for each selection wanted
        if len(self.view.sel()):
            if self.multiselect:
                for sel in self.view.sel():
                    self.get_scope(sel.b)
            else:
                self.get_scope(self.view.sel()[0].b)

        # Copy scopes to clipboard
        if self.clipboard:
            sublime.set_clipboard('\n'.join(self.clips))

        # Display in status bar
        if self.show_statusbar:
            sublime.status_message(self.status)

        # Show panel
        if self.show_panel:
            edit = view.begin_edit()
            view.insert(edit, 0, unicode('\n'.join(self.scope_bfr)))
            view.end_edit(edit)
            self.window.run_command("show_panel", {"panel": "output.scope_viewer"})

        if self.console_log:
            print unicode('\n'.join(["Scope Hunter"] + self.scope_bfr)).encode("utf-8")

        if self.highlight_extent:
            highlight_style = 0
            if self.highlight_style == 'underline':
                # Use underline if explicity requested,
                # or if doing a find only when under a selection only (only underline can be seen through a selection)
                self.extents = underline(self.extents)
                highlight_style = sublime.DRAW_EMPTY_AS_OVERWRITE
            elif self.highlight_style == 'outline':
                highlight_style = sublime.DRAW_OUTLINED
            self.view.add_regions(
                'scope_hunter',
                self.extents,
                self.highlight_scope,
                highlight_style
            )


find_scopes = GetSelectionScope().run


class GetSelectionScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        ScopeThreadManager.modified = True

    def is_enabled(self):
        return ScopeThreadManager.is_enabled(self.view)


class ToggleSelectionScopeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        ScopeThreadManager.instant_scoper = False if ScopeThreadManager.instant_scoper else True
        if ScopeThreadManager.instant_scoper:
            ScopeThreadManager.modified = True
            ScopeThreadManager.time = time()
        else:
            win = sublime.active_window()
            if win is not None:
                view = win.active_view()
                if (
                    view is not None and
                    ScopeThreadManager.is_enabled(view) and
                    bool(sh_settings.get("highlight_extent", False)) and
                    len(view.get_regions("scope_hunter"))
                ):
                    view.erase_regions("scope_hunter")

class SelectionScopeListener(sublime_plugin.EventListener):
    def clear_regions(self, view):
        if self.enabled and bool(sh_settings.get("highlight_extent", False)) and len(view.get_regions("scope_hunter")):
            view.erase_regions("scope_hunter")

    def on_selection_modified(self, view):
        self.enabled = ScopeThreadManager.is_enabled(view)
        if not ScopeThreadManager.instant_scoper or not self.enabled:
            # clean up dirty highlights
            self.clear_regions(view)
        else:
            ScopeThreadManager.modified = True
            ScopeThreadManager.time = time()


def sh_run():
    """
    Kick off scoper
    """

    # Ignore selection inside the routine
    ScopeThreadManager.modified = False
    ScopeThreadManager.ignore_all = True
    window = sublime.active_window()
    view = None if window == None else window.active_view()
    if view != None:
        find_scopes(view)
    ScopeThreadManager.ignore_all = False
    ScopeThreadManager.time = time()


def sh_loop():
    """
    Start thread that will ensure scope hunting happens after a barage of events
    Initial hunt is instant, but subsequent events in close succession will
    be ignored and then accounted for with one match by this thread
    """

    while True:
        if not ScopeThreadManager.ignore_all:
            if ScopeThreadManager.modified == True and time() - ScopeThreadManager.time > ScopeThreadManager.wait_time:
                sublime.set_timeout(lambda: sh_run(), 0)
        sleep(0.5)


def init_color_scheme():
    global pref_settings
    global scheme_matcher
    if ColorSchemeMatcher is None:
        # Linux might fail, so disable color matching
        log("ColorSchemeMatcher is not loaded!")
        pref_settings = None
        scheme_matcher = None
    else:
        pref_settings = sublime.load_settings('Preferences.sublime-settings')
        scheme_file = pref_settings.get('color_scheme')
        try:
            scheme_matcher = ColorSchemeMatcher(scheme_file)
        except Exception as e:
            scheme_matcher = None
            log("Theme parsing failed!  Ingoring theme related info.\n%s" % str(e))
        pref_settings.clear_on_change('reload')
        pref_settings.add_on_change('reload', init_color_scheme)


sh_settings = sublime.load_settings('scope_hunter.sublime-settings')

initialized = False

if not 'running_sh_loop' in globals():
    running_sh_loop = True
    thread.start_new_thread(sh_loop, ())
