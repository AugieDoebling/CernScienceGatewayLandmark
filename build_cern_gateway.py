"""
build_cern_gateway.py
=====================================================================
Parametric Blender builder for a Cities: Skylines II signature building:
CERN "Science Gateway" (Renzo Piano / RPBW, Geneva), on a plaza.

LAYOUT (single line along X, linked by a continuous elevated walkway at y=0):

  building1 -17m- building2 -17m- [TUBE1] -28m- [TUBE2] -18m- building3

REAL MEASUREMENTS (metres), provided by the user:
  building 1/2/3 : 43 x 43
  tube 1         : 90 long x 10 dia   tube 2 : 70 long x 10 dia
  gaps           : B1-B2 17, B2-T1 17, T1-T2 28, T2-B3 18
  => overall footprint ~229 x 90 m  (NB: CS2 max lot is 48 x 48 m;
     set SCALE below to shrink to fit, or keep 1.0 for true scale.)

WHAT IT PRODUCES (CS2 conventions)
  * Main mesh : CERN_ScienceGateway        (1 material, same name)
  * Glass     : CERN_ScienceGateway_Gls     (NO material)
  * Grass     : CERN_ScienceGateway_Gra     (NO material)
  * Windows   : CERN_ScienceGateway_Win     (NO material)
  * LOD1/LOD2 : <50% main tris / <=500 tris
  * Exports   : CERN_ScienceGateway.fbx  (binary FBX, Y-up, metres)
  Pivot bottom-centre, ground on Z=0, metric.

RUN:  blender --background --python build_cern_gateway.py
Tested on Blender 3.6 / 4.x / 5.x. Pure bpy, no add-ons.
=====================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

# ---------------------------------------------------------------------------
# PARAMS (metres)
# ---------------------------------------------------------------------------
ASSET_NAME = "CERN_ScienceGateway"

# Final uniform scale applied to everything just before export.
#   1.0   -> true scale (~229 m, oversized vs a CS2 lot)
#   ~0.21 -> ~48 m long, fits a 6x6 lot
SCALE = 1.0

# --- Element dimensions (real) ---------------------------------------------
BLD = 43.0                         # building footprint (43 x 43)
TUBE_DIA = 10.0
TUBE_R = TUBE_DIA / 2.0

# --- Sequence + gaps along X ----------------------------------------------
# building1, gap, building2, gap, tube1, gap, tube2, gap, building3
G_B1B2, G_B2T1, G_T1T2, G_T2B3 = 17.0, 17.0, 28.0, 18.0
TUBE1_LEN, TUBE2_LEN = 90.0, 70.0

# Walk the sequence left->right, then centre about x=0.
def _layout():
    x = 0.0
    spans = []  # (kind, centre, footprint_x)
    def place(kind, fx):
        nonlocal x
        c = x + fx / 2.0
        spans.append((kind, c, fx))
        x += fx
    place("b", BLD); x += G_B1B2
    place("b", BLD); x += G_B2T1
    place("t1", TUBE_DIA); x += G_T1T2
    place("t2", TUBE_DIA); x += G_T2B3
    place("b", BLD)
    total = x
    off = -total / 2.0
    return [(k, c + off, fx) for (k, c, fx) in spans], total

_SPANS, TOTAL_X = _layout()
BLD_X  = [c for (k, c, fx) in _SPANS if k == "b"]
TUBES  = [dict(x=c, length=TUBE1_LEN if k == "t1" else TUBE2_LEN)
          for (k, c, fx) in _SPANS if k in ("t1", "t2")]

# --- Heights (tube tops aligned with building roof tops) -------------------
PLAZA_TOP    = 0.40
GRASS_TOP    = 0.10
SPINE_Z      = 5.0                 # walkway deck top (== tube undersides)
SPINE_T      = 0.6
SPINE_W      = 6.0
RAIL_H       = 1.2
TUBE_Z       = SPINE_Z + TUBE_R    # centre -> bottom rests on the walkway (=5)
BLD_ROOF_Z   = TUBE_Z + TUBE_R     # roof top == tube top (=15)
BLD_ROOF_T   = 0.6
BLD_BODY_TOP = 11.0
BLD_OVERHANG = 2.5
COL_R        = 0.5

TUBE_WALL    = 0.40                # shell thickness (thick-walled rim)
TUBE_SETBACK = 5.0                # glazed end wall recessed inside the rim (~half dia)

# --- Site ------------------------------------------------------------------
MARGIN = 10.0
LOT_X  = TOTAL_X + 2 * MARGIN
LOT_Y  = max(BLD, TUBE1_LEN) + 2 * MARGIN
PLAZA_X = LOT_X - 4.0
PLAZA_Y = LOT_Y - 4.0
SPINE_X0 = BLD_X[0] + BLD / 2.0 - 2.0
SPINE_X1 = BLD_X[-1] - BLD / 2.0 + 2.0
# extend spine across the whole thing
SPINE_X0 = -TOTAL_X / 2.0 + 4.0
SPINE_X1 = TOTAL_X / 2.0 - 4.0

SEG_TUBE = 32
SEG_COL  = 10

OUT_DIR = os.path.dirname(bpy.data.filepath) or os.path.dirname(os.path.abspath(__file__))
if not OUT_DIR:
    OUT_DIR = os.getcwd()
FBX_PATH = os.path.join(OUT_DIR, ASSET_NAME + ".fbx")


# ---------------------------------------------------------------------------
def reset_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
        for item in list(block):
            try:
                block.remove(item)
            except Exception:
                pass
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------
def _new_obj_from_bm(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def add_box(name, sx, sy, sz, cx, cy, cz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)
    return _new_obj_from_bm(bm, name)


def add_cylinder(name, radius, depth, cx, cy, cz, segments, axis='Z', caps=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=True,
                          segments=segments, radius1=radius, radius2=radius, depth=depth)
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(math.radians(90.0), 3, 'Y'))
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)
    return _new_obj_from_bm(bm, name)


def add_strut(name, p0, p1, radius, seg=8):
    p0, p1 = Vector(p0), Vector(p1)
    vec = p1 - p0
    length = vec.length if vec.length > 1e-6 else 0.1
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=seg,
                          radius1=radius, radius2=radius, depth=length)
    rot = Vector((0, 0, 1)).rotation_difference(vec.normalized()).to_matrix()
    bmesh.ops.rotate(bm, verts=bm.verts, matrix=rot)
    bmesh.ops.translate(bm, vec=(p0 + p1) / 2.0, verts=bm.verts)
    return _new_obj_from_bm(bm, name)


def join_objects(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = name
    j.data.name = name
    return j


def set_origin_bottom_center(ob):
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')


def auto_smooth(ob, angle_deg=35.0):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_smooth()
    me = ob.data
    if hasattr(me, "use_auto_smooth"):
        me.use_auto_smooth = True
        me.auto_smooth_angle = math.radians(angle_deg)
    else:
        try:
            bpy.ops.object.shade_auto_smooth(angle=math.radians(angle_deg))
        except Exception:
            pass


def smart_uv(ob, angle=66.0, island_margin=0.02):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=island_margin)
    bpy.ops.object.mode_set(mode='OBJECT')


def clean_mesh(ob, thresh=0.0005):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=thresh)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def tri_count(ob):
    return sum((len(p.vertices) - 2) for p in ob.data.polygons)


def building_dict(x):
    return dict(x=x, y=0.0, sx=BLD, sy=BLD)


BUILDINGS = [building_dict(x) for x in BLD_X]


def perimeter_columns(p, z_bottom, z_top, parts, spacing=9.0):
    hx, hy = p["sx"] / 2.0, p["sy"] / 2.0
    h = z_top - z_bottom
    nx = max(1, round(p["sx"] / spacing))
    ny = max(1, round(p["sy"] / spacing))
    pts = set()
    for i in range(nx + 1):
        xx = -hx + p["sx"] * i / nx
        pts.add((round(xx, 2), -hy)); pts.add((round(xx, 2), hy))
    for j in range(ny + 1):
        yy = -hy + p["sy"] * j / ny
        pts.add((-hx, round(yy, 2))); pts.add((hx, round(yy, 2)))
    for (xx, yy) in pts:
        parts.append(add_cylinder("col", COL_R, h, p["x"] + xx, p["y"] + yy,
                                  z_bottom + h / 2.0, SEG_COL))


def uv_atlas_main(ob):
    """Two-region UV atlas on the main mesh (single material):
       * up-facing roof faces  -> right half  (U 0.5..1.0) = PV-panel texture
       * everything else       -> left half   (U 0.0..0.5) = concrete/steel
    Lets one texture show solar panels on the roofs only. Roofs overlap onto
    the same region (allowed for non-window/glass meshes)."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    uv = bm.loops.layers.uv.verify()
    roof_span = BLD + BLD_OVERHANG
    roof_z_min = BLD_ROOF_Z - 1.2
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.z > 0.85 and c.z > roof_z_min:          # roof top
            bx = min(BLD_X, key=lambda b: abs(b - c.x))
            for l in f.loops:
                co = l.vert.co
                u = min(max((co.x - bx) / roof_span + 0.5, 0.0), 1.0)
                v = min(max((co.y) / roof_span + 0.5, 0.0), 1.0)
                l[uv].uv = (0.5 + u * 0.5, v)               # right half
        else:                                               # concrete half
            for l in f.loops:
                cu, cv = l[uv].uv
                l[uv].uv = (cu * 0.5, cv)
    bm.to_mesh(me)
    bm.free()


def build_solid_tube(t):
    ob = add_cylinder("tube", TUBE_R, t["length"], t["x"], 0.0, TUBE_Z, SEG_TUBE,
                      axis='Y', caps=False)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    m = ob.modifiers.new("sol", 'SOLIDIFY')
    m.thickness = TUBE_WALL
    m.offset = -1.0
    bpy.ops.object.modifier_apply(modifier=m.name)
    return ob


# ---------------------------------------------------------------------------
def build_main():
    parts = []

    parts.append(add_box("plaza", PLAZA_X, PLAZA_Y, PLAZA_TOP - GRASS_TOP,
                         0, 0, (GRASS_TOP + PLAZA_TOP) / 2.0))

    # Continuous elevated walkway spine
    spine_len = SPINE_X1 - SPINE_X0
    spine_cx = (SPINE_X0 + SPINE_X1) / 2.0
    parts.append(add_box("spine", spine_len, SPINE_W, SPINE_T,
                         spine_cx, 0.0, SPINE_Z - SPINE_T / 2.0))
    n = max(6, int(spine_len / 14))
    for i in range(n + 1):
        cx = SPINE_X0 + spine_len * i / n
        h = SPINE_Z - SPINE_T - PLAZA_TOP
        parts.append(add_cylinder("spcol", 0.4, h, cx, 0.0, PLAZA_TOP + h / 2.0, SEG_COL))

    # Three PV pavilions
    for i, p in enumerate(BUILDINGS):
        parts.append(add_box(f"floor{i}", p["sx"] - 1, p["sy"] - 1, 0.4,
                             p["x"], p["y"], PLAZA_TOP + 0.2))
        parts.append(add_box(f"roof{i}", p["sx"] + BLD_OVERHANG, p["sy"] + BLD_OVERHANG,
                             BLD_ROOF_T, p["x"], p["y"], BLD_ROOF_Z - BLD_ROOF_T / 2.0))
        perimeter_columns(p, PLAZA_TOP, BLD_ROOF_Z - BLD_ROOF_T, parts)

    # Tubes (perpendicular, thick-walled open rims) + legs + interior reveal
    tube_bottom = TUBE_Z - TUBE_R
    inner_r = TUBE_R - TUBE_WALL
    for t in TUBES:
        tx, L = t["x"], t["length"]
        parts.append(build_solid_tube(t))
        hL = L / 2.0
        for frac in (0.9, 0.55, 0.2):                 # slanted legs along the span
            for s in (-1, 1):
                yy = s * frac * hL
                top = (tx, yy, tube_bottom)
                bot = (tx, yy + s * 3.5, PLAZA_TOP)
                parts.append(add_strut("leg", top, bot, 0.4, 8))
        for end in (-1, 1):                           # reveal sleeve at each end
            sl_cy = (hL - TUBE_SETBACK / 2.0) * end
            parts.append(add_cylinder("reveal", inner_r * 0.97, TUBE_SETBACK,
                                      tx, sl_cy, TUBE_Z, SEG_TUBE, axis='Y', caps=False))

    main = join_objects(parts, ASSET_NAME)
    clean_mesh(main)
    auto_smooth(main, 35.0)
    smart_uv(main)
    uv_atlas_main(main)        # remap into concrete | PV-panel atlas halves

    mat = bpy.data.materials.new(ASSET_NAME)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.62, 0.64, 0.66, 1.0)
    main.data.materials.clear()
    main.data.materials.append(mat)

    set_origin_bottom_center(main)
    return main


def build_glass():
    parts = []
    for p in BUILDINGS:
        parts.append(add_box("body", p["sx"] - 3.0, p["sy"] - 3.0,
                             BLD_BODY_TOP - (PLAZA_TOP + 0.4),
                             p["x"], p["y"], (PLAZA_TOP + 0.4 + BLD_BODY_TOP) / 2.0))
    inner_r = TUBE_R - TUBE_WALL
    for t in TUBES:
        hL = t["length"] / 2.0
        for end in (-1, 1):
            ey = (hL - TUBE_SETBACK) * end
            parts.append(add_cylinder("tubeglass", inner_r * 0.95, 0.08,
                                      t["x"], ey, TUBE_Z, SEG_TUBE, axis='Y'))
    spine_len = SPINE_X1 - SPINE_X0
    spine_cx = (SPINE_X0 + SPINE_X1) / 2.0
    for sy in (-1, 1):
        parts.append(add_box("rail", spine_len, 0.08, RAIL_H,
                             spine_cx, sy * SPINE_W / 2.0, SPINE_Z + RAIL_H / 2.0))
    g = join_objects(parts, ASSET_NAME + "_Gls")
    clean_mesh(g)
    auto_smooth(g, 40.0)
    smart_uv(g)
    g.data.materials.clear()
    set_origin_bottom_center(g)
    return g


def build_windows():
    parts = []
    for p in BUILDINGS:
        hx, hy = (p["sx"] - 2.0) / 2.0, (p["sy"] - 2.0) / 2.0
        zc = (PLAZA_TOP + BLD_BODY_TOP) / 2.0
        zh = (BLD_BODY_TOP - PLAZA_TOP) * 0.8
        for sy in (-1, 1):
            parts.append(add_box("win", p["sx"] - 4.0, 0.06, zh, p["x"], p["y"] + sy * hy, zc))
        for sx in (-1, 1):
            parts.append(add_box("win", 0.06, p["sy"] - 4.0, zh, p["x"] + sx * hx, p["y"], zc))
    w = join_objects(parts, ASSET_NAME + "_Win")
    smart_uv(w)
    w.data.materials.clear()
    set_origin_bottom_center(w)
    return w


def build_grass():
    g = add_box(ASSET_NAME + "_Gra", LOT_X, LOT_Y, GRASS_TOP, 0, 0, GRASS_TOP / 2.0)
    smart_uv(g)
    g.data.materials.clear()
    set_origin_bottom_center(g)
    return g


def build_lod1(main):
    bpy.ops.object.select_all(action='DESELECT')
    main.select_set(True)
    bpy.context.view_layer.objects.active = main
    bpy.ops.object.duplicate()
    lod = bpy.context.view_layer.objects.active
    lod.name = ASSET_NAME + "_LOD1"
    lod.data.name = lod.name
    m = lod.modifiers.new("dec", 'DECIMATE')
    m.ratio = 0.35
    bpy.ops.object.modifier_apply(modifier=m.name)
    set_origin_bottom_center(lod)
    return lod


def build_lod2():
    parts = []
    parts.append(add_box("l_plaza", PLAZA_X, PLAZA_Y, PLAZA_TOP, 0, 0, PLAZA_TOP / 2.0))
    parts.append(add_box("l_spine", SPINE_X1 - SPINE_X0, SPINE_W, SPINE_Z,
                         (SPINE_X0 + SPINE_X1) / 2.0, 0, SPINE_Z / 2.0))
    for i, p in enumerate(BUILDINGS):
        parts.append(add_box(f"l_b{i}", p["sx"], p["sy"], BLD_ROOF_Z, p["x"], p["y"], BLD_ROOF_Z / 2.0))
    for t in TUBES:
        parts.append(add_cylinder("l_tube", TUBE_R, t["length"], t["x"], 0, TUBE_Z, 10, axis='Y'))
    lod = join_objects(parts, ASSET_NAME + "_LOD2")
    clean_mesh(lod, 0.001)
    smart_uv(lod)
    mm = bpy.data.materials.get(ASSET_NAME)
    if mm:
        lod.data.materials.clear()
        lod.data.materials.append(mm)
    set_origin_bottom_center(lod)
    return lod


def apply_scale(objs):
    if abs(SCALE - 1.0) < 1e-6:
        return
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        o.scale = (SCALE, SCALE, SCALE)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def export_fbx(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=FBX_PATH, use_selection=True, object_types={'MESH'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', global_scale=1.0,
        use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=True,
        add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y',
        path_mode='COPY',
    )


def main():
    reset_scene()
    main_obj = build_main()
    glass    = build_glass()
    windows  = build_windows()
    grass    = build_grass()
    lod1     = build_lod1(main_obj)
    lod2     = build_lod2()
    objs = [main_obj, glass, windows, grass, lod1, lod2]
    apply_scale(objs)
    export_fbx(objs)

    print("\n" + "=" * 60)
    print("CERN Science Gateway built and exported.")
    print(f"  Footprint  : {TOTAL_X:.0f} x {LOT_Y - 2*MARGIN:.0f} m (x SCALE={SCALE})")
    print("  Main  tris :", tri_count(main_obj))
    print("  LOD1  tris :", tri_count(lod1), "(target < 50% of main)")
    print("  LOD2  tris :", tri_count(lod2), "(target <= 500)")
    print("  Glass tris :", tri_count(glass))
    print("  Win   tris :", tri_count(windows))
    print("  Grass tris :", tri_count(grass))
    print("  FBX        :", FBX_PATH)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
