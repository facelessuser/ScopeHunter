# ScopeHunter 2.9.2

Oct 27, 2017

- **FIX**: Support for irregular `.sublime-color-scheme` values.

# ScopeHunter 2.9.1

Oct 21, 2017

- **FIX**: Scheme parsing related fixes.

# ScopeHunter 2.9.0

Oct 19, 2017

- **NEW**: Handle overrides for new color scheme styles and bring back scope info for style attributes.
- **NEW**: Hide names if no names available.
- **NEW**: Small popup format tweaks.
- **NEW**: Add option to manually refresh color scheme in cache.
- **NEW**: Show overrides file names in panel and/or popup.
- **FIX**: Font style read error when no font style.

# ScopeHunter 2.8.0

Oct 18, 2017

- **NEW**: Add support for `.sublime-color-scheme` (some features may not be available as scheme handling has changed).
- **NEW**: Remove "Generate CSS" command as this feature is no longer relevant as schemes have drastically changed.
- **NEW**: Update dependencies.
- **FIX**: On 3150+, ScopeHunter will always give the latest colors (no cached scheme).
- **FIX**: Ensure both bold and italic is shown for style when both are set for a selector.
- **FIX**: Small fixes in color matcher lib for builds <3150.

# ScopeHunter 2.7.0

May 27, 2017

- **NEW**: Popups now require ST 3124+.
- **FIX**: Fix scope matching issues.

# ScopeHunter 2.6.0

Dec 29, 2016

- **NEW**: Add support for X11 color names in color schemes.
- **NEW**: Add new support commands.
- **FIX**: Protect against race condition [#34](https://github.com/facelessuser/ScopeHunter/issues/34)

# ScopeHunter 2.5.6

Oct 19, 2016

- **FIX**: Failure when evaluating bold text [#33](https://github.com/facelessuser/ScopeHunter/pull/33)

# ScopeHunter 2.5.5

Aug 8, 2016

- **FIX**: Some CSS tweaks.

# ScopeHunter 2.5.4

Aug 1, 2016

- **FIX**: Guard against loading mdpopups on old Sublime versions.

# ScopeHunter 2.5.3

Aug 1, 2016

- **FIX**: Fix changelog typo :).

# ScopeHunter 2.5.2

Aug 1, 2016

- **FIX**: Incorrect logic regarding bold.

# ScopeHunter 2.5.1

Jul 31, 2016

- **FIX**: Fix copy all link.

# ScopeHunter 2.5.0

Jul 31, 2016

- **NEW**: Changelog command available in `Package Settings->ScopeHunter`.  
Will render a full changelog in an HTML phantom in a new view.
- **NEW**: Support info command available in `Package Settings->ScopeHunter`.
- **NEW**: Will attempt to tell Package Control to update the most recent  
desired mdpopups.  Really need to test that this actually does works :).
- **NEW**: Requires `mdpopups` version 1.9.0.  Run Package Control  
`Satisfy Dependencies` command if not already present. May require restart after  
update.
- **FIX**: Formatting fixes.
