# User Guide {: .doctitle}
Configuration and usage of ScopeHunter.

---

# Command Usage
All commands are accessible via the command palette.

## Scope Hunter: Show Scope Under Cursor
Show scope under cursor or cursors (depending whether multi-select is enabled)

## Scope Hunter: Toggle Instant Scoper
Toggle scoping under cursor constantly.

# Scope Hunter: User Settings
In order to change the standard settings of Scope Hunter, please go to `Preferences -> Package Settings -> Scope Hunter` and click on `Settings - User`.  Repeat that for `Settings - Default`, copy all the settings from the default file that you wish to change to the user settings file.

# Customizing Tooltip Theme
On the latest ST3 branches, a new tooltip API is available.  ScopeHunter can take advantage of this feature and provide useful scope tooltips when invoked.  ScopeHunter comes with a theme that provides a light and dark variant that will be used depending on how light or dark you current color scheme is.

You can create your own if desired and use it instead of the default.  The theme folder must include a `light.tt_theme` file and a `dark.tt_theme` file.  The `tt_theme` files are a JSON files with a slightly modified syntax allowing JavaScript style comments.  `tt_theme` files point to needed theme assets and set certain variables that are not defined in CSS files.  All assets should be contained within the tt_theme folder and paths in the `tt_theme` files are relative to the `tt_theme` file itself.  Do not use windows style backslashes `\`.

Example tt_theme structure:

```
tt_theme/
    dark.tt_theme
    light.tt_theme
    css/
        dark.css
        light.css
```

Please use the default `tt_theme` as an example and template for creating your own.  In the default `tt_theme` you should be able to see all the settings that can be set, and all the CSS classes that can be targeted.
