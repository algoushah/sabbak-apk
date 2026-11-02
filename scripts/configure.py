import os, re, sys, hashlib, subprocess, struct, zlib, urllib.request
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


def solid_png(path, size=192, rgb=(124, 58, 237)):
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = (b"\x00" + bytes(rgb) * size) * size
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


ok = False
if icon_url.startswith(("http://", "https://")):
    try:
        req = urllib.request.Request(icon_url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=20).read(5_000_000)
        open("/tmp/icon_src", "wb").write(data)
        subprocess.run(["convert", "/tmp/icon_src[0]", "-background", "none",
                        "-resize", "192x192", "-gravity", "center",
                        "-extent", "192x192", dest], check=True)
        ok = True
    except Exception as e:
        print("Icon failed, using default:", e)
if not ok:
    solid_png(dest)
