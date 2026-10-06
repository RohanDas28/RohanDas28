#!/usr/bin/env python3
"""
Generate a neofetch-style info card SVG (840 x 880) matching the terminal theme.
Each row slides and fades in on stagger.
Ensures 100% strict XML validity (all text properly escaped).
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")

W, H = 840, 880
PAD = 24
TITLEBAR_H = 30

BG = "#0d1117"
BG2 = "#111722"
TILE = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
CYAN = "#22d3ee"
GREEN = "#39d353"
YELLOW = "#f2cc60"
PURPLE = "#bc8cff"
BLUE = "#58a6ff"

lines = [
    ("OS", "Ubuntu Linux / Windows 11 x86_64", CYAN),
    ("Host", "Developer Workstation", INK),
    ("Kernel", "Open Source & Web Engineering", INK),
    ("Uptime", "Building & shipping side projects", GREEN),
    ("Shell", "zsh / bash / pwsh", INK),
    ("Role", "Software Developer & Open Source Builder", YELLOW),
    ("Languages", "Python, C, C++, Java, JavaScript, HTML, CSS", PURPLE),
    ("Frameworks", "Next.js, React, Tailwind CSS, Bootstrap", BLUE),
    ("Creative", "Photoshop, Premiere Pro, After Effects, Audition", CYAN),
    ("Tools", "Git, GitHub, Linux, VS Code", GREEN),
    ("Community", "Open Source Contributor & Content Creator", YELLOW),
    ("Status", "Always curious, building high-impact tools", INK),
]

stagger = 0.12
slide_dur = 0.4

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<style>',
    f'.row {{ opacity: 0; animation: fadeIn {slide_dur}s ease-out both; }}',
    '@keyframes fadeIn { 0% { opacity: 0; transform: translateY(10px); } 100% { opacity: 1; transform: translateY(0); } }',
    '@media (prefers-reduced-motion: reduce) { .row { opacity: 1 !important; transform: none !important; animation: none !important; } }',
    '</style>',
    f'<defs><linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]

for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(
    f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
    f'text-anchor="middle">rohan@github: ~$ neofetch</text>'
)

# Header banner in card
header_y = TITLEBAR_H + 46
parts.append(f'<text class="row" style="animation-delay:0.05s" x="{PAD + 10}" y="{header_y}" font-size="28" font-weight="700" fill="{GREEN}">rohan@github</text>')
parts.append(f'<text class="row" style="animation-delay:0.10s" x="{PAD + 10}" y="{header_y + 24}" font-size="18" fill="{MUTED}">--------------------------------------------------</text>')

y_start = header_y + 60
row_height = 42

for idx, (key, val, val_color) in enumerate(lines):
    y = y_start + idx * row_height
    delay = 0.15 + idx * stagger
    key_escaped = html.escape(key)
    val_escaped = html.escape(val)
    parts.append(f'<g class="row" style="animation-delay:{delay:.2f}s">')
    parts.append(f'<text x="{PAD + 10}" y="{y}" font-size="19" font-weight="700" fill="{CYAN}">{key_escaped}:</text>')
    parts.append(f'<text x="{PAD + 180}" y="{y}" font-size="19" fill="{val_color}">{val_escaped}</text>')
    parts.append('</g>')

# Color blocks at bottom
color_blocks_y = y_start + len(lines) * row_height + 20
parts.append(f'<g class="row" style="animation-delay:{0.2 + len(lines)*stagger:.2f}s">')
colors = ["#282c34", "#e06c75", "#98c379", "#e5c07b", "#61afef", "#c678dd", "#56b6c2", "#abb2bf"]
bx_start = PAD + 10
bw = 45
bh = 22
for i, c in enumerate(colors):
    parts.append(f'<rect x="{bx_start + i * (bw + 6)}" y="{color_blocks_y}" width="{bw}" height="{bh}" rx="4" fill="{c}"/>')
parts.append('</g>')

parts.append('</svg>')
svg = "".join(parts)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Successfully wrote {OUT}: {W} x {H}, {len(svg)} bytes")
