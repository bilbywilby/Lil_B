import os
import re, numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(HERE, "..", "assets", "logo", "husky-primary.svg")
OUTDIR = os.path.join(HERE, "..", "assets", "logo")
os.makedirs(os.path.join(OUTDIR, "icons"), exist_ok=True)
os.makedirs(os.path.join(OUTDIR, "favicons"), exist_ok=True)

txt = open(SVG_PATH).read()
W = int(re.search(r'width="(\d+)"', txt).group(1))
H = int(re.search(r'height="(\d+)"', txt).group(1))
d = re.search(r'd="([^"]+)"', txt).group(1)

subpaths = []
for chunk in d.split(" M "):
    chunk = chunk.strip()
    if chunk.startswith("M "):
        chunk = chunk[2:]
    chunk = chunk.replace(" Z", "").replace("L", "").strip()
    nums = [float(v) for v in chunk.split()]
    pts = list(zip(nums[0::2], nums[1::2]))
    subpaths.append(pts)

def render_mask(target_w, target_h, supersample=4):
    sw, sh = target_w*supersample, target_h*supersample
    scale = min(sw / W, sh / H)
    ox = (sw - W*scale) / 2
    oy = (sh - H*scale) / 2
    canvas = np.zeros((sh, sw), dtype=np.uint8)
    for pts in subpaths:
        layer = Image.new("1", (sw, sh), 0)
        spts = [((x*scale)+ox, (y*scale)+oy) for x, y in pts]
        ImageDraw.Draw(layer).polygon(spts, fill=1)
        canvas = np.bitwise_xor(canvas, np.array(layer, dtype=np.uint8))
    mask_img = Image.fromarray((canvas*255).astype(np.uint8), mode="L")
    mask_img = mask_img.resize((target_w, target_h), Image.LANCZOS)
    return mask_img

def render_icon(path, size, fill=(0,0,0,255)):
    mask = render_mask(size, size)
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    solid = Image.new("RGBA", (size, size), fill)
    img = Image.composite(solid, img, mask)
    img.save(path)
    return img

# --- App icon / favicon set (black ink, transparent bg) ---
for size in [1024, 512, 256, 128, 64, 32, 16]:
    render_icon(f"{OUTDIR}/icons/app-icon-{size}.png", size)

render_icon(f"{OUTDIR}/husky-primary.png", 512)
render_icon(f"{OUTDIR}/favicons/favicon-32x32.png", 32)
render_icon(f"{OUTDIR}/favicons/favicon-16x16.png", 16)

# --- Sponsor badge (black ink on white, square, padded) ---
badge_size = 200
mask = render_mask(int(badge_size*0.8), int(badge_size*0.8))
badge = Image.new("RGBA", (badge_size, badge_size), (255,255,255,255))
solid = Image.new("RGBA", mask.size, (0,0,0,255))
pad = (badge_size - mask.size[0])//2, (badge_size - mask.size[1])//2
layer = Image.new("RGBA", (badge_size, badge_size), (0,0,0,0))
layer.paste(solid, pad, mask)
badge = Image.alpha_composite(badge, layer)
badge.save(f"{OUTDIR}/sponsor-badge.png")

# --- Dark mode PNG (white ink, transparent bg) for use on dark surfaces ---
render_icon(f"{OUTDIR}/husky-dark-mode.png", 512, fill=(255,255,255,255))

# --- OG social card 1200x630: white bg, logo left, wordmark right ---
card = Image.new("RGBA", (1200, 630), (255,255,255,255))
logo_h = 480
mask = render_mask(int(logo_h*W/H), logo_h)
solid = Image.new("RGBA", mask.size, (0,0,0,255))
logo_layer = Image.new("RGBA", (1200,630), (0,0,0,0))
logo_layer.paste(solid, (60, 75), mask)
card = Image.alpha_composite(card, logo_layer)
draw = ImageDraw.Draw(card)
try:
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
except Exception:
    font_big = ImageFont.load_default()
    font_small = ImageFont.load_default()
tx = 60 + mask.size[0] + 50
draw.text((tx, 250), "DevHound", font=font_big, fill=(15,23,42,255))
draw.text((tx, 360), "AI-powered code review assistant", font=font_small, fill=(71,85,105,255))
card.convert("RGB").save(f"{OUTDIR}/og-card.png")

print("W,H source:", W, H)
print("done")
