"""Changelog."""
import sublime
import sublime_plugin
import webbrowser

CSS = '''
html { {{'.background'|css}} }
div.scope-hunter { padding: 0; margin: 0; {{'.background'|css}} }
.scope-hunter h1, .scope-hunter h2, .scope-hunter h3, .scope-hunter h4, .scope-hunter h5, .scope-hunter h6 {
    {{'.string'|css}}
}
.scope-hunter blockquote { {{'.comment'|css}} }
'''


class ScopeHunterChangesCommand(sublime_plugin.WindowCommand):
    """Changelog command."""

    def run(self):
        """Show the changelog in a new view."""
        try:
            import mdpopups
            has_phantom_support = (mdpopups.version() >= (1, 10, 0)) and (int(sublime.version()) >= 3118)
        except Exception:
            has_phantom_support = False

        text = sublime.load_resource('Packages/ScopeHunter/CHANGES.md')
        view = self.window.new_file()
        view.set_name('ScopeHunter - Changelog')
        view.settings().set('gutter', False)
        if has_phantom_support:
            mdpopups.add_phantom(
                view,
                'changelog',
                sublime.Region(0),
                text,
                sublime.LAYOUT_INLINE,
                wrapper_class="scope-hunter",
                css=CSS
            )
        else:
            view.run_command('insert', {"characters": text})
        view.set_read_only(True)
        view.set_scratch(True)

    def on_navigate(self, href):
        """Open links."""
        webbrowser.open_new_tab(href)
