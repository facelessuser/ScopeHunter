# ScopeHunter {: .doctitle}
Syntax Scope Viewer in Sublime Text.

---

## ScopeHunter
This is a simple plugin that can get the scope under the cursor(s) in Sublime Text.  This plugin is useful for plugin development.

Dark theme with simple output:

![Tooltip Dark](https://dl.dropboxusercontent.com/u/342698/ScopeHunter/tooltip-simple-dark.png)

Light theme with advanced output:

![Tooltip Light](https://dl.dropboxusercontent.com/u/342698/ScopeHunter/tooltip-copy.png)

## Features
All features are configurable via the settings file

- Optionally show output in tooltip (stylesheets are configurable).
- Optionally auto choose dark or light tooltip theme depending on your color scheme.
- Optionally dump output to auto-popup panel and/or console.
- Optionally dump scope to status bar (no multi-select support).
- Multi-select support for all output except status bar.
- Optionally log scope extent in line/char format and/or point format.
- Optionally copy scope(s) to clipboard.
- Optionally highlight and/or log scope extent.
- Optionally log color scheme colors and selectors.
- Optionally log location of Scheme file and Syntax.
- Supports [SubNotify](https://github.com/facelessuser/SubNotify) messages.
