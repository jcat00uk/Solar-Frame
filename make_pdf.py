"""Printable A4-landscape build pack for the gen4 solar ground mount."""
import json, math, pickle, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d

OUT = "/home/claude/out"
D = json.load(open(f"{OUT}/dims_v4.json"))
mesh = pickle.load(open(f"{OUT}/mesh_v4.pkl", "rb"))
H, T = D["H"], D["T"]; c = s = math.cos(math.radians(45))
PIV = D["PIV"]; YP = D["YP"]; XI = D["XI"]
OM = H/2 + D["CR_H"]; PO = OM + D["MR"]
A4 = (11.69, 8.27)
INK, DIM, ACC = "#222222", "#1f5fa8", "#c0392b"
WOOD, WOOD2, PAL, PAN, BLK = "#d9b27c", "#b98a52", "#c0503c", "#1d2a5c", "#8c8c8c"

def P(t, o): return (PIV[0] + c*t - s*o, PIV[1] + s*t + c*o)

# ---------------------------------------------------------------- page helpers
def new_page(title, sub=""):
    fig = plt.figure(figsize=A4)
    fig.text(0.04, 0.955, title, fontsize=18, weight="bold", color=INK)
    if sub: fig.text(0.04, 0.925, sub, fontsize=10, color="#555")
    fig.add_artist(plt.Line2D([0.04, 0.96], [0.915, 0.915], color="#999", lw=0.8))
    fig.text(0.96, 0.02, f"Solar ground mount v4  ·  fixed 45°  ·  all dimensions in mm  ·  page {len(pages)+1}",
             ha="right", fontsize=8, color="#777")
    pages.append(fig)
    return fig

def dim(ax, p1, p2, off, text, fs=8, col=DIM, ext=True, rot=None):
    p1, p2 = np.array(p1, float), np.array(p2, float)
    d = p2 - p1; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]])
    a, b = p1 + n*off, p2 + n*off
    if ext:
        for p, q in ((p1, a), (p2, b)):
            ax.plot(*zip(p + n*np.sign(off)*15, q + n*np.sign(off)*25), color=col, lw=0.5)
    ax.annotate("", a, b, arrowprops=dict(arrowstyle="<->", color=col, lw=0.8, shrinkA=0, shrinkB=0))
    ang = math.degrees(math.atan2(u[1], u[0]))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    m = (a + b)/2 + n*np.sign(off if off else 1)*12
    ax.text(*m, text, fontsize=fs, color=col, ha="center", va="center", rotation=ang if rot is None else rot,
            bbox=dict(fc="white", ec="none", pad=0.6))

def leader(ax, xy, txt, dxy, col=INK, fs=8):
    ax.annotate(txt, xy, (xy[0]+dxy[0], xy[1]+dxy[1]), fontsize=fs, color=col,
                arrowprops=dict(arrowstyle="-", color=col, lw=0.6), ha="center", va="center",
                bbox=dict(fc="white", ec=col, lw=0.5, boxstyle="round,pad=0.25"))

def tag(ax, xy, letter, fs=9):
    ax.text(*xy, letter, fontsize=fs, weight="bold", color="white", ha="center", va="center",
            bbox=dict(boxstyle="circle,pad=0.25", fc=ACC, ec="none"), zorder=20)

def poly2(ax, pts, fc, ec=INK, lw=0.8, **kw):
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, **kw))

def setup2d(ax, xl, yl):
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")

# ---------------------------------------------------------------- 3D views
LIGHT = np.array([-0.4, -0.6, 0.7]); LIGHT /= np.linalg.norm(LIGHT)
def render(ax, elev, azim, skip=(), fence=False, W=1500, HPX=1150):
    """Orthographic z-buffer render with part outlines (true hidden-surface removal)."""
    tris, cols, ids = [], [], []
    def add(tri, col, pid): tris.append(tri); cols.append(col); ids.append(pid)
    g = np.array([[-1350, -150, -2], [1350, -150, -2], [1350, 1650, -2], [-1350, 1650, -2]], float)
    add(g[[0, 1, 2]], (0.88, 0.88, 0.85), 0); add(g[[0, 2, 3]], (0.88, 0.88, 0.85), 0)
    if fence:
        f = np.array([[-1350, 1600, 0], [1350, 1600, 0], [1350, 1600, 1800], [-1350, 1600, 1800]], float)
        add(f[[0, 1, 2]], (0.6, 0.47, 0.36), 1); add(f[[0, 2, 3]], (0.6, 0.47, 0.36), 1)
        for xe in (-1350, 1350):
            e = np.array([[xe, 1600, 0], [xe, 1625, 0], [xe, 1625, 1800], [xe, 1600, 1800]], float)
            add(e[[0, 1, 2]], (0.5, 0.38, 0.29), 1); add(e[[0, 2, 3]], (0.5, 0.38, 0.29), 1)
    for k, (n, vs, ts, cl) in enumerate(mesh):
        if n.startswith(skip): continue
        V = np.array(vs)
        for t in ts: add(V[list(t)], cl, k+2)
    T3 = np.array(tris); C = np.array(cols, float); I = np.array(ids)
    el, az = math.radians(elev), math.radians(azim)
    d = np.array([math.cos(el)*math.cos(az), math.cos(el)*math.sin(az), math.sin(el)])
    r = np.cross([0, 0, 1], d); r /= np.linalg.norm(r); u = np.cross(d, r)
    X, Y, Z = T3 @ r, T3 @ u, T3 @ d
    m = 25; xmin, xmax, ymin, ymax = X.min(), X.max(), Y.min(), Y.max()
    sc = min((W-2*m)/(xmax-xmin), (HPX-2*m)/(ymax-ymin))
    PX = (X - xmin)*sc + m; PY = (ymax - Y)*sc + m
    nrm = np.cross(T3[:, 1]-T3[:, 0], T3[:, 2]-T3[:, 0]); ln = np.linalg.norm(nrm, axis=1); ln[ln == 0] = 1
    shade = 0.55 + 0.45*np.abs((nrm/ln[:, None]) @ LIGHT)
    img = np.ones((HPX, W, 3)); zb = np.full((HPX, W), -np.inf); idb = np.full((HPX, W), -1)
    for i in range(len(T3)):
        x, y, z = PX[i], PY[i], Z[i]
        x0, x1 = max(int(x.min()), 0), min(int(x.max())+1, W-1)
        y0, y1 = max(int(y.min()), 0), min(int(y.max())+1, HPX-1)
        if x1 < x0 or y1 < y0: continue
        den = (y[1]-y[2])*(x[0]-x[2]) + (x[2]-x[1])*(y[0]-y[2])
        if abs(den) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(x0, x1+1)+0.5, np.arange(y0, y1+1)+0.5)
        l0 = ((y[1]-y[2])*(gx-x[2]) + (x[2]-x[1])*(gy-y[2])) / den
        l1 = ((y[2]-y[0])*(gx-x[2]) + (x[0]-x[2])*(gy-y[2])) / den
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not inside.any(): continue
        zz = l0*z[0] + l1*z[1] + l2*z[2]
        sub = zb[y0:y1+1, x0:x1+1]
        upd = inside & (zz > sub)
        sub[upd] = zz[upd]
        img[y0:y1+1, x0:x1+1][upd] = np.clip(C[i]*shade[i], 0, 1)
        idb[y0:y1+1, x0:x1+1][upd] = I[i]
    edge = np.zeros((HPX, W), bool)
    edge[:, 1:] |= idb[:, 1:] != idb[:, :-1]; edge[1:, :] |= idb[1:, :] != idb[:-1, :]
    img[edge] *= 0.45
    img[idb == -1] = 1.0
    ax.imshow(img, interpolation="antialiased"); ax.set_axis_off()
    def proj(p):
        p = np.asarray(p, float)
        return ((p @ r - xmin)*sc + m, (ymax - p @ u)*sc + m)
    ax._proj = proj

def label3d(fig, ax, pts):
    fig.canvas.draw(); ax.apply_aspect()
    for p, txt, (dx, dy) in pts:
        X, Y = ax._proj(p)
        fx, fy = fig.transFigure.inverted().transform(ax.transData.transform((X, Y)))
        fig.text(fx+dx, fy+dy, txt, fontsize=9, weight="bold", color="white", ha="center", va="center",
                 bbox=dict(boxstyle="circle,pad=0.25", fc=ACC, ec="none"), zorder=30)
        fig.add_artist(plt.Line2D([fx, fx+dx], [fy, fy+dy], color=ACC, lw=0.8, zorder=29))

pages = []
xL = -(XI + T/2); xR = -xL
xr = -(XI + 1.5*T); xpL = -(XI + 2.5*T)
tc1, tc2 = D["tcs"]

# ======================================================== PAGE 1: overview
fig = new_page("Solar ground mount — build pack",
               "Two 500 W panels, fixed 45°, facing south, on two pallets. Timber 45×95 / 45×70 treated (C16).")
ax = fig.add_axes([0.0, 0.08, 0.55, 0.82])
render(ax, 18, -125, fence=True)
ax.text(0.5, 0.97, "From the front (south side)", transform=ax.transAxes, ha="center", fontsize=11)
label3d(fig, ax, [((xL, 100, 95), "A", (0.02, -0.05)), ((xr, *P(200, 0)), "B", (-0.05, 0.02)),
                  ((0, *P(tc1, OM)), "E", (0.0, -0.08))])
ax2 = fig.add_axes([0.5, 0.08, 0.5, 0.82])
render(ax2, 22, 50, skip=("ballast",))
ax2.text(0.5, 0.97, "From behind (fence removed, no ballast)", transform=ax2.transAxes, ha="center", fontsize=11)
label3d(fig, ax2, [((xpL, YP, 800), "C", (0.05, 0.0)), ((-xr, YP, 48), "D", (-0.04, -0.05)),
                   ((0, YP+D["H"]/2+D["FB"], (D["Z1"]+D["Z2"])/2), "F", (0.0, 0.07)),
                   ((-440, 900, 144), "G", (0.03, -0.06)), ((490, 1100, 144), "H", (-0.03, -0.07)),
                   ((xr, *P(800, 0)), "B", (-0.05, 0.03)), ((-xL, 1450, 95), "A", (0.04, -0.03)),
                   ((0, *P(tc2, OM+12)), "K", (0.02, 0.06)), ((500, *P(1500, PO+15)), "L", (0.05, 0.05))])
fig.text(0.04, 0.115, "KEY", fontsize=9, weight="bold")
key = ("A Base beam   B Sloping rail   C Prop   D Foot spacer   E Cross rail   F Rear diagonal\n"
       "G Big pallet 980×1200   H Small pallet 880×900   J Packers   K Mini-rails (bought)\nL Panels   M Bottom ledge   N Seat blocks")
fig.text(0.04, 0.06, key, fontsize=9, va="bottom")
fig.text(0.6, 0.06, f"Overall: {2*D['CR_HALF']} wide × {D['BEAM']} deep × {D['top']:.0f} high\n"
         f"Panel bottom edge {D['panel_zmin']:.0f} above paving · panel top edge {1600-D['panel_ymax']:.0f} from fence",
         fontsize=9, va="bottom")

# ======================================================== PAGE 2: frame views + labels
fig = new_page("Frame without panels", "Use these to see how the parts go together. Letters match the parts pages.")
ax = fig.add_axes([0.0, 0.06, 0.52, 0.84])
render(ax, 20, -130, skip=("panel", "clamp", "ballast"))
ax.text(0.5, 0.97, "Front-left, panels off", transform=ax.transAxes, ha="center", fontsize=11)
label3d(fig, ax, [((xL, 700, 95), "A", (0.0, -0.06)), ((xr, *P(900, 0)), "B", (-0.06, 0.0)),
                  ((xpL, YP, 1000), "C", (-0.05, 0.04)), ((0, *P(tc1, OM)), "E", (0.03, -0.07)),
                  ((0, *P(tc2, OM)), "E", (0.03, 0.06)), ((-xL, 400, 95), "A", (0.04, -0.04)),
                  ((-440, 500, 144), "G", (0.0, -0.08)), ((-1134, *P(tc2, OM+12)), "K", (-0.04, 0.05)),
                  ((xL+30, 350, 70), "J", (-0.05, -0.05))])
ax2 = fig.add_axes([0.5, 0.06, 0.5, 0.84])
render(ax2, 0, 180, skip=("ballast",), fence=True)
ax2.text(0.5, 0.97, "Side view (fence on the left)", transform=ax2.transAxes, ha="center", fontsize=11)
label3d(fig, ax2, [((1300, YP, 700), "C", (-0.05, 0.03)), ((1300, *P(800, 0)), "B", (0.05, 0.03)),
                   ((1300, 800, 48), "A", (0.03, -0.06)), ((1300, YP+60, 50), "D", (-0.05, -0.05)),
                   ((1300, *P(tc1, OM)), "E", (0.06, 0.0)), ((1300, *P(1700, PO)), "L", (0.06, 0.04))])

# ======================================================== PAGE 3: side elevation with dimensions
fig = new_page("Side elevation — dimensions", "Looking from the side. Front (south) is on the right, the fence on the left.")
ax = fig.add_axes([0.03, 0.05, 0.94, 0.85])
u = lambda y: 1600 - y           # fence at u = 0, front toe at u = 1600
setup2d(ax, (-250, 2050), (-260, 1900))
ax.plot([-250, 2000], [0, 0], color=INK, lw=1.2)
for k in range(-200, 2000, 60): ax.plot([k, k-40], [0, -40], color="#999", lw=0.5)
ax.add_patch(Rectangle((-30, 0), 30, 1800, fc="#b08a6e", ec=INK, lw=0.8)); ax.text(-15, 1830, "fence", ha="center", fontsize=8)
# pallets (behind the beam) dashed
for (x0, x1, y0, y1), nm in ((D["big"], "G"), (D["small"], "H")):
    ax.add_patch(Rectangle((u(y1), 0), y1-y0, D["PAL_H"], fc="none", ec=PAL, lw=0.8, ls="--"))
ax.text(u(900), 165, "pallets behind beam (dashed)", fontsize=7, color=PAL, ha="center")
# base beam
ax.add_patch(Rectangle((u(D["BEAM"]), 0), D["BEAM"], H, fc=WOOD, ec=INK, lw=0.8))
# rail with chamfer
r = [P(-60, -7.9), P(-60, H/2), P(D["T_END"], H/2), P(D["T_END"], -H/2), P(-20.4, -H/2)]
poly2(ax, [(u(y), z) for y, z in r], WOOD2, zorder=3)
# prop
ax.add_patch(Rectangle((u(YP+H/2), 0), H, D["PROP_LEN"], fc=WOOD, ec=INK, lw=0.8, zorder=2))
ax.add_patch(Rectangle((u(YP+H/2), 0), H, H, fc="#e8cfa5", ec=INK, lw=0.6, zorder=4))
# cross rails + mini rails + panel
for tc in D["tcs"]:
    poly2(ax, [(u(y), z) for y, z in (P(tc-T/2, H/2), P(tc+T/2, H/2), P(tc+T/2, OM), P(tc-T/2, OM))], WOOD, zorder=5)
    poly2(ax, [(u(y), z) for y, z in (P(tc-17, OM), P(tc+17, OM), P(tc+17, PO), P(tc-17, PO))], "#cfd3d8", zorder=5)
TP0, PL = D["TP0"], D["PL"]
poly2(ax, [(u(y), z) for y, z in (P(TP0, PO), P(TP0+PL, PO), P(TP0+PL, PO+30), P(TP0, PO+30))], PAN, zorder=6)
_YC, _WH, _MO, _MH = D["YC"], D["WH"], D["MO"], D["MH"]
poly2(ax, [(u(0), H), (u(_YC), H), (u(_YC-_WH), H+_WH), (u(0), H+_WH)], "#e8cfa5", zorder=8)
for tc_ in D["tcs"]:
    a_, b_ = P(tc_, H/2+D["CR_H"]-130), P(tc_, H/2+D["CR_H"]+6)
    ax.plot([u(a_[0]), u(b_[0])], [a_[1], b_[1]], color="#555", lw=2.2, zorder=9, solid_capstyle="butt")
tag(ax, (u(30)+60, H+110), "N"); ax.plot([u(30), u(30)+60], [H+25, H+100], color=ACC, lw=0.6)
poly2(ax, [(u(y), z) for y, z in (P(TP0-T, _MO), P(TP0, _MO), P(TP0, _MO+_MH), P(TP0-T, _MO+_MH))], WOOD, zorder=9)
_lm = P(TP0-T/2, _MO+_MH/2); tag(ax, (u(_lm[0])+70, _lm[1]-40), "M")
# bolts
for (y, z) in [tuple(PIV), (YP, D["zA"]-30), (YP, D["zA"]+30), (YP-25, H/2), (YP+25, H/2)]:
    ax.add_patch(Circle((u(y), z), 9, fc="white", ec=INK, lw=0.8, zorder=8))
# tags
tag(ax, (u(800), 47), "A"); tag(ax, (u(P(600, 0)[0]), P(600, 0)[1]), "B"); tag(ax, (u(YP), 700), "C")
tag(ax, (u(YP), 48), "D"); tag(ax, (u(P(tc1, 82)[0])+70, P(tc1, 82)[1]-40), "E"); tag(ax, (u(P(1200, PO+15)[0])+60, P(1200, PO+15)[1]+60), "L")
# dimensions
dim(ax, (u(D["BEAM"]), 0), (1600, 0), -150, f"base beam {D['BEAM']}")
dim(ax, (u(YP), 0), (1600, 0), -90, f"{1600-u(YP):.0f} to prop centre")
dim(ax, (u(PIV[0]), 0), (1600, 0), -40, f"{PIV[0]}", fs=7)
leader(ax, (u(PIV[0]), PIV[1]), f"pivot bolt\n{PIV[1]} up, {PIV[0]} from front", (300, -210))
dim(ax, (u(YP+H/2), 0), (u(YP+H/2), D["PROP_LEN"]), 120, f"prop {D['PROP_LEN']:.0f}")
ax.annotate("", (1950, 0), (1950, D["top"]), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8))
ax.text(1965, D["top"]/2, f"top {D['top']:.0f}", rotation=90, color=DIM, fontsize=8, va="center")
ax.plot([u(D["panel_ymax"]), 1960], [D["top"], D["top"]], color=DIM, lw=0.4, ls=":")
ax.annotate("", (1890, 0), (1890, D["panel_zmin"]), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8))
ax.text(1905, D["panel_zmin"]+40, f"{D['panel_zmin']:.0f}", color=DIM, fontsize=8)
ax.annotate("", (0, 1650), (u(D["panel_ymax"]), 1650), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8))
ax.text(u(D["panel_ymax"])/2, 1690, f"{1600-D['panel_ymax']:.0f} clear", ha="center", color=DIM, fontsize=8)
# rail length along the slope (offset below rail)
dim(ax, (u(P(-60, -H/2)[0]), P(-60, -H/2)[1]), (u(P(D["T_END"], -H/2)[0]), P(D["T_END"], -H/2)[1]), 140, f"sloping rail {D['RAIL']:.0f}")
# angle arc
cx, cz = u(PIV[0]), PIV[1]
th = np.linspace(180, 135, 30)
ax.plot(cx + 260*np.cos(np.radians(th)), cz + 260*np.sin(np.radians(th)), color=ACC, lw=0.9)
ax.plot([cx, cx-300], [cz, cz], color=ACC, lw=0.6, ls=":")
ax.text(cx-300, cz+110, "45°", color=ACC, fontsize=11, weight="bold")
leader(ax, (u(YP), D["zA"]), "2 bolts, 60 apart\n(1170 & 1230 up)", (-330, 120))
leader(ax, (u(YP), H/2), "2 bolts through\nprop + spacer + beam", (-380, 260))

# ======================================================== PAGE 4: rear elevation + plan
fig = new_page("Rear elevation and plan — dimensions", "Rear view is from the fence side, so West is on the right.")
ax = fig.add_axes([0.02, 0.36, 0.96, 0.55])
setup2d(ax, (-1450, 1450), (-260, 1500))
w = lambda x: -x                   # view from behind: mirror x
ax.plot([-1400, 1400], [0, 0], color=INK, lw=1.2)
for x0, x1, nm in ((D["big"][0], D["big"][1], "G"), (D["small"][0], D["small"][1], "H")):
    ax.add_patch(Rectangle((w(x1), 0), x1-x0, D["PAL_H"], fc=PAL, ec=INK, lw=0.6, alpha=0.85))
    tag(ax, (w((x0+x1)/2), 72), nm)
for sg in (-1, 1):
    ax.add_patch(Rectangle((w(sg*XI) if sg > 0 else w(sg*(XI+T)), 0), T, H, fc=WOOD, ec=INK, lw=0.7))       # A
    ax.add_patch(Rectangle((min(w(sg*(XI+2*T)), w(sg*(XI+3*T))), 0), T, D["PROP_LEN"], fc=WOOD, ec=INK, lw=0.7))  # C
    ax.add_patch(Rectangle((min(w(sg*(XI+T)), w(sg*(XI+2*T))), 0), T, H, fc="#e8cfa5", ec=INK, lw=0.6))   # D
    zt = P(D["T_END"], H/2)[1]
    ax.add_patch(Rectangle((min(w(sg*(XI+T)), w(sg*(XI+2*T))), H), T, zt-H, fc=WOOD2, ec=INK, lw=0.6, alpha=0.5))  # B
    ax.add_patch(Rectangle((min(w(sg*XI), w(sg*(XI-22))), D["PAL_H"]/2-39), 22, 78, fc="#999", ec=INK, lw=0.5))  # J
xo, xp, Z1, Z2 = D["xo"], D["xp"], D["Z1"], D["Z2"]
zc = lambda x: Z1 + (x + xp)*(Z2-Z1)/(2*xp)
hz = (D["FW"]/2)/math.cos(math.radians(D["a_diag"]))
poly2(ax, [(w(-xo), zc(-xo)-hz), (w(xo), zc(xo)-hz), (w(xo), zc(xo)+hz), (w(-xo), zc(-xo)+hz)], "#8a5a3a", alpha=0.9, zorder=5)
for x in (-xp, xp): ax.add_patch(Circle((w(x), zc(x)), 10, fc="white", ec=INK, zorder=6))
for tc in D["tcs"]:
    z0 = P(tc, H/2)[1]
    ax.add_patch(Rectangle((-D["CR_HALF"], z0), 2*D["CR_HALF"], 80, fc=WOOD, ec=INK, lw=0.6, alpha=0.6, zorder=1))
tag(ax, (w(-xp)-120, 300), "C"); tag(ax, (w(xp)+120, 300), "C"); tag(ax, (0, zc(0)), "F")
tag(ax, (w(-(XI+T/2)), -60), "A"); tag(ax, (w(XI+T/2), -60), "A")
tag(ax, (-1260, P(tc2, H/2)[1]+40), "E"); tag(ax, (-1260, P(tc1, H/2)[1]+40), "E")
dim(ax, (-D["CR_HALF"], 1400), (D["CR_HALF"], 1400), 0.001, f"cross rail {2*D['CR_HALF']}", ext=False)
dim(ax, (w(XI+3*T), 0), (w(-(XI+3*T)), 0), -200, f"frame outside {2*(XI+3*T)}")
dim(ax, (w(XI), 0), (w(-XI), 0), -120, f"between beams {2*XI}  (pallets 980 + 880 + 22 packer each side)")
leader(ax, (w(-xp), zc(-xp)), f"{Z1} up\n(this end low, West prop)", (-260, -250))
leader(ax, (w(xp), zc(xp)), f"{Z2} up\n(East prop)", (230, 230))
ax.text(1380, -40, "W", fontsize=12, weight="bold"); ax.text(-1420, -40, "E", fontsize=12, weight="bold")
# plan
ax = fig.add_axes([0.08, 0.04, 0.84, 0.31])
setup2d(ax, (-1450, 1450), (-250, 1800))
ax.add_patch(Rectangle((-1400, 1600), 2800, 40, fc="#b08a6e", ec=INK, lw=0.6)); ax.text(0, 1680, "fence (north)", ha="center", fontsize=8)
for (x0, x1, y0, y1) in (D["big"], D["small"]):
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fc=PAL, ec=INK, lw=0.6, alpha=0.8))
ax.add_patch(Rectangle((D["big"][0], 1500-645), 1860, 645, fc="none", ec="#333", lw=1.2, ls="--", zorder=6))
ax.text(0, 1500-645+40, "ballast zone (back 645 mm)", fontsize=7, color="#222", ha="center", zorder=6)
ax.text(-1400, 800, "W", fontsize=12, weight="bold"); ax.text(1370, 800, "E", fontsize=12, weight="bold")
for sg in (-1, 1):
    ax.add_patch(Rectangle((min(sg*XI, sg*(XI+T)), 0), T, D["BEAM"], fc=WOOD, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((min(sg*(XI+T), sg*(XI+2*T)), 0), T, D["T_END"]*c+PIV[0], fc=WOOD2, ec=INK, lw=0.5, alpha=0.7))
    ax.add_patch(Rectangle((min(sg*(XI+2*T), sg*(XI+3*T)), YP-H/2), T, H, fc=WOOD, ec=INK, lw=0.6))
dim(ax, (1300, 0), (1300, D["BEAM"]), -0.001, f"{D['BEAM']}", ext=False)
dim(ax, (D["big"][0], -60), (D["big"][1], -60), 0.001, "980", ext=False, fs=7)
dim(ax, (D["small"][0], -60), (D["small"][1], -60), 0.001, "880", ext=False, fs=7)
ax.text(-1420, -150, "PLAN (from above)   front / south ↓", fontsize=8)

# ======================================================== parts pages
def part(fig, rect, L, Hh, title, holes=(), dims=(), vdims=(), marks=(), note="", shape="rect", fc=WOOD, end_lab=None, later=()):
    ax = fig.add_axes(rect); ax.axis("off")
    padx = max(L*0.06, 60)
    ax.set_xlim(-padx, L+padx*1.6); ax.set_ylim(-Hh*1.6 - 30*len(dims), Hh*2.2)
    if shape == "rect":
        ax.add_patch(Rectangle((0, 0), L, Hh, fc=fc, ec=INK, lw=0.9))
    elif shape[0] == "chamfer":
        cs = shape[1]; poly2(ax, [(cs*L/1800*0+cs, 0), (L, 0), (L, Hh), (0, Hh), (0, cs)], fc)
    elif shape[0] == "para":
        sh = shape[1]; poly2(ax, [(0, 0), (L, 0), (L+sh, Hh), (sh, Hh)], fc)
    for (x, y) in holes:
        ax.plot(x, y, "o", ms=7, mfc="white", mec=INK, mew=1, zorder=5)
    for k, (x, y, lab) in enumerate(later):
        ax.plot(x, y, "o", ms=8, mfc="white", mec=ACC, mew=1.6, ls="none", zorder=5)
        ax.plot(x, y, "x", ms=4, mec=ACC, mew=1, zorder=6)
        if lab: ax.text(x, -Hh*0.12, lab, fontsize=6.5, color=ACC, weight="bold", ha="center", va="top",
                        bbox=dict(fc="white", ec=ACC, lw=0.5, boxstyle="round,pad=0.15"), zorder=6)
    for (x, lab) in marks:
        ax.plot([x, x], [-Hh*0.15, Hh*1.15], color=ACC, lw=1.1, ls="--", zorder=4)
        ax.text(x, Hh*1.25, lab, fontsize=7, color=ACC, ha="center", va="bottom")
    step = Hh*0.45 + 20
    for k, (x0, x1, lab) in enumerate(dims):       # horizontal dims, stacked under the part
        yy = -step*(k+1)
        ax.annotate("", (x0, yy), (x1, yy), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8, shrinkA=0, shrinkB=0))
        for xx in (x0, x1): ax.plot([xx, xx], [0, yy - step*0.15], color=DIM, lw=0.4)
        ax.text(x1, yy, " " + lab, fontsize=8, color=DIM, va="center", ha="left")
    for (x, y0, y1, lab) in vdims:                  # vertical dims at x
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8, shrinkA=0, shrinkB=0))
        ax.text(x + padx*0.15, (y0+y1)/2, lab, fontsize=7.5, color=DIM, va="center")
    if end_lab: ax.text(-padx*0.25, Hh/2, end_lab, rotation=90, fontsize=7, color=ACC, ha="center", va="center")
    p = ax.get_position()
    fig.text(p.x0, p.y1 + 0.004, title, fontsize=10.5, weight="bold", color=INK, va="bottom")
    if note: fig.text(p.x1 + 0.005, p.y0 + p.height*0.55, note, fontsize=7.5, color="#333", va="center")
    return ax

TA = D["tA"]; tcf = [60 + t for t in D["tcs"]]; zA = D["zA"]; PLn = D["PROP_LEN"]
t1, t2 = 60 + TA - 21.2, 60 + TA + 21.2

fig = new_page("Parts 1 — long pieces", "Side face of each piece. Ø10 holes for M10 coach bolts, drilled straight through the 45 mm thickness. Measure from the end marked in red.")
part(fig, [0.04, 0.66, 0.66, 0.2], 1495, H, "A  Base beam  ×2      45×95, cut 1495",
     holes=[(PIV[0], PIV[1]), (YP-25, H/2), (YP+25, H/2)],
     dims=[(0, PIV[0], "150 pivot"), (0, YP-25, "1275"), (0, YP+25, "1325"), (0, 1495, "1495")],
     vdims=[(PIV[0]+40, 0, PIV[1], "50"), (YP+70, 0, H/2, "47")], end_lab="FRONT",
     note="Drill now: pivot hole 50 up,\nfoot pair 47 up.\n\nDRILL LATER (step 5, with the\nframe against the pallets):\n2 coach-screw holes, 61 up —\nLeft beam at 350 & 1450\nRight beam at 650 & 1450")
part(fig, [0.04, 0.37, 0.66, 0.2], D["RAIL"], H, f"B  Sloping rail  ×2      45×95, cut {D['RAIL']:.0f} (square ends)",
     holes=[(60, H/2)], later=[(t1, H/2-21.2, "LATER step 3"), (t2, H/2+21.2, "")], shape=("chamfer", 40),
     marks=[(tcf[0], f"mark only: cross rail {tcf[0]:.0f}"), (tcf[1], f"mark only: {tcf[1]:.0f}")],
     dims=[(0, 60, "60 pivot"), (0, t1, f"{t1:.0f}"), (0, t2, f"{t2:.0f}"), (0, D["RAIL"], f"{D['RAIL']:.0f}")],
     vdims=[(t2+60, H/2+21.2, H, "26"), (t1-60, 0, H/2-21.2, "26")], end_lab="FRONT (low)",
     note="Chamfer the bottom front\ncorner 40×40 so it clears\nthe paving.\n\nPivot hole on the centre line.\nTop pair 26 from the edges.\n\nDrill now: pivot hole only.\nRed dashed holes: LATER, in\nstep 3, through B and C together.\nRed lines: pencil marks only —\nthe cross-rail screw gets a 6 mm\npilot in step 7, never 10 mm.")
part(fig, [0.04, 0.08, 0.66, 0.2], PLn, H, f"C  Prop  ×2      45×95, cut {PLn:.0f} (square ends)",
     holes=[(H/2, 22.5), (H/2, 72.5)], later=[(zA-30, H/2, "LATER step 3"), (zA+30, H/2, "")],
     marks=[(D["Z1"], f"LATER step 6: diagonal {D['Z1']} (West)"), (D["Z2"], f"{D['Z2']} (East)")],
     dims=[(0, H/2, "47"), (0, zA-30, f"{zA-30:.0f}"), (0, zA+30, f"{zA+30:.0f}"), (0, PLn, f"{PLn:.0f}")],
     end_lab="FOOT",
     note="Drill now: foot pair 47 up\nfrom the foot, 22 & 72 across.\nTop pair centred — LATER.\n\nDiagonal hole — LATER — goes the\nOTHER way (through the\n95 mm, centred on the\n45 mm face). West prop\nat 520, East prop at 1050.")

fig = new_page("Parts 2 — cross rails, diagonal and small pieces", "Ø10 holes for M10 coach bolts unless noted.")
L = 2*D["CR_HALF"]; exm = D["CR_HALF"] - (D["GAP"]/2 + D["PW"]) + 10
ax = part(fig, [0.04, 0.66, 0.66, 0.2], L, D["CR_H"], f"E  Cross rail  ×2      45×70, 2400 (no cut), on edge",
     marks=[(180.5, "B"), (L-180.5, "B"), (exm, "K"), (L/2, "K"), (L-exm, "K")],
     dims=[(0, exm, f"{exm:.0f} mini-rail centre"), (0, 180.5, "180 rail centre"), (0, L/2, "1200 middle"), (0, L, "2400")],
     note="Marks on the top edge\n(B = sloping rail, K = mini-rail).\nMini-rails K: 66 from each\nend and in the middle.\nPanel outer edges 56 from\neach end.\n\nDRILL LATER (step 7, with E\nin place): Ø10 through E, 180\nfrom each end, then a 6 mm\npilot 60 deep into B. 1 × M10×130\ncoach screw + washer.")
sh = D["FW"]*math.tan(math.radians(D["a_diag"])); hx = 100/math.cos(math.radians(D["a_diag"]))
part(fig, [0.04, 0.37, 0.66, 0.2], D["DIAG_LEN"], D["FW"], f"F  Rear diagonal  ×1      45×95, {D['DIAG_LEN']:.0f} along the edge",
     holes=[(hx + sh/2, D["FW"]/2), (D["DIAG_LEN"] - hx + sh/2, D["FW"]/2)], shape=("para", sh), fc="#a97850",
     dims=[(sh/2, hx+sh/2, "103 to hole"), (0, D["DIAG_LEN"], f"{D['DIAG_LEN']:.0f} edge length")],
     note=f"Cut both ends {D['a_diag']:.0f}° off square,\nparallel to each other\n(the ends end up vertical).\n\nHoles on the centre line.\nLies flat across the backs\nof the props, low end on\nthe WEST prop.")
part(fig, [0.04, 0.08, 0.2, 0.2], 95, 95, "D  Foot spacer  ×2   45×95×95",
     holes=[(22.5, 47.5), (72.5, 47.5)], dims=[(0, 95, "95")], vdims=[(110, 0, 47.5, "47")], fc="#e8cfa5")
part(fig, [0.3, 0.08, 0.2, 0.2], 100, 78, "J  Packer  ×4   22 thick",
     dims=[(0, 100, "100")], vdims=[(115, 0, 78, "78")], fc="#bbb",
     note="Pallet slat\noffcuts")
fig.text(0.56, 0.24, "D: from the prop offcut. Holes 47 up,\n22 and 72 from one edge, same as the\nprop foot so the bolts line up.\n\n"
         "M  Bottom ledge ×1   45×120 × 2400. On edge, standing\non top of both B's, its front edge touching A.\n"
         "N  Seat block ×2   45×95 × 128 laid flat on A, front\nend flush with A's front end, back end bevelled 45°\n"
         "(full-size template: last page). 2 × 5×75 screws down\ninto A, 1 through M into each block (3 mm pilots).", fontsize=7.5, va="top")

# ======================================================== cutting plan + shopping + assembly
fig = new_page("Cutting plan, shopping list and assembly order")
ax = fig.add_axes([0.04, 0.55, 0.5, 0.35]); setup2d(ax, (-50, 4300), (-350, 1250))
stock = [("3.0 m 45×95", 3000, [("A 1495", 1495), ("A 1495", 1495)]),
         ("3.6 m 45×95", 3600, [(f"B {D['RAIL']:.0f}", D["RAIL"]), (f"B {D['RAIL']:.0f}", D["RAIL"])]),
         ("3.0 m 45×95", 3000, [(f"C {D['PROP_LEN']:.0f}", D["PROP_LEN"]), (f"C {D['PROP_LEN']:.0f}", D["PROP_LEN"]), ("D", 95), ("D", 95)]),
         ("2.4 m 45×70", 2400, [("E 2400", 2400)]), ("2.4 m 45×70", 2400, [("E 2400", 2400)]),
         ("2.4 m 45×120", 2400, [("M 2400", 2400)]),
         ("3.0 m 45×95", 3000, [(f"F {D['DIAG_LEN']:.0f}", D["DIAG_LEN"]), ("N", 128), ("N", 128)])]
for i, (nm, L, cuts) in enumerate(stock):
    yy = 1100 - i*200
    ax.add_patch(Rectangle((0, yy), L, 110, fc="#eee", ec=INK, lw=0.6))
    x = 0
    for lab, cl in cuts:
        ax.add_patch(Rectangle((x, yy), cl, 110, fc=WOOD, ec=INK, lw=0.6))
        ax.text(x+cl/2, yy+55, lab, ha="center", va="center", fontsize=7); x += cl + 3
    ax.text(L+60, yy+55, f"{nm}   (spare {max(0, L-x+3):.0f})", fontsize=7.5, va="center")
ax.text(0, 1250, "Cutting plan (3 mm saw kerf allowed)", fontsize=10, weight="bold")

shop = ("SHOPPING\n"
        "Wickes  45×95 C16: 3×3.0, 1×3.6 m         ~£36\n"
        "Wickes  45×120 C16 treated: 1×2.4 m       ~£10\n"
        "Wickes  45×70 C16 treated: 2×2.4 m          ~£12\n"
        "Toolstation (packs of 10 unless noted):\n"
        "  M10×110 coach bolt & nut (16920)   use 6\n"
        "  M10×160 coach bolt & nut (25722)   use 6\n"
        "  M10×130 coach screw (13250)        use 8\n"
        "  M10 penny washer (90716)  2 packs  use 20\n"
        "  M10 nyloc nut, 50 (81914)          use 12\n"
        "Recommended: ground fixing (brackets +\n  masonry screws) — see ballast box\n"
        "  4.5×50 decking screws (76239)      use 12\n"
        "Wickes 5×75 exterior screws (50)   use 6  ~£3.50\n"
        "DPC strip 100 mm, rubber matting\n\n"
        "ALREADY HAVE: pallets,\n"
        "mini-rails, clamps")
fig.text(0.63, 0.89, shop, fontsize=8.5, va="top", family="monospace")

steps = ("ASSEMBLY ORDER  (full illustrated steps in the separate build guide)\n"
         "1  Cut all pieces; treat cut ends.   2  Drill the Ø10 holes in A, B (pivot only), C (foot) and D.\n"
         "3  Build each side frame FLAT on blocks: A + D + C (2 × M10×160), B at the pivot (M10×110), set 45°,\n"
         "     drill the two top holes through B + C together (2 × M10×110). Tighten everything now.\n"
         "4  Rubber matting, then pallets G (left/West) and H (right/East), back edges 100 mm from the fence.\n"
         "5  Stand the frames up, packers J between beam and pallet, M10×130 coach screws into the pallet blocks.\n"
         "6  Diagonal F across the backs of the props (low end on the West prop), M10×160 through F + prop.\n"
         "7  Cross rails E on edge at 571 and 1632 up the rails: Ø10 through E, 6 mm pilot into B, 1 × M10×130 coach screw each.\n"
         "8  DPC + mini-rails K.  9  Seat blocks N on A; ledge M (45×120) on top of both B's against them.  10  Ground fixing + ballast.  11  Panels.\n"
         "Holes marked LATER on the parts pages are drilled in place, at the step shown — not on the bench.")
fig.text(0.04, 0.55, steps, fontsize=8.5, va="top")
bal = (f"BALLAST (rough check, 60 mph gust from behind, safety factor 1.5)\n"
       f"Frame + pallets + panels already weigh ~{D['timber_kg']+D['pallet_kg']+56:.0f} kg.\n"
       f"To stop it TIPPING you need ~{round(D['wb_tip'],-1):.0f} kg more on the pallets, at the back.\n"
       f"To stop it SLIDING you need ~{round(D['wb_slide'],-1):.0f} kg more — unless the frame is FIXED TO THE GROUND\n"
       f"(e.g. an angle bracket at the front of each base beam, screwed into the paving),\n"
       f"which removes the sliding case, leaving ~{round(D['wb_tip'],-1):.0f} kg.\n"
       f"Ballast can be old slabs, rubble/gravel bags or blocks (~19 kg each). Max 3 high.\n"
       f"The fence shelters it from wind behind, which this check ignores.")
fig.text(0.04, 0.21, bal, fontsize=8.5, va="top",
         bbox=dict(boxstyle="round,pad=0.6", fc="#fff6e5", ec="#d9a441"))
earth = ("EARTHING (ground-mounted panels)\n"
         "The panel frames are bare aluminium out in the open, so they may need\n"
         "bonding together and to earth. Check your battery/inverter manual first.\n"
         "If it asks for it: M5 stainless bolt through each panel's earthing hole\n(marked with the earth symbol), "
         "serrated washer on bare metal, tinned ring terminal,\n6 mm² green/yellow "
         "cable panel to panel, then to the earth point the manual gives.\n"
         "Don't link to the house earth or fit an earth rod yourself — many UK homes\n"
         "have a PME supply with special rules. Get an electrician for that last bit.")
fig.text(0.53, 0.21, earth, fontsize=8.5, va="top",
         bbox=dict(boxstyle="round,pad=0.6", fc="#eef4fb", ec="#7fa4d4"))

from template import make_template
pages.append(make_template(f"Solar ground mount v4 — build pack  ·  page {len(pages)+1}  ·  PRINT AT 100%"))
with PdfPages(f"{OUT}/solar_mount_v4_build_pack.pdf") as pdf:
    for f in pages: pdf.savefig(f)
print("pages:", len(pages))
