"""
Scope Hunter
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
"""

import sublime
import sublime_plugin
from time import time, sleep
import _thread as thread
from ScopeHunter.lib.color_scheme_matcher import ColorSchemeMatcher
from ScopeHunter.lib.rgba import RGBA
from ScopeHunter.scope_hunter_notify import notify, error
import re
import traceback

pref_settings = {}
scheme_matcher = None
sh_settings = {}
css = None


def log(msg):
    """ Logging """
    print("ScopeHunter: %s" % msg)


def underline(regions):
    """ Convert to empty regions """

    new_regions = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            new_regions.append(sublime.Region(start))
            start += 1
    return new_regions


def copy_data(bfr, label, format=None):
    """ Copy data to clipboard from buffer """
    for line in bfr:
        if line.startswith(label + ':'):
            text = line.replace(label + ':', '', 1).strip()
            if format is not None:
                text = format(text)
            sublime.set_clipboard(text)
            notify("Copied: %s" % label)
            break


def color_box(color, caption, link):
    """ Display an HTML color box using the given color """
    rgba = RGBA(color)
    display_color = rgba.get_rgb()
    display_text = rgba.get_rgba().upper()
    font_class = 'color-box-light' if rgba.luminance() <= 127 else 'color-box-dark'
    return (
        '<p><span class="key">%s:</span>'
        '<div class="color-box-frame">'
        '<div class="color-box %s" style="background-color: %s;">%s'
        '</div></div><a href="%s" class="copy-link">(copy)</a></p>' % (
            caption, font_class, display_color, display_text, link
        )
    )


class ScopeThreadManager(object):
    @classmethod
    def load(cls):
        """ Load up defaults """
        cls.wait_time = 0.12
        cls.time = time()
        cls.modified = False
        cls.ignore_all = False
        cls.instant_scoper = False

    @classmethod
    def is_enabled(cls, view):
        """ Check if we can execute """
        return not view.settings().get("is_widget") and not cls.ignore_all

ScopeThreadManager.load()


class ScopeGlobals(object):
    bfr = None
    pt = None

    @classmethod
    def clear(cls):
        """ Clear edit buffer """
        cls.bfr = None
        cls.pt = None


class ScopeHunterInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        """ Insert text into buffer """
        self.view.insert(edit, ScopeGlobals.pt, ScopeGlobals.bfr)


class GetSelectionScope(object):
    def get_extents(self, pt):
        """ Get the scope extent via the sublime API """
        pts = self.view.extract_scope(pt)
        row1, col1 = self.view.rowcol(pts.begin())
        row2, col2 = self.view.rowcol(pts.end())

        # Scale back the extent by one for true points included
        if pts.size() < self.highlight_max_size:
            self.extents.append(sublime.Region(pts.begin(), pts.end()))

        if self.points or self.rowcol:
            if self.points:
                self.scope_bfr.append(
                    "%-30s %s" % (
                        "Scope Extents (Pts):",
                        "(%d, %d)" % (pts.begin(), pts.end())
                    )
                )
            if self.rowcol:
                self.scope_bfr.append(
                    "%-30s %s" % (
                        "Scope Extents (Line/Char):",
                        "(line: %d char: %d, line: %d char: %d)" % (
                            row1 + 1, col1 + 1, row2 + 1, col2 + 1
                        )
                    )
                )

            if self.show_popup:
                self.scope_bfr_tool.append('<h1 class="header">Scope Extent</h1><p>')
                if self.points:
                    self.scope_bfr_tool.append('<span class="key">points:</span><br>')
                    self.scope_bfr_tool.append("(%d, %d)<br>" % (pts.begin(), pts.end()))
                    self.scope_bfr_tool.append('<a href="copy-points" class="copy-link">(copy)</a>')
                    if self.rowcol:
                        self.scope_bfr_tool.append("<br><br>")
                if self.rowcol:
                    self.scope_bfr_tool.append('<span class="key">line/row:</span><br>')
                    self.scope_bfr_tool.append(
                        '(<strong>Line:</strong> %d '
                        '<strong>Char:</strong> %d, '
                        '<strong>Line:</strong> %d '
                        '<strong>Char:</strong> %d)<br>'
                        '<a href="copy-line-row" class="copy-link">(copy)</a>' % (
                            row1 + 1, col1 + 1, row2 + 1, col2 + 1
                        )

                    )
                self.scope_bfr_tool.append("</p>")

    def get_scope(self, pt):
        """ Get the scope at the cursor """
        scope = self.view.scope_name(pt)
        spacing = "\n" + (" " * 31)

        if self.clipboard:
            self.clips.append(scope)

        if self.first and self.show_statusbar:
            self.status = scope
            self.first = False

        self.scope_bfr.append(
            "%-30s %s" % (
                "Scope:",
                self.view.scope_name(pt).strip().replace(" ", spacing)
            )
        )

        if self.show_popup:
            self.scope_bfr_tool.append(
                '<h1 class="header">Scope:</h1><p>%s<br>'
                '<a href="copy-scope" class="copy-link">(copy)</a></p>' % self.view.scope_name(pt).strip()
            )

        return scope

    def get_colors(self, color, color_sim, bgcolor, bgcolor_sim):
        """ Get colors of foreground, background, and simulated transparency colors """
        self.scope_bfr.append("%-30s %s" % ("Foreground:", color))
        if len(color) == 8 and not color.lower().endswith('ff'):
            self.scope_bfr.append(
                "%-30s %s" % ("Foreground (Simulated Trans):", color_sim)
            )

        self.scope_bfr.append("%-30s %s" % ("Background:", bgcolor))
        if len(bgcolor) == 8 and not bgcolor.lower().endswith('ff'):
            self.scope_bfr.append(
                "%-30s %s" % ("Background (Simulated Trans):", bgcolor_sim)
            )

        if self.show_popup:
            self.scope_bfr_tool.append('<h1 class="header">%s</h1>' % "Color")
            self.scope_bfr_tool.append(color_box(color, 'foreground', 'copy-fg'))
            if len(color) == 9 and not color.lower().endswith('ff'):
                self.scope_bfr_tool.append(
                    color_box(color_sim, 'foreground (simulated transparency)', 'copy-fg-sim')
                )
            self.scope_bfr_tool.append(color_box(bgcolor, 'background', 'copy-bg'))
            if len(bgcolor) == 9 and not bgcolor.lower().endswith('ff'):
                self.scope_bfr_tool.append(
                    color_box(bgcolor_sim, 'background (simulated transparency)', 'copy-bg-sim')
                )

    def get_scheme_syntax(self):
        """ Get color scheme and syntax file path """
        global scheme_matcher
        global scheme_matcher_simulated

        self.scheme_file = scheme_matcher.color_scheme.replace('\\', '/')
        self.syntax_file = self.view.settings().get('syntax')
        self.scope_bfr.append("%-30s %s" % ("Scheme File:", self.scheme_file))
        self.scope_bfr.append("%-30s %s" % ("Syntax File:", self.syntax_file))

        if self.show_popup:
            self.scope_bfr_tool.append(
                '<h1 class="header">%s</h1><p>'
                '<a class="file-link" href="scheme">%s</a><br>'
                '<a href="copy-scheme" class="copy-link">(copy)</a></p>' % (
                    "Scheme File", self.scheme_file
                )
            )
            self.scope_bfr_tool.append(
                '<h1 class="header">%s</h1><p>'
                '<a class="file-link" href="syntax">%s</a><br>'
                '<a href="copy-syntax" class="copy-link">(copy)</a></p>' % (
                    "Syntax File", self.syntax_file
                )
            )

    def get_style(self, style):
        """ Get the font style """
        self.scope_bfr.append("%-30s %s" % ("Style:", style))
        if self.show_popup:
            self.scope_bfr_tool.append('<h1 class="header">%s</h1>' % "Style")
            if style == "bold":
                tag = "b"
            elif style == "italic":
                tag = "i"
            elif style == "underline":
                tag = "u"
            else:
                tag = "span"
            self.scope_bfr_tool.append(
                '<p><%(tag)s>%(type)s</%(tag)s><br>'
                '<a href="copy-style" class="copy-link">(copy)</a></p>' % {
                    "type": style, "tag": tag
                }
            )

    def get_selectors(self, color_selector, bg_selector, style_selectors):
        """ Get the selectors used to determine color and/or style """
        self.scope_bfr.append(
            "%-30s %s" % ("Foreground Selector Name:", color_selector.name)
        )
        self.scope_bfr.append(
            "%-30s %s" % ("Foreground Selector Scope:", color_selector.scope)
        )
        self.scope_bfr.append(
            "%-30s %s" % ("Background Selector Name:", bg_selector.name)
        )
        self.scope_bfr.append(
            "%-30s %s" % ("Background Selector Scope:", bg_selector.scope)
        )
        if style_selectors["bold"].name != "" or style_selectors["bold"].scope != "":
            self.scope_bfr.append(
                "%-30s %s" % ("Bold Selector Name:", style_selectors["bold"].name)
            )
            self.scope_bfr.append(
                "%-30s %s" % ("Bold Selector Scope:", style_selectors["bold"].scope)
            )

        if style_selectors["italic"].name != "" or style_selectors["italic"].scope != "":
            self.scope_bfr.append(
                "%-30s %s" % ("Italic Selector Name:", style_selectors["italic"].name)
            )
            self.scope_bfr.append(
                "%-30s %s" % ("Italic Selector Scope:", style_selectors["italic"].scope)
            )

        if self.show_popup:
            self.scope_bfr_tool.append(
                '<h1 class="header">%s</h1><p>' % "Selectors"
            )
            self.scope_bfr_tool.append(
                '<span class="key">foreground selector name:</span><br>%s<br>'
                '<a href="copy-fg-sel-name" class="copy-link">(copy)</a>' % color_selector.name
            )
            self.scope_bfr_tool.append(
                '<br><br><span class="key">foreground selector scope:</span><br>%s<br>'
                '<a href="copy-fg-sel-scope" class="copy-link">(copy)</a>' % color_selector.scope
            )
            self.scope_bfr_tool.append(
                '<br><br><span class="key">background selector name:</span><br>%s<br>'
                '<a href="copy-bg-sel-name" class="copy-link">(copy)</a>' % bg_selector.name
            )
            self.scope_bfr_tool.append(
                '<br><br><span class="key">background selector scope:</span><br>%s<br>'
                '<a href="copy-bg-sel-scope" class="copy-link">(copy)</a>' % bg_selector.scope
            )
            if style_selectors["bold"].name != "" or style_selectors["bold"].scope != "":
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">bold selector name:</span><br>%s<br>'
                    '<a href="copy-bold-sel-name" class="copy-link">(copy)</a>' % style_selectors["bold"].name
                )
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">bold selector scope:</span><br>%s<br>'
                    '<a href="copy-bold-sel-scope" class="copy-link">(copy)</a>' % style_selectors["bold"].scope
                )
            if style_selectors["italic"].name != "" or style_selectors["italic"].scope != "":
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">italic selector name:</span><br>%s<br>'
                    '<a href="copy-italic-sel-name" class="copy-link">(copy)</a>' % style_selectors["italic"].name
                )
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">italic selector scope:</span><br>%s<br>'
                    '<a href="copy-italic-sel-scope" class="copy-link">(copy)</a>' % style_selectors["italic"].scope
                )

    def get_info(self, pt):
        """ Get scope related info """
        global scheme_matcher

        scope = self.get_scope(pt)

        if self.rowcol or self.points or self.highlight_extent:
            self.get_extents(pt)

        if self.scheme_info and scheme_matcher is not None:
            try:
                match = scheme_matcher.guess_color(self.view, pt, scope)
                color = match.fg
                bgcolor = match.bg
                color_sim = match.fg_simulated
                bgcolor_sim = match.bg_simulated
                style = match.style
                bg_selector = match.bg_selector
                color_selector = match.fg_selector
                style_selectors = match.style_selectors

                self.get_colors(color, color_sim, bgcolor, bgcolor_sim)
                self.get_style(style)
                self.get_selectors(color_selector, bg_selector, style_selectors)
                self.get_scheme_syntax()
            except:
                log("Evaluating theme failed!  Ignoring theme related info.\n%s" % str(traceback.format_exc()))
                error("Evaluating theme failed!")
                self.scheme_info = False

        # Divider
        self.scope_bfr.append("")

    def on_navigate(self, href):
        """ Exceute link callback """
        if href == 'copy-all':
            sublime.set_clipboard('\n'.join(self.scope_bfr))
            notify('Copied: All')
        elif href == 'copy-scope':
            copy_data(
                self.scope_bfr,
                r'Scope',
                format=lambda x: x.replace('\n' + ' ' * 31, ' ')
            )
        elif href == 'copy-points':
            copy_data(self.scope_bfr, 'Scope Extents (Pts)')
        elif href == 'copy-line-row':
            copy_data(self.scope_bfr, 'Scope Extents (Line/Char)')
        elif href == 'copy-fg':
            copy_data(self.scope_bfr, 'Foreground')
        elif href == 'copy-fg-sim':
            copy_data(self.scope_bfr, 'Foreground (Simulated Trans)')
        elif href == 'copy-bg':
            copy_data(self.scope_bfr, 'Background')
        elif href == 'copy-bg-sim':
            copy_data(self.scope_bfr, 'Background (Simulated Trans)')
        elif href == 'copy-style':
            copy_data(self.scope_bfr, 'Style')
        elif href == 'copy-fg-sel-name':
            copy_data(self.scope_bfr, 'Foreground Selector Name')
        elif href == 'copy-fg-sel-scope':
            copy_data(self.scope_bfr, 'Foreground Selector Scope')
        elif href == 'copy-bg-sel-name':
            copy_data(self.scope_bfr, 'Background Selector Name')
        elif href == 'copy-bg-sel-scope':
            copy_data(self.scope_bfr, 'Background Selector Scope')
        elif href == 'copy-bold-sel-name':
            copy_data(self.scope_bfr, 'Bold Selector Name')
        elif href == 'copy-bold-sel-scope':
            copy_data(self.scope_bfr, 'Bold Selector Scope')
        elif href == 'copy-italic-sel-name':
            copy_data(self.scope_bfr, 'Italic Selector Name')
        elif href == 'copy-italic-sel-scope':
            copy_data(self.scope_bfr, 'Italic Selector Scope')
        elif href == 'copy-scheme':
            copy_data(self.scope_bfr, 'Scheme File')
        elif href == 'copy-syntax':
            copy_data(self.scope_bfr, 'Syntax File')
        elif href == 'scheme' and self.scheme_file is not None:
            window = self.view.window()
            window.run_command(
                'open_file',
                {
                    "file": "${packages}/%s" % self.scheme_file.replace(
                        '\\', '/'
                    ).replace('Packages/', '', 1)
                }
            )
        elif href == 'syntax' and self.syntax_file is not None:
            window = self.view.window()
            window.run_command(
                'open_file',
                {
                    "file": "${packages}/%s" % self.syntax_file.replace(
                        '\\', '/'
                    ).replace('Packages/', '', 1)
                }
            )

    def run(self, v):
        """ Run ScopeHunter and display in the approriate way """
        global css

        self.view = v
        self.window = self.view.window()
        view = self.window.get_output_panel('scope_viewer')
        self.scope_bfr = []
        self.scope_bfr_tool = ['<style>%s</style>' % (css if css is not None else '')]
        self.clips = []
        self.status = ""
        self.scheme_file = None
        self.syntax_file = None
        self.show_statusbar = bool(sh_settings.get("show_statusbar", False))
        self.show_panel = bool(sh_settings.get("show_panel", False))
        if int(sublime.version()) >= 3070:
            self.show_popup = bool(sh_settings.get("show_popup", False))
        else:
            self.show_popup = False
        self.clipboard = bool(sh_settings.get("clipboard", False))
        self.multiselect = bool(sh_settings.get("multiselect", False))
        self.rowcol = bool(sh_settings.get("extent_line_char", False))
        self.points = bool(sh_settings.get("extent_points", False))
        self.console_log = bool(sh_settings.get("console_log", False))
        self.highlight_extent = bool(sh_settings.get("highlight_extent", False))
        self.highlight_scope = sh_settings.get("highlight_scope", 'invalid')
        self.highlight_style = sh_settings.get("highlight_style", 'underline')
        self.highlight_max_size = int(sh_settings.get("highlight_max_size", 100))
        self.scheme_info = bool(sh_settings.get("show_color_scheme_info", False))
        self.first = True
        self.extents = []

        # Get scope info for each selection wanted
        if len(self.view.sel()):
            if self.multiselect:
                for sel in self.view.sel():
                    self.get_info(sel.b)
            else:
                self.get_info(self.view.sel()[0].b)

        # Copy scopes to clipboard
        if self.clipboard:
            sublime.set_clipboard('\n'.join(self.clips))

        # Display in status bar
        if self.show_statusbar:
            sublime.status_message(self.status)

        # Show panel
        if self.show_panel:
            ScopeGlobals.bfr = '\n'.join(self.scope_bfr)
            ScopeGlobals.pt = 0
            view.run_command('scope_hunter_insert')
            ScopeGlobals.clear()
            self.window.run_command("show_panel", {"panel": "output.scope_viewer"})

        if self.show_popup:
            self.view.show_popup(
                '<div class="content">' +
                ''.join(self.scope_bfr_tool) +
                '<br><a href="copy-all" class="copy-link">(copy all)</a></div>',
                location=-1, max_width=600, on_navigate=self.on_navigate
            )

        if self.console_log:
            print('\n'.join(["Scope Hunter"] + self.scope_bfr))

        if self.highlight_extent:
            highlight_style = 0
            if self.highlight_style == 'underline':
                # Use underline if explicity requested,
                # or if doing a find only when under a selection only
                # (only underline can be seen through a selection)
                self.extents = underline(self.extents)
                highlight_style = sublime.DRAW_EMPTY_AS_OVERWRITE
            elif self.highlight_style == 'outline':
                highlight_style = sublime.DRAW_OUTLINED
            self.view.add_regions(
                'scope_hunter',
                self.extents,
                self.highlight_scope,
                '',
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
        if (
            self.enabled and
            bool(sh_settings.get("highlight_extent", False)) and
            len(view.get_regions("scope_hunter"))
        ):
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
    view = None if window is None else window.active_view()
    if view is not None:
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
            if (
                ScopeThreadManager.modified is True and
                time() - ScopeThreadManager.time > ScopeThreadManager.wait_time
            ):
                sublime.set_timeout(lambda: sh_run(), 0)
        sleep(0.5)


def init_css():
    global sh_settings
    global css
    global scheme_matcher

    css_file = sh_settings.get('css_file', None)
    if css_file is None:
        if scheme_matcher.is_dark_theme:
            css_file = 'Packages/' + sh_settings.get(
                'dark_css_override',
                'Packages/ScopeHunter/css/dark.css'
            )
        else:
            css_file = 'Packages/' + sh_settings.get(
                'light_css_override',
                'Packages/ScopeHunter/css/light.css'
            )
    else:
        css_file = 'Packages/' + css_file

    try:
        css = sublime.load_resource(css_file).replace('\r', '\n')
    except:
        css = None
    sh_settings.clear_on_change('reload')
    sh_settings.add_on_change('reload', init_css)


def init_color_scheme():
    global pref_settings
    global scheme_matcher
    pref_settings = sublime.load_settings('Preferences.sublime-settings')
    scheme_file = pref_settings.get('color_scheme')
    try:
        scheme_matcher = ColorSchemeMatcher(scheme_file)
    except:
        scheme_matcher = None
        log("Theme parsing failed!  Ingoring theme related info.\n%s" % str(traceback.format_exc()))
    pref_settings.clear_on_change('reload')
    pref_settings.add_on_change('reload', init_color_scheme)
    init_css()


def plugin_loaded():
    global sh_settings
    sh_settings = sublime.load_settings('scope_hunter.sublime-settings')

    init_color_scheme()

    if 'running_sh_loop' not in globals():
        global running_sh_loop
        running_sh_loop = True
        thread.start_new_thread(sh_loop, ())
