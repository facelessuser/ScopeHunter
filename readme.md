# About
This is a simple plugin get the scope under the cursor(s) in Sublime Text.  This is useful for plugin development.

# Usage
All commands are accessible via the command palatte.

## Scope Hunter: Show Scope Under Cursor
Show scope under cursor or cursors (depending whether multi-select is enabled)

## Scope Hunter: Toggle Instant Scoper
Toggle scoping under cursor constantly.

# Features
All features are configurable via the settings file

- Dump scope to status bar (no multi-select support)
- Dump scope extent in line/char format and/or point format
- Dump output to auto-popup panel and/or console
- Copy scope(s) to clipboard
- Multi-select support for all output except status bar
- Highlight scope extent

# License

Scope Hunter is released under the MIT license.

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Version 0.4.1
- Console logging is back

# Version 0.4.0
- Add highlight scope extent option
- Remove console logging

# Version 0.3.0
- Fix regression with on demand command

# Version 0.2.1
- Fix regression with on demand command

# Version 0.2.0
- Fix console setting not being checked
- Fix output format
- Do not log duplicate entries to console
- Ignore widget views

# Version 0.1.0
- First release
