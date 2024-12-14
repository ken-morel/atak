from functools import cached_property
from pathlib import Path

import PIL.Image
import PIL.ImageTk

MEDIA_DIR = None


def parse_media_spec(spec):
    if "{" in spec:
        assert "}" in spec, f"Unterminated spec {spec}"
        b = spec.index("{")
        e = spec.index("}")
        return spec[:b], parse_media_spec_props(spec[b + 1 : e])
    else:
        return spec, {}


def parse_media_spec_props(props):
    from .component.parser import evaluate_literal

    props = props.split(";")
    return {
        x.split(":")[0]: evaluate_literal(x.split(":")[1].strip(), None)
        for x in props
        if x.strip()
    }


def get_media(spec):
    spec, props = parse_media_spec(spec)
    assert (
        n := spec.count(":")
    ) >= 1, f"media spec should include one ':', has: {n}"
    match tuple(spec.split(":", 1)):
        case ("img", path):
            if path[0] == "@":
                return MediaImage(path[1:], props)
            else:
                return Image(path, props)
        case wrong:
            raise ValueError(f"Unrecognised media {spec!r}")

def get_image(spec):
    if not spec.startswith('img:'):
        spec = 'img:' + spec
    return get_media(spec)

class Resource:
    pass


class Image(Resource):
    @cached_property
    def image(self):
        image = PIL.Image.open(self.full_path)
        iw, ih = image.size
        width, height = self.props.get("width"), self.props.get("height")
        if width == height == None:
            return image
        elif width is None:
            width = height / ih * iw
        elif height is None:
            height = width / iw * ih
        return image.resize((int(width), int(height)))

    @cached_property
    def tk(self):
        return PIL.ImageTk.PhotoImage(self.image)

    def get(self):
        return self.tk

    def __init__(self, path, props):
        if not "." in path:
            path += ".png"
        self.path = path
        self.full_path = path
        self.props = props


class MediaImage(Image):
    @cached_property
    def image(self):
        if MEDIA_DIR is None:
            raise RuntimeError("Media directory not set")
        image = PIL.Image.open(self.full_path)
        iw, ih = image.size
        width, height = self.props.get("width"), self.props.get("height")
        if width == height == None:
            return image
        elif width is None:
            width = height / ih * iw
        elif height is None:
            height = width / iw * ih
        return image.resize((int(width), int(height)))

    @property
    def full_path(self):
        return MEDIA_DIR / "img" / self.path

    @cached_property
    def tk(self):
        return PIL.ImageTk.PhotoImage(self.image)

    def get(self):
        return self.tk

    def __init__(self, path, props):
        if not "." in path:
            path += ".png"
        self.path = path
        self.props = props
