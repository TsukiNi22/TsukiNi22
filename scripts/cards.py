#!/usr/bin/env python3
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Edition:
##  10/11/2026 by Tsukini

File Name:
##  cards.py

File Description:
##  Render the banner and the project cards of the profile README (SVG, one dark theme)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

##### Import #####
# Import that can't be in the try
from sys import exit, stderr

# Import that can be checked
try:
    from pathlib import Path # Used for the paths of the config and of the assets
    from urllib.request import urlopen # Used to read the index of my-universe
    from xml.sax.saxutils import escape # Used to escape the texts of the SVG
    import subprocess # Used to check the output branch of the snake
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

##### README #####
ACTIVITY_START, ACTIVITY_END = "<!-- profile:activity:start -->", "<!-- profile:activity:end -->"

def activity(snake: str) -> str: # Activity section, the contribution snake of the output branch
    return f'## Activity\n\n<img src="{snake}/snake-dark.svg" width="100%" alt="Contribution snake">'

def snake_ready(branch: str) -> bool: # True once the workflow pushed the snake on its branch
    result = subprocess.run(["git", "ls-remote", "--exit-code", "--heads", "origin", branch], cwd=ROOT,
                            capture_output=True, check=False)
    return result.returncode == 0

def render_readme(path: Path, profile: dict) -> bool: # Fill the activity block of the README, True when changed
    text = path.read_text(encoding="utf-8")
    start, end = text.find(ACTIVITY_START), text.find(ACTIVITY_END)
    if start < 0 or end < start:
        stderr.write(f"missing markers {ACTIVITY_START} / {ACTIVITY_END} in {path}\n")
        return False
    block = activity(profile["snake"]) if snake_ready(profile["snake_branch"]) else ""
    new = f"{text[:start + len(ACTIVITY_START)]}\n{block}\n{text[end:]}" if block else \
          f"{text[:start + len(ACTIVITY_START)]}\n{text[end:]}"
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True

##### Main #####
def read_universe(url: str) -> dict[str, dict]: # Packages of my-universe by name
    with urlopen(url, timeout=20) as response:
        index = json.load(response)
    return {source["name"]: source for source in index["sources"]}

def main() -> int:
    parser = argparse.ArgumentParser(description="Render the banner and the cards of the profile README")
    parser.add_argument("--config", type=Path, default=ROOT / "cards.toml", help="cards configuration")
    parser.add_argument("--out", type=Path, default=ROOT / "assets", help="output folder of the SVG")
    parser.add_argument("--readme", type=Path, nargs="?", const=ROOT / "README.md",
                        help="also fill the activity section of the README (once the snake branch exists)")
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
    print(f"✓ {count} SVG rendered in {args.out}")
    if args.readme is not None:
        print(f"✓ {args.readme} {'updated' if render_readme(args.readme, config['profile']) else 'unchanged'}")
    return 0

exit(main())
