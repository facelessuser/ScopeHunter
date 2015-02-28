from .png import Writer
from .rgba import RGBA
import base64
import io

CHECK_LIGHT = "#FFFFFF"
CHECK_DARK = "#CCCCCC"

LIGHT = 0
DARK = 1


def to_list(rgb):
    """
    Take a color of the format #RRGGBBAA (alpha optional and will be stripped)
    and convert to a list with format [r, g, b].
    """
    return [
        int(rgb[1:3], 16),
        int(rgb[3:5], 16),
        int(rgb[5:7], 16)
    ]


def checkered_color(color, background):
    """ Mix color with the checkered color """
    checkered = RGBA(color)
    checkered.apply_alpha(background)
    return checkered.get_rgb()


def color_box(color, border, size=16, border_size=1, check_size=4):
    """
    Create an RGBA color box with the specified RGBA color
    and RGB(A) border (alpha will be stripped out of border color).

    Define size of swatch, border width,  and size of checkered board squares.
    """
    assert size - (border_size * 2) >= 0, "Border size too big!"

    # Create bytes buffer for png
    f = io.BytesIO()

    # Mix transparent color with checkered colors
    # And covert colors to to lists containing r, g, b channels
    light = to_list(checkered_color(color, CHECK_LIGHT))
    dark = to_list(checkered_color(color, CHECK_DARK))
    border = to_list(border)

    # Size of color swatch between borders
    color_size = size - (border_size * 2)

    # Draw borders and create the checkered
    # pattern with the mixed light and dark colors
    p = [border * size]
    check_color_y = DARK
    for y in range(0, color_size):
        if y % check_size == 0:
            check_color_y = DARK if check_color_y == LIGHT else LIGHT
        row = list(border * border_size)
        check_color_x = check_color_y
        for x in range(0, color_size):
            if x % check_size == 0:
                check_color_x = DARK if check_color_x == LIGHT else LIGHT
            row += (dark if check_color_x == DARK else light)
        row += border * border_size
        p.append(row)
    p.append(border * size)

    # Write out png
    img = Writer(size, size)
    img.write(f, p)

    # Read out png bytes and base64 encode
    f.seek(0)
    return "<img src=\"data:image/png;base64,%s\">" % (
        base64.b64encode(f.read()).decode('ascii')
)
