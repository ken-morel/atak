from pathlib import Path


def pixel_difference(pix1, pix2):
    r, g, b = zip(pix1, pix2)
    return abs(r[0] - r[1]) + abs(g[0] - g[1]) + abs(b[0] - b[1])


def rmbg(
    infile: Path,
    outfile: Path = None,
    color: tuple[int, int, int] = (255, 255, 255),
    replace: tuple[int, int, int, int] = (0, 0, 0, 0),
    tolerance: int = 10,
):
    from PIL import Image

    image = Image.open(infile).convert("RGBA")
    width, height = image.size
    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))[:3]
            if pixel_difference(pixel, color) < tolerance:
                image.putpixel((x, y), replace)
    image.save(outfile or infile)


for x in Path(".").glob("*.png"):
    rmbg(x, color=(255, 255, 255), replace=(255, 255, 255, 0))
