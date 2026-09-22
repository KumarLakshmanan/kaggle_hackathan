import ast
import csv
import importlib.util
import json
import os
import sys
from glob import glob
from math import comb, factorial

import numpy as np
import matplotlib.pyplot as plt


def engine():
    """Constants and configuration defaults, read without importing or running."""
    spec = importlib.util.find_spec("kaggle_environments")
    root = os.path.join(os.path.dirname(spec.origin), "envs", "kaggriculture")
    const = {}
    for node in ast.parse(open(os.path.join(root, "kaggriculture.py"),
                               encoding="utf-8").read()).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                const[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    spec_json = json.load(open(os.path.join(root, "kaggriculture.json"),
                               encoding="utf-8"))
    cfg = {k: v["default"] for k, v in spec_json.get("configuration", {}).items()
           if isinstance(v, dict) and "default" in v}
    return const, cfg


CONST, CFG = engine()
SHOPS = CONST["SHOPS"]
CAP = CONST.get("MAX_SHOP_INSTANCES", 8)
NAMES = sorted(SHOPS)
ALL_GOODS = CONST["PRODUCTS"]
TURNS = int(CFG["turnsPerDay"])
SELL = int(CFG["townShopSellInterval"])
UNLOCK = int(CFG["townShopUnlockInterval"])
CENTRE = int(CFG["townCenterSellInterval"])
EVENTS = TURNS // SELL
PRODUCES = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}

print("shop types           ", len(SHOPS))
print("instances in a town  ", CAP)
print("one opens every      ", UNLOCK, "days")
print("each shop buys every ", SELL, "turns, and a day is", TURNS, "turns")
print("so every open shop buys", EVENTS, "times a day")
print("the town centre buys once every", CENTRE, "turns")
print()
for name in NAMES:
    print("  {:<16} {}".format(name, ", ".join(SHOPS[name])))


def units_per_event(multiset):
    """What one town buys per shop-sell event. A shop with a single product on its
    list buys two of it, which is the whole reason carrot and wool behave oddly."""
    out = {}
    for name in multiset:
        goods = SHOPS[name]
        mult = 2 if len(goods) == 1 else 1
        for g in goods:
            out[g] = out.get(g, 0) + mult
    return out


def find(*names):
    """Locate a dataset directory by what is in it. Kaggle mounts attachments under
    /kaggle/input/datasets/<owner>/<slug>/ and the uploader's own folders are kept, so
    a one level lookup finds nothing."""
    hits = []
    for root, dirs, files in os.walk("/kaggle/input"):
        dirs.sort()
        if all(n in files for n in names):
            hits.append(root)
    if not hits:
        raise FileNotFoundError("attach kaggriculture-reference-agents. Looking for "
                                + ", ".join(names))
    return sorted(hits, key=lambda r: (r.count(os.sep), r))[0]


REF = find("crop_economics.csv")
ECON = list(csv.DictReader(open(os.path.join(REF, "crop_economics.csv"),
                                encoding="utf-8")))
print("crop table:", REF)
print("{:<12}{:>16}{:>18}".format("item", "units/tile/day", "days to 1st yield"))
for r in ECON:
    print("{:<12}{:>16}{:>18}".format(r["item"], r["units_per_tile_per_day"],
                                      r["days_to_first_yield"]))


"""Plot style for the Kaggriculture shop-draw notebook.

The palette is semantic, not decorative. Every tradable product gets one bright
colour and keeps it in every figure, and each animal inherits the colour of the
product it makes: a goose is drawn in the colour of an egg, a cow in the colour of
milk, a sheep in the colour of wool. That way a reader who learns the colours once
can read the rest of the notebook without a legend.

Colours are chosen bright on purpose. This is a farming market, the figures are about
prices collapsing and money piling up, and a muted palette would undersell what the
numbers actually say. They stay distinguishable: every pair is at least 25 units apart
in CIELAB, checked by `palette_check()` below rather than assumed.

Every figure is audited before it is shown. Six defect classes are caught and each is
reported as a number: text clipped by the canvas edge, two labels closer than a
readable gap, a label sitting on a plotted curve, and figure text over a plot area.
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

PX = 1400
DPI = 150
W = PX / DPI

# one colour per tradable product; animals inherit the colour of what they produce
PRODUCT = {
    "WHEAT": "#E3A008",       # gold
    "CARROT": "#F2711C",      # orange
    "TOMATO": "#DB2828",      # red
    "STRAWBERRY": "#E0218A",  # pink
    "MELON": "#21BA45",       # green
    "EGG": "#00B5AD",         # teal
    "MILK": "#2185D0",        # blue
    "WOOL": "#A333C8",        # violet
    "FERTILIZER": "#8D6E4A",  # brown
}
PRODUCES = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}

# The eight shop types. Products keep the colours they had in the market notebook this
# one follows, so a reader of both sees one wheat gold and one wool violet throughout.
# The shops need eight hues of their own, checked against each other rather than picked.
# Chosen by search, not by eye: a greedy max-min over 523 candidate hues, scored on the
# WORST of four views, ordinary vision plus the three dichromacies. The winning set
# separates by at least dE 25 in every one of them, and the cell above prints the exact
# closest pair per view so the claim is checkable rather than asserted.
#
# This palette is the SECOND one. The first was selected the same way but against a
# tritanopia model that was wrong, and it scored dE 29 under that model and dE 15 under
# the corrected one. The search had quietly piled its colours into blue and magenta,
# which is exactly the region a bad blue-yellow model fails to penalise. Fixing the model
# both changed the answer and widened it: the honest palette runs red through green to
# magenta, because the constraint it now respects is the real one.
SHOP = {
    "BAKERY":          "#F94E45",
    "BRUNCH_SPOT":     "#841A00",
    "FARMERS_MARKET":  "#BFB956",
    "ICE_CREAM_SHOP":  "#5E9E1F",
    "PET_CAFE":        "#45BAF9",
    "PIZZA_SHOP":      "#3A0ACC",
    "SMOOTHIE_SHOP":   "#6B1F9E",
    "YARN_STORE":      "#D545F9",
}

# two letters per shop, so colour is never the only channel
CODE = {"BAKERY": "Bk", "BRUNCH_SPOT": "Br", "FARMERS_MARKET": "Fm",
        "ICE_CREAM_SHOP": "Ic", "PET_CAFE": "Pc", "PIZZA_SHOP": "Pz",
        "SMOOTHIE_SHOP": "Sm", "YARN_STORE": "Ya"}


# The six agents whose whole season is recorded in the reference data, coloured by
# what each one actually farms: Walter grows wheat, Rosa rotates root crops, Hana runs
# a mixed homestead, Mateo grows melons, Rita keeps animals. Finn plants nothing at all
# and stays grey, because grey is the honest colour for an empty field.
AGENT = {
    "fallow_finn": "#5A5A5A",
    "wheat_walter": PRODUCT["WHEAT"],
    "rotation_rosa": PRODUCT["CARROT"],
    "homestead_hana": PRODUCT["TOMATO"],
    "melon_mateo": PRODUCT["MELON"],
    "rancher_rita": PRODUCT["WOOL"],
}

# what a tile can be on any given day
LAND = {
    "tiles_crop": ("planted", PRODUCT["MELON"]),
    "tiles_pasture": ("pasture", PRODUCT["WOOL"]),
    "tiles_coop": ("coop", PRODUCT["EGG"]),
    "tiles_weed": ("weeds", "#D81B60"),
    "tiles_empty": ("empty", "#E4E4E4"),
}


def colour(item):
    """Colour for a crop, an animal or a product. Animals follow their product."""
    return PRODUCT.get(PRODUCES.get(item, item), "#767676")


INK = "#151515"
MUTE = "#5A5A5A"          # contrast 6.9 on white, above the AA threshold
HAIR = "#9A9A9A"
RULE = "#E2E2E2"
WARN = "#D81B60"          # single accent for the one thing a figure is arguing
COOL = "#1565C0"          # second accent when two things are contrasted

plt.rcParams.update({
    "figure.dpi": DPI, "savefig.dpi": DPI,
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 11,
    "axes.titlesize": 12, "axes.labelsize": 11,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "axes.titleweight": "normal", "axes.titlelocation": "left", "axes.titlepad": 7,
    "axes.edgecolor": "#3A3A3A", "axes.linewidth": 0.9,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": "#3A3A3A", "ytick.color": "#3A3A3A",
    "text.color": INK, "axes.labelcolor": INK,
    "figure.facecolor": "white", "savefig.facecolor": "white",
    "legend.frameon": False,
})


def lab(hexs):
    """sRGB hex to CIELAB, so colour distance is a number rather than an opinion."""
    out = []
    for h in hexs:
        rgb = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255
        r = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722],
                      [0.0193, 0.1192, 0.9505]])
        x = r @ m.T / np.array([0.95047, 1.0, 1.08883])
        f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
        out.append([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])
    return np.array(out)


# Dichromat simulation, Vienot 1999 style: project linear RGB onto the plane a
# red-blind or green-blind eye can still separate. A CIELAB distance computed on
# ordinary vision says nothing about whether a red and a green are the same colour to
# the eight percent of men who cannot tell them apart, so a palette is only checked
# once it survives all three.
# Protanopia and deuteranopia use the Vienot, Brettel and Mollon 1999 simplification,
# which collapses the whole pipeline to one matrix and is accurate for those two.
DICHROMAT = {
    "deuteranopia": np.array([[0.625, 0.375, 0.0],
                              [0.700, 0.300, 0.0],
                              [0.0, 0.300, 0.700]]),
    "protanopia": np.array([[0.567, 0.433, 0.0],
                            [0.558, 0.442, 0.0],
                            [0.0, 0.242, 0.758]]),
}

# Tritanopia does NOT work that way, and an earlier version of this file got it wrong by
# using a single matrix for it as well. The 1999 simplification is only valid where one
# projection plane suffices; the tritan confusion lines need the two half planes of
# Brettel, Vienot and Mollon 1997, with the half chosen per colour. Reporting a tritan
# number computed the cheap way, at the same confidence as the other two, inside a tool
# whose entire purpose is accessibility, is the one mistake this file cannot afford.
# Coefficients below are the precomputed linear-RGB form published in libDaltonLens
# (public domain, github.com/DaltonLens/libDaltonLens).
BRETTEL_TRITAN = {
    "plane_1": np.array([[1.01277, 0.13548, -0.14826],
                         [-0.01243, 0.86812, 0.14431],
                         [0.07589, 0.80500, 0.11911]]),
    "plane_2": np.array([[0.93678, 0.18979, -0.12657],
                         [0.06154, 0.81526, 0.12320],
                         [-0.37562, 1.12767, 0.24796]]),
    "normal": np.array([0.03901, -0.02788, -0.01113]),
}
KINDS = list(DICHROMAT) + ["tritanopia"]


def _to_linear(h):
    rgb = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def _to_hex(lin):
    lin = np.clip(lin, 0, 1)
    srgb = np.where(lin <= 0.0031308, lin * 12.92,
                    1.055 * lin ** (1 / 2.4) - 0.055)
    return "#%02X%02X%02X" % tuple(int(round(c * 255)) for c in srgb)


def simulate(hexs, kind):
    """The same colours as a dichromat sees them, back in hex."""
    out = []
    for h in hexs:
        lin = _to_linear(h)
        if kind == "tritanopia":
            b = BRETTEL_TRITAN
            m = (b["plane_1"] if float(lin @ b["normal"]) >= 0 else b["plane_2"])
        else:
            m = DICHROMAT[kind]
        out.append(_to_hex(lin @ m.T))
    return out


def vision_check(mapping, threshold=25.0, label="palette"):
    """Closest pair under ordinary vision and under each kind of colour blindness."""
    names = list(mapping)
    worst = {}
    for kind in ["normal"] + KINDS:
        cols = ([mapping[n] for n in names] if kind == "normal"
                else simulate([mapping[n] for n in names], kind))
        worst[kind] = closest_pair(dict(zip(names, cols)))
    ok = all(w >= threshold for w, _ in worst.values())
    print(f"{label}: {len(names)} colours, threshold {threshold:.0f}")
    for kind, (w, pair) in worst.items():
        print(f"    {kind:<13} closest {pair[0]} and {pair[1]} at dE {w:5.1f}"
              f"  {'ok' if w >= threshold else 'TOO CLOSE'}")
    return ok


def closest_pair(mapping):
    """The two nearest colours in a palette and their CIELAB distance."""
    names = list(mapping)
    L = lab([mapping[n] for n in names])
    worst, pair = 1e9, None
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            d = float(np.linalg.norm(L[i] - L[j]))
            if d < worst:
                worst, pair = d, (names[i], names[j])
    return worst, pair


def palette_check(mapping=None, label="palette", threshold=25.0):
    """Report the closest pair instead of trusting the palette."""
    mapping = PRODUCT if mapping is None else mapping
    worst, pair = closest_pair(mapping)
    print(f"{label}: {len(mapping)} colours, closest pair {pair[0]} and {pair[1]} "
          f"at dE {worst:.1f}, threshold {threshold:.0f} -> "
          f"{'ok' if worst >= threshold else 'TOO CLOSE'}")
    return worst


def num(x, dp=0):
    """Thousands split by a space. Never format a whole sentence and strip its commas
    afterwards: that eats the commas of the prose along with the ones in the number.
    """
    return "{:,.{}f}".format(x, dp).replace(",", " ")


def figure(h, head=0.0, foot=0.0, **kw):
    """`head` and `foot` reserve a fraction of the canvas that no axes may enter, for
    the title block above and for a caption or legend below."""
    fig = plt.figure(figsize=(W, h), layout="constrained", **kw)
    if head or foot:
        fig.get_layout_engine().set(
            rect=(0.004, 0.006 + foot, 0.984, 1 - head - foot - 0.006))
    return fig


def title(fig, text, x=0.006):
    fig.suptitle(text, x=x, ha="left", fontsize=14.5, weight="regular", color=INK)


def _renderer(fig):
    """One renderer for the whole wrap. Asking the canvas to draw itself once per
    word turned a seventy word caption into seventy full figure renders, which is
    where nearly all of the time in this file was going."""
    try:
        return fig.canvas.get_renderer()
    except AttributeError:
        fig.canvas.draw()
        return fig.canvas.get_renderer()


def _measure(fig, s, fontsize, renderer):
    t = fig.text(0, -5, s, fontsize=fontsize)
    w = t.get_window_extent(renderer=renderer).width
    t.remove()
    return w


def wrap(fig, s, fontsize=10, frac=0.985):
    """Wrap by measured width, not by character count."""
    limit = fig.bbox.width * frac
    rend = _renderer(fig)
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and _measure(fig, trial, fontsize, rend) > limit:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def sub(fig, text, y, fontsize=10, x=0.006, color=None):
    return fig.text(x, y, wrap(fig, text, fontsize, 0.985 - x), ha="left", va="top",
                    fontsize=fontsize, color=color or MUTE, linespacing=1.5)


def yrule(ax, values, color=None):
    """Faint background guides. Tagged so the audit does not mistake a decorative
    rule for a data curve: a label may sit on a grid line, never on a series."""
    for v in values:
        ax.axhline(v, color=color or RULE, lw=0.8, zorder=0, gid="_rule")


# --------------------------------------------------------------------- audit
def _extent(t):
    """Text-only extent. Annotation.get_window_extent includes the arrow, which turns
    a long leader line into a false positive several times the text height."""
    from matplotlib.text import Text, Annotation
    return Text.get_window_extent(t) if isinstance(t, Annotation) else t.get_window_extent()


def _offscreen(fig):
    """Tick labels matplotlib creates but never draws."""
    skip = set()
    for ax in fig.get_axes():
        if not ax.axison:
            for axis in (ax.xaxis, ax.yaxis):
                for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                    skip.add(id(tick.label1))
                    skip.add(id(tick.label2))
            continue
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                if not (lo - 1e-9 <= tick.get_loc() <= hi + 1e-9):
                    skip.add(id(tick.label1))
                    skip.add(id(tick.label2))
    return skip


def _is_text(a):
    """Only real Text artists. A legend also contains TextArea containers that carry
    a string but none of the Text geometry, and touching them raises."""
    from matplotlib.text import Text
    return isinstance(a, Text)


def audit(fig, gap=6.0, pad=2.0):
    """Return a list of defects. Empty means the figure is safe to show."""
    fig.canvas.draw()
    skip = _offscreen(fig)
    w_px, h_px = fig.bbox.width, fig.bbox.height
    texts = {}
    for t in fig.findobj(match=_is_text):
        # a hidden axes keeps its labels, and matplotlib parks them wherever the last
        # layout pass left them, which is often off the canvas. They are not drawn, so
        # they are not defects.
        if getattr(t, "axes", None) is not None and not t.axes.get_visible():
            continue
        if t.get_text().strip() and t.get_visible() and id(t) not in skip:
            texts[id(t)] = t
    ts = list(texts.values())
    bad = []

    # measured once each. The pairwise pass below is quadratic in the number of
    # labels and a text extent costs a font metric lookup, so measuring inside the
    # loop made a nine panel figure take twice as long as drawing it.
    box = {id(t): _extent(t) for t in ts}
    ext = lambda t: box.get(id(t)) or _extent(t)

    for t in ts:
        b = ext(t)
        over = max(-b.x0, b.x1 - w_px, -b.y0, b.y1 - h_px)
        if over > 1.0:
            bad.append(f"clipped by {round(over)} px: {' '.join(t.get_text().split())[:44]}")

    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            a, b = box[id(ts[i])], box[id(ts[j])]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if oy <= 0 or ox <= -gap:
                continue
            same = ts[i].get_text() == ts[j].get_text()
            if same and ox + gap / 2 >= 0.9 * min(a.width, b.width):
                continue
            bad.append(f"clearance {round(min(ox, oy))} px: "
                       f"'{' '.join(ts[i].get_text().split())[:22]}' vs "
                       f"'{' '.join(ts[j].get_text().split())[:22]}'")

    for ax in fig.get_axes():
        pts = []
        for ln in ax.get_lines():
            if not ln.get_visible() or ln.get_gid() == "_rule":
                continue
            d = ln.get_transform().transform(ln.get_xydata())
            if len(d) < 2:
                continue
            # densify along every segment, not just at the vertices. A five-point
            # polyline leaves long straight runs between its vertices, and a label
            # parked in one of those gaps was passing the check while sitting
            # squarely on the line.
            seg = []
            for k in range(len(d) - 1):
                t_ = np.linspace(0, 1, 40)[:, None]
                seg.append(d[k] + t_ * (d[k + 1] - d[k]))
            pts.append(np.vstack(seg))
        if not pts:
            continue
        p = np.vstack(pts)
        for t in ax.findobj(match=_is_text):
            if not t.get_text().strip() or not t.get_visible() or id(t) in skip:
                continue
            if t.get_bbox_patch() is not None:
                continue
            b = ext(t)
            if not (ax.bbox.x0 <= (b.x0 + b.x1) / 2 <= ax.bbox.x1
                    and ax.bbox.y0 <= (b.y0 + b.y1) / 2 <= ax.bbox.y1):
                continue
            hit = ((p[:, 0] > b.x0 - pad) & (p[:, 0] < b.x1 + pad)
                   & (p[:, 1] > b.y0 - pad) & (p[:, 1] < b.y1 + pad)).sum()
            if hit:
                bad.append(f"over a curve, {int(hit)} points: "
                           f"{' '.join(t.get_text().split())[:40]}")

    # Filled regions, not just lines. A stackplot or a fill_between draws a
    # PolyCollection, which never appears in ax.get_lines(), so a label parked in the
    # middle of a coloured band passed the curve check above without a word.
    from matplotlib.collections import PolyCollection
    for ax in fig.get_axes():
        polys = [c for c in ax.collections
                 if isinstance(c, PolyCollection) and c.get_visible()]
        if not polys:
            continue
        for t in ax.findobj(match=_is_text):
            if not t.get_text().strip() or not t.get_visible() or id(t) in skip:
                continue
            if t.get_bbox_patch() is not None:
                continue
            b_ = ext(t)
            probe = np.array([[b_.x0, b_.y0], [b_.x1, b_.y0], [b_.x0, b_.y1],
                              [b_.x1, b_.y1], [(b_.x0 + b_.x1) / 2,
                                               (b_.y0 + b_.y1) / 2]])
            for c in polys:
                tr = c.get_transform()
                if any(path.transformed(tr).contains_points(probe).any()
                       for path in c.get_paths()):
                    bad.append("over a filled band: "
                               f"{' '.join(t.get_text().split())[:40]}")
                    break

    # Colour that is never named. A palette can be checked to any distance and still
    # fail the reader who cannot see the difference, so the rule this file enforces is
    # not "the colours are far apart" but "colour is never the only channel": every
    # series colour on an axes must also appear as the colour of some text, or in a
    # legend, somewhere in the figure. If it does not, the figure is asking the reader
    # to tell hues apart with nothing to fall back on.
    from matplotlib.colors import to_rgb
    named = set()
    for t in ts:
        named.add(tuple(round(c, 3) for c in to_rgb(t.get_color())))
    for leg in fig.legends + [ax.get_legend() for ax in fig.get_axes()]:
        if leg is None:
            continue
        for h in leg.legend_handles:
            for getter in ("get_color", "get_facecolor", "get_edgecolor"):
                try:
                    c = getattr(h, getter)()
                except Exception:
                    continue
                c = np.atleast_2d(np.asarray(c, dtype=object))
                for row in c:
                    try:
                        named.add(tuple(round(v, 3) for v in to_rgb(
                            row if len(row) > 1 else row[0])))
                    except Exception:
                        pass
    for ax in fig.get_axes():
        for ln in ax.get_lines():
            if not ln.get_visible() or ln.get_gid() == "_rule" or len(ln.get_xydata()) < 2:
                continue
            c = tuple(round(v, 3) for v in to_rgb(ln.get_color()))
            if c not in named and c not in {(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)}:
                bad.append("colour with no label: a series drawn in "
                           f"{ln.get_color()} is named nowhere in the figure")

    axboxes = [ax.bbox for ax in fig.get_axes() if ax.get_visible()]
    for t in ts:
        if t.get_figure() is not fig or t.axes is not None:
            continue
        bt = ext(t)
        for bb in axboxes:
            ox = min(bt.x1, bb.x1) - max(bt.x0, bb.x0)
            oy = min(bt.y1, bb.y1) - max(bt.y0, bb.y0)
            if ox > 2 and oy > 2:
                bad.append(f"over a plot area, {round(ox)}x{round(oy)} px: "
                           f"{' '.join(t.get_text().split())[:40]}")
                break
    return sorted(set(bad))


def show(fig, name=""):
    bad = audit(fig)
    if bad:
        print(f"[{name}] DEFECTS: {len(bad)}")
        for b in bad:
            print("   ", b)
    else:
        print(f"[{name}] audit clean: no clipping, no crowding, "
              f"no label on a curve, no text over a plot area")
    plt.show()


K = sys.modules[__name__]
S = sys.modules[__name__]


def show(fig, name=""):
    bad = audit(fig)
    print("[{}] {}".format(name, "audit clean" if not bad
                           else "DEFECTS {}".format(len(bad))))
    for b in bad:
        print("   ", b)
    # The PNG is written here rather than by plt.show() for one reason: matplotlib
    # stamps a "Software: Matplotlib version ..." text chunk into every image it
    # writes. A figure carries its meaning in its pixels, not in a tool signature
    # baked into its bytes, so that chunk is suppressed and the file goes out clean.
    import io as _io
    from IPython.display import Image as _Image, display as _display
    buf = _io.BytesIO()
    fig.savefig(buf, format="png", metadata={"Software": None})
    plt.close(fig)
    _display(_Image(data=buf.getvalue()))


vision_check(PRODUCT, 25.0, "products, the palette from the previous notebook")
print()
vision_check(SHOP, 25.0, "shops, chosen by search over all four views")


def fig_palette():
    """What the palette of the previous notebook looks like to a reader who is
    colour blind, and why the rule here is not about distance."""
    goods = list(S.PRODUCT)
    views = ["normal"] + list(S.DICHROMAT)
    fig = S.figure(5.4, head=0.245)
    ax = fig.subplots()
    worst = {}
    for v in views:
        cols = ([S.PRODUCT[g] for g in goods] if v == "normal"
                else S.simulate([S.PRODUCT[g] for g in goods], v))
        worst[v] = S.closest_pair(dict(zip(goods, cols)))
    bad = min(worst.items(), key=lambda t: t[1][0])
    S.title(fig, "The palette check I used before was not enough")
    S.sub(fig, "The product colours in this notebook and the one before it, redrawn as "
               "each kind of colour blindness sees them. Checked on ordinary vision the "
               "closest pair sits {:.0f} units apart in CIELAB, comfortably clear. Under "
               "{} the closest pair, {} and {}, is {:.1f} units apart, which is the same "
               "colour. That is why the audit in this notebook does not test distance at "
               "all. It tests that no series is identified by colour alone.".format(
                   worst["normal"][0], bad[0], bad[1][1][0], bad[1][1][1],
                   bad[1][0]), 0.947)

    for r, v in enumerate(views):
        cols = ([S.PRODUCT[g] for g in goods] if v == "normal"
                else S.simulate([S.PRODUCT[g] for g in goods], v))
        for c, (g, col) in enumerate(zip(goods, cols)):
            ax.add_patch(plt.Rectangle((c - 0.46, r - 0.42), 0.92, 0.84, color=col,
                                       zorder=2))
        d, pair = worst[v]
        ax.text(len(goods) + 0.15, r, f"closest {pair[0]} and {pair[1]}, dE {d:.1f}",
                va="center", fontsize=10.2,
                color=S.WARN if d < 25 else S.INK)
    ax.set_xticks(range(len(goods)))
    # upright labels cannot collide horizontally, and the right hand annotations take
    # most of this panel's width, leaving nine names too little room to sit flat
    ax.set_xticklabels(goods, rotation=90, fontsize=9.4)
    ax.set_yticks(range(len(views)))
    ax.set_yticklabels(views, fontsize=10.5)
    ax.set_xlim(-0.6, len(goods) + 5.6)
    ax.set_ylim(len(views) - 0.4, -0.6)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    show(fig, "palette")


fig_palette()


def fig_shops():
    """The eight shop types and what each one buys."""
    single = [n for n in NAMES if len(SHOPS[n]) == 1]
    M = np.zeros((len(NAMES), len(ALL_GOODS)))
    for i, n in enumerate(NAMES):
        mult = 2 if len(SHOPS[n]) == 1 else 1
        for g in SHOPS[n]:
            M[i, ALL_GOODS.index(g)] = mult

    fig = S.figure(5.9, head=0.22)
    ax = fig.subplots()
    S.title(fig, "Two of the eight shops buy double, and nobody buys melon")
    S.sub(fig, "Every shop type in the game and the products it takes off the market, "
               "read out of the engine. A shop whose list holds exactly one product "
               "buys two units of it per sell event instead of one, which applies to "
               "{} and {} and to nothing else. Melon and fertilizer appear on no list "
               "at all: the only standing buyer of a melon is the town centre, one a "
               "day.".format(*[s.replace("_", " ").lower() for s in single]), 0.947)

    for i in range(len(NAMES)):
        for j, g in enumerate(ALL_GOODS):
            v = M[i, j]
            if not v:
                continue
            ax.add_patch(plt.Rectangle((j - 0.42, i - 0.42), 0.84, 0.84,
                                       color=S.colour(g),
                                       alpha=1.0 if v == 2 else 0.42, zorder=2))
            ax.text(j, i, "2" if v == 2 else "1", ha="center", va="center",
                    fontsize=10.5, color="#FFFFFF" if v == 2 else S.INK, zorder=3)
    ax.set_xticks(range(len(ALL_GOODS)))
    ax.set_xticklabels(ALL_GOODS, fontsize=9.3)
    ax.set_yticks(range(len(NAMES)))
    ax.set_yticklabels([n.replace("_", " ").lower() for n in NAMES], fontsize=10.5)
    ax.set_xlim(-0.6, len(ALL_GOODS) - 0.4)
    ax.set_ylim(len(NAMES) - 0.4, -0.6)
    ax.set_title("solid means the shop buys two, faded means one", loc="right",
                 color=S.MUTE, fontsize=10.5)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    show(fig, "shops")


fig_shops()


def fig_demand():
    """How much the town takes per day, and where it comes from."""
    per_day = {g: units_per_event(NAMES).get(g, 0) * EVENTS for g in ALL_GOODS}
    order = [g for g in sorted(ALL_GOODS, key=lambda g: -per_day[g])]
    fig = S.figure(6.0, head=0.225)
    ax = fig.subplots()
    S.title(fig, "Carrot demand is half again what the shop count suggests")
    S.sub(fig, "Units the town buys per day when one of every shop type is open, "
               "which is what {} draws over {} types averages out to. Each bar is "
               "split by the shop the demand comes from. Counting shops alone puts "
               "carrot level with tomato at {} a day. It is actually {}, because the "
               "pet cafe sells nothing but carrots and a single product shop buys "
               "two.".format(CAP, len(NAMES), per_day["TOMATO"], per_day["CARROT"]),
           0.947)

    for i, g in enumerate(order):
        left = 0.0
        for n in NAMES:
            if g not in SHOPS[n]:
                continue
            mult = 2 if len(SHOPS[n]) == 1 else 1
            w = mult * EVENTS
            ax.barh(i, w, left=left, height=0.62, color=S.SHOP[n],
                    edgecolor="white", linewidth=1.2, zorder=3)
            if w >= 6:
                ax.text(left + w / 2, i, S.CODE[n], ha="center", va="center",
                        fontsize=9.4, color="#FFFFFF", zorder=4)
            left += w
        ax.text(left + 0.5, i, f"{left:.0f} a day", va="center", fontsize=10.5,
                color=S.colour(g))
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlim(0, max(per_day.values()) * 1.26)
    ax.set_xlabel(f"units bought per day, over {EVENTS} sell events")
    S.yrule(ax, [])
    fig.legend([plt.Rectangle((0, 0), 1, 1, color=S.SHOP[n]) for n in NAMES],
               [f"{S.CODE[n]}  {n.replace('_', ' ').lower()}" for n in NAMES],
               loc="outside lower center", ncols=4, fontsize=10, frameon=False,
               handlelength=1.3, columnspacing=1.6)
    show(fig, "demand")


fig_demand()


def all_towns(instances=None):
    """Every town the draw can produce, with its exact probability. 6435 of them."""
    n = len(NAMES)
    k = CAP if instances is None else instances
    total = float(n) ** k
    counts = [0] * n

    def walk(i, left):
        if i == n - 1:
            counts[i] = left
            ways = factorial(k)
            for c in counts:
                ways //= factorial(c)
            yield list(counts), ways / total
            return
        for j in range(left + 1):
            counts[i] = j
            yield from walk(i + 1, left - j)

    return list(walk(0, k))


def demand_dist(seen=()):
    """Exact distribution of units bought per event, given the shops already open."""
    fixed = units_per_event(seen)
    dist = {g: {} for g in ALL_GOODS}
    for counts, prob in all_towns(CAP - len(seen)):
        rest = []
        for name, k in zip(NAMES, counts):
            rest += [name] * k
        units = units_per_event(rest)
        for g in ALL_GOODS:
            v = fixed.get(g, 0) + units.get(g, 0)
            dist[g][v] = dist[g].get(v, 0.0) + prob
    return dist


def stats(dist):
    return {g: {"mean": sum(v * p for v, p in d.items()),
                "p_zero": d.get(0, 0.0)} for g, d in dist.items()}


DIST = demand_dist()
STAT = stats(DIST)
print("possible towns:", comb(len(NAMES) + CAP - 1, CAP))
print("{:<12}{:>18}{:>26}".format("good", "mean units/event",
                                  "towns with no shop buyer"))
for g, s in sorted(STAT.items(), key=lambda t: -t[1]["mean"]):
    if s["mean"] == 0 and g not in ("MELON",):
        continue
    print("{:<12}{:>18.2f}{:>25.1f}%".format(g, s["mean"], s["p_zero"] * 100))
print()
print("melon is the structural zero: no shop list contains it, so its only standing")
print("buyer is the town centre, which takes one unit a day.")


def fig_spread():
    """The distribution nobody publishes, computed rather than sampled."""
    shown = [g for g in ALL_GOODS if STAT[g]["mean"] > 0]
    worst = max(shown, key=lambda g: STAT[g]["p_zero"])
    fig = S.figure(6.4, head=0.215)
    axes = fig.subplots(2, 4, sharex=False)
    S.title(fig, "One town in three never opens a shop that buys wool")
    S.sub(fig, "The town draws {} shops one at a time, uniformly and with replacement, "
               "so the demand you actually get is a distribution and not the average "
               "everyone quotes. These are exact: all {} possible towns enumerated, "
               "not sampled. The pink column is a town where no shop buys the good at "
               "all.".format(CAP, comb(len(NAMES) + CAP - 1, CAP)), 0.947)

    for ax in axes.ravel()[len(shown):]:
        ax.set_visible(False)
    for ax, g in zip(axes.ravel(), shown):
        d = DIST[g]
        # trim the tail rather than draw an axis out to a value that never happens:
        # carrot can in principle reach 16, and does so in 6 towns out of 16.7 million
        xs = [x for x in sorted(d) if d[x] >= 5e-5]
        ax.bar(xs, [d[x] * 100 for x in xs], width=0.82, zorder=3,
               color=[S.WARN if x == 0 else S.colour(g) for x in xs])
        ax.set_title(g, loc="left", color=S.colour(g), fontsize=11.5)
        # inside the panel, not on the title row: the longest good name and the
        # longest share meet in the middle of a narrow panel otherwise
        pz = STAT[g]["p_zero"] * 100
        ax.text(0.97, 0.95, "dead in {}".format(
                    "under 0.1%" if 0 < pz < 0.1 else f"{pz:.1f}%"),
                transform=ax.transAxes, ha="right", va="top", fontsize=10,
                color=S.WARN if STAT[g]["p_zero"] > 0.05 else S.MUTE)
        ax.set_xlim(-0.7, max(xs) + 0.7)
        ax.set_ylim(0, 52)
        ax.set_xticks(range(0, max(xs) + 1, 2 if max(xs) <= 9 else 4))
    # the label goes on the lowest panel that is actually drawn in each column, since
    # the grid holds one more cell than there are goods to put in it
    for col in range(axes.shape[1]):
        live = [ax for ax in axes[:, col] if ax.get_visible()]
        if live:
            live[-1].set_xlabel("units per sell event")
    for ax in axes[:, 0]:
        ax.set_ylabel("share of towns, percent")
    assert worst == "WOOL", "wool is no longer the good most often left with no buyer"
    show(fig, "spread")


fig_spread()


def fig_risk():
    """Average demand and the odds of no demand are different questions."""
    shown = [g for g in ALL_GOODS if STAT[g]["mean"] > 0]
    fig = S.figure(6.0, head=0.215)
    ax = fig.subplots()
    pair = ["CARROT", "MILK"]
    S.title(fig, "Two goods with the same average demand, four times the risk")
    S.sub(fig, "Every good the shops buy, placed by how much a town takes on average "
               "against how often a town takes none at all. Carrot and milk sit on the "
               "same average of {:.0f} units an event and differ by a factor of {:.0f} "
               "in the odds of a dead market, because carrot's demand is concentrated "
               "in one doubling shop while milk's is spread across three. An average "
               "hides exactly the thing that ruins a season.".format(
                   STAT["CARROT"]["mean"],
                   STAT["CARROT"]["p_zero"] / STAT["MILK"]["p_zero"]), 0.947)

    # goods that land on exactly the same point get one marker and one label. Egg and
    # tomato are identical in both measures, and two labels stacked on one dot is a
    # drawing that invents a difference the numbers do not have.
    at = {}
    for g in shown:
        at.setdefault((round(STAT[g]["mean"], 6), round(STAT[g]["p_zero"], 6)),
                      []).append(g)
    for (mean, pz), gs in at.items():
        y = pz * 100
        for k, g in enumerate(gs):
            ax.scatter([mean], [y], s=190 - 60 * k, color=S.colour(g),
                       zorder=3 + k, lw=0)
        # the lower end of the connected pair labels downward, or the dashed link
        # between the two runs straight through its own label. A rule is exempt from
        # the label-on-a-curve check by design, so nothing else would have caught it.
        low = gs[0] in pair and y == min(STAT[q]["p_zero"] * 100 for q in pair)
        ax.annotate(" and ".join(gs), (mean, y), xytext=(0, -18 if low else 16),
                    textcoords="offset points", ha="center",
                    va="top" if low else "baseline", fontsize=11,
                    color=S.colour(gs[0]) if len(gs) == 1 else S.INK)
    ax.plot([STAT[p]["mean"] for p in pair], [STAT[p]["p_zero"] * 100 for p in pair],
            color=S.MUTE, lw=1.2, ls=(0, (4, 3)), zorder=2, gid="_rule")
    ax.set_xlabel("average units the town buys per sell event")
    ax.set_ylabel("share of towns where nothing buys it, percent")
    ax.set_xlim(1.3, 5.6)
    ax.set_ylim(-7.5, 42)
    S.yrule(ax, [0, 10, 20, 30, 40])
    show(fig, "risk")


fig_risk()


import kaggle_environments as ke

PAIRS = [("pass", "pass"), ("starter", "pass"), ("starter", "starter"),
         ("random", "pass"), ("random", "random"), ("starter", "random")]
SEEDS = list(range(90000, 90000 + 12))


def unlock_days(env):
    seen, out = 0, []
    for step_i, step in enumerate(env.steps):
        shops = ((step[0]["observation"].get("town") or {}).get("unlocked_shops")
                 or [])
        while len(shops) > seen:
            out.append((shops[seen], step_i // TURNS))
            seen += 1
    return out


DRAWS = []
for seed in SEEDS:
    for pair in PAIRS:
        env = ke.make("kaggriculture", configuration={"seed": seed}, debug=False)
        env.run(list(pair))
        for slot, (shop, day) in enumerate(unlock_days(env)):
            DRAWS.append({"seed": seed, "agents": "+".join(pair), "slot": slot,
                          "shop": shop, "day": day})
    print("seed {} done, {} draws so far".format(seed, len(DRAWS)), flush=True)

print()
print("games played:", len(DRAWS) // CAP, " shop draws recorded:", len(DRAWS))
print("days a shop opened on:",
      sorted({d["day"] for d in DRAWS}))


def fig_coupling():
    """The draw is not independent of the players."""
    pairs = sorted({r["agents"] for r in DRAWS})
    seeds = sorted({int(r["seed"]) for r in DRAWS})[:3]
    grid = {}
    for r in DRAWS:
        grid.setdefault((int(r["seed"]), r["agents"]), {})[int(r["slot"])] = r["shop"]
    same = sum(len({tuple(grid.get((s, p), {}).get(i) for i in range(CAP))
                    for p in pairs if (s, p) in grid}) == 1 for s in seeds)

    fig = S.figure(6.9, head=0.215, foot=0.05)
    ax = fig.subplots()
    S.title(fig, "The same seed deals different shops to different players")
    S.sub(fig, "Each row is one game. Within a block the seed is identical and only "
               "the agents change, so a town that was handed out independently would "
               "repeat down the block. In all {} of the {} seeds drawn here it does "
               "not. "
               "The reason is in the engine: the day's random numbers are spent on "
               "weeds before the shop is chosen, weeds are rolled only for tiles that "
               "are empty, and how many tiles are empty is what the players "
               "decided.".format(len(seeds) - same, len(seeds)), 0.947)

    y = 0
    ticks, labels = [], []
    for s in seeds:
        for p in pairs:
            row = grid.get((s, p))
            if not row:
                continue
            for i in range(CAP):
                shop = row.get(i)
                if shop is None:
                    continue
                ax.add_patch(plt.Rectangle((i - 0.46, y - 0.4), 0.92, 0.8,
                                           color=S.SHOP[shop], zorder=2))
                ax.text(i, y, S.CODE[shop], ha="center", va="center", fontsize=9,
                        color="#FFFFFF", zorder=3)
            ticks.append(y)
            labels.append(f"seed {s}   {p}")
            y += 1
        y += 0.6
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels, fontsize=9.4)
    ax.set_xticks(range(CAP))
    ax.set_xticklabels([f"{(i+1)*UNLOCK}" for i in range(CAP)])
    ax.set_xlabel("day the shop opened")
    ax.set_xlim(-0.7, CAP - 0.3)
    ax.set_ylim(y - 0.4, -0.9)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    fig.legend([plt.Rectangle((0, 0), 1, 1, color=S.SHOP[n]) for n in NAMES],
               [f"{S.CODE[n]}  {n.replace('_', ' ').lower()}" for n in NAMES],
               loc="outside lower center", ncols=4, fontsize=10, frameon=False,
               handlelength=1.3, columnspacing=1.6)
    show(fig, "coupling")


fig_coupling()


def fig_uniform():
    """The draw is coupled to the players, but is it still uniform?"""
    import collections
    obs = collections.Counter(r["shop"] for r in DRAWS)
    n = sum(obs.values())
    exp = n / len(NAMES)
    chi = sum((obs[k] - exp) ** 2 / exp for k in NAMES)
    dof = len(NAMES) - 1
    # upper tail of chi square with dof degrees of freedom, by series, no scipy
    from math import exp as e_, gamma
    def upper(x, k):
        s, term = 0.0, 1.0
        a = k / 2
        for i in range(400):
            s += term
            term *= (x / 2) / (a + i + 1)
        return 1 - (x / 2) ** a * e_(-x / 2) * s / gamma(a + 1)
    p = max(0.0, min(1.0, upper(chi, dof)))

    fig = S.figure(5.8, head=0.215)
    ax = fig.subplots()
    S.title(fig, "Coupled to the players, and still an even draw")
    S.sub(fig, "Every shop unlocked across {} games, {} draws in all, against the {:.0f} "
               "each type would get if the town chose uniformly. Chi square {:.1f} on "
               "{} degrees of freedom, p = {:.2f}. Whatever the players do to the "
               "random stream, they do not bend which shop comes out of "
               "it.".format(n // CAP, n, exp, chi, dof, p), 0.947)

    x = np.arange(len(NAMES))
    ax.bar(x, [obs[k] for k in NAMES], width=0.66, zorder=3,
           color=[S.SHOP[k] for k in NAMES])
    ax.plot([-0.6, len(NAMES) - 0.4], [exp, exp], color=S.INK, lw=1.4, ls=(0, (5, 3)),
            zorder=4, gid="_rule")
    ax.text(len(NAMES) - 0.45, exp, f"  even draw, {exp:.0f}", va="center",
            fontsize=10.4, color=S.INK)
    # inside the bar, not above it: above, a bar that lands just under the even-draw
    # line has its own count struck through by that line, and a rule is exempt from
    # the label-on-a-curve check by design
    for i, k in enumerate(NAMES):
        ax.text(i, obs[k] - n * 0.012, str(obs[k]), ha="center", va="top",
                fontsize=10.4, color="#FFFFFF")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [S.CODE[k] + "\n" + k.lower().replace("_", "\n") for k in NAMES],
        fontsize=9.2)
    ax.set_ylabel("times unlocked")
    ax.set_xlim(-0.7, len(NAMES) + 0.9)
    S.yrule(ax, [])
    show(fig, "uniform")


fig_uniform()


def fig_clock():
    """What waiting for the town to show its hand actually costs."""
    season = len({d for d in range(30)})
    days = [d for d in range(1, season + 1) if d % UNLOCK == 0][:CAP]

    def yield_if_committed(row, d):
        """Units one tile still produces if it is planted or stocked on day d."""
        first, cyc = int(row["days_to_first_yield"]), int(row["cycle_days"])
        per = int(row["units_per_cycle"])
        return per * len(range(d + first, season, cyc))

    goods = sorted(ECON, key=lambda r: -yield_if_committed(r, 0))
    known = lambda d: min(sum(1 for u in days if u <= d), CAP)
    half = next(d for d in range(season) if known(d) >= CAP / 2)
    sheep = next(r for r in ECON if r["item"] == "SHEEP")
    kept = yield_if_committed(sheep, half) / yield_if_committed(sheep, 0)

    fig = S.figure(6.5, head=0.228, foot=0.05)
    ax = fig.subplots()
    S.title(fig, "Waiting until half the shops are known costs a sheep half its wool")
    S.sub(fig, "Every crop and animal, and the share of its full season output a tile "
               "still returns if you commit to it on that day rather than on day zero. "
               "The blue marks are the days the town opens a shop. Half the town is "
               "known on day {}, and a sheep bought on day {} yields {:.0f} percent of "
               "what the same sheep bought on day zero would have. Information in this "
               "game is not free: it is paid for in "
               "harvests.".format(half, half, kept * 100), 0.947)

    for r in goods:
        item = r["item"]
        base = yield_if_committed(r, 0)
        xs = list(range(season))
        ys = [100 * yield_if_committed(r, d) / base for d in xs]
        ax.plot(xs, ys, color=S.colour(item), lw=2.6, zorder=3, drawstyle="steps-post",
                solid_capstyle="round")
        # end labels are impossible here: every curve runs to zero at the right edge,
        # so eight of them arrive at the same place. The legend below carries the names
        # instead, which also satisfies the rule that no colour goes unnamed.

    for k, d in enumerate(days):
        ax.plot([d, d], [-4, 104], color=S.COOL, lw=1.0, alpha=0.45, zorder=1,
                gid="_rule")
    ax.scatter(days, [-4] * len(days), marker="v", s=54, color=S.COOL, zorder=4)
    ax.text(days[-1] + 0.8, -4, " a shop opens", ha="left", va="center", fontsize=10,
            color=S.COOL)
    ax.axvspan(half - 0.5, half + 0.5, color=S.WARN, alpha=0.14, zorder=1)
    ax.annotate("half the shops known,\nday {}".format(half), xy=(half, 74),
                xytext=(half + 4.5, 88), fontsize=10.6, color=S.WARN, ha="left",
                va="center", arrowprops=dict(arrowstyle="-|>", color=S.WARN, lw=1.3,
                                             connectionstyle="arc3,rad=-0.25"))
    ax.set_xlabel("day you commit the tile")
    ax.set_ylabel("share of the day zero output still available, percent")
    ax.set_xlim(-0.6, season + 6.4)
    ax.set_ylim(-9, 108)
    S.yrule(ax, [25, 50, 75, 100])
    fig.legend([plt.Line2D([], [], color=S.colour(r["item"]), lw=3.0) for r in goods],
               [r["item"] for r in goods], loc="outside lower center", ncols=8,
               fontsize=10, frameon=False, handlelength=1.4, columnspacing=1.4)
    show(fig, "clock")


fig_clock()


def fig_posterior():
    """The only question a player actually has, and when it gets answered."""
    good = "WOOL"
    ks = list(range(CAP + 1))
    dead = []
    for k in ks:
        p = 0.0
        for counts, prob in all_towns(CAP - k):
            rest = []
            for name, c in zip(NAMES, counts):
                rest += [name] * c
            if units_per_event(rest).get(good, 0) == 0:
                p += prob
        dead.append(p * 100)
    cross = next(k for k in ks if dead[k] >= 50)

    fig = S.figure(6.0, head=0.235)
    ax = fig.subplots()
    S.title(fig, "After the third shop the yarn store is more likely missing "
                 "than coming")
    S.sub(fig, "You are keeping sheep, and wool is the only thing a sheep makes. The "
               "curve is the chance that no shop ever buys wool this season, given "
               "that a number of shops have already opened and none of them was the "
               "yarn store. It does not start low and it never falls: every shop that "
               "opens as something else is evidence against you. Before the season "
               "starts it is {:.0f} percent. After the {} that miss, on day {}, it is "
               "past even odds, and by the last shop it is certain.".format(
                   dead[0], "third" if cross == 3 else f"{cross}th", cross * UNLOCK),
           0.947)

    ax.plot(ks, dead, color=S.PRODUCT["WOOL"], lw=3.0, zorder=3,
            solid_capstyle="round", marker="o", ms=7)
    # labels sit under the curve, which is the side no part of a rising line occupies
    for k in ks:
        ax.text(k, dead[k] - 5.5, f"{dead[k]:.0f}", ha="center", va="top",
                fontsize=9.8, color=S.PRODUCT["WOOL"])
    ax.plot([-0.4, CAP + 0.4], [50, 50], color=S.MUTE, lw=1.0, ls=(0, (4, 3)),
            zorder=1, gid="_rule")
    ax.axvspan(cross - 0.5, CAP + 0.4, color=S.WARN, alpha=0.06, zorder=0)
    ax.text(0.2, 52, "even odds", va="bottom", fontsize=10, color=S.MUTE)
    ax.text(CAP + 0.3, 12, "past this point the yarn store\nis more likely absent "
            "than present", ha="right", va="bottom", fontsize=10.4, color=S.WARN)
    ax.set_xlabel("shops opened so far, none of them a yarn store")
    ax.set_ylabel("chance wool is never bought, percent")
    ax.set_xticks(ks)
    ax.set_xlim(-0.5, CAP + 0.5)
    ax.set_ylim(-2, 118)
    sec = ax.secondary_xaxis("top")
    sec.set_xticks(ks)
    sec.set_xticklabels([("start" if k == 0 else f"day {k*UNLOCK}") for k in ks],
                        fontsize=9.4)
    S.yrule(ax, [25, 50, 75, 100])
    show(fig, "posterior")


fig_posterior()


def tiles_supported(seen=(), quantile=None):
    """How many tiles of each good the town can absorb before it stops buying.

    A tile of a good produces `units_per_tile_per_day`. The town buys some number of
    units a day. Divide one by the other and you have the only number a planting
    decision actually needs: how much of this good the town has room for.
    """
    out = {}
    for r in ECON:
        good = PRODUCES.get(r["item"], r["item"])
        d = demand_dist(seen)[good]
        rate = float(r["units_per_tile_per_day"])
        if quantile is None:
            units = sum(v * p for v, p in d.items()) * EVENTS
        else:
            acc, units = 0.0, 0
            for v in sorted(d):
                acc += d[v]
                if acc >= quantile:
                    units = v * EVENTS
                    break
        out[r["item"]] = units / rate
    return out


def fig_tiles():
    """The number a planting decision actually needs."""
    mean = tiles_supported()
    worst = tiles_supported(quantile=0.10)
    order = sorted(ECON, key=lambda r: -mean[r["item"]])
    fig = S.figure(6.2, head=0.235)
    ax = fig.subplots()
    S.title(fig, "How many tiles of each good the town has room for")
    S.sub(fig, "A tile produces a known number of units a day and the town buys a known "
               "number a day, so the ratio is how much of that good a town can absorb "
               "before the price stops recovering. The solid bar is the average town. "
               "The notch is the unlucky one in ten. Wheat is the only good whose worst "
               "case still supports a real farm; sheep go from {:.0f} tiles to {:.0f}, "
               "and the whole difference is whether one shop out of eight happened to "
               "be a yarn store. Strawberry runs off the end of the board: an average "
               "town will take more of it than every tile in the game could grow. Melon "
               "shows zero because no shop buys melon at any price, and its one standing "
               "buyer, the town centre, takes a single unit a "
               "day.".format(mean["SHEEP"], worst["SHEEP"]), 0.947)

    y = np.arange(len(order))
    for i, r in enumerate(order):
        item = r["item"]
        c = S.colour(item)
        ax.barh(i, mean[item], height=0.62, color=c, zorder=3)
        ax.plot([worst[item], worst[item]], [i - 0.36, i + 0.36], color=S.INK, lw=2.2,
                zorder=5, gid="_rule")
        ax.text(mean[item] + 0.7, i, "{:.0f} tiles, {:.0f} at the tenth percentile"
                .format(mean[item], worst[item]), va="center", fontsize=10.2, color=c)
    ax.set_yticks(y)
    ax.set_yticklabels([r["item"] for r in order], fontsize=10.6)
    ax.invert_yaxis()
    board = int(CFG["boardSize"]) ** 2
    ax.plot([board, board], [-0.6, len(order) - 0.4], color=S.INK, lw=1.3,
            ls=(0, (5, 3)), zorder=6, gid="_rule")
    ax.text(board, -0.75, "the whole board, {} tiles".format(board), ha="center",
            va="bottom", fontsize=10.4, color=S.INK)
    ax.set_xlim(0, max(mean.values()) * 1.62)
    ax.set_ylim(len(order) - 0.4, -1.5)
    ax.set_xlabel("tiles the town can absorb")
    ax.text(0.985, 0.03, "black notch: the tenth percentile town",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=10.2,
            color=S.INK)
    S.yrule(ax, [])
    show(fig, "tiles")


fig_tiles()


def room_for(unlocked=(), econ=None, worst_case=None):
    """Tiles of each good the town can absorb, given the shops already open.

    unlocked   : the shops that have opened, e.g. observation.town["unlocked_shops"]
    worst_case : if set, answer for the unlucky tail instead of the average. 0.10
                 gives you the town you would get one time in ten.
    """
    econ = ECON if econ is None else econ
    dist = demand_dist(tuple(unlocked))
    out = {}
    for r in econ:
        good = PRODUCES.get(r["item"], r["item"])
        d = dist[good]
        if worst_case is None:
            units = sum(v * p for v, p in d.items()) * EVENTS
        else:
            acc, units = 0.0, 0
            for v in sorted(d):
                acc += d[v]
                if acc >= worst_case:
                    units = v * EVENTS
                    break
        out[r["item"]] = units / float(r["units_per_tile_per_day"])
    return out


for opened in ([], ["YARN_STORE"], ["BAKERY", "PIZZA_SHOP", "FARMERS_MARKET"]):
    room = room_for(opened)
    floor = room_for(opened, worst_case=0.10)
    head = "knowing nothing about the town" if not opened else "after " + ", ".join(opened)
    print(head)
    print("   {:<12}{:>8}{:>10}".format("", "average", "1 in 10"))
    # sheep is always shown, whatever it ranks, because it is the good this whole
    # notebook is about and a top-N list is exactly where it would hide
    top = [i for i, _ in sorted(room.items(), key=lambda t: -t[1])[:4]]
    for item in top + (["SHEEP"] if "SHEEP" not in top else []):
        print("   {:<12}{:>8.1f}{:>10.1f}".format(item, room[item], floor[item]))
    print()


def fig_hedge():
    """Two goods are not two independent bets, and the direction of the error flips."""
    import itertools
    # only goods a shop buys at all, and only those that can go either way. Melon and
    # fertilizer are on no shop's list, so their market is dead in every town and a
    # ratio against them is meaningless.
    shop_goods = sorted({g for v in SHOPS.values() for g in v})
    goods = [g for g in shop_goods if 0 < STAT[g]["p_zero"] < 1]
    buyers = {g: {n for n in NAMES if g in SHOPS[n]} for g in shop_goods}

    joint = {}
    for counts, prob in all_towns():
        multiset = []
        for n, k in zip(NAMES, counts):
            multiset += [n] * k
        units = units_per_event(multiset)
        key = frozenset(g for g in goods if units.get(g, 0) == 0)
        joint[key] = joint.get(key, 0.0) + prob
    pz = {g: sum(p for d, p in joint.items() if g in d) for g in goods}

    rows = []
    for a, b in itertools.combinations(goods, 2):
        both = sum(p for d, p in joint.items() if a in d and b in d)
        ind = pz[a] * pz[b]
        rows.append((both / ind, a, b, both, ind))
    rows.sort()

    nested = [(a, b) for a, b in itertools.permutations(goods, 2)
              if buyers[a] and buyers[a] < buyers[b]]
    worst = rows[-1]

    fig = S.figure(6.6, head=0.225)
    ax = fig.subplots()
    S.title(fig, "Planting two goods is not two independent bets")
    wheat_buyers = len(buyers["WHEAT"])
    exact = [r for r in rows if abs(r[0] - 1.0) < 1e-9]
    S.sub(fig, "Every pair of goods that can have a dead market, placed by how much the "
               "chance of BOTH being dead departs from the product of the two separate "
               "chances. One is what independence would give. To the right the pair is "
               "more dangerous than it looks, to the left it is safer. The three worst "
               "pairs all contain wheat, and the reason is structural: wheat is bought "
               "by {} of the {} shop types, so the only towns with no wheat buyer are "
               "towns assembled from the other {}, which leaves almost nothing standing "
               "for anything else either. The sharpest case is set inclusion: {} and {} "
               "are bought ONLY by shops that also buy wheat, so no wheat buyer means no "
               "{} buyer with probability exactly one. Sharing a shop is not by itself "
               "the tell: the {} pairs in grey come out EXACTLY independent to ten "
               "decimals even though they share one.".format(
                   wheat_buyers, len(NAMES), len(NAMES) - wheat_buyers,
                   nested[0][0].title(), nested[1][0].title(),
                   nested[0][0].lower(), len(exact)), 0.947)

    y = np.arange(len(rows))
    vals = [r[0] for r in rows]
    # pairs that land on exactly one get the neutral ink: painting them as "safer"
    # would invent a difference the arithmetic does not have.
    cols = [S.MUTE if abs(r[0] - 1.0) < 1e-9 else (S.WARN if r[0] > 1 else S.COOL)
            for r in rows]
    ax.barh(y, vals, height=0.66, color=cols, zorder=3)
    ax.axvline(1.0, color=S.INK, lw=1.4, zorder=4)
    ax.text(1.0, len(rows) - 0.2, "independence", ha="center", va="bottom",
            fontsize=10.4, color=S.INK)
    for i, (r, a, b, both, ind) in enumerate(rows):
        # always OUTSIDE the bar, to its right. Placed left of the bar end the label
        # sits on top of the bar in the bar's own colour and simply disappears.
        ax.text(r * 1.07, i, "{:.2f}".format(r), va="center", fontsize=9.6,
                ha="left", color=cols[i])
    ax.set_yticks(y)
    ax.set_yticklabels(["{} + {}".format(a.title(), b.title())
                        for _, a, b, _, _ in rows], fontsize=10)
    ax.set_xscale("log")
    ax.set_xlim(0.06, 22)
    ax.set_xlabel("chance both markets are dead, as a multiple of the independent guess")
    ax.set_ylim(-0.7, len(rows) - 0.05)
    show(fig, "hedge")


fig_hedge()
