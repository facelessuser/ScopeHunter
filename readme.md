[![Donate via PayPal][donate-image]][donate-link]
[![Discord][discord-image]][discord-link]
[![Build][github-ci-image]][github-ci-link]
[![Package Control Downloads][pc-image]][pc-link]
![License][license-image]
# ScopeHunter

This is a simple plugin that can get the scope under the cursor(s) in Sublime Text.  This plugin is useful for plugin
development.

![Screenshot 1](docs/src/markdown/images/screenshot1.png)

![Screenshot 2](docs/src/markdown/images/screenshot2.png)

## Features
All features are configurable via the settings file

- Tooltip output showing scope, context backtrace, scope extent, color values, links to current syntax and relevant
  color schemes.
- Customizable to show only the information you care about.
- Auto copy scope to clipboard on execution.
- Quick copy any or all information to the clipboard.
- Toggle instant scoping to keep showing scope as you move around a file.
- Supports [SubNotify](https://github.com/facelessuser/SubNotify) messages.

# Documentation

https://facelessuser.github.io/ScopeHunter/

# License

Scope Hunter is released under the MIT license.

Copyright (c) 2012 - 2021 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[github-ci-image]: https://github.com/facelessuser/ScopeHunter/workflows/build/badge.svg
[github-ci-link]: https://github.com/facelessuser/ScopeHunter/actions?workflow=build
[discord-image]: https://img.shields.io/discord/678289859768745989?logo=discord&logoColor=aaaaaa&color=mediumpurple&labelColor=333333
[discord-link]: https://discord.gg/TWs8Tgr
[pc-image]: https://img.shields.io/packagecontrol/dt/ScopeHunter.svg?labelColor=333333&logo=sublime%20text
[pc-link]: https://packagecontrol.io/packages/ScopeHunter
[license-image]: https://img.shields.io/badge/license-MIT-blue.svg?labelColor=333333
[donate-image]: https://img.shields.io/badge/Donate-PayPal-3fabd1?logo=paypal
[donate-link]: https://www.paypal.me/facelessuser
