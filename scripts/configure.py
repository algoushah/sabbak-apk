import os, re, sys, hashlib, struct, zlib, io, urllib.request
from urllib.parse import urlparse

url = os.environ.get("APP_URL", "").strip()
name = os.environ.get("APP_NAME", "").strip() or "App"
icon_url = os.environ.get("ICON_URL", "").strip()

p = urlparse(url)
if p.scheme not in ("http", "https") or not p.netloc:
    sys.exit("Invalid URL: must start with http:// or https://")
name = re.sub(r"[\r\n\t]+", " ", name)[:30]


def res(s):
    s = s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
    s = s.replace("@", "\\@").replace("?", "\\?")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


with open("app/src/main/res/values/strings.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n')
    f.write('    <string name="app_name" formatted="false">%s</string>\n' % res(name))
    f.write('    <string name="app_url" formatted="false">%s</string>\n' % res(url))
    f.write("</resources>\n")

app_id = "com.sabbak.w" + hashlib.sha1(url.encode()).hexdigest()[:10]
with open(os.environ["GITHUB_ENV"], "a") as f:
    f.write("APP_ID=%s\n" % app_id)
print("appId:", app_id)

dest = "app/src/main/res/mipmap-xxxhdpi/ic_launcher.png"
os.makedirs(os.path.dirname(dest), exist_ok=True)
PNG_SIG = b"\x89PNG\r\n\x1a\n"
SIZE = 192


def solid_png(path, size=SIZE, rgb=(124, 58, 237)):
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = (b"\x00" + bytes(rgb) * size) * size
    png = (PNG_SIG
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def fetch_icon(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read(5_000_000)


def try_pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


ok = False
if icon_url.startswith(("http://", "https://")):
    try:
        data = fetch_icon(icon_url)
        head = data[:200].lstrip().lower()
        if head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in data[:2000].lower()):
            raise ValueError("SVG is not supported, use a PNG link")
        if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
            raise ValueError("The link returned a web page, not an image")
        Image = try_pillow()
        if Image is not None:
            # Any format (PNG, JPG, WebP, ICO, GIF): normalise to a 192x192 PNG
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            img.thumbnail((SIZE, SIZE))
            canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
            canvas.paste(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))
            canvas.save(dest, "PNG")
        elif data.startswith(PNG_SIG):
            with open(dest, "wb") as f:
                f.write(data)
        else:
            raise ValueError("Not a PNG and Pillow is not installed")
        ok = True
        print("Icon OK")
    except Exception as e:
        print("::warning::Icon failed, using default icon: %s" % e)
if not ok:
    solid_png(dest)
