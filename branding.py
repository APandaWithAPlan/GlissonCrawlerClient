import base64
import io
import os

from PIL import Image, ImageDraw, ImageOps

from config import BASE_DIR

LOGO_SOURCE = os.path.join(BASE_DIR, "glisson.jpg")


def logo_data_uri(size: int = 200) -> str:
    im = Image.open(LOGO_SOURCE).convert("RGB")
    im = ImageOps.fit(im, (size, size), method=Image.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

    circular = Image.new("RGBA", (size, size))
    circular.paste(im, (0, 0), mask)

    buf = io.BytesIO()
    circular.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def favicon_path() -> str:
    out_path = os.path.join(BASE_DIR, "assets", "favicon.png")
    if not os.path.exists(out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        im = Image.open(LOGO_SOURCE).convert("RGB")
        im = ImageOps.fit(im, (64, 64), method=Image.LANCZOS)
        im.save(out_path, format="PNG")
    return out_path


def avatar_path(size: int = 128) -> str:
    out_path = os.path.join(BASE_DIR, "assets", "avatar.png")
    if not os.path.exists(out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        im = Image.open(LOGO_SOURCE).convert("RGB")
        im = ImageOps.fit(im, (size, size), method=Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        circular = Image.new("RGBA", (size, size))
        circular.paste(im, (0, 0), mask)
        circular.save(out_path, format="PNG")
    return out_path
