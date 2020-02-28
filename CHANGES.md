# ScopeHunter

## 2.13.0

- **NEW**: Add support for blending colors in the `HSL` and `HWB` color spaces in color schemes. Sublime has a bug where
  it blends in these color spaces in a surprising way. We do not fully match it, but we will not currently fail anymore.
- **NEW**: Support `+`, `-`, and `*` in `alpha()`/`a()`.
- **NEW**: Support `lightness()` and `saturation()`.
- **NEW**: Support `foreground_adjust` in color schemes. 

## 2.12.0

- **NEW**: Add support for color scheme `alpha()`/`a()` blend and `hwb()` colors.

## 2.11.1

- **FIX**: Allow `-` in variables names. Write color translations to main scheme object and ensure filtering is done after color translations.

## 2.11.0

- **NEW**: Add support for `.hidden-color-scheme`.

## 2.10.

- **FIX**: Create fallback file read for resource race condition.

## 2.10.

- **FIX**: Parse legacy `foregroundSelection` properly.

## 2.10.

- **NEW**: Add support `.sublime-color-scheme` hashed syntax highlighting.
- **FIX**: Copy of color entries.
- **FIX**: `.sublime-color-scheme` merge logic.

## 2.9.3

- **FIX**: Parse color schemes properly when extension is unexpected.

## 2.9.2

- **FIX**: Support for irregular `.sublime-color-scheme` values.

## 2.9.1

- **FIX**: Scheme parsing related fixes.

## 2.9.0

- **NEW**: Handle overrides for new color scheme styles and bring back scope info for style attributes.
- **NEW**: Hide names if no names available.
- **NEW**: Small popup format tweaks.
- **NEW**: Add option to manually refresh color scheme in cache.
- **NEW**: Show overrides file names in panel and/or popup.
- **FIX**: Font style read error when no font style.

## 2.8.0

- **NEW**: Add support for `.sublime-color-scheme` (some features may not be available as scheme handling has changed).
- **NEW**: Remove "Generate CSS" command as this feature is no longer relevant as schemes have drastically changed.
- **NEW**: Update dependencies.
- **FIX**: On 3150+, ScopeHunter will always give the latest colors (no cached scheme).
- **FIX**: Ensure both bold and italic is shown for style when both are set for a selector.
- **FIX**: Small fixes in color matcher lib for builds <3150.

## 2.7.0

- **NEW**: Popups now require ST 3124+.
- **FIX**: Fix scope matching issues.

## 2.6.0

- **NEW**: Add support for X11 color names in color schemes.
- **NEW**: Add new support commands.
- **FIX**: Protect against race condition (#34)

## 2.5.6

- **FIX**: Failure when evaluating bold text (!33)

## 2.5.5

- **FIX**: Some CSS tweaks.

## 2.5.4

- **FIX**: Guard against loading mdpopups on old Sublime versions.

## 2.5.3

- **FIX**: Fix changelog typo :).

## 2.5.2

- **FIX**: Incorrect logic regarding bold.

## 2.5.1

- **FIX**: Fix copy all link.

## 2.5.0

- **NEW**: Changelog command available in `Package Settings->ScopeHunter`.  
Will render a full changelog in an HTML phantom in a new view.
- **NEW**: Support info command available in `Package Settings->ScopeHunter`.
- **NEW**: Will attempt to tell Package Control to update the most recent  
desired mdpopups.  Really need to test that this actually does works :).
- **NEW**: Requires `mdpopups` version 1.9.0.  Run Package Control  
`Satisfy Dependencies` command if not already present. May require restart after  
update.
- **FIX**: Formatting fixes.
