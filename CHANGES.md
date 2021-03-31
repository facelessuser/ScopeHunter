# ScopeHunter

## 2.16

- **NEW**: Due to Sublime schemes ever evolving, there were a few things (like "forward fill" scopes) that we didn't
  have support for. These implementation details are hard to reverse engineer, so to make support easier moving forward,
  we now use Sublime's `View.style()` to get the style at a given point instead of manually parsing the scheme
  ourselves. This means we no longer provide the original defined colors from the scheme file, but instead only the end
  result after overlaying transparent colors etc. Because of this,
  `show_simulated_alpha_colors` option has been removed.
- **NEW**: Because we are no longer parsing the scheme files ourselves anymore, we can no longer provide contributing
  scopes to individual style components. The related `selectors` option has been removed.
- **FIX**: Fix issue with Sublime 4095 `auto` light/dark color scheme resolution.
- **FIX**: Reduce dependencies by relying on the `coloraide` in `mdpopups` which we already include.
- **FIX**: Remove old `tooltip_theme` option that hasn't been used in quite some time.

## 2.15.2

- **FIX**: Better styling for popups.
- **FIX**: `tmTheme` support compressed hex; therefore, ScopeHunter must account for these colors.
- **FIX**: Fix false positive on hashed foreground colors.

## 2.15.1

- **FIX**: Fix issue with support commands.

## 2.15.0

- **NEW**: Format dialog a little more compact.
- **NEW**: Require new `coloraide` dependency. With this dependency, schemes that use `min-contrast` should work now.
- **NEW**: ScopeHunter now only shows information in tooltip. Showing info in separate panel and console has been
  dropped as tooltip functionality is available on all latest Sublime versions.
- **NEW**: Backtrace info available in Sublime Text build 4087.
- **NEW**: Add `image_border_color` option.
- **FIX**: Fix bug with copying color scheme name.
- **FIX**: Fix some issues related to schemes (Celeste theme) using invalid colors, such as `"none"` to reset background
  colors etc.

## 2.14.0

- **NEW**: Add support for `glow` and `underline` styles.
- **FIX**: Fix font style reporting in popups.

## 2.13.1

- **FIX**: ST4 now handles `HSL` properly, remove workaround for build 4069.
- **FIX**: `+`/`-` have to be followed by spaces in `saturation`, `lightness`, and `alpha` or they should be treated as
  part of the number following them. `*` does not need a space.
- **FIX**: Add support for `deg` unit type for the hue channel with `HSL` and `HWB`.
- **FIX**: Sublime will ignore the unit types `rad`, `grad`, and `turn` for `HSL` and `HWB`, but add support for them in
  case Sublime ever does.

## 2.13.0

- **NEW**: Add support for blending colors in the `HSL` and `HWB` color spaces in color schemes. Sublime has a bug where
  it blends in these color spaces in a surprising way. We do not fully match it, but we will not currently fail anymore.
- **NEW**: Support `+`, `-`, and `*` in `alpha()`/`a()`.
- **NEW**: Support `lightness()` and `saturation()`.
- **NEW**: Support `foreground_adjust` in color schemes.

## 2.12.0

- **NEW**: Add support for color scheme `alpha()`/`a()` blend and `hwb()` colors.

## 2.11.1

- **FIX**: Allow `-` in variables names. Write color translations to main scheme object and ensure filtering is done
  after color translations.

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
