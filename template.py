"""Full-size (1:1) A4 landscape cutting template for seat block N."""
import json, math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle

D = json.load(open("/home/claude/out/dims_v4.json"))
INK, ACC, DIM, GHOST = "#111111", "#c0392b", "#1f5fa8", "#888888"
W_IN, H_IN = 11.69, 8.27
W_MM, H_MM = W_IN*25.4, H_IN*25.4
YC, WH, WW = D["YC"], D["WH"], D["WW"]          # 109.2, 45, 95
TOPL = YC - WH                                   # 64.2
c = math.cos(math.radians(45))
M_SCREW_UP, M_SCREW_END = 35, D["CR_HALF"] - (D["XI"] + D["T"]/2)   # 35 up, ~225 from M's end
SCREWS = (20, 45)                                # counterbores from the front end, on A's centre line


def hdim(ax, x0, x1, y, text, above=True):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.7, shrinkA=0, shrinkB=0))
    ax.text((x0+x1)/2, y + (1.6 if above else -1.6), text, color=DIM, fontsize=7.5, ha="center",
            va="bottom" if above else "top")

def vdim(ax, x, y0, y1, text, right=True):
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.7, shrinkA=0, shrinkB=0))
    ax.text(x + (1.6 if right else -1.6), (y0+y1)/2, text, color=DIM, fontsize=7.5, va="center",
            ha="left" if right else "right")

def ext(ax, p0, p1):
    ax.plot(*zip(p0, p1), color=DIM, lw=0.35)


def make_template(footer=""):
    fig = plt.figure(figsize=(W_IN, H_IN))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W_MM); ax.set_ylim(0, H_MM); ax.set_aspect("equal"); ax.axis("off")

    ax.text(12, H_MM - 10, "Seat block N — full-size template", fontsize=17, weight="bold", color=INK, va="top")
    ax.text(12, H_MM - 19, "Make 2 from 45×95 (from the same 3.0 m length as F). Print at 100% / \"Actual size\" (not \"Fit to page\"), then check the bar below is exactly 100 mm.",
            fontsize=8.5, color="#444", va="top")

    # ---- 100 mm check bar
    bx, by = 12, 8
    ax.add_patch(Rectangle((bx, by), 100, 4, fc="none", ec=INK, lw=0.8))
    for k in range(11):
        ax.plot([bx + 10*k, bx + 10*k], [by, by + (7 if k % 5 == 0 else 5.5)], color=INK, lw=0.6)
        if k % 5 == 0: ax.text(bx + 10*k, by + 8, f"{10*k}", fontsize=6.5, ha="center", va="bottom")
    for k in range(10):
        if k % 2 == 0: ax.add_patch(Rectangle((bx + 10*k, by), 10, 4, fc=INK, ec="none"))
    ax.text(bx + 104, by + 2, "← must measure 100 mm", fontsize=8, va="center", weight="bold")

    # ================= 1. SIDE PROFILE (trace on both narrow 45 mm faces)
    x0, y0 = 12, 80
    prof = [(x0, y0), (x0 + YC, y0), (x0 + TOPL, y0 + WH), (x0, y0 + WH)]
    ax.plot([x0 - 10, x0 + YC + 12], [y0, y0], color=GHOST, lw=0.8, ls="--")
    ax.text(x0 + 78, y0 - 24, "dashed line = top of base beam A", fontsize=7, color=GHOST, va="top")
    cx, cy = x0 + YC, y0
    up, back = (-c, c), (c, c)
    MH_ = 60     # only the bottom of M is drawn
    Mpts = [(cx, cy), (cx + MH_*up[0], cy + MH_*up[1]),
            (cx + MH_*up[0] + 45*back[0], cy + MH_*up[1] + 45*back[1]), (cx + 45*back[0], cy + 45*back[1])]
    ax.plot([Mpts[1][0], Mpts[0][0], Mpts[3][0], Mpts[2][0]], [Mpts[1][1], Mpts[0][1], Mpts[3][1], Mpts[2][1]], color=GHOST, lw=0.8, ls="--")
    zz = [(Mpts[1][0] + k/6*45*back[0] + (2.5 if k % 2 else -2.5)*up[0], Mpts[1][1] + k/6*45*back[1] + (2.5 if k % 2 else -2.5)*up[1]) for k in range(7)]
    ax.plot([p[0] for p in zz], [p[1] for p in zz], color=GHOST, lw=0.8)
    mx, my = sum(p[0] for p in Mpts)/4, sum(p[1] for p in Mpts)/4
    ax.text(mx + 4, my + 4, "ledge M\n(not part of\nthe template)", fontsize=6.5, color=GHOST, ha="center", va="center", rotation=-45)
    sp = (cx + M_SCREW_UP*up[0], cy + M_SCREW_UP*up[1])
    ax.plot([sp[0] + 45*back[0], sp[0] - 30*c], [sp[1] + 45*back[1], sp[1] - 30*c], color=ACC, lw=0.8, ls=(0, (3, 2)))
    ax.add_patch(Polygon(prof, closed=True, fc="#f3e6cf", ec=INK, lw=1.6))
    for xs in SCREWS:
        ax.plot([x0 + xs, x0 + xs], [y0 + WH, y0 + WH - 75], color=ACC, lw=0.8, ls=(0, (3, 2)))
    ax.text(x0 + 16, y0 + 8, "N  side view", fontsize=9, weight="bold", va="center")
    ax.text(x0 + TOPL - 13, y0 + WH - 8, "45°", fontsize=9, color=ACC, weight="bold")
    ext(ax, (x0, y0), (x0, y0 - 14)); ext(ax, (x0 + YC, y0), (x0 + YC, y0 - 14))
    hdim(ax, x0, x0 + YC, y0 - 12, f"{YC:.0f}", above=False)
    ext(ax, (x0, y0 + WH), (x0, y0 + WH + 10)); ext(ax, (x0 + TOPL, y0 + WH), (x0 + TOPL, y0 + WH + 10))
    hdim(ax, x0, x0 + TOPL, y0 + WH + 7, f"{TOPL:.0f}")
    vdim(ax, x0 + 4, y0 + 2, y0 + WH - 2, "45")
    ax.text(x0 - 4, y0 - 26, "FRONT end — flush with the\nfront end of base beam A", fontsize=7.5, va="top", color=ACC)
    ax.annotate("45° face — ledge M rests flat against this", (x0 + (YC + TOPL)/2 - 3, y0 + WH/2 - 3), (12, 178),
                fontsize=8, arrowprops=dict(arrowstyle="-", color=ACC, lw=0.6))
    ax.annotate("screw through M into N, 35 up from M's bottom edge", sp, (12, 171),
                fontsize=8, arrowprops=dict(arrowstyle="-", color=ACC, lw=0.6))
    ax.text(12, 164, "Red dashes = screw paths.  Thick black line = cut line.", fontsize=7.5, color="#555")

    # ================= 2. TOP VIEW
    tx, ty = 163, 18
    ax.add_patch(Rectangle((tx, ty), YC, WW, fc="#f3e6cf", ec=INK, lw=1.6))
    ax.add_patch(Rectangle((tx + TOPL, ty), YC - TOPL, WW, fc="#e2cfae", ec=INK, lw=0.6, hatch="////"))
    ax.plot([tx, tx + TOPL], [ty + WW - 45]*2, color=GHOST, lw=0.6, ls="--")
    for xs in SCREWS:
        ax.add_patch(Circle((tx + xs, ty + WW - 22.5), 1.5, fc="white", ec=ACC, lw=1.0))
        ax.plot([tx + xs - 5, tx + xs + 5], [ty + WW - 22.5]*2, color=ACC, lw=0.6)
        ax.plot([tx + xs]*2, [ty + WW - 27.5, ty + WW - 17.5], color=ACC, lw=0.6)
    ax.text(tx + 4, ty + 22, "N  top view", fontsize=9, weight="bold")
    ax.text(tx + TOPL + (YC - TOPL)/2, ty + 40, "45°\nslope", fontsize=7, ha="center", color="#333",
            bbox=dict(fc="#e2cfae", ec="none", pad=1))
    ax.text(tx + TOPL/2, ty + WW - 47, "over A (45)", fontsize=6.5, color=GHOST, ha="center", va="top")
    for k, xs in enumerate(SCREWS):
        hdim(ax, tx, tx + xs, ty + WW - 33 - 6*k, f"{xs}")
    ax.text(tx, ty + WW + 3, "OUTSIDE edge — over base beam A (B side)", fontsize=7.5, color=ACC, va="bottom")
    ax.text(tx + TOPL/2, ty + 3, "inside edge — overhangs inwards", fontsize=7, color="#555", va="bottom", ha="center")
    vdim(ax, tx - 6, ty, ty + WW - 26, "95", right=False)
    vdim(ax, tx - 6, ty + WW - 22.5, ty + WW, "22", right=False)
    hdim(ax, tx, tx + YC, ty - 9, f"{YC:.0f}  (FRONT end on the left)")

    # ================= 3. how to use
    ax.text(172, 186, "HOW TO USE", fontsize=9, weight="bold", color=ACC, va="top")
    steps = ["Cut out the side view along the thick line.",
             f"Cut a 45×95 piece square to {YC:.0f} long. Lay it flat (45 high).",
             "Trace the side view onto BOTH 45 mm edges, front ends level.",
             "Join the 45° lines across the top; saw the bevel (mitre saw at",
             "    45° bevel, or by hand). Make two — mirror images.",
             "Screws (top view crosses): 3 mm pilot through N into A,",
             "    then a 5×75 exterior screw (30 mm bites into A).",
             f"Through M from its back face: 3 mm pilot and a 5×75, {M_SCREW_UP} up from",
             f"    M's bottom edge and {M_SCREW_END:.0f} from each end of M."]
    num = 0; out = []
    for t in steps:
        if t.startswith("    "): out.append("      " + t.strip())
        else: num += 1; out.append(f"{num}.  {t}")
    ax.text(172, 179, "\n".join(out), fontsize=7.8, va="top", linespacing=1.45)
    if footer: ax.text(W_MM - 8, 3, footer, fontsize=7.5, color="#888", ha="right")
    return fig


if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages("/home/claude/out/seat_block_template.pdf") as pdf:
        pdf.savefig(make_template("Solar ground mount v4 — seat block template"))
    print("ok")
