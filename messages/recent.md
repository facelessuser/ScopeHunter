# ScopeHunter 2.16.0

New release!

See `Preferences->Package Settings->ScopeHunter->Changelog` for more info on previous releases.

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
