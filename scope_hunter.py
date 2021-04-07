"""
Scope Hunter.

Licensed under MIT
Copyright (c) 2012 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
from time import time, sleep
import threading
from ScopeHunter.scope_hunter_notify import notify
from textwrap import dedent
import mdpopups
from collections import namedtuple
from mdpopups.coloraide import Color
import os

AUTO = int(sublime.version()) >= 4095

HEX = {"hex": True}
HEX_NA = {"hex": True, "alpha": False}
SRGB_SPACES = ('srgb', 'hsl', 'hwb')

SCOPE_CONTEXT_BACKTRACE_SUPPORT = int(sublime.version()) >= 4087

if 'sh_thread' not in globals():
    sh_thread = None

sh_settings = {}

ADD_CSS = dedent(
    '''
    html.light {
      --sh-button-color: color(var(--mdpopups-bg) blend(black 85%));
    }
    html.dark {
      --sh-button-color: color(var(--mdpopups-bg) blend(white 85%));
    }
    div.scope-hunter { margin: 0; padding: 0.5rem; }
    .scope-hunter .small { font-size: 0.8rem; }
    .scope-hunter .header { {{'.string'|css('color')}} }
    ins { text-decoration: underline; }
    span.glow { background-color: color(var(--foreground) a(0.2)); }
    div.color-helper { margin: 0; padding: 0rem; }
    .scope-hunter a.button {
        display: inline-block;
        padding: 0.25rem;
        color:  var(--foreground);
        background-color: var(--sh-button-color);
        border-radius: 0.25rem;
        text-decoration: none;
        font-style: none;
        font-weight: normal;
    }
    .scope-hunter hr {
        border-color: var(--sh-button-color);
    }
    '''
)

COPY_ALL = '''
---

[Copy All](copy-all){: .small .button}
'''

# Text Entry
ENTRY = "{:30} {}"
SCOPE_KEY = "Scope"
CONTEXT_BACKTRACE_KEY = "Scope Context Backtrace"
PTS_KEY = "Scope Extents (Pts)"
PTS_VALUE = "({:d}, {:d})"
CHAR_LINE_KEY = "Scope Extents (Line:Char)"
CHAR_LINE_VALUE = "({:d}:{:d}, {:d}:{:d})"
FG_KEY = "Fg"
BG_KEY = "Bg"
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
SCHEME_KEY = "Scheme File"
SYNTAX_KEY = "Syntax File"
OVERRIDE_SCHEME_KEY = "Scheme"


class SchemeColors(
    namedtuple(
        'SchemeColors',
        [
            'fg', "bg", "style", "source", "line", "col"
        ]
    )
):
    """Scheme colors."""


def log(msg):
    """Logging."""
    print("ScopeHunter: {}".format(msg))


def debug(msg):
    """Debug."""
    if sh_settings.get('debug', False):
        log(msg)


def scheme_scope_format(scope):
    """Scheme scope format."""

    return '\n\n{}'.format(
        '\n'.join(
            ['- {}'.format(x) for x in scope.split(',')]
        )
    )


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
        notify("Copied: {}".format(label))


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


class GetSelectionScope:
    """Get the scope and the selection(s)."""

    def setup(self, sh_settings):
        """Setup."""

        self.show_out_of_gamut_preview = True
        self.setup_image_border(sh_settings)
        self.setup_sizes()

    def setup_image_border(self, sh_settings):
        """Setup_image_border."""

        border_color = sh_settings.get('image_border_color')
        border_color = None
        if border_color is not None:
            try:
                border_color = Color(border_color, filters=SRGB_SPACES)
                border_color.fit("srgb", in_place=True)
            except Exception:
                border_color = None

        if border_color is None:
            # Calculate border color for images
            border_color = Color(
                self.view.style()['background'],
                filters=SRGB_SPACES
            ).convert("hsl")
            border_color.lightness = border_color.lightness + (30 if border_color.luminance() < 0.5 else -30)

        self.default_border = border_color.convert("srgb").to_string(**HEX)
        self.out_of_gamut = Color("transparent", filters=SRGB_SPACES).to_string(**HEX)
        self.out_of_gamut_border = Color(
            self.view.style().get('redish', "red"),
            filters=SRGB_SPACES
        ).to_string(**HEX)

    def setup_sizes(self):
        """Get sizes."""

        # Calculate color box height
        self.line_height = self.view.line_height()
        top_pad = self.view.settings().get('line_padding_top', 0)
        bottom_pad = self.view.settings().get('line_padding_bottom', 0)
        if top_pad is None:
            # Sometimes we strangely get None
            top_pad = 0
        if bottom_pad is None:
            bottom_pad = 0
        box_height = self.line_height - int(top_pad + bottom_pad) - 6

        self.height = self.width = box_height * 2

    def check_size(self, height, scale=4):
        """Get checkered size."""

        check_size = int((height - 2) / scale)
        if check_size < 2:
            check_size = 2
        return check_size

    def init_template_vars(self):
        """Initialize template variables."""

        self.template_vars = {}

    def next_index(self):
        """Get next index into scope buffer."""

        self.index += 1
        return self.index

    def get_color_box(self, color, key, index):
        """Display an HTML color box using the given color."""

        border = self.default_border
        box_height = int(self.height)
        box_width = int(self.width)
        check_size = int(self.check_size(box_height))
        if isinstance(color, list):
            box_width = box_width * (len(color) if len(color) >= 1 else 1)
            colors = [c.upper() for c in color]
        else:
            colors = [color.upper()]
        if check_size < 2:
            check_size = 2
        self.template_vars['{}_preview'.format(key)] = '{}'.format(
            mdpopups.color_box(
                colors, border, height=box_height,
                width=box_width, border_size=1, check_size=check_size
            )
        )
        self.template_vars['{}_color'.format(key)] = ', '.join(colors)
        self.template_vars['{}_index'.format(key)] = index

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
                self.scope_bfr.append(ENTRY.format(PTS_KEY + ':', PTS_VALUE.format(pts.begin(), pts.end())))
            if self.rowcol_info:
                self.scope_bfr.append(
                    ENTRY.format(CHAR_LINE_KEY + ':', CHAR_LINE_VALUE.format(row1 + 1, col1 + 1, row2 + 1, col2 + 1))
                )

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

        self.scope_bfr.append(ENTRY.format(SCOPE_KEY + ':', self.view.scope_name(pt).strip().replace(" ", spacing)))

        self.template_vars['scope'] = '<br>'.join(self.view.scope_name(pt).strip().split(' '))
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
            backtrace += '{}: {}'.format(i, ctx)

        if SCOPE_CONTEXT_BACKTRACE_SUPPORT and self.context_backtrace_info:
            self.scope_bfr.append(ENTRY.format(CONTEXT_BACKTRACE_KEY + ':', spacing.join(stack)))

            self.template_vars['context_backtrace'] = True
            self.template_vars["context_backtrace_stack"] = stack
            self.template_vars['context_backtrace_index'] = self.next_index()

        return backtrace

    def get_appearance(self, color, bgcolor, style, source, line, col):
        """Get colors of foreground, background, and font styles."""

        self.source = source
        self.line = line
        self.column = col

        self.scope_bfr.append(ENTRY.format(FG_KEY + ":", color))
        self.scope_bfr.append(ENTRY.format(BG_KEY + ":", bgcolor))
        self.scope_bfr.append(ENTRY.format(STYLE_KEY + ":", "normal" if not style else style))

        self.template_vars['appearance'] = True
        self.get_color_box(color, 'fg', self.next_index())
        self.get_color_box(bgcolor, 'bg', self.next_index())

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

    def find_schemes(self):
        """Finc the syntax files."""

        # Attempt syntax specific from view
        scheme_file = self.view.settings().get('color_scheme', None)

        # Get global scheme
        if scheme_file is None:
            pref_settings = sublime.load_settings('Preferences.sublime-settings')
            scheme_file = pref_settings.get('color_scheme')

        if scheme_file == 'auto' and AUTO:
            info = sublime.ui_info()
            scheme_file = info['color_scheme']['resolved_value']

        scheme_file = scheme_file.replace('\\', '/')

        package_overrides = []
        user_overrides = []
        if scheme_file.endswith('.hidden-color-scheme'):
            pattern = '%s.hidden-color-scheme'
        else:
            pattern = '%s.sublime-color-scheme'

        for override in sublime.find_resources(pattern % os.path.basename(os.path.splitext(scheme_file)[0])):
            if override == scheme_file:
                continue
            if override.startswith('Packages/User/'):
                user_overrides.append(override)
            else:
                package_overrides.append(override)
        return scheme_file, package_overrides + user_overrides

    def get_scheme_syntax(self):
        """Get color scheme and syntax file path."""

        self.scheme_file, self.overrides = self.find_schemes()
        self.syntax_file = self.view.settings().get('syntax')
        self.scope_bfr.append(ENTRY.format(SYNTAX_KEY + ":", self.syntax_file))
        self.scope_bfr.append(ENTRY.format(SCHEME_KEY + ":", self.scheme_file))
        text = []
        for idx, override in enumerate(self.overrides, 1):
            text.append(ENTRY.format(OVERRIDE_SCHEME_KEY + (" {}:".format(idx)), override))
        self.scope_bfr.append('\n'.join(text))

        self.template_vars['files'] = True
        self.template_vars["syntax"] = self.syntax_file
        self.template_vars["syntax_index"] = self.next_index()
        self.template_vars["scheme"] = self.scheme_file
        self.template_vars["scheme_index"] = self.next_index()
        self.template_vars["overrides"] = self.overrides
        self.template_vars["overrides_index"] = self.next_index()

    def guess_style(self, scope, selected=False, no_bold=False, no_italic=False, explicit_background=False):
        """Guess color."""

        # Remove leading '.' to account for old style CSS
        scope_style = self.view.style_for_scope(scope.lstrip('.'))
        style = {}
        style['foreground'] = scope_style['foreground']
        style['background'] = scope_style.get('background')
        style['bold'] = scope_style.get('bold', False) and not no_bold
        style['italic'] = scope_style.get('italic', False) and not no_italic
        style['underline'] = scope_style.get('underline', False)
        style['glow'] = scope_style.get('glow', False)

        font_styles = []
        for k, v in style.items():
            if k in ('bold', 'italic', 'underline', 'glow'):
                if v is True:
                    font_styles.append(k)
        font_styles = ' '.join(font_styles)

        defaults = self.view.style()
        if not explicit_background and not style.get('background'):
            style['background'] = defaults.get('background', '#FFFFFF')
        if selected:
            sfg = scope_style.get('selection_foreground', defaults.get('selection_foreground'))
            if sfg != '#00000000':
                style['foreground'] = sfg
            style['background'] = defaults.get('selection', '#0000FF')

        source = scope_style.get('source_file', '')
        line = ''
        col = ''
        if source:
            line = scope_style.get('source_line', '')
            col = scope_style.get('source_column', '')

        print("{}:{}:{}".format(source, line, col))

        return SchemeColors(style['foreground'], style['background'], font_styles, source, line, col)

    def get_info(self, pt):
        """Get scope related info."""

        scope = self.get_scope(pt)

        self.get_scope_context_backtrace(pt)

        if self.rowcol_info or self.points_info or self.highlight_extent:
            self.get_extents(pt)

        if (self.appearance_info):
            match = self.guess_style(scope)
            color = match.fg
            bgcolor = match.bg
            style = match.style
            if self.appearance_info:
                self.get_appearance(color, bgcolor, style, match.source, match.line, match.col)

        if self.file_path_info:
            self.get_scheme_syntax()

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
        elif key == 'copy-bg':
            copy_data(self.scope_bfr, BG_KEY, index)
        elif key == 'copy-style':
            copy_data(self.scope_bfr, STYLE_KEY, index)
        elif key == 'copy-scheme':
            copy_data(self.scope_bfr, SCHEME_KEY, index)
        elif key == 'copy-syntax':
            copy_data(self.scope_bfr, SYNTAX_KEY, index)
        elif key == 'copy-overrides':
            copy_data(
                self.scope_bfr,
                "{} {}".format(OVERRIDE_SCHEME_KEY, params[2]),
                index,
                lambda text: self.overrides[int(params[2]) - 1]
            )
        elif key == 'scheme' and self.scheme_file is not None:
            window = self.view.window()
            window.run_command(
                'open_file',
                {
                    "file": "${{packages}}/{}".format(
                        self.scheme_file.replace(
                            '\\', '/'
                        ).replace('Packages/', '', 1)
                    )
                }
            )
        elif key == 'source' and self.source is not None:
            window = self.view.window()
            file = sublime.expand_variables(
                "${{packages}}/{}:{}:{}".format(
                    self.source.replace(
                        '\\', '/'
                    ).replace('Packages/', '', 1),
                    self.line,
                    self.column
                ),
                window.extract_variables()
            )
            window.open_file(
                file,
                sublime.ENCODED_POSITION
            )
        elif key == 'syntax' and self.syntax_file is not None:
            window = self.view.window()
            window.run_command(
                'open_file',
                {
                    "file": "${{packages}}/{}".format(
                        self.syntax_file.replace(
                            '\\', '/'
                        ).replace('Packages/', '', 1)
                    )
                }
            )
        elif key == 'override':
            window = self.view.window()
            window.run_command(
                'open_file',
                {
                    "file": "${{packages}}/{}".format(
                        self.overrides[int(params[2]) - 1].replace('Packages/', '', 1)
                    )
                }
            )

    def run(self, v):
        """Run ScopeHunter and display in the approriate way."""

        self.view = v
        self.setup(sh_settings)

        self.window = self.view.window()
        self.scope_bfr = []
        self.scope_bfr_tool = []
        self.clips = []
        self.popup_template = sublime.load_resource('Packages/ScopeHunter/popup.j2')
        self.scheme_file = None
        self.syntax_file = None
        self.show_popup = bool(sh_settings.get("show_popup", False))
        self.clipboard = bool(sh_settings.get("clipboard", False))
        self.multiselect = bool(sh_settings.get("multiselect", False))
        self.highlight_extent = bool(sh_settings.get("highlight_extent", False))
        self.highlight_scope = sh_settings.get("highlight_scope", 'invalid')
        self.highlight_style = sh_settings.get("highlight_style", 'outline')
        self.highlight_max_size = int(sh_settings.get("highlight_max_size", 100))
        self.context_backtrace_info = bool(sh_settings.get("context_backtrace", False))
        self.rowcol_info = bool(sh_settings.get("extent_line_char", False))
        self.points_info = bool(sh_settings.get("extent_points", False))
        self.appearance_info = bool(sh_settings.get("styling", False))
        self.file_path_info = bool(sh_settings.get("file_paths", False))
        self.scheme_info = self.appearance_info
        self.extents = []

        # Get scope info for each selection wanted
        self.index = -1
        if len(self.view.sel()):
            if self.multiselect:
                count = 0
                for sel in self.view.sel():
                    if count > 0:
                        self.scope_bfr_tool.append('\n<hr>\n')
                    self.init_template_vars()
                    self.get_info(sel.b)
                    count += 1
            else:
                self.init_template_vars()
                self.get_info(self.view.sel()[0].b)

        # Copy scopes to clipboard
        if self.clipboard:
            sublime.set_clipboard('\n'.join(self.clips))

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

        if self.scheme_info or self.rowcol_info or self.points_info or self.file_path_info:
            tail = mdpopups.md2html(self.view, COPY_ALL)
        else:
            tail = ''

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


def init_plugin():
    """Setup plugin variables and objects."""

    global sh_thread
    global pref_settings
    global sh_settings

    # Preferences Settings
    pref_settings = sublime.load_settings('Preferences.sublime-settings')

    # Setup settings
    sh_settings = sublime.load_settings('scope_hunter.sublime-settings')

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

    sh_thread.kill()
