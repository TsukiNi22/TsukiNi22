#!/usr/bin/env python3
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Edition:
##  10/11/2026 by Tsukini

File Name:
##  cards.py

File Description:
##  Render the banner, the project cards and the activity panels of the profile README (SVG, dark theme)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

##### Import #####
# Import that can't be in the try
from sys import exit, stderr

# Import that can be checked
try:
    from pathlib import Path # Used for the paths of the config and of the assets
    from os import environ # Used for the token of the workflow
    from urllib.request import Request, urlopen # Used to read my-universe and the GitHub API
    from xml.sax.saxutils import escape # Used to escape the texts of the SVG
    import subprocess # Used to get the token of gh on a local run
    import math # Used for the size of the planets
    import argparse # Used for the arguments
    import tomllib # Used to read cards.toml
    import random # Used for the stars (fixed seed: same output every run)
    import json # Used to read the index of my-universe
except ImportError as e:
    stderr.write(f"Import Error ({__file__}): {e}\n")
    exit(255)

# Check if the program is call and not imported
if __name__ != "__main__":
    stderr.write(f"The {__file__} can only be executed and not imported!\n")
    exit(84)

##### Const #####
ROOT = Path(__file__).resolve().parent.parent
FONT = "-apple-system, 'Segoe UI', Ubuntu, 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'Fira Code', 'JetBrains Mono', Menlo, Consolas, monospace"
THEMES = { # one dark theme: the same look on the light and the dark GitHub themes
    "dark": {
        "bg": "#0d1117", "card": "#161b22", "card2": "#111a3a", "border": "#30363d", "text": "#e6edf3",
        "muted": "#9198a1", "accent": "#5b74ff", "accent2": "#2e48f7", "star": "#ffffff",
        "hand": "#3fb950", "ai": "#a371f7", "pre": "#d29922", "pill": "#21262d",
        "sky1": "#070b1d", "sky2": "#121a4a", "sky3": "#0d1117",
    },
}
LANG_COLORS = {"C++20": "#f34b7d", "C": "#a8b9cc", "x86_64": "#c08b3e", "Python": "#3572a5", "Shell": "#89e051", "Dockerfile": "#2496ed",
               "Lua": "#000080", "Skills": "#2e48f7", "Config": "#2e48f7"}
SIZES = {"large": (420, 172), "small": (276, 124), "row": (860, 48)}
ROW_GAP = 5 # space between two lines of the list on GitHub, in SVG units
STAR_SIZES = (2.8, 3.8, 5.0, 6.6) # size of the stars of the contribution sky, by level

##### Text #####
def text_width(text: str, size: float, bold: bool = False) -> float: # Approximate width of a text in a sans font
    text = text.replace("`", "")
    wide = sum(1 for c in text if ord(c) > 0x2e80) # CJK glyphs are about one em wide
    return (len(text) - wide) * size * (0.58 if bold else 0.55) + wide * size

def wrap(text: str, size: float, width: float, lines: int) -> list[str]: # Cut a text in lines fitting a width
    out: list[str] = []
    line = ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if text_width(test, size) <= width:
            line = test
            continue
        out.append(line)
        line = word
    out.append(line)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1].rstrip(".,:;") + "…"
    return out

def inline_code(line: str, code: bool, theme: dict) -> tuple[str, bool]: # `code` in mono accent, state kept between lines
    out = ""
    for i, part in enumerate(line.split("`")):
        if i > 0:
            code = not code
        if part:
            out += f'<tspan class="mono" fill="{theme["accent"]}">{escape(part)}</tspan>' if code else escape(part)
    return out, code

##### Shapes #####
def stars(rng: random.Random, count: int, width: int, height: int, color: str, twinkle: int,
          avoid: tuple[float, float, float, float] | None = None, light: tuple[float, float] = (0.25, 0.9),
          sizes: tuple[float, ...] = (0.6, 0.8, 1.0, 1.2, 1.6)) -> str: # Random stars, none in the avoid box
    out = []
    for i in range(count):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        while avoid and avoid[0] <= x <= avoid[2] and avoid[1] <= y <= avoid[3]:
            x, y = rng.uniform(0, width), rng.uniform(0, height)
        r = rng.choice(sizes)
        opacity = rng.uniform(*light)
        anim = ""
        if i < twinkle:
            dur, begin = rng.uniform(2.0, 6.5), rng.uniform(0, 5)
            anim = (f'<animate attributeName="opacity" values="{opacity:.2f};{opacity / 6:.2f};{opacity:.2f}" '
                    f'dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" opacity="{opacity:.2f}">{anim}</circle>')
    return "".join(out)

def orbit(rng: random.Random, width: int, height: int, theme: dict, scale: float) -> str: # Circle with a moon
    cx = width - rng.uniform(0, 30) * scale
    cy = rng.choice((rng.uniform(-10, 25), height - rng.uniform(-10, 25))) * 1.0
    r = rng.uniform(55, 85) * scale
    dur = rng.uniform(14, 30)
    turn = rng.choice((360, -360))
    start = rng.uniform(0, 360)
    moon = rng.uniform(2.5, 4) * scale + 1
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{theme["accent"]}" stroke-opacity=".24" '
            f'stroke-width="1.5" stroke-dasharray="{rng.choice(("none", "4 6", "2 5"))}"/>'
            f'<g transform="rotate({start:.0f} {cx:.1f} {cy:.1f})"><g><animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx:.1f} {cy:.1f}" to="{turn} {cx:.1f} {cy:.1f}" dur="{dur:.0f}s" repeatCount="indefinite"/>'
            f'<circle cx="{cx + r:.1f}" cy="{cy:.1f}" r="{moon * 2.4:.1f}" fill="{theme["accent"]}" opacity=".15"/>'
            f'<circle cx="{cx + r:.1f}" cy="{cy:.1f}" r="{moon:.1f}" fill="{theme["accent"]}" opacity=".75"/></g></g>')

def planet(rng: random.Random, width: int, height: int, theme: dict, scale: float) -> str: # Small planet floating
    r = rng.uniform(9, 14) * scale
    cx = width - rng.uniform(26, 50) * scale
    cy = height - rng.uniform(26, 44) * scale
    tilt = rng.uniform(-30, 10)
    dur = rng.uniform(5, 9)
    return (f'<defs><radialGradient id="pl" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#8fa0ff"/>'
            f'<stop offset=".6" stop-color="#2e48f7"/><stop offset="1" stop-color="#101a66"/></radialGradient></defs>'
            f'<g opacity=".8"><animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" '
            f'dur="{dur:.1f}s" repeatCount="indefinite"/>'
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r * 1.9:.1f}" ry="{r * 0.45:.1f}" fill="none" stroke="{theme["accent"]}" '
            f'stroke-opacity=".35" stroke-width="1.2" transform="rotate({tilt:.0f} {cx:.1f} {cy:.1f})"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#pl)"/>'
            f'<path d="M{cx - r * 1.9:.1f},{cy:.1f} A{r * 1.9:.1f},{r * 0.45:.1f} 0 0 0 {cx + r * 1.9:.1f},{cy:.1f}" fill="none" '
            f'stroke="{theme["accent"]}" stroke-opacity=".7" stroke-width="1.4" transform="rotate({tilt:.0f} {cx:.1f} {cy:.1f})"/></g>')

def meteor(rng: random.Random, width: int, height: int) -> dict: # Path and timing of a shooting star
    x0, y0 = rng.uniform(width * 0.3, width * 1.1), rng.uniform(-20, height * 0.3)
    dx, dy = -rng.uniform(120, 200), rng.uniform(50, 90)
    period, begin = rng.uniform(6, 13), rng.uniform(0, 6)
    return {"x": x0, "y": y0, "dx": dx, "dy": dy, "period": period, "begin": begin, "travel": 0.12}

def draw_meteor(star: dict, theme: dict, uid: str = "tail", offset: float = 0) -> str: # Shooting star, shifted up by offset
    tail = star.get("tail", 34)
    norm = (star["dx"] ** 2 + star["dy"] ** 2) ** 0.5
    tx, ty = -star["dx"] / norm * tail, -star["dy"] / norm * tail
    x0, y0 = star["x"], star["y"] - offset
    end, dur, begin = star["travel"], f'{star["period"]:.2f}s', f'{star["begin"]:.2f}s'
    return (f'<defs><linearGradient id="{uid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{tx:.1f}" y2="{ty:.1f}">'
            f'<stop offset="0" stop-color="{theme["star"]}"/><stop offset="1" stop-color="{theme["star"]}" stop-opacity="0"/>'
            f'</linearGradient></defs><g opacity="0">'
            f'<animate attributeName="opacity" values="0;.9;.9;0;0" keyTimes="0;{end * 0.1:.4f};{end * 0.8:.4f};{end:.4f};1" '
            f'dur="{dur}" begin="{begin}" repeatCount="indefinite"/><animateTransform attributeName="transform" '
            f'type="translate" values="{x0:.0f} {y0:.0f};{x0 + star["dx"]:.0f} {y0 + star["dy"]:.0f};'
            f'{x0 + star["dx"]:.0f} {y0 + star["dy"]:.0f}" keyTimes="0;{end:.4f};1" dur="{dur}" begin="{begin}" '
            f'repeatCount="indefinite"/><path d="M0,0 L{tx:.1f},{ty:.1f}" stroke="url(#{uid})" stroke-width="{star.get("size", 1.6)}" '
            f'stroke-linecap="round"/><circle r="1.4" fill="{theme["star"]}"/></g>')

def shooting_star(rng: random.Random, width: int, height: int, theme: dict) -> str: # Star crossing the card now and then
    return draw_meteor(meteor(rng, width, height), theme)

def cloud(rng: random.Random, width: int, height: int, theme: dict) -> dict: # Place, size and drift of a nebula
    x, y = rng.uniform(width * 0.4, width), rng.uniform(0, height)
    r = rng.uniform(50, 90)
    dx, dy = rng.uniform(-40, 40), rng.uniform(-20, 20)
    color = rng.choice((theme["accent"], theme["ai"], "#2e9cf7"))
    return {"x": x, "y": y, "r": r, "dx": dx, "dy": dy, "color": color, "tx": rng.uniform(16, 28), "ty": rng.uniform(12, 22)}

def draw_cloud(neb: dict, uid: str = "neb", offset: float = 0) -> str: # Soft glow drifting slowly, shifted up by offset
    x, y = neb["x"], neb["y"] - offset
    return (f'<defs><radialGradient id="{uid}"><stop offset="0" stop-color="{neb["color"]}" stop-opacity=".22"/>'
            f'<stop offset="1" stop-color="{neb["color"]}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{neb["r"]:.0f}" fill="url(#{uid})"><animate attributeName="cx" '
            f'values="{x:.0f};{x + neb["dx"]:.0f};{x:.0f}" dur="{neb["tx"]:.0f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{y:.0f};{y + neb["dy"]:.0f};{y:.0f}" dur="{neb["ty"]:.0f}s" '
            f'repeatCount="indefinite"/></circle>')

def nebula(rng: random.Random, width: int, height: int, theme: dict) -> str: # Soft glow drifting slowly
    return draw_cloud(cloud(rng, width, height, theme))

def list_sky(count: int, theme: dict) -> dict: # One sky shared by every line of the list: the lines show their slice
    width, height = SIZES["row"]
    total = count * height + (count - 1) * ROW_GAP
    rng = random.Random("list")
    meteors: list[dict] = []
    for _ in range(4):
        period = rng.uniform(8, 15)
        meteors.append({"x": rng.uniform(width * 0.25, width * 1.05), "y": -40.0, "dx": -rng.uniform(160, 340),
                        "dy": total + 80.0, "period": period, "begin": rng.uniform(0, 7),
                        "travel": rng.uniform(1.4, 2.2) / period, "tail": 70, "size": 1.9})
    clouds = [cloud(rng, width, total, theme) for _ in range(max(2, count // 2))]
    for neb in clouds:
        neb["x"] = rng.uniform(width * 0.25, width)
    return {"meteors": meteors, "clouds": clouds}

def sky(rng: random.Random, width: int, height: int, theme: dict, large: bool) -> str: # Random animated background
    scale = 1.0 if large else 0.65
    out = nebula(rng, width, height, theme) if rng.random() < 0.6 else ""
    out += stars(rng, 26 if large else 14, width, height, theme["star"], 26, light=(0.12, 0.35), sizes=(0.5, 0.7, 0.9))
    out += stars(rng, 8 if large else 4, width, height, theme["star"], 8, (0, 14, width - 26, height - 6))
    out += orbit(rng, width, height, theme, scale) if rng.random() < 0.55 else planet(rng, width, height, theme, scale)
    if rng.random() < 0.75:
        out += shooting_star(rng, width, height, theme)
    return out

def pill(x: float, y: float, label: str, color: str, theme: dict, filled: bool = False) -> tuple[str, float]: # Tag
    width = text_width(label, 11, True) + 18
    fill = color if filled else theme["pill"]
    stroke = color if not filled else "none"
    text = theme["bg"] if filled else color
    svg = (f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="20" rx="10" fill="{fill}" stroke="{stroke}" '
           f'stroke-opacity="0.55"/><text x="{x + width / 2:.1f}" y="{y + 14}" text-anchor="middle" '
           f'class="pill" fill="{text}">{escape(label)}</text>')
    return svg, width

def svg_document(width: int, height: int, body: str, style: str = "") -> str: # Root of every SVG
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img"><style>text{{font-family:{FONT}}} .mono{{font-family:{MONO}}} '
            f'.pill{{font-size:11px;font-weight:600}} '
            f'{style}</style>{body}</svg>\n')

##### Banner #####
def banner(profile: dict, packages: int, theme: dict, name: str) -> str: # Header of the README
    width, height = 1000, 250
    rng = random.Random(22)
    body = (f'<defs><linearGradient id="sky" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{theme["sky1"]}"/>'
            f'<stop offset=".6" stop-color="{theme["sky2"]}"/><stop offset="1" stop-color="{theme["sky3"]}"/></linearGradient>'
            f'<radialGradient id="planet" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#8fa0ff"/>'
            f'<stop offset=".55" stop-color="#2e48f7"/><stop offset="1" stop-color="#101a66"/></radialGradient>'
            f'<radialGradient id="glow"><stop offset="0" stop-color="#2e48f7" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="#2e48f7" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="{width}" height="{height}" rx="16" fill="url(#sky)"/>')
    body += stars(rng, 110, width, height, theme["star"], 30, (40, 50, 740, 228))

    # Planet with its ring and a moon in orbit
    cx, cy = 820, 125
    body += (f'<circle cx="{cx}" cy="{cy}" r="120" fill="url(#glow)"/>'
             f'<ellipse cx="{cx}" cy="{cy}" rx="105" ry="22" fill="none" stroke="{theme["accent"]}" stroke-width="2" '
             f'stroke-opacity=".35" transform="rotate(-18 {cx} {cy})"/>'
             f'<circle cx="{cx}" cy="{cy}" r="58" fill="url(#planet)"/>'
             f'<path d="M{cx - 105},{cy} A105,22 0 0 0 {cx + 105},{cy}" fill="none" stroke="{theme["accent"]}" '
             f'stroke-width="2.5" stroke-opacity=".8" transform="rotate(-18 {cx} {cy})"/>'
             f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" '
             f'dur="18s" repeatCount="indefinite"/><circle cx="{cx + 92}" cy="{cy - 38}" r="7" fill="{theme["accent"]}"/>'
             f'<circle cx="{cx + 92}" cy="{cy - 38}" r="12" fill="{theme["accent"]}" opacity=".18"/></g>')

    # Texts
    body += (f'<g><text x="56" y="108" font-size="58" font-weight="800" fill="{theme["text"]}" '
             f'letter-spacing="-1">{escape(profile["name"])}</text>'
             f'<text x="60" y="146" font-size="22" fill="{theme["accent"]}">{escape(profile["subtitle"])}</text>'
             f'<text x="60" y="180" font-size="16" fill="{theme["muted"]}">{escape(profile["tagline"])}</text></g>')
    x = 60.0
    for label, color in ((f"my-universe · {packages} packages", theme["accent"]), ("rpm · deb · arch", theme["muted"])):
        svg, w = pill(x, 202, label, color, theme)
        body += svg
        x += w + 8
    return svg_document(width, height, body)

##### Cards #####
def card(entry: dict, info: dict | None, theme: dict) -> str: # One project card
    width, height = SIZES[entry["kind"]]
    large = entry["kind"] == "large"
    rng = random.Random(entry["id"])
    lang = entry.get("lang", "")
    lang_color = LANG_COLORS.get(lang.split(" ")[0], theme["accent"])
    body = (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{theme["card"]}"/>'
            f'<stop offset="1" stop-color="{theme["card2"]}"/></linearGradient>'
            f'<clipPath id="clip"><rect width="{width}" height="{height}" rx="12"/></clipPath></defs>'
            f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="url(#bg)" stroke="{theme["border"]}"/>'
            f'<g clip-path="url(#clip)">{sky(rng, width, height, theme, large)}'
            f'<rect width="4" height="{height}" fill="{lang_color}"/></g>')

    # Title and version
    size = 20 if large else 15
    top = 38 if large else 30
    body += (f'<g><text x="22" y="{top}" font-size="{size}" font-weight="700" fill="{theme["text"]}">'
             f'{escape(entry["title"])}</text>')
    if info:
        x = width - 16
        versions = [(f'v{info["version"].split("-")[0]}', theme["accent"])]
        if info.get("pre"):
            versions.insert(0, (f'{info["pre"]} pre', theme["pre"]))
        for label, color in reversed(versions):
            x -= text_width(label, 11, True) + 18
            svg, w = pill(x, top - 15, label, color, theme)
            body += svg
            x -= 6

    # Description
    font = 13 if large else 11.5
    line_height = 19 if large else 16
    code = False
    for i, line in enumerate(wrap(entry["text"], font, width - 44, 3)):
        y = (top + 30 if large else top + 22) + i * line_height
        spans, code = inline_code(line, code, theme)
        body += f'<text x="22" y="{y}" font-size="{font}" fill="{theme["muted"]}">{spans}</text>'

    # Tags: language, made, formats or custom tags
    y = height - (34 if large else 28)
    body += (f'<circle cx="28" cy="{y + 10}" r="5" fill="{lang_color}"/>'
             f'<text x="39" y="{y + 14}" font-size="12" fill="{theme["muted"]}">{escape(lang)}</text>')
    made = info["category"] if info else entry.get("made", "")
    tags: list[tuple[str, str]] = []
    if made:
        tags.append((made, theme["hand"] if made == "hand-made" else theme["ai"]))
    if large: # small cards: the made tag only
        formats = list(info["formats"]) if info else []
        tags += [(" · ".join(formats), theme["muted"])] if formats else [(t, theme["muted"]) for t in entry.get("tags", [])]
    x = 39 + text_width(lang, 12) + 14
    if tags:
        for label, color in tags:
            svg, w = pill(x, y, label, color, theme)
            body += svg
            x += w + 6
    body += "</g>"
    return svg_document(width, height, body)

def row(entry: dict, index: int, theme: dict, sky_of: dict) -> str: # One line of the project list
    width, height = SIZES["row"]
    rng = random.Random(entry["id"])
    lang = entry.get("lang", "")
    lang_color = LANG_COLORS.get(lang.split(" ")[0], theme["accent"])
    lang_width = text_width(lang, 12)
    offset = (index - 1) * (height + ROW_GAP)
    shared = "".join(draw_cloud(neb, f"neb{i}", offset) for i, neb in enumerate(sky_of["clouds"]))
    shared += "".join(draw_meteor(star, theme, f"tail{i}", offset) for i, star in enumerate(sky_of["meteors"]))
    body = (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{theme["card"]}"/>'
            f'<stop offset="1" stop-color="{theme["card2"]}"/></linearGradient>'
            f'<clipPath id="clip"><rect width="{width}" height="{height}" rx="10"/></clipPath></defs>'
            f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="url(#bg)" stroke="{theme["border"]}"/>'
            f'<g clip-path="url(#clip)">{shared}'
            f'{stars(rng, 22, width, height, theme["star"], 22, light=(0.12, 0.4), sizes=(0.5, 0.7, 0.9))}'
            f'<rect width="4" height="{height}" fill="{lang_color}"/></g>')
    line = wrap(entry["text"], 13, width - 216 - lang_width - 60, 1)[0]
    body += (f'<text x="22" y="30" font-size="15" font-weight="700" fill="{theme["text"]}">{escape(entry["title"])}</text>'
             f'<text x="216" y="29" font-size="13" fill="{theme["muted"]}">{escape(line)}</text>'
             f'<circle cx="{width - 18 - lang_width - 10:.1f}" cy="24.5" r="4.5" fill="{lang_color}"/>'
             f'<text x="{width - 18}" y="29" font-size="12" text-anchor="end" fill="{theme["muted"]}">{escape(lang)}</text>')
    return svg_document(width, height, body)

##### GitHub #####
def github_token() -> str: # Token of the workflow, else the one of gh (local runs), else none
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        if environ.get(name):
            return environ[name]
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""

def github(path: str, token: str, query: str | None = None) -> object: # GET of the REST API, or a GraphQL query
    url = "https://api.github.com/graphql" if query else f"https://api.github.com/{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "tsukini22-profile-cards"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps({"query": query}).encode() if query else None
    with urlopen(Request(url, data=data, headers=headers), timeout=20) as response:
        return json.load(response)

def read_calendar(user: str, token: str) -> dict: # Contribution calendar of the last year (GraphQL needs a token)
    query = (f'{{user(login:"{user}"){{contributionsCollection{{contributionCalendar{{totalContributions '
             f'weeks{{contributionDays{{date contributionCount weekday}}}}}}}}}}}}')
    return github("", token, query)["data"]["user"]["contributionsCollection"]["contributionCalendar"]

##### Activity #####
def frame(width: int, height: int, theme: dict, seed: str, count: int = 90) -> str: # Sky background of a panel
    rng = random.Random(seed)
    return (f'<defs><linearGradient id="sky" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{theme["sky1"]}"/>'
            f'<stop offset=".6" stop-color="{theme["sky2"]}"/><stop offset="1" stop-color="{theme["sky3"]}"/></linearGradient>'
            f'<clipPath id="frame"><rect width="{width}" height="{height}" rx="14"/></clipPath></defs>'
            f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="url(#sky)" stroke="{theme["border"]}"/>'
            f'<g clip-path="url(#frame)">{nebula(rng, width, height, theme)}'
            f'{stars(rng, count, width, height, theme["star"], count // 2, light=(0.15, 0.6))}</g>')

def title(x: float, y: float, label: str, note: str, theme: dict) -> str: # Header of a panel
    return (f'<text x="{x}" y="{y}" class="mono" font-size="13" font-weight="700" letter-spacing="2" '
            f'fill="{theme["accent"]}">{escape(label)}</text>'
            f'<text x="{x}" y="{y + 18}" font-size="12" fill="{theme["muted"]}">{escape(note)}</text>')

STAR_DEFS = ('<defs><linearGradient id="spike"><stop offset="0" stop-color="#ffffff" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#ffffff"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
             '<radialGradient id="halo"><stop offset="0" stop-color="#5b74ff" stop-opacity=".75"/><stop offset=".6" '
             'stop-color="#2e48f7" stop-opacity=".18"/><stop offset="1" stop-color="#2e48f7" stop-opacity="0"/></radialGradient>'
             '<radialGradient id="glow"><stop offset="0" stop-color="#dfe5ff" stop-opacity=".9"/><stop offset=".35" '
             'stop-color="#7d8fff" stop-opacity=".35"/><stop offset="1" stop-color="#2e48f7" stop-opacity="0"/></radialGradient>'
             '</defs>')

def sparkle(x: float, y: float, size: float, opacity: float, diagonal: bool = False, extra: str = "") -> str:
    """Star like on a photo: soft glow, thin spikes fading at their ends, bright core (STAR_DEFS needed)"""
    spike = max(0.7, size / 5)
    spikes = "".join(f'<rect x="{-size * 1.3:.1f}" y="{-spike / 2:.2f}" width="{size * 2.6:.1f}" height="{spike:.2f}" '
                     f'fill="url(#spike)" transform="rotate({angle})"/>' for angle in (0, 90))
    if diagonal:
        spikes += "".join(f'<rect x="{-size:.1f}" y="{-spike / 3:.2f}" width="{size * 2:.1f}" height="{spike / 1.5:.2f}" '
                          f'fill="url(#spike)" opacity=".7" transform="rotate({angle})"/>' for angle in (45, 135))
    return (f'<g transform="translate({x:.1f} {y:.1f})" opacity="{opacity}"><g>{extra}'
            f'<circle r="{size * 0.8:.1f}" fill="url(#glow)"/>{spikes}<circle r="{max(0.8, size / 4.5):.2f}" fill="#ffffff"/>'
            f'</g></g>')

def streaks(days: list[dict]) -> tuple[int, int, str]: # Current streak, longest streak and the end of the longest
    current = longest = run = 0
    end = ""
    for day in days:
        run = run + 1 if day["contributionCount"] else 0
        if run > longest:
            longest, end = run, day["date"]
    for day in reversed(days[:-1] if not days[-1]["contributionCount"] else days): # today may still be empty
        if not day["contributionCount"]:
            break
        current += 1
    return current, longest, end

def nice_date(date: str) -> str: # 2026-10-24 -> Oct 24
    names = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    return f"{names[int(date[5:7]) - 1]} {int(date[8:])}"

def contribution_sky(calendar: dict, theme: dict) -> str: # Contribution calendar as a starry sky, with its numbers
    width, height = 860, 352
    rng = random.Random("contributions")
    weeks = calendar["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]]
    active = sorted(day["contributionCount"] for day in days if day["contributionCount"])
    def level(count: int) -> int: # 0 (none) to 4 (busiest quarter)
        if not count or not active:
            return 0
        return 1 + min(3, sum(count > active[len(active) * q // 4] for q in (1, 2, 3)))
    body = frame(width, height, theme, "contributions", 0) + STAR_DEFS

    # Numbers
    current, longest, longest_end = streaks(days)
    top_day = max(days, key=lambda d: d["contributionCount"])
    tiles = [(f'{calendar["totalContributions"]}', "contributions", "in the last year"),
             (f"{current} d", "current streak", "days in a row"),
             (f"{longest} d", "longest streak", f"ended {nice_date(longest_end)}" if longest_end else ""),
             (f'{top_day["contributionCount"]}', "brightest day", nice_date(top_day["date"])),
             (f'{calendar["totalContributions"] / len(days):.1f}', "per day", f'{len(active)} active days')]
    gap = 10
    tile_width = (width - 48 - gap * (len(tiles) - 1)) / len(tiles)
    for i, (value, label, note) in enumerate(tiles):
        x = 24 + i * (tile_width + gap)
        body += (f'<rect x="{x:.1f}" y="62" width="{tile_width:.1f}" height="62" rx="10" fill="#0b1124" fill-opacity=".72" '
                 f'stroke="{theme["border"]}"/><text x="{x + 14:.1f}" y="88" font-size="20" font-weight="800" '
                 f'fill="{theme["text"]}">{escape(value)}</text>'
                 f'<text x="{x + 14:.1f}" y="104" font-size="10.5" font-weight="700" letter-spacing=".6" '
                 f'fill="{theme["accent"]}">{escape(label.upper())}</text>'
                 f'<text x="{x + 14:.1f}" y="117" font-size="10" fill="{theme["muted"]}">{escape(note)}</text>')

    # Sky: one star per day on the grid of the calendar
    left, right, top, step_y = 70, width - 24, 150, 17
    step_x = (right - left) / max(1, len(weeks) - 1)
    for weekday, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body += (f'<text x="24" y="{top + weekday * step_y + 4}" font-size="10" fill="{theme["muted"]}">{label}</text>')
    points: dict[str, tuple[float, float]] = {}
    months: dict[str, float] = {}
    totals: list[int] = []
    today = days[-1]["date"]
    today_at = (0.0, 0.0, 0)
    for w, week in enumerate(weeks):
        totals.append(sum(day["contributionCount"] for day in week["contributionDays"]))
        for day in week["contributionDays"]:
            x = left + w * step_x + rng.uniform(-1.6, 1.6)
            y = top + day["weekday"] * step_y + rng.uniform(-1.6, 1.6)
            points[day["date"]] = (x, y)
            months.setdefault(day["date"][:7], left + w * step_x)
            lvl = level(day["contributionCount"])
            if day["date"] == today:
                today_at = (x, y, day["contributionCount"])
            if lvl == 0:
                body += f'<circle cx="{x:.1f}" cy="{y:.1f}" r=".8" fill="{theme["star"]}" opacity=".14"/>'
                continue
            size = STAR_SIZES[lvl - 1]
            opacity = (0.6, 0.75, 0.9, 1.0)[lvl - 1]
            low = rng.uniform(0.45, 0.7)
            twinkle = (f'<animateTransform attributeName="transform" type="scale" values="1;{low:.2f};1" '
                       f'dur="{rng.uniform(2, 6):.1f}s" begin="{rng.uniform(0, 5):.1f}s" repeatCount="indefinite"/>')
            if lvl >= 2: # halo behind the star, growing and shrinking at its own pace
                breath = rng.uniform(2.5, 5.5)
                body += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="url(#halo)"><animate attributeName="r" '
                         f'values="{size * 0.5:.1f};{size * 1.8:.1f};{size * 0.5:.1f}" dur="{breath:.1f}s" '
                         f'begin="{rng.uniform(0, 4):.1f}s" repeatCount="indefinite"/></circle>')
            body += sparkle(x, y, size, opacity, lvl == 4, twinkle)

    # Constellations: the busiest days joined in date order when they are close
    busiest = sorted(sorted(days, key=lambda d: -d["contributionCount"])[:18], key=lambda d: d["date"])
    for a, b in zip(busiest, busiest[1:]):
        (x1, y1), (x2, y2) = points[a["date"]], points[b["date"]]
        if math.hypot(x2 - x1, y2 - y1) < 90:
            body += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{theme["accent"]}" '
                     f'stroke-opacity=".5" stroke-width="1"/>')

    # Today: golden star with radar waves and a label
    tx, ty, tcount = today_at
    gold = "#ffcc4d"
    for delay in (0, 1.2):
        body += (f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="4" fill="none" stroke="{gold}" stroke-width="1.6" opacity="0">'
                 f'<animate attributeName="r" values="4;20" dur="2.4s" begin="{delay}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values=".9;0" dur="2.4s" begin="{delay}s" repeatCount="indefinite"/></circle>')
    label = f"today · {tcount}"
    label_width = text_width(label, 11, True) + 18
    lx, ly = tx - label_width - 22, ty - 30
    body += (f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="9" fill="{gold}" opacity=".3"><animate attributeName="r" values="7;11;7" '
             f'dur="2.4s" repeatCount="indefinite"/></circle>'
             f'<path d="M{tx - 5:.1f},{ty - 5:.1f} L{lx + label_width - 6:.1f},{ly + 10:.1f}" stroke="{gold}" stroke-opacity=".7"/>'
             f'<rect x="{lx:.1f}" y="{ly - 1:.1f}" width="{label_width:.1f}" height="20" rx="10" fill="#2b2208" '
             f'stroke="{gold}" stroke-opacity=".8"/><text x="{lx + label_width / 2:.1f}" y="{ly + 13:.1f}" text-anchor="middle" '
             f'font-size="11" font-weight="700" fill="{gold}">{escape(label)}</text>'
             f'<g transform="translate({tx:.1f} {ty:.1f})"><rect x="-9" y="-.8" width="18" height="1.6" fill="{gold}"/>'
             f'<rect x="-.8" y="-9" width="1.6" height="18" fill="{gold}"/><circle r="3.4" fill="#fff4cc"/></g>')

    # Contributions per week, under the sky
    base, bar_height = top + 6 * step_y + 52, 34
    peak = max(totals) or 1
    body += (f'<defs><linearGradient id="bar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{theme["accent2"]}" '
             f'stop-opacity=".35"/><stop offset="1" stop-color="#9fb0ff"/></linearGradient></defs>')
    for w, total in enumerate(totals):
        h = max(1.5, bar_height * total / peak) if total else 1
        body += (f'<rect x="{left + w * step_x - step_x * 0.32:.1f}" y="{base - h:.1f}" width="{step_x * 0.64:.1f}" '
                 f'height="{h:.1f}" rx="1.5" fill="url(#bar)" opacity="{0.35 if not total else 0.9}"/>')
    body += f'<text x="24" y="{base - 2}" font-size="10" fill="{theme["muted"]}">per week</text>'

    # Months and legend
    names = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    for month, x in list(months.items())[1:]:
        body += f'<text x="{x:.0f}" y="{base + 18}" font-size="10.5" fill="{theme["muted"]}">{names[int(month[5:]) - 1]}</text>'
    x = width - 24
    body += f'<text x="{x}" y="34" text-anchor="end" font-size="10.5" fill="{theme["muted"]}">more</text>'
    x -= 44
    for lvl in (4, 3, 2, 1):
        body += sparkle(x, 30, STAR_SIZES[lvl - 1], (0.6, 0.75, 0.9, 1.0)[lvl - 1], lvl == 4)
        x -= 16
    body += (f'<text x="{x - 2:.0f}" y="34" text-anchor="end" font-size="10.5" fill="{theme["muted"]}">less</text>'
             f'<circle cx="{x - 40:.0f}" cy="30" r="6" fill="#ffcc4d" opacity=".3"/><circle cx="{x - 40:.0f}" cy="30" r="3" '
             f'fill="#fff4cc"/>'
             f'<text x="{x - 50:.0f}" y="34" text-anchor="end" font-size="10.5" fill="{theme["muted"]}">today</text>')
    body += title(24, 30, "CONTRIBUTION SKY", "one star per day of the last year, brighter when busier", theme)
    return svg_document(width, height, body)

def terminal(packages: list[dict], theme: dict) -> str: # ./universe list typed in a terminal, in a loop with clear
    width, line = 860, 21
    height = 96 + (len(packages) + 3) * line
    period, char = 34.0, 0.08 # one loop, time to type a letter
    command, clear = "./universe list", "clear"
    body = (f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="#0a0e18" stroke="{theme["border"]}"/>'
            f'<path d="M.5,34 h{width - 1}" stroke="{theme["border"]}"/>'
            f'<circle cx="22" cy="17" r="6" fill="#ff5f57"/><circle cx="42" cy="17" r="6" fill="#febc2e"/>'
            f'<circle cx="62" cy="17" r="6" fill="#28c840"/><text x="{width / 2}" y="22" text-anchor="middle" '
            f'class="mono" font-size="12" fill="{theme["muted"]}">tsukini@fedora: ~/my-universe</text>')
    prompt = (f'<tspan fill="{theme["hand"]}">tsukini@fedora</tspan><tspan fill="{theme["muted"]}">:</tspan>'
              f'<tspan fill="{theme["accent"]}">~/my-universe</tspan><tspan fill="{theme["muted"]}">$ </tspan>')
    prompt_width = len("tsukini@fedora:~/my-universe$ ") * 7.8
    x0 = 22 + prompt_width

    # Timeline of one loop (seconds)
    typed_at = 0.8
    output_at = typed_at + len(command) * char + 0.35
    clear_at = period - 3.0 # `clear` typed on the last prompt
    cleared_at = clear_at + len(clear) * 0.12 + 0.4 # screen empty until the end of the loop
    def k(t: float) -> str: # time -> keyTime
        return f"{t / period:.4f}"
    def typing(text: str, start: float, step: float, until: float, uid: str, y: float) -> str: # Text typed letter by letter
        times = ["0"] + [k(start + n * step) for n in range(len(text) + 1)] + [k(until)]
        widths = ["0"] + [f"{n * 7.8:.1f}" for n in range(len(text) + 1)] + ["0"]
        return (f'<clipPath id="{uid}"><rect x="{x0:.0f}" y="{y - 15}" height="20" width="0"><animate attributeName="width" '
                f'values="{";".join(widths)}" keyTimes="{";".join(times)}" calcMode="discrete" dur="{period}s" '
                f'repeatCount="indefinite"/></rect></clipPath><text x="{x0:.0f}" y="{y}" class="mono" font-size="13" '
                f'fill="{theme["text"]}" clip-path="url(#{uid})">{escape(text)}</text>')
    def shown(start: float, end: float) -> str: # Visible from start to end of each loop
        return (f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{k(start)};{k(end)}" calcMode="discrete" '
                f'dur="{period}s" repeatCount="indefinite"/>')
    def cursor(x: float, y: float) -> str: # Blinking block cursor
        return (f'<rect x="{x:.0f}" y="{y - 13:.0f}" width="8" height="16" fill="{theme["text"]}"><animate '
                f'attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>')

    # First prompt: always there, the command is typed then erased by clear
    y = 64
    body += f'<text x="22" y="{y}" class="mono" font-size="13">{prompt}</text>' + typing(command, typed_at, char, cleared_at, "cmd", y)
    body += (f'<g opacity="1"><animate attributeName="opacity" values="1;0;1" keyTimes="0;{k(typed_at)};{k(cleared_at)}" '
             f'calcMode="discrete" dur="{period}s" repeatCount="indefinite"/>{cursor(x0, y)}</g>')

    # Output line by line
    columns = [("NAME", 22), ("CATEGORY", 200), ("VERSION", 330), ("PRE-RELEASE", 440), ("FORMATS", 580), ("RELEASED", 730)]
    rows = [[(label, theme["muted"]) for label, _ in columns]]
    for pkg in sorted(packages, key=lambda pkg: pkg["category"] != "hand-made"): # hand-made first, then ai-made
        made_color = theme["hand"] if pkg["category"] == "hand-made" else theme["ai"]
        rows.append([(pkg["name"], theme["text"]), (pkg["category"], made_color), (pkg["version"].split("-")[0], theme["accent"]),
                     (pkg.get("pre") or "-", theme["pre"] if pkg.get("pre") else theme["muted"]),
                     (" ".join(pkg["formats"]), theme["muted"]), ((pkg.get("release") or {}).get("date", "-"), theme["muted"])])
    for i, cells in enumerate(rows):
        y += line
        bold = ' font-weight="700"' if i == 0 else ""
        texts = "".join(f'<text x="{x}" y="{y}" class="mono" font-size="13" fill="{color}"{bold}>{escape(text)}</text>'
                        for (text, color), (_, x) in zip(cells, columns))
        body += f'<g opacity="0">{shown(output_at + i * 0.12, cleared_at)}{texts}</g>'

    # Last prompt: cursor while reading, then `clear` is typed
    y += line * 1.6
    ready_at = output_at + len(rows) * 0.12 + 0.2
    body += (f'<g opacity="0">{shown(ready_at, cleared_at)}<text x="22" y="{y:.0f}" class="mono" font-size="13">{prompt}</text>'
             f'{typing(clear, clear_at, 0.12, cleared_at, "clear", y)}'
             f'<g opacity="1"><animate attributeName="opacity" values="1;0" keyTimes="0;{k(clear_at)}" calcMode="discrete" '
             f'dur="{period}s" repeatCount="indefinite"/>{cursor(x0, y)}</g></g>')
    return svg_document(width, height, body)

##### Main #####
def read_universe(url: str) -> dict[str, dict]: # Packages of my-universe by name
    with urlopen(url, timeout=20) as response:
        index = json.load(response)
    return {source["name"]: source for source in index["sources"]}

def render_space(config: dict, universe: dict, theme: dict, name: str, out: Path) -> int: # Activity panels, count written
    user = config["profile"]["user"]
    token = github_token()
    cards = [entry for entry in config["card"] if entry["kind"] != "row"]
    packages = [universe[e["universe"]] for e in cards if e.get("universe")]
    data: dict = {}
    def calendar() -> dict:
        if "calendar" not in data:
            data["calendar"] = read_calendar(user, token)
        return data["calendar"]
    panels = {
        "terminal": lambda: terminal(packages, theme),
        "sky": lambda: contribution_sky(calendar(), theme),
    }
    count = 0
    for panel, render in panels.items():
        try:
            svg = render()
        except (OSError, ValueError, KeyError, TypeError) as e: # keep the last image when GitHub cannot be read
            stderr.write(f"{panel}: cannot be rendered, the previous image is kept ({e})\n")
            continue
        (out / f"{panel}-{name}.svg").write_text(svg, encoding="utf-8")
        count += 1
    return count

def main() -> int:
    parser = argparse.ArgumentParser(description="Render the banner and the cards of the profile README")
    parser.add_argument("--config", type=Path, default=ROOT / "cards.toml", help="cards configuration")
    parser.add_argument("--out", type=Path, default=ROOT / "assets", help="output folder of the SVG")
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    try:
        universe = read_universe(config["profile"]["universe"])
    except (OSError, ValueError, KeyError) as e:
        stderr.write(f"cannot read the index of my-universe: {e}\n")
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    count = 0
    for name, theme in THEMES.items():
        (args.out / f"banner-{name}.svg").write_text(banner(config["profile"], len(universe), theme, name), encoding="utf-8")
        count += 1
        rows = [entry for entry in config["card"] if entry["kind"] == "row"]
        sky_of = list_sky(len(rows), theme)
        for index, entry in enumerate(rows, 1):
            (args.out / f"{entry['id']}-{name}.svg").write_text(row(entry, index, theme, sky_of), encoding="utf-8")
            count += 1
        for entry in (entry for entry in config["card"] if entry["kind"] != "row"):
            info = universe.get(entry.get("universe", ""))
            if entry.get("universe") and info is None:
                stderr.write(f"{entry['id']}: package {entry['universe']} not in my-universe\n")
                return 1
            (args.out / f"{entry['id']}-{name}.svg").write_text(card(entry, info, theme), encoding="utf-8")
            count += 1
            if entry.get("pin"): # small copy for the Pinned section, with its own sky
                pinned = entry | {"kind": "small", "id": f"{entry['id']}-pin"}
                (args.out / f"{pinned['id']}-{name}.svg").write_text(card(pinned, info, theme), encoding="utf-8")
                count += 1
        count += render_space(config, universe, theme, name, args.out)
    print(f"✓ {count} SVG rendered in {args.out}")
    return 0

exit(main())
