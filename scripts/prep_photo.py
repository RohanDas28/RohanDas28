"""
Prepare the profile photo for clean ASCII conversion:
  1. Remove the background cleanly (HSV threshold/floodfill for solid studio backgrounds,
     with rembg fallback if available) so the subject is isolated on white.
  2. Bilateral-smooth skin and textures while keeping drawn/facial lines sharp.
  3. Stretch tones so skin lands near bright/white and hair/features stay dark.
  4. Darken linework (difference-of-gaussians ridges) — eyes, glasses, mustache, pupils.
  5. Composite onto white and crop square around the subject.

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

Usage:
    python scripts/prep_photo.py [input.png] [output.png]
"""
import os
import sys
import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "profile.png")
if not os.path.exists(INP):
    alt_inp = os.path.join(HERE, "..", "source-photo.png")
    if os.path.exists(alt_inp):
        INP = alt_inp

OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

LINE_WEIGHT = 0.65     # how hard facial contours and lines are pushed toward black

print(f"Reading input image: {INP}")
img_bgr = cv2.imread(INP)
if img_bgr is None:
    raise FileNotFoundError(f"Could not load image at {INP}")

h, w = img_bgr.shape[:2]

# 1. Segment background
# Check if yellow/studio background is present
hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
lower_yellow = np.array([12, 80, 90])
upper_yellow = np.array([45, 255, 255])
bg_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

# If yellow background covers corner regions, use precise floodFill segmentation
corners_yellow = (bg_mask[0, 0] > 0) or (bg_mask[0, w - 1] > 0)

if corners_yellow and np.sum(bg_mask > 0) > (h * w * 0.15):
    print("Detected studio background, applying precise color floodfill segmentation...")
    flood = bg_mask.copy()
    mask_flood = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, mask_flood, (0, 0), 255)
    cv2.floodFill(flood, mask_flood, (w - 1, 0), 255)
    subject_mask = cv2.bitwise_not(flood)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    subject_mask = cv2.morphologyEx(subject_mask, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(subject_mask)
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    person_mask = np.uint8(labels == largest_label) * 255
    contours, _ = cv2.findContours(person_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(person_mask, contours, -1, 255, -1)
    alpha = person_mask.astype(np.float32)
else:
    try:
        from rembg import remove
        print("Using rembg for background removal...")
        cut = remove(Image.open(INP).convert("RGBA"))
        alpha = np.array(cut.split()[-1]).astype(np.float32)
    except Exception as e:
        print(f"rembg not available or failed ({e}); falling back to edge/intensity mask")
        alpha = np.full((h, w), 255, dtype=np.float32)

# 2. Bilateral smoothing (removes texture noise while keeping high-contrast edges sharp)
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
smooth = gray
for _ in range(3):
    smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

# 3. Tone stretch over subject area only
valid_pixels = smooth[alpha > 128]
if len(valid_pixels) > 0:
    lo, hi = np.percentile(valid_pixels, [2, 92])
    tone = np.clip((smooth.astype(np.float32) - lo) / max(hi - lo, 1.0), 0, 1)
else:
    tone = smooth.astype(np.float32) / 255.0

# 4. Difference-of-Gaussians edge enhancement (sharpens glasses, eyes, mustache)
fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
coarse = cv2.GaussianBlur(smooth, (0, 0), 6.0).astype(np.float32)
lines = np.clip((coarse - fine) / 40.0, 0, 1)
out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255.0

# 5. Composite onto pure white with subtle feathering
feathered_alpha = cv2.GaussianBlur(alpha / 255.0, (0, 0), 1.0)
out = out * feathered_alpha + 255.0 * (1.0 - feathered_alpha)

# 6. Square crop around subject with margin
ys, xs = np.where(alpha > 20)
if len(xs) > 0 and len(ys) > 0:
    side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 60
    cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
    canvas = np.full((side, side), 255, np.uint8)
    x0, y0 = cx - side // 2, cy - side // 2
    sx0, sy0 = max(x0, 0), max(y0, 0)
    sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
else:
    canvas = out.astype(np.uint8)

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
Image.fromarray(canvas, mode="L").save(OUT)
print(f"Successfully wrote {OUT} ({canvas.shape[1]}x{canvas.shape[0]})")
