# User Guide

## Command Usage

All commands are accessible via the command palette.

### Scope Hunter: Show Scope Under Cursor

Show scope under cursor or cursors (depending whether multi-select is enabled).

### Scope Hunter: Toggle Instant Scoper

Toggle scoping under cursor constantly, but only for the current active file view.

## Scope Hunter: User Settings

In order to change the standard settings of Scope Hunter, please go to `Preferences -> Package Settings -> Scope Hunter`
and click on `Settings - User`.  Repeat that for `Settings - Default`, copy all the settings that you wish to change
from the default settings to the user settings file.

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

### Scope Info

Control the info displayed.  You can keep it to just the scope, or you can extend it show other useful info.

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

    // Show current syntax and color scheme paths
    // (click to open if using tooltips)
    "file_paths": true,
```

#### `extent_points`

Show the extent of the scope as view points.

#### `extent_line_char`

Show the extent of the scope as line/char or row/col format.

#### `styling`

Show not only the color value, the text styling.

#### `file_paths`

Show the file paths of the color scheme and language file that are responsible for giving the styled appearance of your
view.  In the tooltip, you can click these links and open the responsible file directly in Sublime Text.

### Scope Highlighting

When `highlight_extent` is enabled, this controls the visual style of the highlights.  Due to the way the Sublime Text
API for highlighting regions works, colors must be described as scope names from your color scheme file.  Just define
the scope to use and the supported style as shown below.

```js
    ///////////////////////////
    // Highlight Configuration
    ///////////////////////////

    // Highlight scope extent in view
    "highlight_extent": true,

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

    ///////////////////////////
    // Graphics
    ///////////////////////////

    // By default, image border is calculated based on theme background, but if for
    // some reason, it isn't sufficient in your popup, set it to any color using
    // valid CSS for RGB, HSL, or HWB colors.
    "image_border_color": null
```

#### `clipboard`

Auto-copies just the scope to the clipboard.

#### `multiselect`

Allow displaying of the scope info for multiple cursor selections.

#### `highlgiht_max_size`

For performance, ScopeHunter is limited to highlight regions less that a given size.  If a region is bigger than the
defined limit, it will not be highlighted.  You can control that limit here.

####  `use_sub_notify`

If you have the [SubNotify][subnotify] installed, this will enable or disable messages through it.

#### `image_border_color`

Image border color is calculated from the current color scheme, but if a more visible or different border is desired
on the color previews, you can change it with this option.

--8<-- "refs.txt"
