# ScopeHunter 2.12.0

- **NEW**: Add support for color scheme `alpha()`/`a()` blend and `hwb()` colors.

# ScopeHunter 2.11.1

- **FIX**: Allow `-` in variables names. Write color translations to main scheme object and ensure filtering is done after color translations.

# ScopeHunter 2.11.0

- **NEW**: Add support for `.hidden-color-scheme`.

# ScopeHunter 2.10.

- **FIX**: Create fallback file read for resource race condition.

# ScopeHunter 2.10.

- **FIX**: Parse legacy `foregroundSelection` properly.

# ScopeHunter 2.10.

- **NEW**: Add support `.sublime-color-scheme` hashed syntax highlighting.
- **FIX**: Copy of color entries.
- **FIX**: `.sublime-color-scheme` merge logic.

# ScopeHunter 2.9.3

- **FIX**: Parse color schemes properly when extension is unexpected.

# ScopeHunter 2.9.2

- **FIX**: Support for irregular `.sublime-color-scheme` values.

# ScopeHunter 2.9.1

- **FIX**: Scheme parsing related fixes.

# ScopeHunter 2.9.0

- **NEW**: Handle overrides for new color scheme styles and bring back scope info for style attributes.
- **NEW**: Hide names if no names available.
- **NEW**: Small popup format tweaks.
- **NEW**: Add option to manually refresh color scheme in cache.
- **NEW**: Show overrides file names in panel and/or popup.
- **FIX**: Font style read error when no font style.

# ScopeHunter 2.8.0

- **NEW**: Add support for `.sublime-color-scheme` (some features may not be available as scheme handling has changed).
- **NEW**: Remove "Generate CSS" command as this feature is no longer relevant as schemes have drastically changed.
- **NEW**: Update dependencies.
- **FIX**: On 3150+, ScopeHunter will always give the latest colors (no cached scheme).
- **FIX**: Ensure both bold and italic is shown for style when both are set for a selector.
- **FIX**: Small fixes in color matcher lib for builds <3150.

# ScopeHunter 2.7.0

- **NEW**: Popups now require ST 3124+.
- **FIX**: Fix scope matching issues.

# ScopeHunter 2.6.0

- **NEW**: Add support for X11 color names in color schemes.
- **NEW**: Add new support commands.
- **FIX**: Protect against race condition (#34)

# ScopeHunter 2.5.6

- **FIX**: Failure when evaluating bold text (!33)

# ScopeHunter 2.5.5

- **FIX**: Some CSS tweaks.

# ScopeHunter 2.5.4

- **FIX**: Guard against loading mdpopups on old Sublime versions.

# ScopeHunter 2.5.3

- **FIX**: Fix changelog typo :).

# ScopeHunter 2.5.2

- **FIX**: Incorrect logic regarding bold.

# ScopeHunter 2.5.1

- **FIX**: Fix copy all link.

# ScopeHunter 2.5.0

- **NEW**: Changelog command available in `Package Settings->ScopeHunter`.  
Will render a full changelog in an HTML phantom in a new view.
- **NEW**: Support info command available in `Package Settings->ScopeHunter`.
- **NEW**: Will attempt to tell Package Control to update the most recent  
desired mdpopups.  Really need to test that this actually does works :).
- **NEW**: Requires `mdpopups` version 1.9.0.  Run Package Control  
`Satisfy Dependencies` command if not already present. May require restart after  
update.
- **FIX**: Formatting fixes.
