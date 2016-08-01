"""Changelog."""
import sublime
import sublime_plugin
import mdpopups

CSS = '''
.scope-hunter h1, .scope-hunter h2, .scope-hunter h3, .scope-hunter h4, .scope-hunter h5, .scope-hunter h6 {
    {{'.string'|css('color')}}
}
.scope-hunter blockquote { {{'.comment'|css('color')}} }
'''


class ScopeHunterChangesCommand(sublime_plugin.WindowCommand):
    """Changelog command."""

    def run(self):
        """Show the changelog in a new view."""
        text = sublime.load_resource('Packages/ScopeHunter/CHANGES.md')
        view = self.window.new_file()
        view.set_name('ScopeHunter - Changelog')
        view.settings().set('gutter', False)
        html = '<div class="scope-hunter">%s</div>' % mdpopups.md2html(view, text)
        mdpopups.add_phantom(view, 'changelog', sublime.Region(0), html, sublime.LAYOUT_INLINE, css=CSS)
        view.set_read_only(True)
        view.set_scratch(True)

    def is_enabled(self):
        """Check if is enabled."""
        return (mdpopups.version() >= (1, 7, 3)) and (int(sublime.version()) >= 3118)

    is_visible = is_enabled
