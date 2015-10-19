"""
Scope Hunter.

Licensed under MIT
Copyright (c) 2012 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
from time import time, sleep
import threading
from ScopeHunter.lib.color_scheme_matcher import ColorSchemeMatcher
from ScopeHunter.scope_hunter_notify import notify, error
from ScopeHunter.lib.color_box import color_box
from ScopeHunter.lib.file_strip.json import sanitize_json
import json
import traceback
import os

if 'sh_thread' not in globals():
    sh_thread = None

scheme_matcher = None
sh_settings = {}
sh_theme = None

TOOLTIP_SUPPORT = int(sublime.version()) >= 3072


def log(msg):
    """Logging."""
    print("ScopeHunter: %s" % msg)


def extent_style(option):
    """Configure style of region based on option."""

    style = sublime.HIDE_ON_MINIMAP
    if option == "outline":
        style |= sublime.DRAW_NO_FILL
    elif option == "none":
        style |= sublime.HIDDEN
    elif option == "underline":
        style |= sublime.DRAW_EMPTY_AS_OVERWRITE
    elif option == "thin_underline":
        style |= sublime.DRAW_NO_FILL
        style |= sublime.DRAW_NO_OUTLINE
        style |= sublime.DRAW_SOLID_UNDERLINE
    elif option == "squiggly":
        style |= sublime.DRAW_NO_FILL
        style |= sublime.DRAW_NO_OUTLINE
        style |= sublime.DRAW_SQUIGGLY_UNDERLINE
    elif option == "stippled":
        style |= sublime.DRAW_NO_FILL
        style |= sublime.DRAW_NO_OUTLINE
        style |= sublime.DRAW_STIPPLED_UNDERLINE
    return style


def underline(regions):
    """Convert to empty regions."""

    new_regions = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            new_regions.append(sublime.Region(start))
            start += 1
    return new_regions


def copy_data(bfr, label, index, copy_format=None):
    """Copy data to clipboard from buffer."""

    line = bfr[index]
    if line.startswith(label + ':'):
        text = line.replace(label + ':', '', 1).strip()
        if format is not None:
            text = copy_format(text)
        sublime.set_clipboard(text)
        notify("Copied: %s" % label)


def get_color_box(color, caption, link, index):
    """Display an HTML color box using the given color."""

    border = '#CCCCCC' if scheme_matcher.is_dark_theme else '#333333'
    return (
        '<p><span class="key">%s: </span> %s&nbsp;%s'
        '<br><a href="%s:%d" class="copy-link">(copy)</a></p>' % (
            caption,
            color_box(color, border, 16),
            color.upper(),
            link,
            index
        )
    )


class ScopeHunterEditCommand(sublime_plugin.TextCommand):
    """Edit a view."""

    bfr = None
    pt = None

    def run(self, edit):
        """Insert text into buffer."""

        cls = ScopeHunterEditCommand
        self.view.insert(edit, cls.pt, cls.bfr)

    @classmethod
    def clear(cls):
        """Clear edit buffer."""

        cls.bfr = None
        cls.pt = None


class GetSelectionScope(object):
    """Get the scope and the selection(s)."""

    def next_index(self):
        """Get next index into scope buffer."""

        self.index += 1
        return self.index

    def get_extents(self, pt):
        """Get the scope extent via the sublime API."""

        # pts = self.view.extract_scope(pt)
        # pts1 = self.view.extract_scope(pts.begin())
        # pts2 = self.view.extract_scope(pts.end() - 1)
        # intersect = pts1.intersection(pts2)
        # # print('-----debug extent-----')
        # # print(pt)
        # # print(pts)
        # # print(pts1)
        # # print(pts2)
        # # print(intersect)
        # if (
        #     (pts1.contains(pt) and pt != pts1.end()) and
        #     (not pts2.contains(pt) or pt == pts2.end())
        # ):
        #     pts = sublime.Region(pts1.begin(), intersect.begin())
        # elif (
        #     (pts2.contains(pt) and pt != pts2.end()) and
        #     (not pts1.contains(pt) or pt == pts1.end())
        # ):
        #     if pt == pts1.end():
        #         pts = sublime.Region(pts1.end(), pts2.end())
        #     elif (pts1.begin() == pts2.begin()) or (pts1.end() == pts2.end()):
        #         pts = pts1.cover(pts2)
        pts = None
        file_end = self.view.size()
        scope_name = self.view.scope_name(pt)
        for r in self.view.find_by_selector(scope_name):
            if r.contains(pt):
                pts = r
                break
            elif pt == file_end and r.end() == pt:
                pts = r
                break

        if pts is None:
            pts = sublime.Region(pt)

        row1, col1 = self.view.rowcol(pts.begin())
        row2, col2 = self.view.rowcol(pts.end())

        # Scale back the extent by one for true points included
        if pts.size() < self.highlight_max_size:
            self.extents.append(sublime.Region(pts.begin(), pts.end()))

        if self.points_info or self.rowcol_info:
            if self.points_info:
                self.scope_bfr.append(
                    "%-30s %s" % (
                        "Scope Extents (Pts):",
                        "(%d, %d)" % (pts.begin(), pts.end())
                    )
                )
            if self.rowcol_info:
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
                if self.points_info:
                    self.scope_bfr_tool.append('<span class="key">pts:</span> ')
                    self.scope_bfr_tool.append("(%d, %d)" % (pts.begin(), pts.end()))
                    self.scope_bfr_tool.append(
                        '<br><a href="copy-points:%d" class="copy-link">(copy)</a>' % self.next_index()
                    )
                    if self.rowcol_info:
                        self.scope_bfr_tool.append("<br><br>")
                if self.rowcol_info:
                    self.scope_bfr_tool.append('<span class="key">line/char:</span> ')
                    self.scope_bfr_tool.append(
                        '(<strong>Line:</strong> %d '
                        '<strong>Char:</strong> %d, '
                        '<strong>Line:</strong> %d '
                        '<strong>Char:</strong> %d)'
                        '<br><a href="copy-line-char:%d" class="copy-link">(copy)</a>' % (
                            row1 + 1, col1 + 1, row2 + 1, col2 + 1, self.next_index()
                        )

                    )
                self.scope_bfr_tool.append("</p>")

    def get_scope(self, pt):
        """Get the scope at the cursor."""

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
                '<h1 class="header">Scope</h1><p>%s'
                '<br><a href="copy-scope:%d" class="copy-link">(copy)</a></p>' % (
                    self.view.scope_name(pt).strip(), self.next_index()
                )
            )

        return scope

    def get_appearance(self, color, color_sim, bgcolor, bgcolor_sim, style):
        """Get colors of foreground, background, and simulated transparency colors."""

        self.scope_bfr.append("%-30s %s" % ("Fg:", color))
        if self.show_simulated and len(color) == 9 and not color.lower().endswith('ff'):
            self.scope_bfr.append(
                "%-30s %s" % ("Fg (Simulated Alpha):", color_sim)
            )

        self.scope_bfr.append("%-30s %s" % ("Bg:", bgcolor))
        if self.show_simulated and len(bgcolor) == 9 and not bgcolor.lower().endswith('ff'):
            self.scope_bfr.append(
                "%-30s %s" % ("Bg (Simulated Alpha):", bgcolor_sim)
            )

        self.scope_bfr.append("%-30s %s" % ("Style:", style))

        if self.show_popup:
            self.scope_bfr_tool.append('<h1 class="header">%s</h1>' % "Appearance")
            self.scope_bfr_tool.append(get_color_box(color, 'fg', 'copy-fg', self.next_index()))
            if self.show_simulated and len(color) == 9 and not color.lower().endswith('ff'):
                self.scope_bfr_tool.append(
                    get_color_box(color_sim, 'fg (simulated alpha)', 'copy-fg-sim', self.next_index())
                )
            self.scope_bfr_tool.append(get_color_box(bgcolor, 'bg', 'copy-bg', self.next_index()))
            if self.show_simulated and len(bgcolor) == 9 and not bgcolor.lower().endswith('ff'):
                self.scope_bfr_tool.append(
                    get_color_box(bgcolor_sim, 'bg (simulated alpha)', 'copy-bg-sim', self.next_index())
                )

            if style == "bold":
                tag = "b"
            elif style == "italic":
                tag = "i"
            elif style == "underline":
                tag = "u"
            else:
                tag = "span"
            self.scope_bfr_tool.append(
                '<p><span class="key">style:</span> <%(tag)s>%(type)s</%(tag)s>'
                '<br><a href="copy-style:%(index)d" class="copy-link">(copy)</a></p>' % {
                    "type": style, "tag": tag, "index": self.next_index()
                }
            )

    def get_scheme_syntax(self):
        """Get color scheme and syntax file path."""

        self.scheme_file = scheme_matcher.color_scheme.replace('\\', '/')
        self.syntax_file = self.view.settings().get('syntax')
        self.scope_bfr.append("%-30s %s" % ("Scheme File:", self.scheme_file))
        self.scope_bfr.append("%-30s %s" % ("Syntax File:", self.syntax_file))

        if self.show_popup:
            self.scope_bfr_tool.append('<h1 class="header">%s</h1><p>' % 'Files')
            self.scope_bfr_tool.append(
                '<span class="key">scheme:</span> '
                '<a class="file-link" href="scheme">%s</a>'
                '<br><a href="copy-scheme:%d" class="copy-link">(copy)</a><br><br>' % (
                    self.scheme_file, self.next_index()
                )
            )
            self.scope_bfr_tool.append(
                '<span class="key">syntax:</span> '
                '<a class="file-link" href="syntax">%s</a>'
                '<br><a href="copy-syntax:%d" class="copy-link">(copy)</a></p>' % (
                    self.syntax_file, self.next_index()
                )
            )

    def get_selectors(self, color_selector, bg_selector, style_selectors):
        """Get the selectors used to determine color and/or style."""

        self.scope_bfr.append(
            "%-30s %s" % ("Fg Name:", color_selector.name)
        )
        self.scope_bfr.append(
            "%-30s %s" % ("Fg Scope:", color_selector.scope)
        )
        self.scope_bfr.append(
            "%-30s %s" % ("Bg Name:", bg_selector.name)
        )
        self.scope_bfr.append(
            "%-30s %s" % ("Bg Scope:", bg_selector.scope)
        )
        if style_selectors["bold"].name != "" or style_selectors["bold"].scope != "":
            self.scope_bfr.append(
                "%-30s %s" % ("Bold Name:", style_selectors["bold"].name)
            )
            self.scope_bfr.append(
                "%-30s %s" % ("Bold Scope:", style_selectors["bold"].scope)
            )

        if style_selectors["italic"].name != "" or style_selectors["italic"].scope != "":
            self.scope_bfr.append(
                "%-30s %s" % ("Italic Name:", style_selectors["italic"].name)
            )
            self.scope_bfr.append(
                "%-30s %s" % ("Italic Scope:", style_selectors["italic"].scope)
            )

        if self.show_popup:
            self.scope_bfr_tool.append(
                '<h1 class="header">%s</h1><p>' % "Selectors"
            )
            self.scope_bfr_tool.append(
                '<span class="key">fg name:</span> %s'
                '<br><a href="copy-fg-sel-name:%d" class="copy-link">(copy)</a>' % (
                    color_selector.name, self.next_index()
                )
            )
            self.scope_bfr_tool.append(
                '<br><br><span class="key">fg scope:</span> %s'
                '<br><a href="copy-fg-sel-scope:%d" class="copy-link">(copy)</a>' % (
                    color_selector.scope, self.next_index()
                )
            )
            self.scope_bfr_tool.append(
                '<br><br><span class="key">bg name:</span> %s'
                '<br><a href="copy-bg-sel-name:%d" class="copy-link">(copy)</a>' % (
                    bg_selector.name, self.next_index()
                )
            )
            self.scope_bfr_tool.append(
                '<br><br><span class="key">bg scope:</span> %s'
                '<br><a href="copy-bg-sel-scope:%d" class="copy-link">(copy)</a>' % (
                    bg_selector.scope, self.next_index()
                )
            )
            if style_selectors["bold"].name != "" or style_selectors["bold"].scope != "":
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">bold name:</span> %s'
                    '<br><a href="copy-bold-sel-name:%d" class="copy-link">(copy)</a>' % (
                        style_selectors["bold"].name, self.next_index()
                    )
                )
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">bold scope:</span> %s'
                    '<br><a href="copy-bold-sel-scope:%d" class="copy-link">(copy)</a>' % (
                        style_selectors["bold"].scope, self.next_index()
                    )
                )
            if style_selectors["italic"].name != "" or style_selectors["italic"].scope != "":
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">italic name:</span> %s'
                    '<br><a href="copy-italic-sel-name:%d" class="copy-link">(copy)</a>' % (
                        style_selectors["italic"].name, self.next_index()
                    )
                )
                self.scope_bfr_tool.append(
                    '<br><br><span class="key">italic scope:</span> %s'
                    '<br><a href="copy-italic-sel-scope:%d" class="copy-link">(copy)</a>' % (
                        style_selectors["italic"].scope, self.next_index()
                    )
                )
            self.scope_bfr_tool.append('</p>')

    def get_info(self, pt):
        """Get scope related info."""

        scope = self.get_scope(pt)

        if self.rowcol_info or self.points_info or self.highlight_extent:
            self.get_extents(pt)

        if (self.appearance_info or self.selector_info) and scheme_matcher is not None:
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

                if self.appearance_info:
                    self.get_appearance(color, color_sim, bgcolor, bgcolor_sim, style)

                if self.selector_info:
                    self.get_selectors(color_selector, bg_selector, style_selectors)
            except Exception:
                log("Evaluating theme failed!  Ignoring theme related info.\n%s" % str(traceback.format_exc()))
                error("Evaluating theme failed!")
                self.scheme_info = False

        if self.file_path_info and scheme_matcher:
            self.get_scheme_syntax()

        # Divider
        self.next_index()
        self.scope_bfr.append("------")

    def on_navigate(self, href):
        """Exceute link callback."""

        params = href.split(':')
        key = params[0]
        index = int(params[1]) if len(params) > 1 else None
        if key == 'copy-all':
            sublime.set_clipboard('\n'.join(self.scope_bfr))
            notify('Copied: All')
        elif key == 'copy-scope':
            copy_data(
                self.scope_bfr,
                r'Scope',
                index,
                lambda x: x.replace('\n' + ' ' * 31, ' ')
            )
        elif key == 'copy-points':
            copy_data(self.scope_bfr, 'Scope Extents (Pts)', index)
        elif key == 'copy-line-char':
            copy_data(self.scope_bfr, 'Scope Extents (Line/Char)', index)
        elif key == 'copy-fg':
            copy_data(self.scope_bfr, 'Fg', index)
        elif key == 'copy-fg-sim':
            copy_data(self.scope_bfr, 'Fg (Simulated Alpha)', index)
        elif key == 'copy-bg':
            copy_data(self.scope_bfr, 'Bg', index)
        elif key == 'copy-bg-sim':
            copy_data(self.scope_bfr, 'Bg (Simulated Alpha)', index)
        elif key == 'copy-style':
            copy_data(self.scope_bfr, 'Style', index)
        elif key == 'copy-fg-sel-name':
            copy_data(self.scope_bfr, 'Fg Name', index)
        elif key == 'copy-fg-sel-scope':
            copy_data(self.scope_bfr, 'Fg Scope', index)
        elif key == 'copy-bg-sel-name':
            copy_data(self.scope_bfr, 'Bg Name', index)
        elif key == 'copy-bg-sel-scope':
            copy_data(self.scope_bfr, 'Bg Scope', index)
        elif key == 'copy-bold-sel-name':
            copy_data(self.scope_bfr, 'Bold Name', index)
        elif key == 'copy-bold-sel-scope':
            copy_data(self.scope_bfr, 'Bold Scope', index)
        elif key == 'copy-italic-sel-name':
            copy_data(self.scope_bfr, 'Italic Name', index)
        elif key == 'copy-italic-sel-scope':
            copy_data(self.scope_bfr, 'Italic Scope', index)
        elif key == 'copy-scheme':
            copy_data(self.scope_bfr, 'Scheme File', index)
        elif key == 'copy-syntax':
            copy_data(self.scope_bfr, 'Syntax File', index)
        elif key == 'scheme' and self.scheme_file is not None:
            window = self.view.window()
            window.run_command(
                'open_file',
                {
                    "file": "${packages}/%s" % self.scheme_file.replace(
                        '\\', '/'
                    ).replace('Packages/', '', 1)
                }
            )
        elif key == 'syntax' and self.syntax_file is not None:
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
        """Run ScopeHunter and display in the approriate way."""

        self.view = v
        self.window = self.view.window()
        view = self.window.get_output_panel('scope_viewer')
        self.scope_bfr = []
        self.scope_bfr_tool = ['<style>%s</style>' % (sh_theme.css if sh_theme.css is not None else '')]
        self.clips = []
        self.status = ""
        self.scheme_file = None
        self.syntax_file = None
        self.show_statusbar = bool(sh_settings.get("show_statusbar", False))
        self.show_panel = bool(sh_settings.get("show_panel", False))
        if TOOLTIP_SUPPORT:
            self.show_popup = bool(sh_settings.get("show_popup", False))
        else:
            self.show_popup = False
        self.clipboard = bool(sh_settings.get("clipboard", False))
        self.multiselect = bool(sh_settings.get("multiselect", False))
        self.console_log = bool(sh_settings.get("console_log", False))
        self.highlight_extent = bool(sh_settings.get("highlight_extent", False))
        self.highlight_scope = sh_settings.get("highlight_scope", 'invalid')
        self.highlight_style = sh_settings.get("highlight_style", 'outline')
        self.highlight_max_size = int(sh_settings.get("highlight_max_size", 100))
        self.rowcol_info = bool(sh_settings.get("extent_line_char", False))
        self.points_info = bool(sh_settings.get("extent_points", False))
        self.appearance_info = bool(sh_settings.get("styling", False))
        self.show_simulated = bool(sh_settings.get("show_simulated_alpha_colors", False))
        self.file_path_info = bool(sh_settings.get("file_paths", False))
        self.selector_info = bool(sh_settings.get("selectors", False))
        self.scheme_info = self.appearance_info or self.selector_info
        self.first = True
        self.extents = []

        # Get scope info for each selection wanted
        self.index = -1
        if len(self.view.sel()):
            if self.multiselect:
                count = 0
                for sel in self.view.sel():
                    if count > 0 and self.show_popup:
                        self.scope_bfr_tool.append('<div class="divider"></div>')
                    self.get_info(sel.b)
                    count += 1
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
            ScopeHunterEditCommand.bfr = '\n'.join(self.scope_bfr)
            ScopeHunterEditCommand.pt = 0
            view.run_command('scope_hunter_edit')
            ScopeHunterEditCommand.clear()
            self.window.run_command("show_panel", {"panel": "output.scope_viewer"})

        if self.show_popup:
            if self.scheme_info or self.rowcol_info or self.points_info or self.file_path_info:
                tail = '<div class="divider"></div><a href="copy-all" class="copy-link">(copy all)</a></div>'
            else:
                tail = '</div>'
            self.view.show_popup(
                '<div class="content">' +
                ''.join(self.scope_bfr_tool) +
                tail,
                location=-1, max_width=600, on_navigate=self.on_navigate
            )

        if self.console_log:
            print('\n'.join(["Scope Hunter"] + self.scope_bfr))

        if self.highlight_extent:
            style = extent_style(self.highlight_style)
            if style == 'underline':
                self.extents = underline(self.extents)
            self.view.add_regions(
                'scope_hunter',
                self.extents,
                self.highlight_scope,
                '',
                style
            )

get_selection_scopes = GetSelectionScope()


class GetSelectionScopeCommand(sublime_plugin.TextCommand):
    """Command to get the selection(s) scope."""

    def run(self, edit):
        """On demand scope request."""

        sh_thread.modified = True

    def is_enabled(self):
        """Check if we should scope this view."""

        return sh_thread.is_enabled(self.view)


class ToggleSelectionScopeCommand(sublime_plugin.ApplicationCommand):
    """Command to toggle instant scoper."""

    def run(self):
        """Enable or disable instant scoper."""

        sh_thread.instant_scoper = False if sh_thread.instant_scoper else True
        if sh_thread.instant_scoper:
            sh_thread.modified = True
            sh_thread.time = time()
        else:
            win = sublime.active_window()
            if win is not None:
                view = win.active_view()
                if (
                    view is not None and
                    sh_thread.is_enabled(view) and
                    bool(sh_settings.get("highlight_extent", False)) and
                    len(view.get_regions("scope_hunter"))
                ):
                    view.erase_regions("scope_hunter")


class SelectionScopeListener(sublime_plugin.EventListener):
    """Listern for instant scoping."""

    def clear_regions(self, view):
        """Clear the highlight regions."""

        if (
            bool(sh_settings.get("highlight_extent", False)) and
            len(view.get_regions("scope_hunter"))
        ):
            view.erase_regions("scope_hunter")

    def on_selection_modified(self, view):
        """Clean up regions or let thread know there was a modification."""

        enabled = sh_thread.is_enabled(view)
        if not sh_thread.instant_scoper or not enabled:
            # clean up dirty highlights
            if enabled:
                self.clear_regions(view)
        else:
            sh_thread.modified = True
            sh_thread.time = time()


class ShThread(threading.Thread):
    """Load up defaults."""

    def __init__(self):
        """Setup the thread."""
        self.reset()
        threading.Thread.__init__(self)

    def reset(self):
        """Reset the thread variables."""
        self.wait_time = 0.12
        self.time = time()
        self.modified = False
        self.ignore_all = False
        self.instant_scoper = False
        self.abort = False

    def payload(self):
        """Code to run."""
        # Ignore selection inside the routine
        self.modified = False
        self.ignore_all = True
        window = sublime.active_window()
        view = None if window is None else window.active_view()
        if view is not None:
            get_selection_scopes.run(view)
        self.ignore_all = False
        self.time = time()

    def is_enabled(self, view):
        """Check if we can execute."""
        return not view.settings().get("is_widget") and not self.ignore_all

    def kill(self):
        """Kill thread."""
        self.abort = True
        while self.is_alive():
            pass
        self.reset()

    def run(self):
        """Thread loop."""
        while not self.abort:
            if not self.ignore_all:
                if (
                    self.modified is True and
                    time() - self.time > self.wait_time
                ):
                    sublime.set_timeout(self.payload, 0)
            sleep(0.5)


class ShTheme(object):
    """Theme object for the tooltip."""

    def __init__(self):
        """Initialize."""

        self.setup()

    def read_theme(self, theme, default_theme):
        """Read tooltip theme."""

        theme_content = None
        self.border_color = '#000'

        for t in (theme, default_theme):
            try:
                theme_content = json.loads(
                    sanitize_json(sublime.load_resource(t))
                )
                break
            except Exception:
                pass

        if theme_content is not None:
            self.border_color = theme_content.get('border_color', None)
            self.css_file = '/'.join(
                [os.path.dirname(theme), theme_content.get('css', '')]
            )
            try:
                self.css = sublime.load_resource(self.css_file).replace('\r', '')
            except Exception:
                self.css = None

    def has_changed(self):
        """
        See if scheme has changed.

        Reload events recently are always reloading,
        So maybe we will use this to check if reload is needed.
        """
        pref_settings = sublime.load_settings('Preferences.sublime-settings')
        return self.scheme_file != pref_settings.get('color_scheme')

    def get_theme_res(self, *args, **kwargs):
        """Get theme resource."""

        link = kwargs.get('link', False)
        res = '/'.join(('Packages', self.tt_theme) + args)
        return 'res://' + res if link else res

    def setup(self):
        """Setup the theme object."""

        pref_settings = sublime.load_settings('Preferences.sublime-settings')
        self.scheme_file = pref_settings.get('color_scheme')
        self.tt_theme = sh_settings.get('tooltip_theme', 'ScopeHunter/tt_theme').rstrip('/')
        theme_file = 'dark' if scheme_matcher.is_dark_theme else 'light'

        self.read_theme(
            'Packages/%s/%s.tt_theme' % (self.tt_theme, theme_file),
            'Packages/ScopeHunter/tt_theme/%s.tt_theme' % theme_file
        )


def init_color_scheme():
    """Setup color scheme match object with current scheme."""

    global scheme_matcher
    pref_settings = sublime.load_settings('Preferences.sublime-settings')
    scheme_file = pref_settings.get('color_scheme')
    try:
        scheme_matcher = ColorSchemeMatcher(scheme_file)
    except Exception:
        scheme_matcher = None
        log("Theme parsing failed!  Ingoring theme related info.\n%s" % str(traceback.format_exc()))


def reinit_plugin():
    """Relaod scheme object and tooltip theme."""

    init_color_scheme()
    sh_theme.setup()


def init_plugin():
    """Setup plugin variables and objects."""

    global sh_thread
    global sh_settings
    global sh_theme

    # Preferences Settings
    pref_settings = sublime.load_settings('Preferences.sublime-settings')

    # Setup settings
    sh_settings = sublime.load_settings('scope_hunter.sublime-settings')

    # Setup color scheme
    init_color_scheme()
    sh_theme = ShTheme()

    pref_settings.clear_on_change('scopehunter_reload')
    pref_settings.add_on_change('scopehunter_reload', reinit_plugin)

    sh_settings.clear_on_change('reload')
    sh_settings.add_on_change('reload', sh_theme.setup)

    # Setup thread
    if sh_thread is not None:
        # This shouldn't be needed, but just in case
        sh_thread.kill()
    sh_thread = ShThread()
    sh_thread.start()


def plugin_loaded():
    """Setup plugin."""

    init_plugin()


def plugin_unloaded():
    """Kill the thead."""

    sh_thread.kill()
