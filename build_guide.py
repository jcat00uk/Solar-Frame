"""Step-by-step illustrated build guide (A4 landscape PDF) for the gen4 solar ground mount."""
import json, math, pickle, textwrap
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon

OUT = "/home/claude/out"
D = json.load(open(f"{OUT}/dims_v4.json"))
MESH = {n: (np.array(vs, float), np.array(ts, int), tuple(cl))
        for n, vs, ts, cl in pickle.load(open(f"{OUT}/mesh_v4.pkl", "rb"))}
NAMES = list(MESH)

H, T, XI, PIV, YP = D["H"], D["T"], D["XI"], D["PIV"], D["YP"]
CR_H, MR = D["CR_H"], D["MR"]; OM = H/2 + CR_H; PO = OM + MR
TCS = D["tcs"]; c = s = math.cos(math.radians(45))
def P(t, o): return (PIV[0] + c*t - s*o, PIV[1] + s*t + c*o)
def S3(x, t, o): y, z = P(t, o); return np.array([x, y, z], float)

A4 = (11.69, 8.27)
INK, ACC, DIM = "#222222", "#c0392b", "#1f5fa8"
HI = np.array([0.96, 0.47, 0.05])
WOOD = (0.72, 0.55, 0.30); OFFCUT = (0.60, 0.42, 0.26); BLACK = (0.13, 0.13, 0.13)

# ------------------------------------------------------------------ meshes
def prism_x(pts, x0, x1):
    V = np.array([(x0, y, z) for y, z in pts] + [(x1, y, z) for y, z in pts], float)
    F = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6)]
    for i in range(4):
        j = (i + 1) % 4; F += [(i, j, 4+j), (i, 4+j, 4+i)]
    return V, np.array(F)
def box_mesh(x0, x1, y0, y1, z0, z1): return prism_x([(y0, z0), (y1, z0), (y1, z1), (y0, z1)], x0, x1)
def slope_mesh(t0, t1, o0, o1, x0, x1): return prism_x([P(t0, o0), P(t1, o0), P(t1, o1), P(t0, o1)], x0, x1)
def cyl_mesh(p0, p1, r, n=18):
    p0, p1 = np.array(p0, float), np.array(p1, float); a = (p1 - p0) / np.linalg.norm(p1 - p0)
    u = np.cross(a, [0, 0, 1]);  u = np.cross(a, [0, 1, 0]) if np.linalg.norm(u) < 1e-6 else u
    u /= np.linalg.norm(u); v = np.cross(a, u)
    ring = np.array([math.cos(t)*u + math.sin(t)*v for t in np.linspace(0, 2*math.pi, n, endpoint=False)]) * r
    V = np.vstack([p0 + ring, p1 + ring, [p0], [p1]]); F = []
    for i in range(n):
        j = (i + 1) % n; F += [(i, j, n+j), (i, n+j, n+i), (2*n, j, i), (2*n+1, n+i, n+j)]
    return V, np.array(F)

def part(n, xf=None, col=None):
    V, F, cl = MESH[n]
    return (n, xf(V) if xf else V, F, col or cl)
def parts(names, xf=None): return [part(n, xf) for n in names]
def syn(n, VF, col): return (n, VF[0], VF[1], col)
def sel(*pre): return [n for n in NAMES if n.startswith(pre)]

PALLETS = [n for n in NAMES if "pallet" in n]
PACKERS = sel("packer_"); CS_PAL = sel("coach_screw_")
def side(sd):
    core = [f"base_beam_{sd}", f"foot_spacer_{sd}", f"prop_{sd}", f"sloping_rail_{sd}"]
    bolts = [n for n in sel("pivot_bolt", "prop_top_bolt", "foot_bolt") if f"_{sd}_" in n]
    return core + bolts
SIDES = side("L") + side("R")
DIAG = ["rear_diagonal_150x40"] + sel("diag_bolt")
CROSS = sel("cross_rail_"); MINI = sel("mini_rail_")
PANELS = ["panel_1", "panel_2"]; CLAMPS = sel("clamp")
BALLAST = sorted(sel("ballast_"))[:16]

MATS = [syn(f"mat_beam_{sg}", box_mesh(*sorted((sg*(XI-15), sg*(XI+3*T+15))), 0, 1500, -1.9, 0), BLACK) for sg in (-1, 1)]
MATS += [syn(f"mat_pal_{i}", box_mesh(p[0]+10, p[1]-10, p[2]+10, p[3]-10, -1.9, 0), BLACK) for i, p in enumerate((D["big"], D["small"]))]
STOPS = []
for sg in (-1, 1):
    cx = sg*(XI + T/2)
    STOPS.append(syn(f"stop_{sg}", box_mesh(cx-85, cx+85, -150, 0, 0, 40), OFFCUT))
    for k, dx in enumerate((-45, 45)):
        STOPS.append(syn(f"stop_screw_{sg}_{k}", cyl_mesh((cx+dx, -75, 40), (cx+dx, -75, 47), 8), (0.6, 0.6, 0.65)))
CR_SCREWS = []      # M10x130 coach screw + washer: down through E, 60 mm into B
for i, tc in enumerate(TCS):
    for sg in (-1, 1):
        x = sg*(XI + 1.5*T)
        CR_SCREWS.append(syn(f"crs_w_{i}_{sg}", cyl_mesh(S3(x, tc, OM), S3(x, tc, OM+2.5), 12.5), (0.7, 0.7, 0.72)))
        CR_SCREWS.append(syn(f"crs_h_{i}_{sg}", cyl_mesh(S3(x, tc, OM+2.5), S3(x, tc, OM+9.5), 8.5, n=6), (0.6, 0.6, 0.65)))
DPC = [syn(f"dpc_{i}", prism_x([P(tc-T/2-4, OM-1), P(tc+T/2+4, OM-1), P(tc+T/2+4, OM+2), P(tc-T/2-4, OM+2)], -150, 150), BLACK)
       for i, tc in enumerate(TCS)]

# ------------------------------------------------------------------ renderer
LIGHT = np.array([-0.4, -0.6, 0.7]); LIGHT /= np.linalg.norm(LIGHT)
def dil(m, k=1):
    out = m.copy()
    for _ in range(k):
        o = out.copy(); o[1:] |= out[:-1]; o[:-1] |= out[1:]; o[:, 1:] |= out[:, :-1]; o[:, :-1] |= out[:, 1:]; out = o
    return out

def render(ax, items, elev, azim, hl=(), fit=None, fade=0.35, fence=False, gb=None, dpi=200):
    pos = ax.get_position(); W = int(pos.width*A4[0]*dpi); HP = int(pos.height*A4[1]*dpi)
    hl = set(hl)
    allV = np.vstack([it[1] for it in items])
    if gb is None:
        lo, up = allV.min(0), allV.max(0); gb = (lo[0]-250, up[0]+250, lo[1]-250, up[1]+250)
    tris, cols, ids = [], [], []
    g = np.array([[gb[0], gb[2], -2], [gb[1], gb[2], -2], [gb[1], gb[3], -2], [gb[0], gb[3], -2]], float)
    for tri in (g[[0, 1, 2]], g[[0, 2, 3]]): tris.append(tri); cols.append((0.87, 0.87, 0.84)); ids.append(0)
    if fence:
        f = np.array([[gb[0], 1600, 0], [gb[1], 1600, 0], [gb[1], 1600, 1800], [gb[0], 1600, 1800]], float)
        for tri in (f[[0, 1, 2]], f[[0, 2, 3]]): tris.append(tri); cols.append((0.62, 0.49, 0.38)); ids.append(1)
    names = ["__g", "__f"]; cent = {}
    for k, (n, V, F, cl) in enumerate(items):
        cl = np.array(cl, float)
        if hl and n not in hl and fade: cl = cl*(1-fade) + fade
        names.append(n); cent[n] = V.mean(0)
        for t in F: tris.append(V[t]); cols.append(cl); ids.append(k+2)
    T3 = np.array(tris); C = np.array(cols, float); I = np.array(ids)
    el, az = math.radians(elev), math.radians(azim)
    d = np.array([math.cos(el)*math.cos(az), math.cos(el)*math.sin(az), math.sin(el)])
    r = np.cross([0, 0, 1], d); r /= np.linalg.norm(r); u = np.cross(d, r)
    pts = np.asarray(fit, float) if fit is not None else np.vstack([allV, g])
    fx, fy = pts @ r, pts @ u
    m = 20; xmin, xmax, ymin, ymax = fx.min(), fx.max(), fy.min(), fy.max()
    sc = min((W-2*m)/(xmax-xmin), (HP-2*m)/(ymax-ymin))
    ox = (W - (xmax-xmin)*sc)/2; oy = (HP - (ymax-ymin)*sc)/2
    X = (T3 @ r - xmin)*sc + ox; Y = (ymax - T3 @ u)*sc + oy; Z = T3 @ d
    nrm = np.cross(T3[:, 1]-T3[:, 0], T3[:, 2]-T3[:, 0]); ln = np.linalg.norm(nrm, axis=1); ln[ln == 0] = 1
    shade = 0.55 + 0.45*np.abs((nrm/ln[:, None]) @ LIGHT)
    img = np.ones((HP, W, 3)); zb = np.full((HP, W), -np.inf); idb = np.full((HP, W), -1)
    for i in range(len(T3)):
        x, y, z = X[i], Y[i], Z[i]
        x0, x1 = max(int(x.min()), 0), min(int(x.max())+1, W-1)
        y0, y1 = max(int(y.min()), 0), min(int(y.max())+1, HP-1)
        if x1 < x0 or y1 < y0: continue
        den = (y[1]-y[2])*(x[0]-x[2]) + (x[2]-x[1])*(y[0]-y[2])
        if abs(den) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(x0, x1+1)+0.5, np.arange(y0, y1+1)+0.5)
        l0 = ((y[1]-y[2])*(gx-x[2]) + (x[2]-x[1])*(gy-y[2]))/den
        l1 = ((y[2]-y[0])*(gx-x[2]) + (x[0]-x[2])*(gy-y[2]))/den
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not inside.any(): continue
        zz = l0*z[0] + l1*z[1] + l2*z[2]
        sub = zb[y0:y1+1, x0:x1+1]; upd = inside & (zz > sub); sub[upd] = zz[upd]
        img[y0:y1+1, x0:x1+1][upd] = np.clip(C[i]*shade[i], 0, 1)
        idb[y0:y1+1, x0:x1+1][upd] = I[i]
    edge = np.zeros((HP, W), bool)
    edge[:, 1:] |= idb[:, 1:] != idb[:, :-1]; edge[1:, :] |= idb[1:, :] != idb[:-1, :]
    img[edge] *= 0.45
    if hl:
        hid = [k for k, n in enumerate(names) if n in hl]
        mk = np.isin(idb, hid)
        band = dil(mk, 2) & ~(~dil(~mk, 1))
        img[band] = HI
    img[idb == -1] = 1.0
    ax.imshow(img, interpolation="antialiased"); ax.set_axis_off(); ax.set_autoscale_on(False)
    ax._proj = lambda p: (((np.asarray(p, float) @ r) - xmin)*sc + ox, (ymax - np.asarray(p, float) @ u)*sc + oy)
    ax._cent = cent

def note(fig, ax, p, text, dxy, kind="tag", fs=8.5):
    ax.apply_aspect()
    if isinstance(p, str): p = ax._cent[p]
    X, Y = ax._proj(p)
    fx, fy = fig.transFigure.inverted().transform(ax.transData.transform((X, Y)))
    tx, ty = fx + dxy[0], fy + dxy[1]
    fig.add_artist(plt.Line2D([fx, tx], [fy, ty], color=ACC, lw=0.9, zorder=29))
    fig.add_artist(plt.Line2D([fx], [fy], marker="o", ms=2.5, color=ACC, zorder=29))
    if kind == "tag":
        fig.text(tx, ty, text, fontsize=9.5, weight="bold", color="white", ha="center", va="center",
                 bbox=dict(boxstyle="circle,pad=0.28", fc=ACC, ec="none"), zorder=30)
    else:
        fig.text(tx, ty, text, fontsize=fs, color=INK, ha="center", va="center", zorder=30,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=ACC, lw=0.8))

def line3(ax, p0, p1, **kw):
    a, b = ax._proj(p0), ax._proj(p1); ax.plot([a[0], b[0]], [a[1], b[1]], **kw)

# ------------------------------------------------------------------ page + text helpers
pages = []; NSTEP = 12
STEP_TITLES = ["Cut the timber", "Mark and drill", "Build the two side frames", "Mats and pallets",
               "Stand the frames up and fix to the pallets", "Rear diagonal brace",
               "Cross rails", "Mini-rails and DPC strips", "Bottom ledge", "Ballast", "Fit the panels", "Final checks and upkeep"]
STEP_PAGE = [i + 2 for i in range(1, NSTEP + 1)]

def page(title, step=None, sub=""):
    fig = plt.figure(figsize=A4)
    if step:
        fig.text(0.04, 0.955, f"STEP {step}", fontsize=11, weight="bold", color=ACC, va="top")
        fig.text(0.04, 0.925, title, fontsize=19, weight="bold", color=INK, va="top")
        for i in range(1, NSTEP+1):
            done, cur = i < step, i == step
            fig.text(0.57 + i*0.028, 0.935, str(i), fontsize=7.5, ha="center", va="center",
                     color="white" if (cur or done) else "#999", weight="bold",
                     bbox=dict(boxstyle="circle,pad=0.35", fc=ACC if cur else ("#bbb" if done else "white"),
                               ec=ACC if cur else "#bbb", lw=0.8))
    else:
        fig.text(0.04, 0.945, title, fontsize=21, weight="bold", color=INK, va="top")
        if sub: fig.text(0.04, 0.9, sub, fontsize=10.5, color="#555", va="top")
    fig.add_artist(plt.Line2D([0.04, 0.96], [0.875, 0.875], color="#bbb", lw=0.8))
    fig.text(0.96, 0.018, f"Solar ground mount v4 — build guide  ·  left = West, right = East (seen from the front)  ·  page {len(pages)+1}",
             ha="right", fontsize=7.5, color="#888")
    pages.append(fig); return fig

LH = lambda fs: fs*1.32/72/A4[1]
def _h(fig, t):
    bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
    return bb.height / (fig.get_figheight()*fig.dpi)
class Col:
    def __init__(self, fig, x=0.635, y=0.845, w=0.33, chars=56, fs=9.0):
        self.f, self.x, self.y, self.w, self.ch, self.fs = fig, x, y, w, chars, fs
    def gap(self, g=0.012): self.y -= g
    def head(self, t, col=ACC):
        tt = self.f.text(self.x, self.y, t, fontsize=9, weight="bold", color=col, va="top"); self.y -= _h(self.f, tt) + 0.008
    def box(self, title, lines, fc, ec, bullet="•"):
        fs = self.fs - 0.4; wrapped = []
        for ln in lines:
            w = textwrap.wrap(ln, self.ch - 3) or [""]
            wrapped += [(bullet + "  " if bullet else "") + w[0]] + [("     " if bullet else "") + x for x in w[1:]]
        y0 = self.y
        t1 = self.f.text(self.x, y0 - 0.007, title, fontsize=fs, weight="bold", color=INK, va="top")
        h1 = _h(self.f, t1)
        t2 = self.f.text(self.x, y0 - 0.007 - h1 - 0.005, "\n".join(wrapped), fontsize=fs, va="top", color=INK, linespacing=1.3)
        h = 0.007 + h1 + 0.005 + _h(self.f, t2) + 0.009
        self.f.add_artist(FancyBboxPatch((self.x - 0.007, y0 - h), self.w + 0.008, h, boxstyle="round,pad=0.002",
                                         transform=self.f.transFigure, fc=fc, ec=ec, lw=0.8, zorder=0))
        self.y = y0 - h - 0.013
    def steps(self, items):
        for i, t in enumerate(items, 1):
            w = textwrap.wrap(t, self.ch - 2)
            self.f.text(self.x, self.y, str(i), fontsize=self.fs, weight="bold", color=ACC, va="top")
            tt = self.f.text(self.x + 0.02, self.y, "\n".join(w), fontsize=self.fs, color=INK, va="top", linespacing=1.3)
            self.y -= _h(self.f, tt) + 0.009

def step_text(fig, need=None, steps=(), check=None, tip=None, warn=None, fs=9.0):
    col = Col(fig, fs=fs)
    if need: col.box("YOU NEED", need, "#f2f2f2", "#cccccc")
    col.steps(steps); col.gap(0.004)
    if check: col.box("CHECK", check, "#eaf6ea", "#7bb77b", bullet="□")
    if tip: col.box("TIP", [tip], "#e8f0fa", "#7fa4d4", bullet="")
    if warn: col.box("CAREFUL", [warn], "#fff4e0", "#e0a43c", bullet="")
    return col

def caption(fig, ax, text):
    p = ax.get_position(); fig.text(p.x0 + 0.006, p.y1 - 0.006, text, fontsize=8.5, color="#333", va="top", style="italic",
                                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5), zorder=25)

MAIN = [0.02, 0.06, 0.59, 0.8]
TOP = [0.02, 0.36, 0.59, 0.5]
DET = [0.04, 0.045, 0.5, 0.3]

# ================================================================== COVER
ALL = (MATS + parts(PALLETS + PACKERS + CS_PAL + SIDES + DIAG + CROSS + MINI + PANELS + CLAMPS + BALLAST
                    + ["bottom_ledge", "seat_block_L", "seat_block_R"])
       + CR_SCREWS + DPC)
fig = page("Solar ground mount — step-by-step build guide",
           sub="Two 500 W panels  ·  fixed 45°  ·  facing south  ·  on two pallets  ·  use with the measured drawings in the build pack")
ax = fig.add_axes([0.0, 0.04, 0.6, 0.82]); render(ax, ALL, 20, -128, fence=True)
col = Col(fig, y=0.84)
col.head("CONTENTS", INK)
fig.text(col.x, col.y, "\n".join([f"Step {i:>2}   {t}" for i, t in enumerate(STEP_TITLES, 1)] + ["Template   Seat block N (full size)"]), fontsize=9, va="top", linespacing=1.45)
fig.text(col.x + 0.29, col.y, "\n".join([str(p) for p in STEP_PAGE] + [str(STEP_PAGE[-1] + 1)]), fontsize=9, va="top", linespacing=1.45, ha="right", color="#666")
col.y -= (NSTEP+1)*LH(9)*1.45/1.32*1.17 + 0.035
col.box("BEFORE YOU START", [
    "Left and right always mean as seen standing in FRONT of the panels (south side): left = West, right = East.",
    "New parts in each picture are outlined in orange. Parts already fitted are shown faded.",
    "Two people for anything over head height and for the panels (28 kg each, and they catch the wind like a sail).",
    "Don't fit panels on a windy day. Panels make electricity whenever light hits them — keep the connectors capped.",
    "Wear glasses when drilling and gloves/mask when cutting treated timber. Don't burn the offcuts.",
], "#fff4e0", "#e0a43c")

# ================================================================== NEED page
fig = page("What you need", sub="Tick things off as you gather them. Letters are used on every page.")
def table(x, y, title, rows, widths, fs=8.6):
    fig.text(x, y, title, fontsize=10.5, weight="bold", va="top"); y -= 0.035
    for r in rows:
        xx = x
        for cell, w in zip(r, widths):
            fig.text(xx, y, cell, fontsize=fs, va="top"); xx += w
        y -= LH(fs)*1.35
    return y
table(0.04, 0.84, "Timber and parts", [
    ("□", "A", "Base beam", "2", "45×95 × 1495"),
    ("□", "B", "Sloping rail", "2", "45×95 × 1786"),
    ("□", "C", "Prop", "2", "45×95 × 1315"),
    ("□", "D", "Foot spacer", "2", "45×95 × 95"),
    ("□", "E", "Cross rail", "2", "45×70 × 2400"),
    ("□", "F", "Rear diagonal", "1", "45×95 × 2400"),
    ("□", "J", "Packer", "4", "22 thick, 100×78"),
    ("□", "G", "Big pallet", "1", "980 × 1200"),
    ("□", "H", "Small pallet", "1", "880 × 900"),
    ("□", "K", "Mini-rail", "6", "from your kit"),
    ("□", "L", "Panel", "2", "1961 × 1134"),
    ("□", "", "Panel clamps", "6", "kit: 4 end, 2 middle"),
    ("□", "M", "Bottom ledge", "1", "45×120 × 2400"),
    ("□", "N", "Seat block", "2", "45×95 × 128, bevelled"),
], (0.02, 0.025, 0.11, 0.03, 0.12))
table(0.38, 0.84, "Fixings", [
    ("□", "M10 × 110 coach bolt", "6", "step 3"),
    ("□", "M10 × 160 coach bolt", "6", "steps 3, 6"),
    ("□", "M10 nyloc nut", "12", "steps 3, 6"),
    ("□", "M10 × 130 coach screw", "8", "steps 5, 7"),
    ("□", "M10 penny washer", "20", "all"),
    ("□", "Ground fixing (recommended)", "", "step 10"),
    ("□", "4.5 × 50 decking screw", "12", "step 8"),
    ("□", "5 × 75 exterior screw", "6", "step 9"),
    ("□", "DPC strip 100 mm", "0.6 m", "step 8"),
    ("□", "Staples / clouts", "few", "step 8"),
    ("□", "Rubber matting", "strips", "step 4"),
    ("□", "End-grain preservative", "", "step 1"),
    ("□", "Ballast ~300–510 kg", "", "step 10"),
], (0.02, 0.15, 0.04, 0.06))
table(0.7, 0.84, "Tools", [
    ("□", "Tape, pencil, square"), ("□", "Saw (hand or circular)"), ("□", "Drill / driver"),
    ("□", "10 mm wood bit, 150 mm+ long"), ("□", "6 mm and 3 mm wood bits"),
    ("□", "Masonry bit (if fixing to the ground)"),
    ("□", "17 mm socket or spanner"), ("□", "Hammer"), ("□", "2 clamps"),
    ("□", "Angle finder or phone level app"), ("□", "Spirit level"), ("□", "Staple gun"),
    ("□", "Driver bits for the screws"), ("□", "3 blocks or bricks"), ("□", "Glasses, gloves, helper"),
], (0.02, 0.2))
fig.text(0.04, 0.1, "Washers go under every nut (12) and every coach-screw head (8) — 2 packs of 10. Coach-bolt heads don't need one.\n"
         "The coach-bolt packs come with plain nuts — use the nyloc nuts instead; keep the plain ones as spares.",
         fontsize=8.8, va="top", color="#444")

# ================================================================== STEP 1 cut
fig = page(STEP_TITLES[0], 1)
ax = fig.add_axes([0.04, 0.38, 0.55, 0.46]); ax.axis("off"); ax.set_xlim(-50, 4300); ax.set_ylim(-200, 1560)
stock = [("3.0 m 45×95", 3000, [("A 1495", 1495), ("A 1495", 1495)]),
         ("3.6 m 45×95", 3600, [("B 1786", 1786), ("B 1786", 1786)]),
         ("3.0 m 45×95", 3000, [("C 1315", 1315), ("C 1315", 1315), ("D", 95), ("D", 95)]),
         ("2.4 m 45×70", 2400, [("E 2400", 2400)]), ("2.4 m 45×70", 2400, [("E 2400", 2400)]),
         ("2.4 m 45×120", 2400, [("M 2400", 2400)]),
         ("3.0 m 45×95", 3000, [("F 2400", 2400), ("N", 128), ("N", 128)])]
for i, (nm, L, cuts) in enumerate(stock):
    yy = 1360 - i*230
    ax.add_patch(Rectangle((0, yy), L, 120, fc="#eee", ec=INK, lw=0.6))
    x = 0
    for lab, cl in cuts:
        if lab.startswith("F"):
            sh = 95*math.tan(math.radians(D["a_diag"]))*120/95
            ax.add_patch(Polygon([(x, yy), (x+cl, yy), (x+cl+sh, yy+120), (x+sh, yy+120)], fc="#a97850", ec=INK, lw=0.6))
        else:
            ax.add_patch(Rectangle((x, yy), cl, 120, fc="#d9b27c" if lab[0] != "S" else "#b98a52", ec=INK, lw=0.6))
        ax.text(x+cl/2 + (25 if lab.startswith("F") else 0), yy+60, lab, ha="center", va="center", fontsize=7.5); x += cl + 3
    ax.text(L+80, yy+60, nm, fontsize=8, va="center")
ax.text(0, 1530, "Cutting plan — each bar is one length of timber", fontsize=10, weight="bold")
ax2 = fig.add_axes([0.04, 0.06, 0.26, 0.28]); ax2.axis("off"); ax2.set_aspect("equal"); ax2.set_xlim(-40, 420); ax2.set_ylim(-60, 260)
ax2.add_patch(Polygon([(40, 0), (400, 0), (400, 95), (0, 95), (0, 40)], fc="#d9b27c", ec=INK))
ax2.add_patch(Polygon([(0, 0), (40, 0), (0, 40)], fc="white", ec=ACC, ls="--"))
ax2.text(0, 130, "B — chamfer one corner", fontsize=9, weight="bold")
ax2.text(60, 20, "40 × 40 off the bottom\nfront corner (both rails)", fontsize=7.5, va="bottom")
ax3 = fig.add_axes([0.32, 0.06, 0.27, 0.28]); ax3.axis("off"); ax3.set_aspect("equal"); ax3.set_xlim(-40, 440); ax3.set_ylim(-60, 260)
sh = 150*math.tan(math.radians(D["a_diag"]))
ax3.add_patch(Polygon([(0, 0), (380, 0), (380+sh, 150), (sh, 150)], fc="#a97850", ec=INK))
ax3.plot([0, 0], [0, 150], color=ACC, ls="--", lw=0.8)
ax3.text(4, 160, f"{D['a_diag']:.0f}°", color=ACC, fontsize=9, weight="bold")
ax3.text(0, 205, "F — both ends angled", fontsize=9, weight="bold")
ax3.text(60, 60, f"ends cut {D['a_diag']:.0f}° off square,\nparallel to each other", fontsize=7.5)
step_text(fig, need=["Timber from the list on page 2", "Saw, tape, square, pencil", "End-grain preservative + brush"], steps=[
    "Check your timber is straight. Put the best two 45×95 lengths aside for the base beams A.",
    "Mark every piece from a square end, following the cutting plan. Cut square unless shown otherwise.",
    "Cut the pairs (A, B, C) and stand each pair side by side — they must be the same length.",
    "B: take a 40 × 40 triangle off the bottom corner at one end. That end is the FRONT (low) end.",
    f"F: from the last 3.0 m 45×95, cut 2400 along its long edge, both ends {D['a_diag']:.0f}° off square and parallel.",
    "D: cut two 95 mm spacers from the C offcut. M: the 2.4 m 45×120 is used whole.",
    "N: cut two 128 mm pieces from what's left of F's length and bevel one end of each at 45° using the full-size template on the last page.",
    "J: from any 22 mm board (a spare pallet board or fence board) cut four 100 × 78 packers.",
    "Brush preservative onto every cut end and let it dry.",
], tip="Write each piece's letter on it in pencil.")

# ================================================================== STEP 2 drill
fig = page(STEP_TITLES[1], 2)
ax = fig.add_axes([0.04, 0.07, 0.56, 0.77]); ax.axis("off"); ax.set_xlim(-160, 2000); ax.set_ylim(-80, 2300)
def drill_part(y0, L, title, holes, later=(), front="FRONT", dims=(), marks=()):
    ax.add_patch(Rectangle((0, y0), L, 140, fc="#d9b27c", ec=INK, lw=0.8))
    ax.text(0, y0+190, title, fontsize=9.5, weight="bold")
    ax.text(-25, y0+70, front, rotation=90, fontsize=7, color=ACC, ha="right", va="center")
    for x, yy in holes: ax.plot(x, y0 + yy*140/95, "o", ms=6.5, mfc="white", mec=INK, mew=1.1)
    for k, (x, yy, lab) in enumerate(later):
        ax.add_patch(plt.Circle((x, y0 + yy*140/95), 16, fc="none", ec=ACC, lw=1.2, ls=(0, (2, 1.5)), zorder=5))
        if lab: ax.text(x, y0 + 150, lab, fontsize=6.8, color="white", weight="bold", ha="center", va="bottom",
                        bbox=dict(fc=ACC, ec="none", boxstyle="round,pad=0.2"), zorder=6)
    for x, lab in marks:
        ax.plot([x, x], [y0 - 8, y0 + 148], color=ACC, lw=1, ls=":", zorder=4)
        ax.text(x, y0 + 70, lab, fontsize=6.3, color=ACC, ha="center", va="center", zorder=6,
                bbox=dict(fc="white", ec=ACC, lw=0.5, boxstyle="round,pad=0.15"))
    for k, (x, lab) in enumerate(dims):
        yy = y0 - 45 - 55*k
        ax.annotate("", (0, yy), (x, yy), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8, shrinkA=0, shrinkB=0))
        ax.plot([x, x], [yy-10, y0], color=DIM, lw=0.4)
        ax.text(x+12, yy, lab, fontsize=7.5, color=DIM, va="center")
TA = D["tA"]; t1, t2 = 60 + TA - 21.2, 60 + TA + 21.2
cr1, cr2 = [round(60 + t) for t in D["tcs"]]
drill_part(1900, 1495, "A  Base beam ×2  —  drill 3 holes now", [(150, 50), (1275, 47.5), (1325, 47.5)],
           dims=[(150, "150 (50 up)"), (1275, "1275 (47 up)"), (1325, "1325 (47 up)")])
drill_part(1300, D["RAIL"], "B  Sloping rail ×2  —  drill the pivot hole only", [(60, 47.5)],
           later=[(t1, 26, "LATER — step 3"), (t2, 69, "")], marks=[(cr1, f"mark only {cr1}"), (cr2, f"mark only {cr2}")],
           dims=[(60, "60, centred"), (t1, f"{t1:.0f}"), (t2, f"{t2:.0f}")])
drill_part(700, D["PROP_LEN"], "C  Prop ×2  —  drill the foot pair only", [(47.5, 22.5), (47.5, 72.5)],
           later=[(D["zA"]-30, 47.5, "LATER — step 3"), (D["zA"]+30, 47.5, "")], front="FOOT",
           marks=[(D["Z1"], "LATER step 6"), (D["Z2"], "LATER step 6")],
           dims=[(47.5, "47 from foot, 22 & 72 across"), (D["zA"]-30, f"{D['zA']-30:.0f}"), (D["zA"]+30, f"{D['zA']+30:.0f}")])
ax.add_patch(Rectangle((0, 150), 140, 140, fc="#e8cfa5", ec=INK, lw=0.8))
for x in (22.5, 72.5): ax.plot(x*140/95, 150 + 47.5*140/95, "o", ms=6.5, mfc="white", mec=INK, mew=1.1)
ax.text(0, 340, "D  Foot spacer ×2  —  drill 2 holes now", fontsize=9.5, weight="bold")
ax.text(180, 220, "47 up, 22 and 72 from one edge\n(same pattern as the foot of C)", fontsize=7.5, va="center")
ax.plot(1000, 300, "o", ms=6.5, mfc="white", mec=INK, mew=1.1); ax.text(1040, 300, "= drill now, on the bench", fontsize=8, va="center")
ax.add_patch(plt.Circle((1000, 200), 16, fc="none", ec=ACC, lw=1.2, ls=(0, (2, 1.5)))); ax.text(1040, 200, "= DON'T drill yet — in place later", fontsize=8, va="center", color=ACC, weight="bold")
ax.plot([1000, 1000], [60, 130], color=ACC, lw=1, ls=":"); ax.text(1040, 95, "= pencil mark only", fontsize=8, va="center", color=ACC)
ax.text(1000, 0, "Not to scale across the width. Full drawings: build pack.", fontsize=7.5, color="#666", va="center")
step_text(fig, fs=8.4, need=["Pieces A, B, C, D", "Drill, 10 mm wood bit, square, tape, clamps"], steps=[
    "Mark the hole centres, measuring from the end marked FRONT (A, B) or FOOT (C).",
    "Drill ONLY the solid black holes: 10 mm, square to the face. Clamp each pair together and drill both in one go.",
    "Mark the red dashed holes and the dotted lines in pencil — but don't drill them yet.",
], warn="DON'T DRILL YET — these are drilled in place so they line up: "
        "B + C top pair (step 3, through both together) · C diagonal + F (step 6, with F clamped on) · "
        "A to pallet (step 5) · "
        f"cross rails (step 7: 10 mm through E, then only a 6 mm pilot into B at {cr1} / {cr2} — never 10 mm) · "
        "mini-rails (step 8) · seat blocks and M (step 9) · ground fixings (step 10).",
   tip="Put a scrap of wood under the exit side and drill into it — the hole comes out clean instead of splintering.")

# ================================================================== STEP 3 side frames (flat)
BLK = 100; X0 = 0
def flat(off):
    def f(V):
        V = V.copy(); V[:, 0] -= off
        return np.c_[V[:, 2] + X0, V[:, 1], -V[:, 0] - XI + BLK]
    return f
SL = side("L")
def layer(n):
    if n.startswith(("prop_L",)) and not n.startswith("prop_top"): return 2
    if n.startswith(("foot_spacer", "sloping_rail")): return 1
    if n.startswith(("prop_top_bolt", "foot_bolt")): return 4
    if n.startswith("pivot_bolt"): return 3
    return 0
EXP = {0: 0, 1: 75, 2: 150, 3: 300, 4: 330}
BENCH = [syn("blk0", box_mesh(-170, 270, 120, 335, 0, BLK), (0.62, 0.62, 0.62)),
         syn("blk1", box_mesh(-170, 270, 1150, 1365, 0, BLK), (0.62, 0.62, 0.62)),
         syn("blk2", box_mesh(930, 1110, 1120, 1330, 0, BLK + 45), (0.62, 0.62, 0.62))]
fig = page(STEP_TITLES[2], 3)
ax = fig.add_axes([0.0, 0.42, 0.33, 0.44])
UEXP = {0: 0, 1: 260, 2: 520, 3: 760, 4: 900}
def ushift(off):
    def f(V): V = V.copy(); V[:, 0] -= off; return V
    return f
exp_items = [part(n, ushift(UEXP[layer(n)])) for n in SL if not n.endswith("_nut")]
render(ax, exp_items, 20, -128, hl=[n for n in SL], fade=0)
caption(fig, ax, "How the layers stack (left frame, exploded)")
for n in SL:
    if n.endswith("_shank"):
        Vb = MESH[n][0]; cy, cz = Vb[:, 1].mean(), Vb[:, 2].mean()
        line3(ax, (-XI, cy, cz), (-(XI + 3*T) - UEXP[layer(n)], cy, cz), color=DIM, lw=0.7, ls="--")
note(fig, ax, "base_beam_L", "A", (0.04, -0.05)); note(fig, ax, "foot_spacer_L", "D", (0.03, -0.06))
note(fig, ax, "sloping_rail_L", "B", (0.04, 0.04)); note(fig, ax, "prop_L", "C", (0.03, 0.05))
note(fig, ax, "foot_bolt0_L_head", "M10×160 ×2", (0.02, -0.07), "box")
note(fig, ax, "pivot_bolt_L_head", "M10×110", (0.06, -0.03), "box")
note(fig, ax, "prop_top_bolt1_L_head", "M10×110 ×2", (0.06, 0.03), "box")
ax = fig.add_axes([0.31, 0.42, 0.31, 0.44])
render(ax, BENCH + parts(SL, flat(0)), 40, 180, hl=(), fade=0)
caption(fig, ax, "Build it flat on blocks, outside face up")
pv = flat(0)(np.array([[-(XI+1.5*T), PIV[0], PIV[1]]]))[0]
note(fig, ax, pv, "45°", (0.05, -0.05), "box")
ft = flat(0)(np.array([[-(XI+2.5*T), YP - H/2, H]]))[0]
note(fig, ax, ft, "90°", (-0.02, -0.08), "box")
tp = flat(0)(np.array([[-(XI+2.5*T), YP + H/2, D["PROP_LEN"]]]))[0]
note(fig, ax, tp, "top of C flush with\ntop edge of B", (0.1, 0.0), "box")
fr = flat(0)(np.array([[-(XI+T/2), 0, H/2]]))[0]
note(fig, ax, fr, "FRONT end\non your right", (0.03, -0.07), "box")
ax = fig.add_axes([0.04, 0.04, 0.56, 0.34]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 4.2)
lay = [("C  prop", 2.9, "#d9b27c"), ("D spacer / B rail", 2.1, "#e8cfa5"), ("A  beam", 1.3, "#d9b27c")]
for lab, yy, fc in lay:
    ax.add_patch(Rectangle((1.2, yy), 3.2, 0.7, fc=fc, ec=INK, lw=0.8)); ax.text(4.6, yy+0.35, lab, fontsize=8.5, va="center")
ax.add_patch(Rectangle((2.6, 0.8), 0.25, 3.1, fc="#bbb", ec=INK, lw=0.6))
ax.add_patch(Polygon([(2.35, 3.6), (3.1, 3.6), (2.95, 3.9), (2.5, 3.9)], fc="#999", ec=INK, lw=0.6))
ax.add_patch(Rectangle((2.25, 1.05), 0.95, 0.12, fc="#ccc", ec=INK, lw=0.5)); ax.add_patch(Rectangle((2.4, 0.75), 0.65, 0.3, fc="#888", ec=INK, lw=0.5))
ax.text(3.3, 3.95, "coach bolt head — outside", fontsize=8, va="center")
ax.text(3.3, 0.9, "penny washer + nyloc nut — inside (underneath)", fontsize=8, va="center")
ax.text(1.2, 0.3, "Every bolt: head on the outside face, washer and nut on the inside face.", fontsize=8.5, weight="bold")
ax.text(6.8, 3.6, "Mirror pair", fontsize=9.5, weight="bold")
ax.text(6.8, 3.4, "Both frames are built outside face up, with the\nprop pointing away from you:\n\n"
        "   LEFT (West) frame  → front end on your RIGHT\n   RIGHT (East) frame → front end on your LEFT\n\n"
        "That way the props end up on the outside of\nboth frames when you stand them up.", fontsize=8.2, va="top")
step_text(fig, fs=8.6, need=["A, B, C, D (one of each per frame)", "Per frame: 2 × M10×160, 3 × M10×110, 5 washers, 5 nyloc nuts",
                     "3 blocks or bricks, square, angle finder, 2 clamps, hammer, 17 mm socket"], steps=[
    "Set 3 blocks on flat ground. Lay A on them on its side (inside face down) with the FRONT end on your right. The prop will point away from you.",
    "Stack D on A over the foot holes, then C on top, square to A. Tap 2 × M10×160 down through C, D and A until the necks bite. Washer + nyloc underneath, finger tight.",
    "Lay B on A at the front (same layer as D) and bolt through the pivot holes with 1 × M10×110, finger tight.",
    "Swing B up so it lies under the top of C. Set C square to A, then adjust until the top of C is flush with the top edge of B and B is at 45° to A.",
    "Clamp B to C. Drill both top holes through B and C together, then fit 2 × M10×110.",
    "Tighten all 5 nuts: snug, plus a quarter turn — the washer should just start to bite.",
    "Build the right (East) frame the same way, but with the front end on your LEFT.",
], warn="The nuts end up next to the pallets later, where a spanner won't fit — so tighten everything now.")

# ================================================================== upright steps
def view(step, items, hl, elev, azim, fence=False, det=None, notes=(), dnotes=(), cap=None, dcap=None, text=None):
    fig = page(STEP_TITLES[step-1], step)
    ax = fig.add_axes(TOP if det else MAIN); render(ax, items, elev, azim, hl=hl, fence=fence)
    if cap: caption(fig, ax, cap)
    for n in notes: note(fig, ax, *n)
    if det:
        ax2 = fig.add_axes(DET); render(ax2, det[0], det[1], det[2], hl=hl, fit=det[3], fence=det[4] if len(det) > 4 else False)
        ax2.add_patch(Rectangle((0, 0), 1, 1, transform=ax2.transAxes, fill=False, ec="#999", lw=0.8))
        if dcap: caption(fig, ax2, dcap)
        for n in dnotes: note(fig, ax2, *n)
    step_text(fig, **text)
    return fig

def around(p, dx, dy, dz):
    p = np.asarray(p, float)
    return np.array([p + np.array([sx*dx, sy*dy, sz*dz]) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])

B4 = MATS + parts(PALLETS)
view(4, B4, [m[0] for m in MATS] + PALLETS, 28, -125, fence=True,
     notes=[("pallet_big_deck_3", "G", (0.0, 0.08)), ("pallet_small_deck_3", "H", (0.05, 0.08)),
            ("mat_beam_-1", "rubber strip", (-0.08, -0.06), "box"), ("mat_beam_1", "rubber strip", (0.05, -0.08), "box")],
     cap="View from the front-left",
     text=dict(need=["Pallets G and H", "Rubber matting", "Tape measure"], steps=[
         "Sweep the paving and check the space: the finished frame is 2.4 m wide and 1.5 m deep, with its back 100 mm from the fence.",
         "Lay a strip of rubber about 160 wide and 1.5 m long where each base beam will stand: the strips' inside edges 1904 apart.",
         "Lay rubber under the pallets' bottom boards.",
         "Put the big pallet G on the left (West) and the small pallet H on the right (East), side by side and touching, back edges in one straight line 100 mm from the fence.",
         "The big pallet's 1200 side runs front-to-back; the small one's 900 side runs front-to-back.",
     ], check=["Width across both pallets about 1860", "Back edges in a straight line, 100 mm from the fence"],
     tip="If the paving slopes sideways, pack under the low pallet so the decks are level side to side. A slight fall front-to-back doesn't matter."))

B5 = B4 + parts(PACKERS + CS_PAL + SIDES)
view(5, B5, PACKERS + CS_PAL + SIDES, 24, -128,
     det=(B5, 18, 112, around((-985, 1440, 70), 140, 80, 90)),
     notes=[("base_beam_L", "A", (-0.02, -0.07)), ("prop_L", "C", (-0.05, 0.03)), ("sloping_rail_R", "B", (0.05, 0.03)),
            ("prop_R", "C", (0.05, 0.0))],
     dnotes=[("packer_L_1450", "J packer", (0.08, -0.04), "box"), ("coach_screw_L_1450", "M10×130 coach screw\n+ washer", (-0.1, 0.06), "box"),
             ("pallet_big_block_02", "pallet block", (0.1, 0.07), "box")],
     cap="Both side frames standing, fixed to the pallets", dcap="Detail: back end of the left beam, from behind",
     text=dict(need=["Both side frames", "4 packers J", "4 × M10×130 coach screws + 4 washers", "10 mm and 6 mm bits, 17 mm socket", "A helper"], steps=[
         "Stand the left frame on its rubber strip, props on the outside, with the back end of the beam level with the back of the pallets.",
         "Slide packers J into the gap between the beam and the pallet's outside blocks: left beam at 350 and 1450 from its front end. Trim them if the gap is tighter than 22 mm.",
         "Drill 10 mm through the beam and packer, 61 up (middle of the block). Then a 6 mm pilot 60 mm into the block.",
         "Fit an M10×130 coach screw with a washer and tighten with the 17 mm socket. Do both.",
         "Repeat on the right: packers at 650 and 1450 from the front end of the right beam.",
     ], check=["Beams parallel: 1904 between their inside faces at the front and the back",
               "Base square: front of one beam to back of the other is the same both ways (±5 mm)"],
     warn="The frames are top-heavy until the diagonal is on. Have a helper hold them, or tack a temporary batten across the tops of the props."))

B6 = B5 + parts(DIAG)
view(6, B6, DIAG, 18, 78,
     det=(B6, 12, 72, around((-1060, 1390, 520), 170, 120, 150)),
     notes=[("rear_diagonal_150x40", "F", (0.0, 0.08)), ("prop_L", "West prop\n(low end, 520 up)", (0.07, -0.02), "box"),
            ("prop_R", "East prop\n(high end, 1050 up)", (-0.08, 0.05), "box")],
     dnotes=[("diag_bolt_L_head", "M10×160 from the back,\nnut on the front of the prop", (0.13, 0.05), "box")],
     cap="View from behind (fence side) — West is on the RIGHT here", dcap="Detail: low (West) end",
     text=dict(need=["Diagonal F", "2 × M10×160, 2 washers, 2 nyloc nuts", "10 mm bit at least 150 mm long", "Clamps, tape, a helper"], steps=[
         "From behind, hold F flat against the back faces of both props. The low end goes on the West prop (the LEFT one when you stand in front).",
         "Line it up: hole centres on the prop centre lines, 520 up on the West prop and 1050 up on the East prop. The ends should stand vertical and overhang each prop by about 80.",
         "Square the frame first: measure corner to corner across the back both ways and push the tops of the props sideways until the two measurements match. Then clamp F.",
         "Drill 10 mm straight through F and the prop (140 mm) at each end, keeping the drill level.",
         "Coach bolt from the back, washer and nyloc nut on the front face of the prop. Tighten both.",
     ], check=["Props vertical side to side (spirit level)", "Frame doesn't rock when you push the top of a prop"],
     tip="Drill a little way, check the drill is still level from the side, then carry on. If your bit is too short, drill F first, then use its holes to start the holes in the props."))

B7 = B6
B8 = B7 + parts(CROSS) + CR_SCREWS
c0 = S3(-(XI+1.5*T), TCS[0], OM)
view(7, B8, CROSS + [x[0] for x in CR_SCREWS], 28, -130,
     det=(B8, 35, -120, around(c0, 160, 130, 130)),
     notes=[("cross_rail_1", "E", (0.03, -0.08)), ("cross_rail_2", "E", (0.03, 0.07))],
     dnotes=[("crs_h_0_-1", "M10×130 coach screw + washer,\n1 per crossing", (0.13, 0.06), "box"),
             ("sloping_rail_L", "B", (-0.05, -0.05))],
     cap="Cross rails standing on edge", dcap="Detail: lower-left crossing",
     text=dict(fs=8.6, need=["2 cross rails E", "4 × M10×130 coach screws + 4 washers", "10 mm and 6 mm bits, square, 17 mm socket, a helper"], steps=[
         "Check the pencil marks on the top edge of each sloping rail B: 571 and 1632 from the front (low) end — the cross-rail centres.",
         "Mark each E at 180 from both ends — the centre of each B.",
         "Stand the lower E on its 45 mm edge (70 tall) across both B's at the 571 marks, overhanging 180 each side, square to the frame.",
         "Drill 10 mm down through E only. Then swap to the 6 mm bit and drill a pilot about 60 mm into B.",
         "Fit an M10×130 coach screw with a washer. Do the other end, then the upper E at the 1632 marks.",
     ], check=["Diagonals between the ends of the two cross rails are equal", "Both rails sit tight on both B's — pack any gap with a thin offcut"],
     warn="Only a 6 mm pilot into B — never the 10 mm bit. A 10 mm hole leaves the coach screw nothing to grip.",
     tip="Drill the first end, fit its screw loosely, check the rail is square across the frame, then drill the second end."))

B9 = B8 + parts(MINI) + DPC
view(8, B9, MINI + [x[0] for x in DPC], 30, -120,
     det=(B9, 40, -100, around(S3(0, TCS[0], OM), 260, 120, 110)),
     notes=[("mini_rail_1_1", "K", (-0.04, -0.06)), ("mini_rail_1_2", "K", (0.0, -0.08)), ("mini_rail_1_3", "K", (0.04, -0.06)),
            ("mini_rail_2_2", "K", (0.0, 0.07))],
     dnotes=[("dpc_0", "DPC strip under\nthe panel gap", (-0.12, -0.05), "box"), ("mini_rail_1_2", "mini-rail K", (0.1, 0.06), "box")],
     cap="Mini-rails on both cross rails", dcap="Detail: middle of the lower cross rail",
     text=dict(need=["6 mini-rails + rubber pads (kit)", "12 × 4.5×50 green decking screws", "DPC strip, about 2 × 300 mm", "Staple gun, 3 mm bit"], steps=[
         "Staple a 300 mm piece of DPC over the middle of each cross rail. The gap between the panels sits above it, and it keeps the drips off the timber.",
         "Mark the mini-rail centres on top of each E: 66 from each end, and the middle (1200). Keep them clear of the coach-screw heads (180 from each end).",
         "Put a kit rubber pad under each mini-rail, running along the cross rail. The middle ones sit on the DPC.",
         "Drill 3 mm pilots and fix each mini-rail with 2 decking screws.",
     ], check=["Outer mini-rails line up top and bottom (string line or straight edge)",
               "Middle mini-rails exactly in the centre — the 20 mm panel gap goes here"],
     tip="Use the coated decking screws, not the self-drilling ones from the kit — those are made for thin metal roofing, not timber."))

LEDGE = ["bottom_ledge", "seat_block_L", "seat_block_R"]
B10 = B9 + parts(LEDGE)
fig = page(STEP_TITLES[8], 9)
ax = fig.add_axes(TOP); render(ax, B10, 30, -120, hl=LEDGE)
caption(fig, ax, "Bottom ledge standing on both sloping rails, held by two seat blocks")
note(fig, ax, "bottom_ledge", "M", (0.0, -0.09)); note(fig, ax, "seat_block_L", "N", (-0.05, -0.05)); note(fig, ax, "seat_block_R", "N", (0.05, -0.05))
ax = fig.add_axes([0.03, 0.04, 0.56, 0.31]); ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-45, 355); ax.set_ylim(28, 222)
ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False, ec="#999", lw=0.8))
TP0, MO, YC, WH, MH = D["TP0"], D["MO"], D["YC"], D["WH"], D["MH"]
PO_ = H/2 + D["CR_H"] + D["MR"]
def PP(t, o): return P(t, o)
Bpts = [PP(-60, -7.5), PP(-60, H/2), PP(330, H/2), PP(330, -H/2), PP(-20, -H/2)]
ax.add_patch(Polygon(Bpts, closed=True, fc="none", ec="#aaa", lw=0.8, ls="--"))
bl = PP(200, 0); ax.text(bl[0]+6, bl[1]-6, "B (M stands on its top)", fontsize=6.5, color="#888", rotation=45, va="center")
ax.add_patch(Rectangle((-45, 30), 400, 65, fc="#d9b27c", ec=INK, lw=0.8))
ax.text(300, 62, "base beam A", fontsize=7.5, ha="center", va="center")
ax.add_patch(plt.Circle(PIV, 6, fc="white", ec=INK, lw=0.7))
ax.add_patch(Polygon([(0, 95), (YC, 95), (YC-WH, 95+WH), (0, 95+WH)], fc="#e8cfa5", ec=INK, lw=1.0))
Mp = [PP(TP0-T, MO), PP(TP0, MO), PP(TP0, MO+MH), PP(TP0-T, MO+MH)]
ax.add_patch(Polygon(Mp, closed=True, fc="#c49a63", ec=INK, lw=0.9))
Lp = [PP(TP0, PO_), PP(TP0+260, PO_), PP(TP0+260, PO_+30), PP(TP0, PO_+30)]
ax.add_patch(Polygon(Lp, closed=True, fc="#1d2a5c", ec=INK, lw=0.6))
pc = PP(TP0+180, PO_+15); ax.text(*pc, "panel", fontsize=8, color="white", ha="center", va="center", rotation=45, clip_on=True)
for xs_ in (20, 45):
    ax.add_patch(Rectangle((xs_-2, 95+WH-75), 4, 75, fc="#7d838b", ec=INK, lw=0.4, zorder=5))
    ax.add_patch(Rectangle((xs_-5, 95+WH), 10, 3, fc="#7d838b", ec=INK, lw=0.4, zorder=5))
cc_ = math.cos(math.radians(45))
sp0 = (YC - 35*cc_, 95 + 35*cc_)
bk = (sp0[0] + 45*cc_, sp0[1] + 45*cc_)
s0 = (bk[0] + 2*cc_, bk[1] + 2*cc_); s1 = (sp0[0] - 30*cc_, sp0[1] - 30*cc_)
ax.plot([s0[0], s1[0]], [s0[1], s1[1]], color="#7d838b", lw=3.2, solid_capstyle="butt", zorder=7)
mc = PP(TP0-T/2, MO+MH*0.62); ax.text(*mc, "M", fontsize=10, weight="bold", ha="center", va="center")
ax.text(14, 105, "N", fontsize=10, weight="bold")
def ld(p, t, d):
    ax.annotate(t, p, (p[0]+d[0], p[1]+d[1]), fontsize=6.6, va="center", ha="center",
                arrowprops=dict(arrowstyle="-", color=ACC, lw=0.7), bbox=dict(fc="white", ec=ACC, lw=0.6, boxstyle="round,pad=0.25"))
ld((20, 130), "2 × 5×75 screws down\nthrough N into A", (-2, 62))
ld(((s0[0]+s1[0])/2, (s0[1]+s1[1])/2), "1 × 5×75 screw through M into N,\n35 up from M's bottom edge", (165, 25))
ld((YC, 95), "M's front edge just\ntouches the top of A", (60, -42))
ax.text(YC-WH/2+4, 95+WH/2-14, "45° face", fontsize=6.5, rotation=-45, ha="center", va="center", color="#333")
pa, pb = PP(TP0+70, MO+20), PP(TP0+15, MO+20)
ax.annotate("", pb, pa, arrowprops=dict(arrowstyle="->", color=ACC, lw=1.2))
ax.text(pa[0]+3, pa[1]-2, "panel pushes\nM into N", fontsize=6.6, color=ACC, va="top")
caption(fig, ax, "Side view at one base beam (front on the left)")
step_text(fig, fs=8.5, need=["Ledge M (45×120), 2 seat blocks N (full-size template on the last page)", "6 × 5×75 exterior screws (Wickes, pack of 50)", "3 mm bit"], steps=[
    "Set a seat block N on top of each base beam A: front end flush with A's front end, 45° face towards the back, and its outside edge lined up with A's outside face (next to B). The rest overhangs inwards.",
    "Drill two 3 mm pilots straight down through the block into A (positions on the template) and drive 2 × 5×75 screws.",
    "Stand M on edge across both sloping rails B, behind the blocks: its bottom face sits on the top edge of each B, its front edge just touches A, and its front face rests flat on both 45° faces. Equal overhang each side.",
    f"From behind, at each block: drill a 3 mm pilot through M into the block, 35 up from M's bottom edge and {D['CR_HALF']-(D['XI']+D['T']/2):.0f} from its end, then drive one 5×75 screw.",
], check=["M sits tight on both blocks and on top of both sloping rails", "Top of M about 25 mm above the top of the mini-rails (about 5 mm below the panel glass)",
          "Nothing sticks up higher than M (it would shade the panels)"],
   tip="The panels push M straight into the blocks, so the screws only have to stop M lifting off when a panel is removed.")

B11 = B10 + parts(BALLAST)
view(10, B11, BALLAST, 25, 55,
     notes=[(BALLAST[5], "ballast at the back", (0.02, 0.1), "box")],
     cap="View from behind",
     text=dict(fs=8.6, need=["Ballast: about 510 kg loose, or about 300 kg if the frame is fixed to the ground — dense concrete blocks (about 19 kg each), old slabs, or bags of gravel/rubble",
                     "Optional ground fixing: 2 galvanised angle brackets + masonry frame screws"], steps=[
         "Fix the frame to the ground if you can: for example a galvanised angle bracket at the front end of each base beam, screwed into the beam and down into the paving with masonry frame screws (or into a solid concrete base).",
         "Put the ballast on the pallet decks as close to the back as you can, spread evenly left and right.",
         "Lay blocks flat and tight together, no more than 3 high, clear of the diagonal.",
         "Fixed to the ground: about 300 kg (16 blocks). Not fixed: about 510 kg (27 blocks) — without a fixing, a strong gust from behind can push the whole frame forward.",
     ], tip="Do this BEFORE fitting the panels — once the panels are on, the frame can catch the wind.",
     check=["Frame fixed to the ground, or the full loose ballast in place", "Nothing can slide off the deck", "Weight roughly even left/right"]))

B12 = B11 + parts(PANELS + CLAMPS)
view(11, B12, PANELS + CLAMPS, 20, -118, fence=True,
     det=(B12, 22, -60, around(S3(0, TCS[0], PO + 20), 150, 110, 90)),
     notes=[("panel_1", "L", (-0.03, 0.08)), ("panel_2", "L", (0.03, 0.08))],
     dnotes=[("clampM_0", "middle clamp grips\nboth panels", (0.1, 0.06), "box")],
     cap="Panels fitted", dcap="Detail: middle clamp on the lower rail",
     text=dict(need=["2 panels", "Kit clamps: 4 end, 2 middle", "A helper (two people per panel)"], steps=[
         "Pick a calm, dry day. Cover the panel faces or leave the cables capped — they're live in daylight.",
         "Look for drain holes in the bottom corners of the panel frames. Cut a shallow 20 mm notch in the top of the ledge where each one will sit.",
         "Slide the clamp T-bolts into the mini-rails.",
         "Lay the left panel on with its bottom edge resting against the ledge, outer edge 56 from the end of the cross rails. Fit its two end clamps loosely.",
         "Lay the right panel with a 20 mm gap. Fit the two middle clamps across the gap, then the right end clamps.",
         "Check both panels are square and level with each other, then tighten every clamp firmly.",
         "Clip the cables neatly along a rail, connectors off the ground. Connect up following your battery / inverter instructions.",
     ], warn="Panels are 2 m long and 28 kg. Don't stand on the frame and don't lean the panels where a gust can catch them. "
             "Before connecting up, see the earthing note in step 12."))

fig = page(STEP_TITLES[11], 12)
ax = fig.add_axes(TOP); render(ax, ALL, 22, -55, fence=True)
_earth = ("EARTHING — the panels are out in the open, so their aluminium frames may need bonding together and to earth. "
          "Check your battery/inverter manual (Anker Solarbank) first. If it asks for it: an M5 stainless bolt through each panel's earthing hole "
          "(marked with the earth symbol), a serrated washer on bare metal, a tinned ring terminal, and 6 mm² green/yellow cable from panel to panel, "
          "then to the earth point the manual gives. Don't link it to the house earth or fit an earth rod yourself — many UK homes have a PME "
          "supply with special rules for outdoor metalwork. Get an electrician for that last connection.")
fig.text(0.045, 0.31, "\n".join(textwrap.wrap(_earth, 98)), fontsize=8.6, va="top", linespacing=1.4,
         bbox=dict(boxstyle="round,pad=0.7", fc="#fff4e0", ec="#e0a43c"))
caption(fig, ax, "Finished — view from the front-right")
step_text(fig, check=[
    "All 12 nyloc nuts tight, with thread showing past the nylon",
    "All 8 coach screws tight (4 into the pallets, 4 at the cross rails)",
    "Panels at 45° (phone level app on the panel frame)",
    "Frame fixed to the ground (or full ballast) and ballast in place",
    "Rubber under every point that touches the paving",
    "No timber sitting in a puddle after rain",
    "Earthing sorted if your system needs it — see the box on the left",
], steps=[
    "After the first windy week: re-check every nut and clamp. New timber shrinks a little and they loosen.",
    "Every year: re-check nuts and clamps; push a screwdriver into the pallet blocks and beam ends to look for rot; re-treat cut ends; clear leaves from under the panels; check the ballast hasn't moved.",
    "Wipe the panels when they're dusty — a soft brush and plain water.",
], tip="Brush leaves off the bottom ledge now and then. If a pallet rots, take off the ballast, undo its two coach screws and slide in a new one.", fs=8.4)

from template import make_template
tpl = make_template(f"Solar ground mount v4 — build guide  ·  page {len(pages)+1}  ·  PRINT AT 100%"); pages.append(tpl)
with PdfPages(f"{OUT}/solar_mount_v4_build_guide.pdf") as pdf:
    for f in pages: pdf.savefig(f)
print("pages:", len(pages))
