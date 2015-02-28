from .png import Writer
import base64
import io


def color_box(color, border, size):
    f = io.BytesIO()
    color_size = size - 2
    p = [border * size]
    p += [border + color * color_size + border] * color_size
    p += [border * size]
    img = Writer(size, size)
    img.write(f, p)
    f.seek(0)
    return "<img src=\"data:%s;base64,%s\"/>" % (
        "image/png",
        base64.b64encode(f.read()).decode('ascii')
    )
