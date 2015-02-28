from .png import Writer
import base64
import io


def color_box(color, border, size=16, border_size=1):
    f = io.BytesIO()
    assert size - (border_size * 2) >= 0, "Border size too big!"
    color_size = size - (border_size * 2)
    p = [border * size]
    p += [
        (border * border_size) +
        (color * color_size) +
        (border * border_size)
    ] * color_size
    p += [border * size]
    img = Writer(size, size)
    img.write(f, p)
    f.seek(0)
    return "<img src=\"data:image/png;base64,%s\">" % (
        base64.b64encode(f.read()).decode('ascii')
)
