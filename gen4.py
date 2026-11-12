"""gen4 - fixed 45 deg solar ground mount on two pallets (paving site).

Axes: x = across (east-west), y = front->back (south->north, y=0 at the front toe),
z = up. Panels face south (towards -y). Fence is behind, ~1.6 m from the front toe.

Timber: 45x95 C16 treated (Wickes) for structure, existing 150x40 board as rear
diagonal, two pallets (980x1200 and 880x900, assumed 144 high) as the base deck.
"""
import math, itertools, os, cadquery as cq

OUT = os.environ.get("OUT", "/home/claude/out")
os.makedirs(OUT, exist_ok=True)

# ---------------- parameters ----------------
TILT = 45.0
th = math.radians(TILT); c, s = math.cos(th), math.sin(th)
H, T = 95, 45            # 45x95 timber: H = depth, T = thickness
FB, FW = 45, 95          # 45x95 laid flat (rear diagonal)
BEAM = 1500              # base beam length (front toe to back end)
PIV = (150, 50)          # pivot bolt (y, z) on base beam
XI = 952                 # base beam inner face (pallets 1860 wide + 22 packer each side)
PL, PW, GAP, PT = 1961, 1134, 20, 30   # panel length/width/gap/thickness
HOLE = 5.5               # M10 clearance hole radius
YP = 1300                # prop centre line (y)
MR = 25                  # mini-rail height
TP0 = 45 + (95 - 50 - 47.5*math.cos(math.radians(45)))/math.sin(math.radians(45)) + 0.05  # ~61.2; panel bottom edge (ledge M sits on B with its front corner on A), distance along slope from pivot
PAL_H, SLAT = 144, 22    # pallet height and board thickness
BALLAST = True           # show ballast blocks
BLOCK = (440, 215, 100, 19.0)   # dense concrete block L, W, H (mm) and kg

parts, hw = {}, {}

# ---------------- helpers ----------------
def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))

def P(t, o):             # point on sloping rail: t along slope from pivot, o normal offset
    return (PIV[0] + c*t - s*o, PIV[1] + s*t + c*o)

def poly(pts, x0, x1):
    a, b = sorted((x0, x1))
    return cq.Workplane("YZ").workplane(offset=a).polyline(pts).close().extrude(b-a)

def slope(t0, t1, o0, o1, x0, x1):
    return poly([P(t0, o0), P(t1, o0), P(t1, o1), P(t0, o1)], x0, x1)

def xcyl(y, z, x0, x1, r):
    a, b = sorted((x0, x1))
    return cq.Workplane("YZ").workplane(offset=a).center(y, z).circle(r).extrude(b-a)

def xhole(w, y, z, x0, x1, r=HOLE):
    a, b = sorted((x0, x1))
    return w.cut(xcyl(y, z, a-1, b+1, r))

def ycyl(x, z, y0, y1, r):
    a, b = sorted((y0, y1))
    pl = cq.Plane(origin=(x, a, z), xDir=(1, 0, 0), normal=(0, 1, 0))
    return cq.Workplane(pl).circle(r).extrude(b-a)

def bolt_x(name, y, z, xa, xb):       # xa = head side, xb = nut side
    d = 1 if xb > xa else -1
    hw[name+"_shank"] = xcyl(y, z, xa, xb, 5)
    hw[name+"_head"] = xcyl(y, z, xa-d*9.5, xa-d*3, 8.5)
    hw[name+"_washer_h"] = xcyl(y, z, xa-d*3, xa, 15)
    hw[name+"_washer_n"] = xcyl(y, z, xb, xb+d*3, 15)
    hw[name+"_nut"] = xcyl(y, z, xb+d*3, xb+d*11, 8.5)

def bolt_y(name, x, z, ya, yb):
    d = 1 if yb > ya else -1
    hw[name+"_shank"] = ycyl(x, z, ya, yb, 5)
    hw[name+"_head"] = ycyl(x, z, ya-d*9.5, ya-d*3, 8.5)
    hw[name+"_washer_h"] = ycyl(x, z, ya-d*3, ya, 15)
    hw[name+"_washer_n"] = ycyl(x, z, yb, yb+d*3, 15)
    hw[name+"_nut"] = ycyl(x, z, yb+d*3, yb+d*11, 8.5)

def rail_top_z(y):       # z of the sloping rail's top surface at a given y
    return PIV[1] + (y - PIV[0]) * math.tan(th) + (H/2) / c

# ---------------- side frames ----------------
tA = (YP - PIV[0]) / c                      # prop meets rail at this slope distance
zA = PIV[1] + (YP - PIV[0]) * math.tan(th)  # rail centreline height at prop
T_END = tA + 100
RAIL = T_END + 60
tcs = (TP0 + 450, TP0 + PL - 450)           # cross-rail positions along slope
assert tcs[1] + T/2 < T_END, "top cross rail runs off the sloping rail"

top_pair = [(YP, zA - 30), (YP, zA + 30)]
foot_pair = [(YP - 25, H/2), (YP + 25, H/2)]

for name, sg in (("L", -1), ("R", 1)):      # sg = outward direction
    bx = (sg*XI, sg*(XI+T))                 # base beam layer (innermost)
    rx = (sg*(XI+T), sg*(XI+2*T))           # rail layer
    px = (sg*(XI+2*T), sg*(XI+3*T))         # prop layer (outermost)

    b = box(*bx, 0, BEAM, 0, H)
    b = xhole(b, *PIV, *bx)
    for (y, z) in foot_pair: b = xhole(b, y, z, *bx)
    parts[f"base_beam_{name}"] = b

    r = slope(-60, T_END, -H/2, H/2, *rx).cut(box(-2000, 2000, -200, 400, -50, 2))
    r = xhole(r, *PIV, *rx)
    for (y, z) in top_pair: r = xhole(r, y, z, *rx)
    parts[f"sloping_rail_{name}"] = r

    y0, y1 = YP - H/2, YP + H/2
    PROP_LEN = rail_top_z(y1)                 # square-cut top, level with rail top at back face
    p = box(*px, y0, y1, 0, PROP_LEN)
    for (y, z) in top_pair + foot_pair: p = xhole(p, y, z, *px)
    parts[f"prop_{name}"] = p

    sp = box(*rx, y0, y1, 0, H)
    for (y, z) in foot_pair: sp = xhole(sp, y, z, *rx)
    parts[f"foot_spacer_{name}"] = sp

    bolt_x(f"pivot_bolt_{name}", *PIV, rx[1], bx[0])
    for k, (y, z) in enumerate(top_pair): bolt_x(f"prop_top_bolt{k}_{name}", y, z, px[1], rx[0])
    for k, (y, z) in enumerate(foot_pair): bolt_x(f"foot_bolt{k}_{name}", y, z, px[1], bx[0])

# ---------------- rear diagonal (existing 150x40 board, flat on prop backs) ----------------
xp = XI + 2.5*T                              # prop centre x
xo = xp + 100                                # board runs 100 past each prop centre
Z1, Z2 = 520, 1050                           # diagonal centreline at left / right prop
zc = lambda x: Z1 + (x + xp) * (Z2 - Z1) / (2*xp)
a_diag = math.atan2(Z2 - Z1, 2*xp)
hwz = (FW/2) / math.cos(a_diag)
yb0, yb1 = YP + H/2, YP + H/2 + FB
pl = cq.Plane(origin=(0, yb1, 0), xDir=(1, 0, 0), normal=(0, -1, 0))
diag = cq.Workplane(pl).polyline([(-xo, zc(-xo)-hwz), (xo, zc(xo)-hwz),
                                  (xo, zc(xo)+hwz), (-xo, zc(-xo)+hwz)]).close().extrude(FB)
for k, x in enumerate((-xp, xp)):
    hole = ycyl(x, zc(x), YP - H/2 - 1, yb1 + 1, HOLE)
    diag = diag.cut(hole)
    pn = "prop_L" if x < 0 else "prop_R"
    parts[pn] = parts[pn].cut(hole)
    bolt_y(f"diag_bolt_{'L' if x < 0 else 'R'}", x, zc(x), yb1, YP - H/2)
parts["rear_diagonal_150x40"] = diag
DIAG_LEN = 2*xo / math.cos(a_diag)

# ---------------- cross rails, mini-rails, panels, clamps ----------------
CR_HALF = 1200
CR_H = 70                                    # cross rails 45x70 on edge
for i, tc in enumerate(tcs):
    parts[f"cross_rail_{i+1}"] = slope(tc - T/2, tc + T/2, H/2, H/2 + CR_H, -CR_HALF, CR_HALF)
OM = H/2 + CR_H; PO = OM + MR
ex = GAP/2 + PW
for i, tc in enumerate(tcs):
    for k, (x0, x1) in enumerate(((-ex - 50, -ex + 70), (-60, 60), (ex - 70, ex + 50))):
        parts[f"mini_rail_{i+1}_{k+1}"] = slope(tc - 17, tc + 17, OM, PO, x0, x1)
parts["panel_1"] = slope(TP0, TP0 + PL, PO, PO + PT, -ex, -GAP/2)
parts["panel_2"] = slope(TP0, TP0 + PL, PO, PO + PT, GAP/2, ex)
# bottom ledge M (45x120 on edge) stands on the top face of both sloping rails B; its front-bottom edge
# just touches the top of base beam A, and its front face rests on a seat block N (45x95 laid flat, bevelled 45)
LP = 0; GUS = 0; MH = 120
MO = H/2
parts["bottom_ledge"] = slope(TP0 - T, TP0, MO, MO + MH, -CR_HALF, CR_HALF)
YC = P(TP0 - T, MO)[0]
WH, WW = 45, 95
for name, sg in (("L", -1), ("R", 1)):
    xo_, xi_ = sg*(XI + T), sg*(XI + T - WW)
    parts[f"seat_block_{name}"] = poly([(0, H), (YC, H), (YC - WH, H + WH), (0, H + WH)], xo_, xi_)
for i, tc in enumerate(tcs):
    hw[f"clampE_L_{i}"] = slope(tc-20, tc+20, PO, PO+PT+5, -ex-6, -ex).union(slope(tc-20, tc+20, PO+PT, PO+PT+5, -ex-6, -ex+15))
    hw[f"clampE_R_{i}"] = slope(tc-20, tc+20, PO, PO+PT+5, ex, ex+6).union(slope(tc-20, tc+20, PO+PT, PO+PT+5, ex-15, ex+6))
    hw[f"clampM_{i}"] = slope(tc-20, tc+20, PO, PO+PT+5, -GAP/2, GAP/2).union(slope(tc-20, tc+20, PO+PT, PO+PT+5, -25, 25))

# ---------------- pallets (simplified block pallets) ----------------
def pallet(tag, x0, x1, y0, y1):
    blk_h = PAL_H - 3*SLAT
    xs = (x0, (x0+x1)/2 - 50, x1 - 100)      # block / runner columns (left edge)
    ys = (y0, (y0+y1)/2 - 50, y1 - 100)
    for i, xa in enumerate(xs):
        parts[f"{tag}_bottom_{i}"] = box(xa, xa+100, y0, y1, 0, SLAT)
        parts[f"{tag}_stringer_{i}"] = box(xa, xa+100, y0, y1, SLAT+blk_h, 2*SLAT+blk_h)
        for j, ya in enumerate(ys):
            parts[f"{tag}_block_{i}{j}"] = box(xa, xa+100, ya, ya+100, SLAT, SLAT+blk_h)
    n = 7; pitch = (y1 - y0 - 100) / (n - 1)
    for k in range(n):
        ya = y0 + k*pitch
        parts[f"{tag}_deck_{k}"] = box(x0, x1, ya, ya+100, PAL_H-SLAT, PAL_H)
    return [(xa, ya) for xa in (xs[0], xs[2]) for ya in ys]

PX0 = -XI + 22
big = (PX0, PX0 + 980, BEAM - 1200, BEAM)
small = (PX0 + 980, PX0 + 980 + 880, BEAM - 900, BEAM)
pallet("pallet_big", *big)
pallet("pallet_small", *small)

# packers + coach screws: beam -> outer pallet blocks (2 per beam)
for name, sg, pal in (("L", -1, big), ("R", 1, small)):
    for ya in (pal[2] + 50, pal[3] - 50):
        parts[f"packer_{name}_{int(ya)}"] = box(sg*XI, sg*(XI-22), ya-50, ya+50, SLAT, PAL_H-2*SLAT)
        hw[f"coach_screw_{name}_{int(ya)}"] = xcyl(ya, SLAT + 39, sg*(XI+T+8), sg*(XI-22-70), 5)

# ---------------- weights + rough wind check ----------------
RHO_T = 550e-9           # treated timber kg/mm^3 (damp)
timber_kg = sum(w.val().Volume() for n, w in parts.items()
                if not n.startswith(("panel", "mini")) and "pallet" not in n) * RHO_T
pallet_kg = sum(w.val().Volume() for n, w in parts.items() if "pallet" in n) * RHO_T
panel_kg = 56.0

def cg_y(names):
    vs = [(parts[n].val().Volume(), parts[n].val().Center().y) for n in names]
    return sum(v*y for v, y in vs) / sum(v for v, _ in vs)

frame_names = [n for n in parts if not n.startswith(("panel", "mini")) and "pallet" not in n]
pal_names = [n for n in parts if "pallet" in n]
pan_names = [n for n in parts if n.startswith("panel")]
yc_p, zc_p = parts["panel_1"].val().Center().y, parts["panel_1"].val().Center().z

g = 9.81
V, RHO_A, CN, SF, MU = 27.0, 1.225, 1.3, 1.5, 0.6     # 60 mph gust, net normal coeff, safety, rubber mat on paving
F = 0.5*RHO_A*V*V*CN * (2*PL*PW/1e6)                   # N, normal to panels
Fy, Fz = F*s, F*c                                       # wind from behind: forward + uplift
Mo = Fz*yc_p/1000 + Fy*zc_p/1000                        # overturning about front toe (N m)
Mr0 = g*(timber_kg*cg_y(frame_names) + pallet_kg*cg_y(pal_names) + panel_kg*cg_y(pan_names))/1000
W0 = (timber_kg + pallet_kg + panel_kg)*g
YB = (BEAM - 3*BLOCK[1]/2)/1000                         # ballast centre y (3 rows at the back)
wb_tip = max(0, (SF*Mo - Mr0)/(g*YB))
wb_slide = max(0, (SF*Fy/MU + Fz - W0)/g)
wb = max(wb_tip, wb_slide)
n_blocks = math.ceil(wb / BLOCK[3])

# ---------------- ballast blocks ----------------
if BALLAST and n_blocks:
    bl, bw, bh, _ = BLOCK
    cols = [PX0 + 20, PX0 + 20 + bl + 20, small[0] + 10, small[0] + 10 + bl]
    placed = 0
    for layer in range(3):
        for row in range(3):
            for xc in cols:
                if placed >= n_blocks: break
                y1 = BEAM - row*bw
                hw[f"ballast_{placed:02d}"] = box(xc, xc + bl, y1 - bw, y1, PAL_H + layer*bh, PAL_H + (layer+1)*bh)
                placed += 1

# ---------------- checks ----------------
allp = {**parts, **hw}; nm = list(allp) if os.environ.get("CHECKS", "1") == "1" else []; adj = {n: set() for n in nm}
for a_, b_ in itertools.combinations(nm, 2):
    if a_.startswith("ballast") or b_.startswith("ballast"): continue
    if allp[a_].val().distance(allp[b_].val()) < 0.6: adj[a_].add(b_); adj[b_].add(a_)
seen = set(); comps = []
for n in nm:
    if n in seen or n.startswith("ballast"): continue
    st = [n]; comp = set()
    while st:
        k = st.pop()
        if k in comp: continue
        comp.add(k); st += list(adj[k])
    seen |= comp; comps.append(comp)
print("connected groups:", len(comps), [sorted(c_)[:3] for c_ in comps if len(c_) < 10])

CHECKS = os.environ.get("CHECKS", "1") == "1"
names = list(parts) if CHECKS else []; bad = []
for a_, b_ in itertools.combinations(names, 2):
    try: v = parts[a_].intersect(parts[b_]).val().Volume()
    except Exception: v = 0
    if v > 50: bad.append((a_, b_, round(v)))
print("overlaps:", bad)

# ---------------- report ----------------
bb = cq.Compound.makeCompound([w.val() for w in parts.values()]).BoundingBox()
panel_bb = cq.Compound.makeCompound([parts[n].val() for n in pan_names]).BoundingBox()
prop_len = PROP_LEN
print(f"footprint x {bb.xmin:.0f}..{bb.xmax:.0f}  y {bb.ymin:.0f}..{bb.ymax:.0f}  top z {bb.zmax:.0f}")
print(f"panel bottom edge z {panel_bb.zmin:.0f}, panel top z {panel_bb.zmax:.0f}, panel back edge y {panel_bb.ymax:.0f}")
print(f"rail {RAIL:.0f}  prop {prop_len:.0f}  diagonal {DIAG_LEN:.0f}  cross rail {2*CR_HALF}")
print(f"weights: timber {timber_kg:.0f} kg, pallets {pallet_kg:.0f} kg, panels {panel_kg:.0f} kg")
print(f"wind {V} m/s: normal {F:.0f} N, uplift {Fz:.0f} N, push {Fy:.0f} N, overturning {Mo:.0f} N m")
print(f"ballast needed: tipping {wb_tip:.0f} kg, sliding {wb_slide:.0f} kg -> {wb:.0f} kg = {n_blocks} blocks")

# ---------------- export ----------------
def col(n):
    if n.startswith("panel") and "pallet" not in n: return cq.Color(0.08, 0.12, 0.30)
    if n.startswith("mini"): return cq.Color(0.80, 0.80, 0.85)
    if n.startswith("ballast"): return cq.Color(0.55, 0.55, 0.55)
    if "pallet" in n: return cq.Color(0.70, 0.25, 0.20)
    if n == "rear_diagonal_150x40": return cq.Color(0.45, 0.28, 0.18)
    if n in hw: return cq.Color(0.60, 0.60, 0.65)
    return cq.Color(0.72, 0.55, 0.30)

asm = cq.Assembly(name="solar_ground_mount_v4")
for n, w in allp.items(): asm.add(w, name=n, color=col(n))
asm.export(f"{OUT}/solar_ground_mount_v4.step")
comp = cq.Compound.makeCompound([w.val() for w in allp.values()])
cq.exporters.export(cq.Workplane(obj=comp), f"{OUT}/solar_ground_mount_v4.stl", tolerance=0.5)
print(len(parts), "parts,", len(hw), "hardware items")

# ---------------- mesh dump for preview renders ----------------
import pickle
mesh = []
for n, w in allp.items():
    if n.endswith(("_washer_h", "_washer_n")): continue
    vs, ts = w.val().tessellate(1.0)
    cl = col(n).toTuple()[:3]
    mesh.append((n, [(v.x, v.y, v.z) for v in vs], ts, cl))
pickle.dump(mesh, open(f"{OUT}/mesh_v4.pkl", "wb"))

import json
json.dump(dict(H=H,T=T,FB=FB,FW=FW,BEAM=BEAM,PIV=PIV,XI=XI,YP=YP,TP0=TP0,MR=MR,CR_H=CR_H,CR_HALF=CR_HALF,
  PL=PL,PW=PW,GAP=GAP,PT=PT,RAIL=RAIL,T_END=T_END,tA=tA,zA=zA,tcs=tcs,PROP_LEN=PROP_LEN,LP=LP,GUS=GUS,MO=MO,YC=YC,WH=WH,WW=WW,MH=MH,LIP=MO+MH-(H/2+CR_H+MR),
  xp=xp,xo=xo,Z1=Z1,Z2=Z2,a_diag=math.degrees(a_diag),DIAG_LEN=DIAG_LEN,PAL_H=PAL_H,
  big=big,small=small,top=bb.zmax,ymin=bb.ymin,panel_zmin=panel_bb.zmin,panel_zmax=panel_bb.zmax,
  panel_ymax=panel_bb.ymax,timber_kg=timber_kg,pallet_kg=pallet_kg,wb_tip=wb_tip,wb_slide=wb_slide,n_blocks=n_blocks),
  open(f"{OUT}/dims_v4.json","w"),indent=1)
