"""
Scope Hunter.

Licensed under MIT
Copyright (c) 2012 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
from time import time, sleep
import threading
from ScopeHunter.scope_hunter_notify import notify, error
import traceback
from textwrap import dedent
from ScopeHunter.lib.color_scheme_matcher import ColorSchemeMatcher

TOOLTIP_SUPPORT = int(sublime.version()) >= 3124
SCOPE_CONTEXT_BACKTRACE_SUPPORT = int(sublime.version()) >= 4087

if TOOLTIP_SUPPORT:
    import mdpopups

if 'sh_thread' not in globals():
    sh_thread = None

scheme_matcher = None
sh_settings = {}

if TOOLTIP_SUPPORT:
    ADD_CSS = dedent(
        '''
        {%- if var.mdpopups_version >= (2, 0, 0) %}
        div.scope-hunter { margin: 0; padding: 0.5rem; }
        {%- else %}
        div.scope-hunter { margin: 0; padding: 0; }
        {%- endif %}
        .scope-hunter .small { font-size: 0.8rem; }
        .scope-hunter .header { {{'.string'|css('color')}} }
        ins { text-decoration: underline; }
        span.glow { background-color: color(var(--foreground) a(0.2)); }
        '''
    )

COPY_ALL = '''
---

[(copy all)](copy-all){: .small} [(reload scheme)](reload){: .small}
'''

RELOAD = '''
---

[(reload scheme)](reload){: .small}
'''


# Text Entry
ENTRY = "%-30s %s"
SCOPE_KEY = "Scope"
CONTEXT_BACKTRACE_KEY = "Scope Context Backtrace"
PTS_KEY = "Scope Extents (Pts)"
PTS_VALUE = "(%d, %d)"
CHAR_LINE_KEY = "Scope Extents (Line/Char)"
CHAR_LINE_VALUE = "(line: %d char: %d, line: %d char: %d)"
FG_KEY = "Fg"
FG_SIM_KEY = "Fg (Simulated Alpha)"
BG_KEY = "Bg"
BG_SIM_KEY = "Bg (Simulated Alpha)"
STYLE_KEY = "Style"
FG_NAME_KEY = "Fg Name"
FG_SCOPE_KEY = "Fg Scope"
BG_NAME_KEY = "Bg Name"
BG_SCOPE_KEY = "Bg Scope"
BOLD_NAME_KEY = "Bold Name"
BOLD_SCOPE_KEY = "Bold Scope"
ITALIC_NAME_KEY = "Italic Name"
ITALIC_SCOPE_KEY = "Italic Scope"
UNDERLINE_NAME_KEY = "Underline Name"
UNDERLINE_SCOPE_KEY = "Underline Scope"
GLOW_NAME_KEY = "Glow Name"
GLOW_SCOPE_KEY = "Glow Scope"
SCHEME_KEY = "tmTheme File"
SYNTAX_KEY = "Syntax File"
OVERRIDE_SCHEME_KEY = "Scheme"
HASHED_FG_KEY = "Hashed Fg"
HASHED_FG_SIM_KEY = "Hashed Fg (Simulated Alpha)"
HASHED_FG_NAME_KEY = "Hashed Fg Name"
HASHED_FG_SCOPE_KEY = "Hashed Fg Scope"


def log(msg):
    """Logging."""
    print("ScopeHunter: %s" % msg)


def debug(msg):
    """Debug."""
    if sh_settings.get('debug', False):
        log(msg)


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
        if copy_format is not None:
            text = copy_format(text)
        sublime.set_clipboard(text)
        notify("Copied: %s" % label)


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

    def init_template_vars(self):
        """Initialize template variables."""

        self.template_vars = {}

    def next_index(self):
        """Get next index into scope buffer."""

        self.index += 1
        return self.index

    def get_color_box(self, color, key, index):
        """Display an HTML color box using the given color."""

        border = '#CCCCCC'
        border2 = '#333333'
        padding = int(self.view.settings().get('line_padding_top', 0))
        padding += int(self.view.settings().get('line_padding_bottom', 0))
        box_height = int(self.view.line_height()) - padding - 2
        check_size = int((box_height - 4) / 4)
        if isinstance(color, list):
            box_width = box_height * (len(color) if len(color) >= 1 else 1)
            colors = [c.upper() for c in color]
        else:
            box_width = box_height
            colors = [color.upper()]
        if check_size < 2:
            check_size = 2
        self.template_vars['%s_preview' % key] = mdpopups.color_box(
            colors, border, border2, height=box_height,
            width=box_width, border_size=2, check_size=check_size
        )
        self.template_vars['%s_color' % key] = ', '.join(colors)
        self.template_vars['%s_index' % key] = index

    def get_extents(self, pt):
        """Get the scope extent via the sublime API."""

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
                self.scope_bfr.append(ENTRY % (PTS_KEY + ':', PTS_VALUE % (pts.begin(), pts.end())))
            if self.rowcol_info:
                self.scope_bfr.append(
                    ENTRY % (CHAR_LINE_KEY + ':', CHAR_LINE_VALUE % (row1 + 1, col1 + 1, row2 + 1, col2 + 1))
                )

            if self.show_popup:
                if self.points_info:
                    self.template_vars["pt_extent"] = True
                    self.template_vars["extent_start"] = pts.begin()
                    self.template_vars["extent_end"] = pts.end()
                    self.template_vars["extent_pt_index"] = self.next_index()
                if self.rowcol_info:
                    self.template_vars["rowcol_extent"] = True
                    self.template_vars["l_start"] = row1 + 1
                    self.template_vars["l_end"] = row2 + 1
                    self.template_vars["c_start"] = col1 + 1
                    self.template_vars["c_end"] = col2 + 1
                    self.template_vars["line_char_index"] = self.next_index()

    def get_scope(self, pt):
        """Get the scope at the cursor."""

        scope = self.view.scope_name(pt)
        spacing = "\n" + (" " * 31)

        if self.clipboard:
            self.clips.append(scope)

        if self.first and self.show_statusbar:
            self.status = scope
            self.first = False

        self.scope_bfr.append(ENTRY % (SCOPE_KEY + ':', self.view.scope_name(pt).strip().replace(" ", spacing)))

        if self.show_popup:
            self.template_vars['scope'] = self.view.scope_name(pt).strip()
            self.template_vars['scope_index'] = self.next_index()

        return scope

    def get_scope_context_backtrace(self, pt):
        """Get the context backtrace of the current scope."""

        spacing = "\n" + (" " * 31)

        if SCOPE_CONTEXT_BACKTRACE_SUPPORT:
            stack = list(reversed(self.view.context_backtrace(pt)))
        else:
            stack = []

        backtrace = ''
        for i, ctx in enumerate(stack):
            backtrace += '%s: %s' % (i, ctx)

        if SCOPE_CONTEXT_BACKTRACE_SUPPORT and self.context_backtrace_info:
            self.scope_bfr.append(ENTRY % (CONTEXT_BACKTRACE_KEY + ':', spacing.join(stack)))

            if self.show_popup:
                self.template_vars['context_backtrace'] = True
                self.template_vars["context_backtrace_stack"] = stack
                self.template_vars['context_backtrace_index'] = self.next_index()

        return backtrace

    def get_appearance(self, color, color_sim, bgcolor, bgcolor_sim, style, color_gradient):
        """Get colors of foreground, background, and simulated transparency colors."""

        self.scope_bfr.append(ENTRY % (FG_KEY + ":", color))
        if self.show_simulated and len(color) == 9 and not color.lower().endswith('ff'):
            self.scope_bfr.append(ENTRY % (FG_SIM_KEY + ":", color_sim))

        colors = []
        colors_sim = []
        show_sim = False
        if color_gradient:
            for c, cs in color_gradient:
                colors.append(c)
                if len(cs) == 9 and not cs.lower().endswith('ff'):
                    show_sim = True
                colors_sim.append(cs)
            self.scope_bfr.append(ENTRY % (HASHED_FG_KEY + ":", ', '.join(colors)))
            if self.show_simulated and show_sim:
                self.scope_bfr.append(ENTRY % (HASHED_FG_SIM_KEY + ":", ', '.join(colors_sim)))

        self.scope_bfr.append(ENTRY % (BG_KEY + ":", bgcolor))
        if self.show_simulated and len(bgcolor) == 9 and not bgcolor.lower().endswith('ff'):
            self.scope_bfr.append(ENTRY % (BG_SIM_KEY + ":", bgcolor_sim))

        self.scope_bfr.append(ENTRY % (STYLE_KEY + ":", "normal" if not style else style))

        if self.show_popup:
            self.template_vars['appearance'] = True
            self.get_color_box(color, 'fg', self.next_index())
            if self.show_simulated and len(color) == 9 and not color.lower().endswith('ff'):
                self.template_vars['fg_sim'] = True
                self.get_color_box(color_sim, 'fg_sim', self.next_index())
            if color_gradient:
                self.template_vars['fg_hash'] = True
                self.get_color_box(colors, 'fg_hash', self.next_index())
                if self.show_simulated and show_sim:
                    self.template_vars['fg_hash_sim'] = True
                    self.get_color_box(colors_sim, 'fg_hash_sim', self.next_index())
            self.get_color_box(bgcolor, 'bg', self.next_index())
            if self.show_simulated and len(bgcolor) == 9 and not bgcolor.lower().endswith('ff'):
                self.template_vars['bg_sim'] = True
                self.get_color_box(bgcolor_sim, 'bg_sim', self.next_index())

            style_label = set()
            style_open = []
            style_close = []

            for s in style.split(' '):
                if s == "bold":
                    style_open.append('<b>')
                    style_close.insert(0, '</b>')
                    style_label.add('bold')
                elif s == "italic":
                    style_open.append('<i>')
                    style_close.insert(0, '</i>')
                    style_label.add('italic')
                elif s == "underline":
                    style_open.append('<ins>')
                    style_close.insert(0, '</ins>')
                    style_label.add('underline')
                elif s == "glow":
                    style_open.append('<span class="glow">')
                    style_close.insert(0, '</span>')
                    style_label.add('glow')

            if len(style_label) == 0:
                style_label.add('normal')

            self.template_vars["style_open"] = ''.join(style_open)
            self.template_vars["style_close"] = ''.join(style_close)
            self.template_vars["style"] = ' '.join(list(style_label))
            self.template_vars["style_index"] = self.next_index()

    def get_scheme_syntax(self):
        """Get color scheme and syntax file path."""

        self.overrides = scheme_matcher.overrides

        self.scheme_file = scheme_matcher.color_scheme.replace('\\', '/')
        is_tmtheme = not self.scheme_file.endswith(('.sublime-color-scheme', '.hidden-color-scheme'))
        self.syntax_file = self.view.settings().get('syntax')
        self.scope_bfr.append(ENTRY % (SYNTAX_KEY + ":", self.syntax_file))
        if is_tmtheme:
            self.scope_bfr.append(ENTRY % (SCHEME_KEY + ":", self.scheme_file))
        text = []
        for idx, override in enumerate(self.overrides, 1):
            text.append(ENTRY % (OVERRIDE_SCHEME_KEY + (" %d:" % idx), override))
        self.scope_bfr.append('\n'.join(text))

        if self.show_popup:
            self.template_vars['files'] = True
            self.template_vars["syntax"] = self.syntax_file
            self.template_vars["syntax_index"] = self.next_index()
            if is_tmtheme:
                self.template_vars["scheme"] = self.scheme_file
                self.template_vars["scheme_index"] = self.next_index()
            self.template_vars["overrides"] = self.overrides
            self.template_vars["overrides_index"] = self.next_index()

    def get_selectors(self, color_selector, bg_selector, style_selectors, color_gradient_selector):
        """Get the selectors used to determine color and/or style."""

        self.scope_bfr.append(ENTRY % (FG_NAME_KEY + ":", color_selector.name))
        self.scope_bfr.append(ENTRY % (FG_SCOPE_KEY + ":", color_selector.scope))
        if color_gradient_selector:
            self.scope_bfr.append(ENTRY % (HASHED_FG_NAME_KEY + ":", color_gradient_selector.name))
            self.scope_bfr.append(ENTRY % (HASHED_FG_SCOPE_KEY + ":", color_gradient_selector.scope))
        self.scope_bfr.append(ENTRY % (BG_NAME_KEY + ":", bg_selector.name))
        self.scope_bfr.append(ENTRY % (BG_SCOPE_KEY + ":", bg_selector.scope))
        if style_selectors["bold"].name != "" or style_selectors["bold"].scope != "":
            self.scope_bfr.append(ENTRY % (BOLD_NAME_KEY + ":", style_selectors["bold"].name))
            self.scope_bfr.append(ENTRY % (BOLD_SCOPE_KEY + ":", style_selectors["bold"].scope))

        if style_selectors["italic"].name != "" or style_selectors["italic"].scope != "":
            self.scope_bfr.append(ENTRY % (ITALIC_NAME_KEY + ":", style_selectors["italic"].name))
            self.scope_bfr.append(ENTRY % (ITALIC_SCOPE_KEY + ":", style_selectors["italic"].scope))

        if style_selectors["underline"].name != "" or style_selectors["underline"].scope != "":
            self.scope_bfr.append(ENTRY % (UNDERLINE_NAME_KEY + ":", style_selectors["underline"].name))
            self.scope_bfr.append(ENTRY % (UNDERLINE_SCOPE_KEY + ":", style_selectors["underline"].scope))

        if style_selectors["glow"].name != "" or style_selectors["glow"].scope != "":
            self.scope_bfr.append(ENTRY % (GLOW_NAME_KEY + ":", style_selectors["glow"].name))
            self.scope_bfr.append(ENTRY % (GLOW_SCOPE_KEY + ":", style_selectors["glow"].scope))

        if self.show_popup:
            self.template_vars['selectors'] = True
            self.template_vars['fg_name'] = color_selector.name
            self.template_vars['fg_name_index'] = self.next_index()
            self.template_vars['fg_scope'] = color_selector.scope
            self.template_vars['fg_scope_index'] = self.next_index()
            if color_gradient_selector:
                self.template_vars['fg_hash_name'] = color_gradient_selector.name
                self.template_vars['fg_hash_name_index'] = self.next_index()
                self.template_vars['fg_hash_scope'] = color_gradient_selector.scope
                self.template_vars['fg_hash_scope_index'] = self.next_index()
            self.template_vars['bg_name'] = bg_selector.name
            self.template_vars['bg_name_index'] = self.next_index()
            self.template_vars['bg_scope'] = bg_selector.scope
            self.template_vars['bg_scope_index'] = self.next_index()
            if style_selectors["bold"].name != "" or style_selectors["bold"].scope != "":
                self.template_vars['bold'] = True
                self.template_vars['bold_name'] = style_selectors["bold"].name
                self.template_vars['bold_name_index'] = self.next_index()
                self.template_vars['bold_scope'] = style_selectors["bold"].scope
                self.template_vars['bold_scope_index'] = self.next_index()
            if style_selectors["italic"].name != "" or style_selectors["italic"].scope != "":
                self.template_vars['italic'] = True
                self.template_vars['italic_name'] = style_selectors["italic"].name
                self.template_vars['italic_name_index'] = self.next_index()
                self.template_vars['italic_scope'] = style_selectors["italic"].scope
                self.template_vars['italic_scope_index'] = self.next_index()
            if style_selectors["underline"].name != "" or style_selectors["underline"].scope != "":
                self.template_vars['underline'] = True
                self.template_vars['underline_name'] = style_selectors["underline"].name
                self.template_vars['underline_name_index'] = self.next_index()
                self.template_vars['underline_scope'] = style_selectors["underline"].scope
                self.template_vars['underline_scope_index'] = self.next_index()
            if style_selectors["glow"].name != "" or style_selectors["glow"].scope != "":
                self.template_vars['glow'] = True
                self.template_vars['glow_name'] = style_selectors["glow"].name
                self.template_vars['glow_name_index'] = self.next_index()
                self.template_vars['glow_scope'] = style_selectors["glow"].scope
                self.template_vars['glow_scope_index'] = self.next_index()

    def get_info(self, pt):
        """Get scope related info."""

        scope = self.get_scope(pt)

        self.get_scope_context_backtrace(pt)

        if self.rowcol_info or self.points_info or self.highlight_extent:
            self.get_extents(pt)

        if (self.appearance_info or self.selector_info) and scheme_matcher is not None:
            try:
                match = scheme_matcher.guess_color(scope)
                color = match.fg
                bgcolor = match.bg
                color_sim = match.fg_simulated
                bgcolor_sim = match.bg_simulated
                style = match.style
                bg_selector = match.bg_selector
                color_selector = match.fg_selector
                style_selectors = match.style_selectors
                color_gradient = match.color_gradient
                color_gradient_selector = match.color_gradient_selector

                # if match.color_gradient is not None:
                #     color = self.view.style_for_scope(scope)["foreground"]
                #     color_sim = color

                if self.appearance_info:
                    self.get_appearance(color, color_sim, bgcolor, bgcolor_sim, style, color_gradient)

                if self.selector_info:
                    self.get_selectors(color_selector, bg_selector, style_selectors, color_gradient_selector)
            except Exception:
                log("Evaluating theme failed!  Ignoring theme related info.")
                debug(str(traceback.format_exc()))
                error("Evaluating theme failed!")
                self.scheme_info = False

        if self.file_path_info and scheme_matcher:
            self.get_scheme_syntax()

        # Divider
        self.next_index()
        self.scope_bfr.append("------")

        if self.show_popup:
            self.scope_bfr_tool.append(
                mdpopups.md2html(
                    self.view,
                    self.popup_template,
                    template_vars=self.template_vars,
                    template_env_options={
                        "trim_blocks": True,
                        "lstrip_blocks": True
                    }
                )
            )

    def on_navigate(self, href):
        """Exceute link callback."""

        params = href.split(':')
        key = params[0]
        index = int(params[1]) if len(params) > 1 else None
        if key == 'reload':
            mdpopups.hide_popup(self.view)
            reinit_plugin()
            self.view.run_command('get_selection_scope')
        if key == 'copy-all':
            sublime.set_clipboard('\n'.join(self.scope_bfr))
            notify('Copied: All')
        elif key == 'copy-scope':
            copy_data(
                self.scope_bfr,
                SCOPE_KEY,
                index,
                lambda x: x.replace('\n' + ' ' * 31, ' ')
            )
        elif key == 'copy-context-backtrace':
            copy_data(
                self.scope_bfr,
                CONTEXT_BACKTRACE_KEY,
                index,
                lambda x: x.replace('\n' + ' ' * 31, '\n')
            )
        elif key == 'copy-points':
            copy_data(self.scope_bfr, PTS_KEY, index)
        elif key == 'copy-line-char':
            copy_data(self.scope_bfr, CHAR_LINE_KEY, index)
        elif key == 'copy-fg':
            copy_data(self.scope_bfr, FG_KEY, index)
        elif key == 'copy-fg-sim':
            copy_data(self.scope_bfr, FG_SIM_KEY, index)
        elif key == 'copy-fg-hash':
            copy_data(self.scope_bfr, HASHED_FG_KEY, index)
        elif key == 'copy-fg-hash-sim':
            copy_data(self.scope_bfr, HASHED_FG_SIM_KEY, index)
        elif key == 'copy-bg':
            copy_data(self.scope_bfr, BG_KEY, index)
        elif key == 'copy-bg-sim':
            copy_data(self.scope_bfr, BG_SIM_KEY, index)
        elif key == 'copy-style':
            copy_data(self.scope_bfr, STYLE_KEY, index)
        elif key == 'copy-fg-sel-name':
            copy_data(self.scope_bfr, FG_NAME_KEY, index)
        elif key == 'copy-fg-sel-scope':
            copy_data(self.scope_bfr, FG_SCOPE_KEY, index)
        elif key == 'copy-fg-hash-sel-name':
            copy_data(self.scope_bfr, HASHED_FG_NAME_KEY, index)
        elif key == 'copy-fg-hash-sel-scope':
            copy_data(self.scope_bfr, HASHED_FG_SCOPE_KEY, index)
        elif key == 'copy-bg-sel-name':
            copy_data(self.scope_bfr, BG_NAME_KEY, index)
        elif key == 'copy-bg-sel-scope':
            copy_data(self.scope_bfr, BG_SCOPE_KEY, index)
        elif key == 'copy-bold-sel-name':
            copy_data(self.scope_bfr, BOLD_NAME_KEY, index)
        elif key == 'copy-bold-sel-scope':
            copy_data(self.scope_bfr, BOLD_SCOPE_KEY, index)
        elif key == 'copy-italic-sel-name':
            copy_data(self.scope_bfr, ITALIC_NAME_KEY, index)
        elif key == 'copy-italic-sel-scope':
            copy_data(self.scope_bfr, ITALIC_SCOPE_KEY, index)
        elif key == 'copy-underline-sel-name':
            copy_data(self.scope_bfr, UNDERLINE_NAME_KEY, index)
        elif key == 'copy-underline-sel-scope':
            copy_data(self.scope_bfr, UNDERLINE_SCOPE_KEY, index)
        elif key == 'copy-glow-sel-name':
            copy_data(self.scope_bfr, GLOW_NAME_KEY, index)
        elif key == 'copy-glow-sel-scope':
            copy_data(self.scope_bfr, GLOW_SCOPE_KEY, index)
        elif key == 'copy-scheme':
            copy_data(self.scope_bfr, SCHEME_KEY, index)
        elif key == 'copy-syntax':
            copy_data(self.scope_bfr, SYNTAX_KEY, index)
        elif key == 'copy-overrides':
            copy_data(self.scope_bfr, OVERRIDE_SCHEME_KEY, index, lambda text: self.overrides[int(params[2]) - 1])
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
        elif key == 'override':
            window = self.view.window()
            window.run_command(
                'open_file',
                {
                    "file": "${packages}/%s" % self.overrides[int(params[2]) - 1].replace('Packages/', '', 1)
                }
            )

    def run(self, v):
        """Run ScopeHunter and display in the approriate way."""

        self.view = v
        self.window = self.view.window()
        view = self.window.create_output_panel('scopehunter.results', unlisted=True)
        self.scope_bfr = []
        self.scope_bfr_tool = []
        self.clips = []
        self.status = ""
        self.popup_template = sublime.load_resource('Packages/ScopeHunter/popup.j2')
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
        self.context_backtrace_info = bool(sh_settings.get("context_backtrace", False))
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
                        self.scope_bfr_tool.append('\n---\n')
                    self.init_template_vars()
                    self.get_info(sel.b)
                    count += 1
            else:
                self.init_template_vars()
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
            self.window.run_command("show_panel", {"panel": "output.scopehunter.results"})

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

        if self.show_popup:
            if self.scheme_info or self.rowcol_info or self.points_info or self.file_path_info:
                tail = mdpopups.md2html(self.view, COPY_ALL)
            else:
                tail = mdpopups.md2html(self.view, RELOAD)

            mdpopups.show_popup(
                self.view,
                ''.join(self.scope_bfr_tool) + tail,
                md=False,
                css=ADD_CSS,
                wrapper_class=('scope-hunter'),
                max_width=1000, on_navigate=self.on_navigate,
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


class ToggleSelectionScopeCommand(sublime_plugin.TextCommand):
    """Command to toggle instant scoper."""

    def run(self, edit):
        """Enable or disable instant scoper."""

        close_display = False

        sh_thread.instant_scoper = False
        if not self.view.settings().get('scope_hunter.view_enable', False):
            self.view.settings().set('scope_hunter.view_enable', True)
            sh_thread.modified = True
            sh_thread.time = time()
        else:
            self.view.settings().set('scope_hunter.view_enable', False)
            close_display = True

        if close_display:
            win = self.view.window()
            if win is not None:
                view = win.get_output_panel('scopehunter.results')
                parent_win = view.window()
                if parent_win:
                    parent_win.run_command('hide_panel', {'cancel': True})
                if TOOLTIP_SUPPORT:
                    mdpopups.hide_popup(self.view)
                if (
                    self.view is not None and
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

        if sh_thread is None:
            return

        enabled = sh_thread.is_enabled(view)
        view_enable = view.settings().get('scope_hunter.view_enable', False)
        if (not sh_thread.instant_scoper and not view_enable) or not enabled:
            # clean up dirty highlights
            if enabled:
                self.clear_regions(view)
        else:
            sh_thread.modified = True
            sh_thread.time = time()

    def on_activated(self, view):
        """Check color scheme on activated and update if needed."""

        if sh_thread is None:
            return

        if not view.settings().get('is_widget', False):
            scheme = view.settings().get("color_scheme")
            if scheme is None:
                pref_settings = sublime.load_settings('Preferences.sublime-settings')
                scheme = pref_settings.get('color_scheme')

            if scheme_matcher is not None and scheme is not None:
                if scheme != scheme_matcher.scheme_file:
                    reinit_plugin()


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


def init_color_scheme():
    """Setup color scheme match object with current scheme."""

    global scheme_matcher
    scheme_file = None

    # Attempt syntax specific from view
    window = sublime.active_window()
    if window is not None:
        view = window.active_view()
        if view is not None:
            scheme_file = view.settings().get('color_scheme', None)

    # Get global scheme
    if scheme_file is None:
        pref_settings = sublime.load_settings('Preferences.sublime-settings')
        scheme_file = pref_settings.get('color_scheme')

    try:
        scheme_matcher = ColorSchemeMatcher(scheme_file)
    except Exception:
        scheme_matcher = None
        log("Theme parsing failed!  Ignoring theme related info.")
        debug(str(traceback.format_exc()))


def reinit_plugin():
    """Reload scheme object and tooltip theme."""

    init_color_scheme()


def init_plugin():
    """Setup plugin variables and objects."""

    global sh_thread
    global sh_settings

    # Preferences Settings
    pref_settings = sublime.load_settings('Preferences.sublime-settings')

    # Setup settings
    sh_settings = sublime.load_settings('scope_hunter.sublime-settings')

    # Setup color scheme
    init_color_scheme()

    pref_settings.clear_on_change('scopehunter_reload')
    pref_settings.add_on_change('scopehunter_reload', reinit_plugin)

    sh_settings.clear_on_change('reload')

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
    """Kill the thread."""

    pref_settings = sublime.load_settings('Preferences.sublime-settings')
    pref_settings.clear_on_change('scopehunter_reload')

    sh_thread.kill()
