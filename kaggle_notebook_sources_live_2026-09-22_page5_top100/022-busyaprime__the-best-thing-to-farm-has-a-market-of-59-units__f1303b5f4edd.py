import csv
import os
import sys
from glob import glob

import numpy as np
import matplotlib.pyplot as plt


def find(*names, column=None, contains=None):
    """Locate a directory by what is inside it, not by a slug. Kaggle mounts a dataset
    under its own name but is free to keep the files in a subfolder of it, and the
    competition input sits in the same tree, so this walks the whole of /kaggle/input
    and takes the shallowest directory holding all the named files.

    A column name can be required of the header, and a string of the first DATA row.
    Both are needed. Kaggle publishes an episode index for several simulation
    competitions and they share the filename manifest.csv AND, byte for byte, the same
    header line, so a header check alone cannot tell them apart. The first data row
    carries the competition in its slug column, and that can."""
    hits = []
    for root, dirs, files in os.walk("/kaggle/input"):
        dirs.sort()
        if not all(n in files for n in names):
            continue
        if column or contains:
            with open(os.path.join(root, names[0]), encoding="utf-8") as fh:
                head = fh.readline()
                first = fh.readline()
            if column and column not in head:
                continue
            if contains and contains not in first:
                continue
        hits.append(root)
    if not hits:
        here = sorted(os.path.dirname(f) for f in
                      glob("/kaggle/input/**/*.csv", recursive=True))
        raise FileNotFoundError(
            "attach kaggriculture-reference-agents and kaggriculture-episodes-index. "
            "Looking for " + ", ".join(names) + ". Directories holding csv files "
            "right now: " + (", ".join(sorted(set(here))) or "none"))
    return sorted(hits, key=lambda r: (r.count(os.sep), r))[0]


REF = find("crop_economics.csv", "season_timeline.csv")
IDX = find("manifest.csv", column="daily_dataset_slug", contains="kaggriculture")
print("reference agents:", REF)
print("episode index:   ", IDX)

used = ["crop_economics.csv", "price_curves.csv", "agents_manifest.csv",
        "baseline_league.csv", "season_timeline.csv", "head_to_head_games.csv"]
total = 0
for name in used:
    n = os.path.getsize(os.path.join(REF, name))
    total += n
    print("  {:<24} {:>7} bytes".format(name, n))
n = os.path.getsize(os.path.join(IDX, "manifest.csv"))
total += n
print("  {:<24} {:>7} bytes".format("manifest.csv", n))
print("  {:<24} {:>7} bytes, {:.0f} KB".format("total read", total, total / 1024))


def load(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


ECON = load(f"{REF}/crop_economics.csv")
CURVE = load(f"{REF}/price_curves.csv")
AGENTS = load(f"{REF}/agents_manifest.csv")
LEAGUE = load(f"{REF}/baseline_league.csv")
TIMELINE = load(f"{REF}/season_timeline.csv")
MANIFEST = load(f"{IDX}/manifest.csv")

FLOOR_CAP = 6000.0          # ">6000" in the data means no reachable floor this season


def depth(v):
    """Market depth as a number. '>6000' means the floor is out of reach."""
    return FLOOR_CAP if str(v).startswith(">") else float(v)


FARMERS = ["fallow_finn", "wheat_walter", "rotation_rosa",
           "homestead_hana", "melon_mateo", "rancher_rita"]
SEEDS = ["7000", "7001", "7002"]


def track(slug, seed, field):
    """One agent, one seed, one column, ordered by day."""
    rows = [r for r in TIMELINE if r["agent_slug"] == slug and r["seed"] == seed]
    rows.sort(key=lambda r: int(r["day"]))
    return [int(r["day"]) for r in rows], [float(r[field]) for r in rows]


def median_track(slug, field):
    """The same, taken day by day across the three recorded seeds."""
    days, _ = track(slug, SEEDS[0], field)
    runs = np.array([track(slug, s, field)[1] for s in SEEDS])
    return days, np.median(runs, axis=0)


print("crops and animals   ", len(ECON))
print("price curves        ", len(CURVE))
print("reference agents    ", len(AGENTS))
print("league pairs        ", len(LEAGUE))
print("season log rows     ", len(TIMELINE), "=",
      len({r["agent_slug"] for r in TIMELINE}), "agents x",
      len({r["seed"] for r in TIMELINE}), "seeds x",
      len({r["day"] for r in TIMELINE}), "days")
print("index days          ", len(MANIFEST), MANIFEST[0]["date"], "to",
      MANIFEST[-1]["date"])
print("episodes indexed    ", sum(int(r["episode_count"]) for r in MANIFEST))


"""Plot style for the Kaggriculture notebook.

The palette is semantic, not decorative. Every tradable product gets one bright
colour and keeps it in every figure, and each animal inherits the colour of the
product it makes: a goose is drawn in the colour of an egg, a cow in the colour of
milk, a sheep in the colour of wool. That way a reader who learns the colours once
can read the rest of the notebook without a legend.

Colours are chosen bright on purpose. This is a farming market, the figures are about
prices collapsing and money piling up, and a muted palette would undersell what the
numbers actually say. They stay distinguishable: every pair is at least 25 units apart
in CIELAB, checked by `palette_check()` below rather than assumed.

Every figure is audited before it is shown. Four defect classes are caught and each is
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


# the figure functions below were written against this module as `K`, and here the
# module is the notebook itself
K = sys.modules[__name__]


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


palette_check()
palette_check(AGENT, "agents")
palette_check({k: v[1] for k, v in LAND.items()}, "land", 20.0)


def fig_trap():
    """The headline: the better a thing looks per tile, the shallower its market."""
    fig = K.figure(6.6, head=0.155)
    ax = fig.subplots()
    K.title(fig, "The best-looking goods have the shallowest markets")
    K.sub(fig, "Every crop and animal in the game. Horizontal, how many units you can "
               "sell before the price hits its floor. Vertical, gross revenue per tile "
               "per day at the base price. Bubble area is the whole season revenue "
               "ceiling. Anything in the shaded corner earns well per tile and runs out "
               "of buyers almost immediately.", 0.945)

    xs = np.array([depth(r["units_until_price_floor"]) for r in ECON])
    ys = np.array([float(r["gross_per_tile_per_day"]) for r in ECON])
    cs = np.array([float(r["season_revenue_ceiling"]) for r in ECON])
    names = [r["item"] for r in ECON]

    ax.axvspan(40, 200, color=K.WARN, alpha=0.07, zorder=0)
    ax.text(85, 316, "shallow market", ha="center", va="top", fontsize=10.5,
            color=K.WARN)

    for x, y, c, n in zip(xs, ys, cs, names):
        ax.scatter([x], [y], s=40 + 900 * (c / cs.max()) ** 0.55,
                   color=K.colour(n), alpha=0.82, edgecolors="white",
                   linewidths=1.6, zorder=3)
    for x, y, n in zip(xs, ys, names):
        # offset in points, never a multiplied coordinate: the x axis is logarithmic
        # and x * -1.09 lands at a negative position, which matplotlib renders
        # hundreds of thousands of pixels off canvas
        right = n not in ("GOOSE", "WHEAT")
        ax.annotate(n, (x, y), xytext=(14 if right else -14, 13),
                    textcoords="offset points", ha="left" if right else "right",
                    va="bottom", fontsize=11, color=K.colour(n))

    ax.set_xscale("log")
    ax.set_xticks([50, 100, 200, 500, 1000, 6000])
    ax.set_xticklabels(["50", "100", "200", "500", "1000", "no floor\nreachable"])
    ax.set_xlim(40, 11000)
    ax.set_ylim(-14, 352)
    ax.set_xlabel("units that can be sold before the price bottoms out")
    ax.set_ylabel("gross revenue per tile per day, at base price")
    top = max(ECON, key=lambda r: float(r["season_revenue_ceiling"]))
    ax.set_title("biggest bubble is {} at {} coins a season".format(
        top["item"], K.num(float(top["season_revenue_ceiling"]))), loc="right",
        color=K.MUTE, fontsize=10.5)
    K.yrule(ax, [0, 50, 100, 150, 200, 250, 300])
    show(fig, "trap")


fig_trap()


def fig_collapse():
    """What the market actually pays as you keep selling."""
    pts = [(1, "base_price"), (50, "price_at_50_sold"), (150, "price_at_150_sold"),
           (400, "price_at_400_sold"), (1000, "price_at_1000_sold")]
    fig = K.figure(6.55, head=0.142)
    a1, a2 = fig.subplots(1, 2, width_ratios=[1.35, 1.0])
    gone = [r["product"] for r in CURVE
            if float(r["price_at_150_sold"]) / float(r["base_price"]) <= 0.10]
    K.title(fig, f"{len(gone)} of the {len(CURVE)} goods lose almost everything "
                 f"by 150 units sold")
    K.sub(fig, "Left, the price a seller receives after a given number of units has "
               "already been sold that season, on a log axis. Right, the same thing as "
               "one number: what fraction of the starting price survives selling 150 "
               "units.", 0.945)

    for r in CURVE:
        p = r["product"]
        ys = [float(r[k]) for _, k in pts]
        a1.plot([x for x, _ in pts], ys, "-o", color=K.colour(p), lw=2.4, ms=6,
                zorder=3, solid_capstyle="round")
        a1.plot([], [], color=K.colour(p), lw=3.2, label=p)
    a1.set_xscale("log")
    a1.set_xticks([1, 50, 150, 400, 1000])
    a1.set_xticklabels(["base", "50", "150", "400", "1000"])
    a1.set_xlim(0.45, 1500)
    a1.set_ylim(-12, 275)
    a1.set_xlabel("units already sold this season")
    a1.set_ylabel("price received per unit")
    a1.set_title("price against volume")
    # below the panels, not above. At the top the legend row shares its line with the
    # figure title and the two collide at any font size that stays readable.
    fig.legend(*a1.get_legend_handles_labels(), loc="outside lower center",
               fontsize=9.8, ncols=9, handlelength=1.3, columnspacing=1.1,
               frameon=False)
    K.yrule(a1, [0, 50, 100, 150, 200, 250])

    keep = sorted(((float(r["price_at_150_sold"]) / float(r["base_price"]), r["product"])
                   for r in CURVE), reverse=True)
    y = np.arange(len(keep))
    a2.barh(y, [k * 100 for k, _ in keep], height=0.66,
            color=[K.colour(p) for _, p in keep], zorder=2)
    for i, (k, p) in enumerate(keep):
        a2.text(k * 100 + 1.6, i, f"{k*100:.0f}%", va="center", fontsize=10,
                color=K.colour(p))
    a2.set_yticks(y)
    a2.set_yticklabels([p for _, p in keep], fontsize=10)
    a2.set_xlim(0, 105)
    a2.set_xlabel("share of base price left after 150 units")
    a2.set_title("what survives 150 units")
    a2.invert_yaxis()
    show(fig, "collapse")


fig_collapse()


def fig_ceiling():
    """Season revenue ceiling, which inverts the per-tile ranking."""
    rows = sorted(ECON, key=lambda r: -float(r["season_revenue_ceiling"]))
    lead = sorted(ECON, key=lambda r: -float(r["gross_per_tile_per_day"]))[0]["item"]
    place = [r["item"] for r in rows].index(lead) + 1
    fig = K.figure(5.4, head=0.175)
    a1, a2 = fig.subplots(1, 2)
    K.title(fig, "Ranked by the whole season, the order turns upside down")
    K.sub(fig, "Left, the most a single tile of each good can earn across the season "
               "once the falling price is taken into account. Right, the same goods "
               "ranked by gross per tile per day, which is what they look like on the "
               "first morning. {} leads the right hand list and comes {} of {} on "
               "the left.".format(lead.title(), place, len(rows)), 0.945)

    y = np.arange(len(rows))
    vals = [float(r["season_revenue_ceiling"]) for r in rows]
    a1.barh(y, vals, height=0.66, color=[K.colour(r["item"]) for r in rows], zorder=2)
    for i, (v, r) in enumerate(zip(vals, rows)):
        a1.text(v + max(vals) * 0.012, i, K.num(v),
                va="center", fontsize=10, color=K.colour(r["item"]))
    a1.set_yticks(y)
    a1.set_yticklabels([r["item"] for r in rows], fontsize=10)
    a1.set_xlim(0, max(vals) * 1.26)
    a1.set_xlabel("season revenue ceiling, coins")
    a1.set_title("whole season")
    a1.invert_yaxis()

    rows2 = sorted(ECON, key=lambda r: -float(r["gross_per_tile_per_day"]))
    v2 = [float(r["gross_per_tile_per_day"]) for r in rows2]
    a2.barh(np.arange(len(rows2)), v2, height=0.66,
            color=[K.colour(r["item"]) for r in rows2], zorder=2)
    for i, (v, r) in enumerate(zip(v2, rows2)):
        a2.text(v + max(v2) * 0.014, i, f"{v:.1f}", va="center", fontsize=10,
                color=K.colour(r["item"]))
    a2.set_yticks(np.arange(len(rows2)))
    a2.set_yticklabels([r["item"] for r in rows2], fontsize=10)
    a2.set_xlim(0, max(v2) * 1.24)
    a2.set_xlabel("gross per tile per day, coins")
    a2.set_title("first morning")
    a2.invert_yaxis()
    show(fig, "ceiling")


fig_ceiling()


# find_spec locates the package without importing it, which keeps the environment loader
# quiet, and ast reads the constants without executing any of the game.
import ast
import importlib.util

SHOPS, CAP, SOURCE, VER = None, None, "the engine", "unknown version"
try:
    import importlib.metadata
    try:
        VER = "version " + importlib.metadata.version("kaggle-environments")
    except Exception:
        pass
    spec = importlib.util.find_spec("kaggle_environments")
    engine = os.path.join(os.path.dirname(spec.origin), "envs", "kaggriculture",
                          "kaggriculture.py")
    const = {}
    for node in ast.parse(open(engine, encoding="utf-8").read()).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                const[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    # fetched separately on purpose. An earlier version of this cell took both in one
    # statement, and on Kaggle, where the installed engine has no MAX_SHOP_INSTANCES,
    # that one KeyError threw away the shop table as well and the whole check silently
    # became a quotation of somebody else's numbers.
    SHOPS = const["SHOPS"]
    CAP = const.get("MAX_SHOP_INSTANCES")
except Exception as exc:
    # if the engine is not on this image the argument still needs its numbers, so fall
    # back to the counts as published, clearly labelled as not recomputed here
    print("engine not readable here:", type(exc).__name__, exc)
    SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
             "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
             "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
             "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
             "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
    CAP, SOURCE = None, "the published counts, NOT recomputed here"

print("read from {} ({}): {} shop types{}".format(
    SOURCE, VER, len(SHOPS),
    ", at most {} instances in one town, drawn with replacement".format(CAP)
    if CAP else ", instance cap not declared in this build"))
for name, goods in SHOPS.items():
    print("   {:<16} {}".format(name, ", ".join(goods)))

shops = {}
for goods in SHOPS.values():
    for g in goods:
        shops[g] = shops.get(g, 0) + 1

print()
print("{:<12}{:>7}{:>12}{:>16}".format("good", "shops", "depth", "coins/tile/day"))
rows = sorted(ECON, key=lambda r: -shops.get(PRODUCES.get(r["item"], r["item"]), 0))
for r in rows:
    good = PRODUCES.get(r["item"], r["item"])
    print("{:<12}{:>7}{:>12}{:>16}".format(
        r["item"], shops.get(good, 0), r["units_until_price_floor"],
        r["gross_per_tile_per_day"]))


def rank(v):
    v = np.asarray(v, float)
    order = np.argsort(np.argsort(v)).astype(float)
    out = order.copy()
    for u in set(v.tolist()):
        m = v == u
        if m.sum() > 1:
            out[m] = order[m].mean()
    return out


rho = float(np.corrcoef(
    rank([depth(r["units_until_price_floor"]) for r in ECON]),
    rank([shops.get(PRODUCES.get(r["item"], r["item"]), 0) for r in ECON]))[0, 1])
print()
print("Spearman between market depth and shop count: {:.2f}".format(rho))
print("wheat is in {} of the {} shops. Melon is in none of them.".format(
    shops.get("WHEAT", 0), len(SHOPS)))


def fig_growth():
    """How many times a tile of each good actually pays inside one season."""
    season = len({r["day"] for r in TIMELINE})
    rows = []
    for r in ECON:
        first, cyc = int(r["days_to_first_yield"]), int(r["cycle_days"])
        days = list(range(first, season, cyc))
        rows.append((r["item"], first, cyc, days,
                     len(days) * int(r["units_per_cycle"]),
                     float(r["units_per_tile_per_day"]) * season))
    rows.sort(key=lambda t: -len(t[3]))
    most = rows[0]
    # three crops tie for the fewest, so the heading names the count, not one of them
    slow = [t[0] for t in rows if len(t[3]) == len(rows[-1][3])]
    short = sum(1 for t in rows if t[4] < t[5])
    over = sum(1 for t in rows if t[4] > t[5])

    fig = K.figure(6.2, head=0.215)
    ax = fig.subplots()
    K.title(fig, "One season fits {} {} harvests, and {} of {}".format(
        len(most[3]), most[0].lower(), len(rows[-1][3]),
        " or ".join(w.lower() for w in slow)))
    K.sub(fig, "A season is {} days long. Each lane is one tile of one good: the grey "
               "stretch is the wait before the first yield, and every dot after it is "
               "a harvest. The number on the right is what the tile actually produces "
               "in a season against what the published rate of units per tile per day "
               "promises, because that rate is units per cycle divided by cycle days "
               "and quietly assumes the first harvest costs no time at all. {} of the "
               "{} come in under the promised number and {} beats "
               "it.".format(season, short, len(rows), over), 0.947)

    for i, (name, first, cyc, days, real, smooth) in enumerate(rows):
        c = K.colour(name)
        ax.barh(i, first, height=0.5, color=K.RULE, zorder=2)
        ax.plot([first, season - 1], [i, i], color=c, lw=1.4, alpha=0.5, zorder=2)
        ax.scatter(days, [i] * len(days), s=44, color=c, zorder=4, lw=0)
        ax.text(first - 0.5, i, "{} d".format(first), ha="right", va="center",
                fontsize=9.4, color=K.MUTE)
        ax.text(season + 0.6, i, "{} units, rate says {:.0f}".format(real, smooth),
                ha="left", va="center", fontsize=10, color=c)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=10.4)
    ax.invert_yaxis()
    ax.set_xlim(-4.2, season + 15.5)
    ax.set_xticks([0, 5, 10, 15, 20, 25, season - 1])
    ax.set_xlabel("day of the season")
    ax.set_title("grey is the wait, each dot is a harvest", loc="right", color=K.MUTE,
                 fontsize=10.5)
    show(fig, "growth")


fig_growth()


def fig_market():
    """Selling a good is what moves its price. Growing it is not enough."""
    seller = "melon_mateo"
    quiet = [a for a in FARMERS if a != seller]
    melon = median_track(seller, "price_melon")[1]
    others = [median_track(a, "price_melon")[1] for a in quiet]
    # the five agents that never sell a melon share one melon curve exactly, in every
    # seed, so drawing five coloured lines would put four of them out of sight under
    # the fifth and invite the reader to read a spread that is not there
    same = all(np.array_equal(v, others[0]) for v in others[1:])
    rest = others[0][-1]

    wheat_open = median_track("fallow_finn", "price_wheat")[1][0]
    closes = [median_track(a, "price_wheat")[1][-1] for a in FARMERS]
    lo, hi = min(closes), max(closes)

    # An upper bound on how much wheat the wheat agent could possibly have sold: give
    # it credit for its entire closing bank and price every unit at the lowest quote
    # on the wheat curve. The real number is smaller. Even the bound is far under the
    # volume the wheat market absorbs before its price floor.
    floor_price = min(float(r[k]) for r in CURVE if r["product"] == "WHEAT"
                      for k in ("price_at_50_sold", "price_at_150_sold",
                                "price_at_400_sold", "price_at_1000_sold"))
    best = max(float(r["bank"]) for r in TIMELINE
               if r["agent_slug"] == "wheat_walter" and r["day"] == "29")
    deep = next(r["units_until_price_floor"] for r in CURVE if r["product"] == "WHEAT")

    fig = K.figure(6.5, head=0.245, foot=0.055)
    a1, a2 = fig.subplots(1, 2)
    K.title(fig, "The only price that falls is the price somebody is selling")
    K.sub(fig, "Median price across the three seeds, day by day, inside each agent's "
               "own season. Melon opens at {:.0f} coins in all six seasons. In the "
               "season of the one agent that sells melons it closes at {:.0f}; in the "
               "other five it closes at {:.0f} along a path the five share to the "
               "coin. Wheat closes above its opening price in all six, including the "
               "season of the agent whose whole strategy is wheat: Walter closes with "
               "at most {} coins, so even crediting every coin to wheat at its "
               "lowest quote of {:.0f} he moved under {:.0f} units, against a market "
               "that absorbs {} before its price floor.".format(
                   melon[0], melon[-1], rest, K.num(best), floor_price,
                   best / floor_price, deep), 0.947)

    assert same, "the five quiet melon curves are no longer identical"
    # black, not grey: grey is the colour the legend gives fallow finn, and this
    # one line belongs to five agents at once rather than to any one of them
    a1.plot(*median_track(quiet[0], "price_melon"), color=K.INK, lw=3.0, zorder=3,
            solid_capstyle="round")
    a1.plot(*median_track(seller, "price_melon"), color=K.AGENT[seller], lw=3.4,
            zorder=4, solid_capstyle="round")
    a1.text(0.8, 300, "the other five never sell one. Their curves are\n"
                      "identical in every seed, so they are drawn as one\n"
                      "black line that belongs to no single agent",
            fontsize=10.2, color=K.INK, ha="left", va="bottom")
    a1.annotate("melon mateo sells melons,\nand closes at {:.0f}".format(melon[-1]),
                xy=(26.6, 42), xytext=(0.8, 104), fontsize=10.6,
                color=K.AGENT[seller], ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", color=K.AGENT[seller], lw=1.5,
                                connectionstyle="arc3,rad=-0.18"))
    a1.set_title("price of melon")
    a1.set_ylim(-14, 384)
    a1.set_ylabel("coins per unit")
    K.yrule(a1, [0, 100, 200, 300])

    for slug in FARMERS:
        a2.plot(*median_track(slug, "price_wheat"), color=K.AGENT[slug], lw=2.2,
                zorder=3, solid_capstyle="round")
    # a band rather than six end labels: the six close within ten coins of each other
    # and any per-line label would point at two lines at once
    a2.axhspan(lo, hi, color=K.COOL, alpha=0.10, zorder=1)
    a2.axhline(wheat_open, color=K.HAIR, lw=1.0, ls=(0, (4, 3)), zorder=1, gid="_rule")
    a2.text(0.8, 55.4, "all six close inside this band,\nbetween {:.0f} and {:.0f}"
            .format(lo, hi), fontsize=10.6, color=K.COOL, ha="left", va="top")
    a2.text(14.2, 23.2, "opens at {:.0f} in every season".format(wheat_open),
            fontsize=9.8, color=K.MUTE, ha="left", va="bottom")
    a2.set_title("price of wheat")
    a2.set_ylim(22, 60)
    a2.set_ylabel("coins per unit")
    K.yrule(a2, [30, 40, 50])
    for ax in (a1, a2):
        ax.set_xlim(0, 29.4)
        ax.set_xlabel("day of the season")

    fig.legend([plt.Line2D([], [], color=K.AGENT[a], lw=3.2) for a in FARMERS],
               [a.replace("_", " ") for a in FARMERS], loc="outside lower center",
               ncols=6, fontsize=10.4, handlelength=1.5, columnspacing=1.8,
               frameon=False)
    show(fig, "market")


fig_market()


def fig_shed():
    """The stock an agent is holding, and what happens when it lets go of it."""
    who = "melon_mateo"
    d, shed = median_track(who, "shed_items")
    _, price = median_track(who, "price_melon")
    _, bank = median_track(who, "bank")
    drop = int(np.argmax(shed[:-1] - shed[1:]))       # the day the shed empties most
    sold = shed[drop] - shed[drop + 1]

    fig = K.figure(6.8, head=0.205)
    a1, a2, a3 = fig.subplots(3, 1, sharex=True, height_ratios=[1.0, 1.0, 1.0])
    K.title(fig, "The price collapses on the day the shed empties")
    K.sub(fig, "One agent, {}, on the median of its three recorded seeds. The shed is "
               "everything harvested and not yet sold. Between day {} and day {} it "
               "gives up {:.0f} items, the quoted melon price falls from {:.0f} coins "
               "to {:.0f}, and the bank gains {} coins. That is {:.0f} coins an item "
               "for a good whose base price is {:.0f}.".format(
                   who.replace("_", " "), drop, drop + 1, sold, price[drop],
                   price[drop + 1], K.num(bank[drop + 1] - bank[drop]),
                   (bank[drop + 1] - bank[drop]) / sold,
                   float(next(r["base_price"] for r in ECON if r["item"] == "MELON"))),
          0.947)

    a1.bar(d, shed, width=0.72, color=K.PRODUCT["MELON"], zorder=3)
    a1.set_ylabel("items in the shed")
    K.yrule(a1, [20, 40, 60])
    a2.plot(d, price, color=K.PRODUCT["MELON"], lw=2.6, zorder=3,
            solid_capstyle="round")
    a2.set_ylabel("melon price, coins")
    a2.set_ylim(-12, 300)
    K.yrule(a2, [0, 100, 200])
    a3.plot(d, bank, color=K.AGENT[who], lw=2.6, zorder=3, solid_capstyle="round")
    a3.set_ylabel("bank, coins")
    a3.set_xlabel("day of the season")
    a3.set_xlim(-0.8, len(d) - 0.2)
    K.yrule(a3, [10000, 20000, 30000])

    for ax in (a1, a2, a3):
        ax.axvspan(drop + 0.5, drop + 1.5, color=K.WARN, alpha=0.12, zorder=1)
    # over the bars, where the only thing in the way is empty shed. The price panel
    # is full from the left edge to the collapse, so nothing fits there.
    # directly over the highlighted pair of days, otherwise a note sitting to the
    # left of the band reads as a caption for the tall bar next to it
    a1.set_ylim(0, max(shed) * 1.42)
    a1.text(drop + 1.0, max(shed) * 1.06, "the shed empties here", ha="center",
            va="bottom", fontsize=10.6, color=K.WARN)
    show(fig, "shed")


fig_shed()


def fig_land():
    """What the fifty tiles are actually doing, day by day."""
    # a band is dropped only if it is empty in every recorded season, not just in the
    # one drawn here, so the claim in the subtitle covers the whole reference set
    keys = [k for k in K.LAND if any(float(r[k]) for r in TIMELINE)]
    unused = [K.LAND[k][0] for k in K.LAND if k not in keys]
    size = {r["agent_slug"] + r["day"]: sum(float(r[k]) for k in K.LAND)
            for r in TIMELINE if r["seed"] == "7000"}
    biggest = max(size.values())
    grew = min(int(d) for d in range(30)
               if size.get("rancher_rita" + str(d), 0) == biggest)

    fig = K.figure(6.6, head=0.175)
    axes = fig.subplots(2, 3, sharex=True, sharey=True)
    K.title(fig, "The land says what the strategy is before the money does")
    K.sub(fig, "The farm on seed 7000, day by day, richest agent first. Every tile "
               "is in exactly one "
               "state, so the bands add up to the whole farm and the top of the grey "
               "is the farm itself: Rita goes from one quadrant of {:.0f} tiles to "
               "three, and both extra quadrants land on the same day, day {}. Pink is "
               "land gone to "
               "weed, the clearest tell of an agent that plants faster than it can "
               "tend. No reference agent in any recorded season ever builds a {}, "
               "which is why that band is missing.".format(
                   biggest / 3, grew, unused[0]), 0.947)

    order = sorted(FARMERS, key=lambda a: -median_track(a, "bank")[1][-1])
    for ax, slug in zip(axes.ravel(), order):
        d, _ = track(slug, "7000", "tiles_crop")
        bands = np.array([track(slug, "7000", k)[1] for k in keys])
        ax.stackplot(d, bands, colors=[K.LAND[k][1] for k in keys], zorder=2)
        w = bands[keys.index("tiles_weed")]
        ax.set_title(slug.replace("_", " "), loc="left", color=K.AGENT[slug],
                     fontsize=11.5)
        # on the title row, not inside the panel: Rita owns three quadrants from
        # day twelve, so her stack fills the panel to the top and leaves a label
        # nowhere to stand that is not on top of a band
        ax.set_title("weeds peak at {:.0f}".format(w.max()), loc="right",
                     fontsize=10.2, color=K.INK)
    for ax in axes[1]:
        ax.set_xlabel("day")
    for ax in axes[:, 0]:
        ax.set_ylabel("tiles")
    axes[0][0].set_xlim(0, 29)
    axes[0][0].set_ylim(0, biggest)
    axes[0][0].set_yticks([0, 25, 50, 75])
    fig.legend([plt.Rectangle((0, 0), 1, 1, color=K.LAND[k][1]) for k in keys],
               [K.LAND[k][0] for k in keys], loc="outside lower center",
               ncols=len(keys), fontsize=10.4, handlelength=1.5, columnspacing=1.8,
               frameon=False)
    show(fig, "land")


fig_land()


def fig_paths():
    """When during the season the money actually arrives, and to whom."""
    START = 3000.0
    DAY = 7
    close = {a: median_track(a, "bank")[1][-1] for a in FARMERS}
    early = {a: median_track(a, "bank")[1][DAY] for a in FARMERS}
    richest = sorted(FARMERS, key=lambda a: -close[a])[:3]
    poorest = sorted(FARMERS, key=lambda a: early[a])[:3]
    assert set(richest) == set(poorest), "the top three are no longer the day 7 bottom"
    spent = sum(median_track(a, "bank")[1][0] < START for a in FARMERS)

    # the deepest point anywhere in the recorded data, and where it happens
    low, low_at, low_who = None, None, None
    for a in FARMERS:
        for sd in SEEDS:
            d, v = track(a, sd, "bank")
            k = int(np.argmin(v))
            if low is None or v[k] < low:
                low, low_at, low_who = v[k], d[k], a

    fig = K.figure(6.1, head=0.20)
    ax = fig.subplots()
    K.title(fig, "The three that finish richest are the three that are poorest "
                 "on day {}".format(DAY))
    K.sub(fig, "Bank balance day by day for the six reference agents whose whole "
               "season is recorded, three seeds each. Faint lines are the individual "
               "seeds, the solid line is the day by day median. Fallow Finn never "
               "plants anything, so its flat grey line is exactly the {} coins every "
               "agent is handed at the start. The record begins at the end of day "
               "zero, by which point {} of the six have already spent into it. On day "
               "{} the three that will finish first, second and third sit at {}, {} "
               "and {} coins, and they are the three lowest on the board.".format(
                   K.num(START), spent, DAY, *[K.num(early[a]) for a in richest]),
          0.947)

    for slug in FARMERS:
        c = K.AGENT[slug]
        for sd in SEEDS:
            d, v = track(slug, sd, "bank")
            ax.plot(d, v, color=c, lw=0.9, alpha=0.32, zorder=2)
        d, v = median_track(slug, "bank")
        ax.plot(d, v, color=c, lw=2.6, zorder=3, solid_capstyle="round")
        ax.text(d[-1] + 0.7, v[-1], slug.replace("_", " "), color=c, fontsize=10.2,
                va="center", ha="left")

    ax.axvspan(0, DAY, color=K.COOL, alpha=0.07, zorder=0)
    ax.text(DAY - 0.4, 47000, "the first {} days".format(DAY), ha="right", va="top",
            fontsize=10.4, color=K.COOL)
    # under the axis, not over it: no curve goes below the trough by definition, so
    # the one strip of the panel guaranteed to stay empty is the strip beneath it
    ax.plot([low_at], [low], marker="v", ms=8, color=K.WARN, zorder=5, clip_on=False)
    ax.text(low_at, -1500, "the deepest anyone digs is {} coins, on day {}".format(
        K.num(low), low_at), fontsize=10.5, color=K.WARN, ha="center", va="top")
    assert low_who in richest, "the deepest trough is no longer one of the winners"
    ax.set_xlabel("day of the season")
    ax.set_ylabel("bank, coins")
    ax.set_xlim(-0.5, 36.6)
    ax.set_ylim(-5200, None)
    K.yrule(ax, [10000, 20000, 30000, 40000, 50000])
    show(fig, "paths")


fig_paths()


def fig_tiers():
    """The reference ladder, and what actually changes at the top of it."""
    rows = sorted(AGENTS, key=lambda r: int(r["tier"]))
    tiers = [int(r["tier"]) for r in rows]
    bank = [float(r["expected_bank"]) for r in rows]

    # The split is the manifest's own `kind` column, not an inference from the blank
    # cells further along the row. Reading those blanks as a declaration of nothing was
    # a real error in an earlier version of this figure: the per-field columns are
    # simply not filled in for the meta_line agents, and the strategy column in the
    # same row describes a large farm.
    meta = [r["kind"] == "meta_line" for r in rows]
    line = next(r for r in rows if r["kind"] == "meta_line")
    top = [b for b, m in zip(bank, meta) if m]
    grown = [b for b, m in zip(bank, meta) if not m]
    spread = max(top) - min(top)

    fig = K.figure(6.1, head=0.20)
    ax = fig.subplots()
    K.title(fig, "Above tier 5 the farm stops changing and only the selling does")
    K.sub(fig, "Expected end-of-season bank for each of the ten reference agents. The "
               "{} agents the manifest marks `authored` each design their own farm, and "
               "the best of them banks {}. The {} marked `meta_line` all run one shared "
               "field plan, described in the dataset as {}, and differ only in when they "
               "sell. That difference alone spreads them by {} coins, which is {:.0f} "
               "percent of everything the best designed farm earns in a whole "
               "season.".format(
                   len(grown), K.num(max(grown)), len(top),
                   "an 8-cow / 5-sheep / 6-strawberry build across three quadrants",
                   K.num(spread), spread / max(grown) * 100), 0.947)

    cols = [K.COOL if m else K.PRODUCT["MELON"] for m in meta]
    ax.bar(tiers, bank, width=0.66, color=cols, zorder=3)
    for t, b, r in zip(tiers, bank, rows):
        ax.text(t, b + 5200, K.num(b), ha="center", fontsize=10, color=K.INK)
        ax.text(t, -9000, r["agent_slug"].replace("_", "\n"), ha="center", va="top",
                fontsize=9.2, color=K.MUTE)
    ax.set_xticks(tiers)
    ax.set_xlabel("reference tier")
    ax.set_ylabel("expected bank at the end of the season, coins")
    ax.set_ylim(-34000, max(bank) * 1.34)
    ax.set_xlim(-0.8, 9.8)
    K.yrule(ax, [50000, 100000, 150000])

    jump = bank[6] / bank[5]
    ax.annotate("x{:.1f} in one tier".format(jump),
                xy=(5.5, (bank[5] + bank[6]) / 2), xytext=(3.3, 132000),
                fontsize=11.5, color=K.WARN, ha="center",
                arrowprops=dict(arrowstyle="-|>", color=K.WARN, lw=1.4,
                                connectionstyle="arc3,rad=-0.25"))
    # a bracket over exactly the four bars it describes: under them it landed on the
    # agent names, which are two lines deep there, and in the header it floated free
    hi = max(bank) * 1.135
    drop = max(bank) * 0.028
    ax.plot([5.62, 5.62, 9.38, 9.38], [hi - drop, hi, hi, hi - drop],
            color=K.COOL, lw=1.3, zorder=4, clip_on=False, gid="_rule")
    ax.text(7.5, hi + drop * 0.55, "same farm, four selling orders, {} coins apart"
            .format(K.num(spread)), ha="center", va="bottom", color=K.COOL,
            fontsize=11)
    ax.set_title("green: designs its own farm      blue: runs the shared field plan",
                 loc="right", color=K.MUTE, fontsize=10.5)
    assert line["crops"].strip() == "" and "cow" in line["strategy"].lower(), \
        "the meta_line rows no longer look the way this figure describes them"
    show(fig, "tiers")


fig_tiers()


def fig_league():
    """Head to head between the reference agents."""
    ags = sorted({r["agent_a"] for r in LEAGUE} | {r["agent_b"] for r in LEAGUE},
                 key=lambda a: next((int(x["tier"]) for x in AGENTS
                                     if x["agent_slug"] == a), 99))
    n = len(ags)
    M = np.full((n, n), np.nan)
    for r in LEAGUE:
        i, j = ags.index(r["agent_a"]), ags.index(r["agent_b"])
        g = int(r["games"])
        if g:
            wa = int(r["wins_a"]) / g
            M[i, j], M[j, i] = wa, 1 - wa
    # not an eyeball claim: the heading is only allowed to say this if it holds
    below = [M[i, j] for i in range(n) for j in range(n) if i > j and not np.isnan(M[i, j])]
    strict = all(v > 0.5 for v in below)
    fig = K.figure(6.4, head=0.155)
    ax = fig.subplots()
    K.title(fig, "Every agent beats every agent below it, without exception"
            if strict else "The ladder holds almost everywhere")
    K.sub(fig, "Win rate of the row agent against the column agent over the recorded "
               "games, ordered by tier. The lower triangle is every matchup an agent "
               "plays against a lower tier, and its {} cells never fall below {:.2f}. "
               "A ladder, not a rock-paper-scissors circle.".format(
                   len(below), min(below)), 0.945)
    # red against green is the one pairing a red-green colour blind reader cannot
    # separate, and neither colour belongs to this notebook. Pink to blue through
    # white reads the same way for everyone and is the palette already in use.
    from matplotlib.colors import LinearSegmentedColormap
    ramp = LinearSegmentedColormap.from_list("league", [K.WARN, "#F4F4F4", K.COOL])
    im = ax.imshow(M, cmap=ramp, vmin=0, vmax=1, interpolation="nearest",
                   aspect="auto")
    for i in range(n):
        for j in range(n):
            if np.isnan(M[i, j]):
                continue
            v = M[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9,
                    color="#151515" if 0.24 < v < 0.76 else "#FFFFFF")
    ax.set_xticks(range(n))
    tier_of = {r["agent_slug"]: int(r["tier"]) for r in AGENTS}
    ax.set_xticklabels([str(tier_of[a]) for a in ags], fontsize=10.5)
    ax.set_xlabel("column: opponent by tier")
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{tier_of[a]}  {a.replace('_', ' ')}" for a in ags],
                       fontsize=9.6)
    ax.set_title("blue means the row agent wins, pink means it loses", loc="right",
                 color=K.MUTE, fontsize=10.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.032, pad=0.015)
    cb.set_label("win rate of the row agent", fontsize=10)
    show(fig, "league")


fig_league()


def fig_margins():
    """Whether the reference ladder is a ladder or a lottery."""
    games = load(REF + "/head_to_head_games.csv")
    by = {}
    for g in games:
        ta, tb = int(g["tier_a"]), int(g["tier_b"])
        gap = abs(ta - tb)
        hi = g["agent_a"] if ta > tb else g["agent_b"]
        m = float(g["margin_a"]) * (1 if ta > tb else -1)
        w, n, ms = by.get(gap, (0, 0, []))
        by[gap] = (w + (g["winner"] == hi), n + 1, ms + [m])
    gaps = sorted(by)
    rate = [100 * by[g][0] / by[g][1] for g in gaps]
    won = sum(by[g][0] for g in gaps)
    seat0 = sum(g["winner"] == (g["agent_a"] if g["seat_of_a"] == "0"
                                else g["agent_b"]) for g in games)

    fig = K.figure(6.0, head=0.175)
    a1, a2 = fig.subplots(1, 2, width_ratios=[1.3, 1.0])
    K.title(fig, "The reference ladder is a ladder, not a lottery")
    K.sub(fig, "All {} recorded games between the ten reference agents. The higher "
               "tier takes {} of them, {:.1f} percent, and not one of the {} upsets "
               "crosses more than {} tiers. Going first is worth nothing measurable: "
               "seat zero wins {} of {}.".format(
                   len(games), won, 100 * won / len(games), len(games) - won,
                   max(g for g in gaps for m in by[g][2] if m < 0),
                   seat0, len(games)), 0.945)

    rng = np.random.default_rng(7)
    for g in gaps:
        ms = np.array(by[g][2]) / 1000
        # the upsets are the point of the panel, so they are not left as six blue
        # dots indistinguishable from the crowd sitting just above the line
        jit = g + rng.uniform(-0.23, 0.23, len(ms))
        up = ms < 0
        a1.scatter(jit[~up], ms[~up], s=27, color=K.COOL, alpha=0.5, lw=0, zorder=3)
        a1.scatter(jit[up], ms[up], s=46, color=K.WARN, lw=0, zorder=5)
        a1.scatter([g], [np.median(ms)], s=260, color=K.INK, zorder=4, marker="_",
                   lw=2.0)
    a1.axhline(0, color=K.WARN, lw=1.2, zorder=1, gid="_rule")
    lost = sum(1 for g in gaps for m in by[g][2] if m < 0)
    a1.text(9.4, 6, "under this line the lower tier won, {} times in {}".format(
        lost, len(games)), ha="right", va="bottom", fontsize=9.8, color=K.WARN)
    a1.set_xlabel("difference in tier between the two agents")
    a1.set_ylabel("margin of the higher tier, thousands of coins")
    a1.set_title("every game, one dot each, black bar is the median")
    a1.set_xticks(gaps)
    K.yrule(a1, [50, 100, 150, 200])

    a2.bar(gaps, rate, width=0.66, zorder=3,
           color=[K.WARN if r < 100 else K.COOL for r in rate])
    for g, r in zip(gaps, rate):
        a2.text(g, r + 1.6, "{:.0f}".format(r), ha="center", fontsize=9.8,
                color=K.WARN if r < 100 else K.COOL)
    a2.set_ylim(0, 116)
    a2.set_xticks(gaps)
    a2.set_xlabel("difference in tier")
    a2.set_ylabel("games won by the higher tier, percent")
    a2.set_title("the same thing as a rate")
    K.yrule(a2, [25, 50, 75, 100])
    show(fig, "margins")


fig_margins()


def fig_ladder():
    """The live ladder over the days the public index covers."""
    d = [r["date"] for r in MANIFEST]
    top = np.array([float(r["top_avg_score"]) for r in MANIFEST])
    med = np.array([float(r["median_avg_score"]) for r in MANIFEST])
    eps = np.array([int(r["episode_count"]) for r in MANIFEST])
    x = np.arange(len(d))
    # Title and caption are computed, not written. This is the one figure whose data
    # changes daily, so a sentence typed by hand here would go stale without warning.
    pk = int(np.argmax(top))
    since = len(d) - 1 - pk
    drop = top[pk] - top[-1]
    mchg = med[-1] - med[pk]
    g0, g1 = top[0] - med[0], top[-1] - med[-1]
    if since >= 3 and drop > 0.02 * top[pk]:
        head = "The ladder stopped climbing and started drifting back"
    elif since >= 3:
        head = "The ladder stopped climbing and has held its level"
    else:
        head = "The ladder is still climbing"

    fig = K.figure(5.8, head=0.155)
    a1, a2 = fig.subplots(2, 1, height_ratios=[1.9, 1.0], sharex=True)
    K.title(fig, head)
    K.sub(fig, f"Public episode index, {len(d)} days, "
               f"{K.num(eps.sum())} episodes in total. Top and median average score per "
               f"day, and the gap between them. The top peaked at {top[pk]:.0f} on "
               f"{d[pk]} and has given back {drop:.0f} points in the {since} days since, "
               f"while the median moved {mchg:+.0f} over the same stretch. The gap "
               f"between them has narrowed from {g0:.0f} to {g1:.0f}.", 0.945)

    a1.fill_between(x, med, top, color=K.WARN, alpha=0.12, zorder=1)
    a1.plot(x, top, lw=2.8, color=K.WARN, zorder=3, solid_capstyle="round")
    a1.plot(x, med, lw=2.8, color=K.COOL, zorder=3, solid_capstyle="round")
    a1.annotate("top agent", (x[-1], top[-1]), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=10.5, color=K.WARN)
    a1.annotate("median agent", (x[-1], med[-1]), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=10.5, color=K.COOL)
    peak = int(np.argmax(top))
    a1.plot([peak], [top[peak]], "o", ms=9, color=K.WARN, zorder=5)
    a1.annotate(f"peak {top[peak]:.0f} on {d[peak]}", (peak, top[peak]),
                xytext=(0, 16), textcoords="offset points", ha="center",
                fontsize=10.5, color=K.WARN)
    a1.set_ylabel("average score")
    a1.set_xlim(-0.6, len(d) + 3.4)
    K.yrule(a1, [1000, 2000, 3000])

    a2.bar(x, eps, width=0.7, color=K.MUTE, alpha=0.55, zorder=2)
    a2.set_ylabel("episodes")
    a2.set_xticks(x[::3])
    a2.set_xticklabels([d[i][5:] for i in range(0, len(d), 3)], fontsize=9.4)
    a2.set_xlabel("date in 2026")
    show(fig, "ladder")


fig_ladder()
