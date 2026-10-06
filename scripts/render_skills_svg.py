#!/usr/bin/env python3
"""
Generate an innovative, animated terminal Skills Dashboard SVG (skills.svg).
Matches the exact 860px width of contrib-heatmap.svg with a dark terminal frame,
4 categorized panels, skill pill tags with colored indicators, and status bar.
Ensures 100% strict XML validity (all text properly escaped).
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "skills.svg")

W = 860
H = 430
PAD = 20
TITLEBAR_H = 30

BG = "#0a0e14"
BG2 = "#0d1420"
FRAME = "#1f6feb"
CARD_BG = "#111722"
CARD_FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
CYAN = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"
PURPLE = "#bc8cff"

categories = [
    {
        "title": "PROGRAMMING LANGUAGES",
        "icon": ">_ ",
        "color": CYAN,
        "skills": [
            ("Python", "#3776ab"), ("C", "#659ad2"), ("C++", "#00599c"),
            ("Java", "#ed8b00"), ("JavaScript", "#f7df1e"), ("HTML5", "#e34f26"), ("CSS3", "#1572b6")
        ]
    },
    {
        "title": "FRAMEWORKS & WEB",
        "icon": "// ",
        "color": GREEN,
        "skills": [
            ("Next.js", "#ffffff"), ("Tailwind CSS", "#38b2ac"),
            ("Bootstrap", "#7952b3"), ("Bulma", "#00d1b2"), ("React", "#61dafb")
        ]
    },
    {
        "title": "SYSTEMS & DEV TOOLS",
        "icon": "$ ",
        "color": GOLD,
        "skills": [
            ("Linux", "#fcc624"), ("Ubuntu", "#e95420"), ("Git", "#f05032"),
            ("GitHub", "#ffffff"), ("VS Code", "#007acc"), ("Bash", "#4eaa25")
        ]
    },
    {
        "title": "CREATIVE & PRODUCTION",
        "icon": "* ",
        "color": PURPLE,
        "skills": [
            ("Photoshop", "#31a8ff"), ("Lightroom", "#31a8ff"),
            ("Premiere Pro", "#ea77ff"), ("After Effects", "#9999ff"),
            ("Audition", "#00e5ff"), ("Audacity", "#0055ff"), ("GIMP", "#e09e51")
        ]
    }
]

# Layout: 2 columns x 2 rows
COL_W = (W - PAD * 2 - 16) / 2
ROW_H = 155
GRID_TOP = TITLEBAR_H + 16

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<style>',
    '.card { opacity: 0; animation: slideUp 0.5s ease-out both; }',
    '@keyframes slideUp { 0% { opacity: 0; transform: translateY(12px); } 100% { opacity: 1; transform: translateY(0); } }',
    '@media (prefers-reduced-motion: reduce) { .card { opacity: 1 !important; transform: none !important; animation: none !important; } }',
    '</style>',
    f'<defs><linearGradient id="sbg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#sbg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
]

for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(
    f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
    f'text-anchor="middle">rohan@github: ~/skills --inspect</text>'
)

# Render 4 panels
for i, cat in enumerate(categories):
    col = i % 2
    row = i // 2
    cx = PAD + col * (COL_W + 16)
    cy = GRID_TOP + row * (ROW_H + 12)
    delay = 0.15 + i * 0.12
    title_escaped = html.escape(cat["icon"] + cat["title"])

    parts.append(f'<g class="card" style="animation-delay:{delay:.2f}s">')
    # Card background
    parts.append(
        f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{COL_W:.1f}" height="{ROW_H:.1f}" rx="8" '
        f'fill="{CARD_BG}" stroke="{CARD_FRAME}" stroke-width="1"/>'
    )
    # Header
    parts.append(
        f'<text x="{cx + 14:.1f}" y="{cy + 24:.1f}" font-size="12" font-weight="700" fill="{cat["color"]}">'
        f'{title_escaped}</text>'
    )
    parts.append(
        f'<line x1="{cx + 14:.1f}" y1="{cy + 34:.1f}" x2="{cx + COL_W - 14:.1f}" y2="{cy + 34:.1f}" '
        f'stroke="{CARD_FRAME}" stroke-dasharray="3,3"/>'
    )

    # Pills layout
    px_start = cx + 14
    py_start = cy + 56
    cur_x = px_start
    cur_y = py_start

    for name, dot_col in cat["skills"]:
        name_escaped = html.escape(name)
        pill_w = len(name) * 8.0 + 26
        if cur_x + pill_w > cx + COL_W - 14:
            cur_x = px_start
            cur_y += 34

        parts.append(
            f'<rect x="{cur_x:.1f}" y="{cur_y - 14:.1f}" width="{pill_w:.1f}" height="22" rx="4" '
            f'fill="#161b22" stroke="{CARD_FRAME}" stroke-width="1"/>'
        )
        parts.append(
            f'<circle cx="{cur_x + 9:.1f}" cy="{cur_y - 3:.1f}" r="3.5" fill="{dot_col}"/>'
        )
        parts.append(
            f'<text x="{cur_x + 18:.1f}" y="{cur_y + 1:.1f}" font-size="11" fill="{TEXT}">{name_escaped}</text>'
        )
        cur_x += pill_w + 8

    parts.append('</g>')

# Footer status bar
foot_y = H - 18
parts.append(f'<line x1="0" y1="{H - 36}" x2="{W}" y2="{H - 36}" stroke="{FRAME}" stroke-opacity="0.25"/>')
parts.append(
    f'<text x="{PAD}" y="{foot_y}" font-size="11" fill="{MUTED}">'
    f'rohan@github:~$ <tspan fill="{GREEN}">echo</tspan> '
    f'<tspan fill="{TEXT}">"Continuously innovating, building &amp; contributing to open-source."</tspan></text>'
)
blink_x = PAD + 540
parts.append(
    f'<rect x="{blink_x}" y="{foot_y - 10}" width="7" height="12" fill="{GREEN}">'
    f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
    f'</rect>'
)

parts.append('</svg>')
svg = "".join(parts)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Successfully wrote {OUT}: {W} x {H}, {len(svg)} bytes")
