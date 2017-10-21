# User Guide

## Command Usage

All commands are accessible via the command palette.

### Scope Hunter: Show Scope Under Cursor
Show scope under cursor or cursors (depending whether multi-select is enabled).

### Scope Hunter: Toggle Instant Scoper

Toggle scoping under cursor constantly, but only for the current active file view.

## Scope Hunter: User Settings

In order to change the standard settings of Scope Hunter, please go to `Preferences -> Package Settings -> Scope Hunter` and click on `Settings - User`.  Repeat that for `Settings - Default`, copy all the settings that you wish to change from the default settings to the user settings file.

### Developer Options

These settings are for debugging issues.

```js
    ///////////////////////////
    // Dev Options
    ///////////////////////////
    "debug": false,
```

#### debug

Turns on debug logging.

### View options

By default, ScopeHunter (on ST3) uses the output panel to communicate the scope.  But if you prefer a more subtle **or** flashier way of displaying the scope, ScopeHunter can be configured to do so.

```js
    ///////////////////////////
    // View Options
    ///////////////////////////

    // Show popup tooltip with info about scope
    "show_popup": false,

    // Show scope in status bar
    "show_statusbar": false,

    // Show scope in auto-popup panel
    "show_panel": true,

    // Show scopes in console
    "console_log": false,
```

#### `show_popup`

This uses the new ST3 tooltip API to display and is my personal favorite.  It shows a styled tooltip with all the information about the scope of the current cursor(s).  You get previews of the colors, and you can click links to copy the info to the clipboard.

#### `show_statusbar`

This shows just the scope in the status bar.  Simple and subtle.

#### `show_panel`

This shows the scope and related info in an output panel.  This allows a user to directly copy and paste the info from the panel.

#### `console_log`

This is useful if you are doing something like `show_statusbar`.  You can keep the output subtle, but you can open the console and get more in depth info that you can copy and paste.

### Scope Info

For modes like `show_panel`, `console_log`, and `show_popup` you can control the info displayed.  You can keep it just to the scope, or you can extend it show other useful info.

```js
    ///////////////////////////
    // Additional Scope Info
    ///////////////////////////

    // Show scope extent in point format
    "extent_points": true,

    // Show scope extent in line/char format
    "extent_line_char": true,

    // Show color and style at the given point
    "styling": true,

    // When showing a color with alpha transparency,
    // Simulate what the color would look like in sublime
    // by mixing the relevant background color,
    "show_simulated_alpha_colors": true,

    // Show the selector names and scopes
    // responsible for the color and styles
    "selectors": true,

    // Show current syntax and color scheme paths
    // (click to open if using tooltips)
    "file_paths": true,

    // Highlight scope extent in view
    "highlight_extent": true,
```

#### `extent_points`

Show the extent of the scope as view points.

#### `extent_line_char`

Show the extent of the scope as line/char or row/col format.

#### `highlight_extent`

Highlight the scope extent.

#### `styling`

Show not only the color value, but also the scope and text styling.

#### `show_simulated_alpha_colors`

When showing color values, ScopeHunter can show the perceived color value of transparent colors.  It mixes the transparent foreground with the background giving the color value you are actually seeing.

#### `selectors`

This shows the color scheme selectors that are responsible for applying the visible color and styles.

#### `file_paths`

Show the file paths of the color scheme and language file that are responsible for giving the styled appearance of your view.  In the tooltip, you can click these links and open the responsible file directly in Sublime Text.

### Scope Highlighting

When `highlight_extent` is enabled, this controls the visual style of the highlights.  Due to the way the Sublime Text API for highlighting regions works, colors must be described as scope names from your color scheme file.  Just define the scope to use and the supported style as shown below.

```js
    ///////////////////////////
    // Highlight Configuration
    ///////////////////////////

    // Scope to use for the color
    "highlight_scope": "invalid",

    // Highlight style (underline|solid|outline|thin_underline|squiggly|stippled)
    "highlight_style": "outline",
```

### Miscellaneous Options

Lastly, there are a couple of other options:

```js
    ///////////////////////////
    // Additional Options
    ///////////////////////////

    // Automatically copy scopes to clipboard
    "clipboard": false,

    // Allow multi-select scope hunting
    "multiselect": true,

    // Max region size to highlight
    "highlight_max_size": 100,

    // Use SubNotify plugin messages if installed
    "use_sub_notify": true
```

#### `clipboard`

Auto-copies just the scope to the clipboard.

#### `multiselect`

Allow displaying of the scope info for multiple cursor selections (does not work for `show_statusbar` as space is very limited).

#### `highlgiht_max_size`

For performance, ScopeHunter is limited to highlight regions less that a given size.  If a region is bigger than the defined limit, it will not be highlighted.  You can control that limit here.

####  `use_sub_notify`

If you have the [SubNotify][subnotify] installed, this will enable or disable messages through it.

--8<-- "refs.md"
