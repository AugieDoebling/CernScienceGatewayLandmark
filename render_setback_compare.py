"""Render the tube end at several setback depths for comparison.
Run: blender --background --python render_setback_compare.py"""
import bpy, os, sys, math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import build_cern_gateway as bgw

SETBACKS = [3.5, 5.0, 6.5]
BC = os.path.join(SCRIPT_DIR, "CERN_ScienceGateway_BaseColor.png")


def setup_look():
    # BaseColor on main material
    mat = bpy.data.materials.get("CERN_ScienceGateway")
    if mat and os.path.exists(BC):
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(BC)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    # temporary blue glass on the _Gls mesh so the recessed wall is visible
    g = bpy.data.objects.get("CERN_ScienceGateway_Gls")
    if g:
        gm = bpy.data.materials.new("preview_glass")
        gm.use_nodes = True
        b = gm.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (0.10, 0.22, 0.40, 1.0)
            if "Roughness" in b.inputs:
                b.inputs["Roughness"].default_value = 0.15
        g.data.materials.clear()
        g.data.materials.append(gm)


def render_one(setback):
    bgw.TUBE_SETBACK = setback
    bgw.main()
    scene = bpy.context.scene
    setup_look()

    tx = bgw.TUBES[0]["x"]
    end_y = bgw.TUBES[0]["length"] / 2.0
    target = Vector((tx, end_y - 5.0, bgw.TUBE_Z))
    cam_data = bpy.data.cameras.new("C"); cam_data.lens = 45
    cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam)
    cam.location = Vector((tx - 22.0, end_y + 32.0, bgw.TUBE_Z + 6.0))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam

    sd = bpy.data.lights.new("S", 'SUN'); sd.energy = 3.0; sd.use_shadow = True
    s = bpy.data.objects.new("S", sd); scene.collection.objects.link(s)
    s.rotation_euler = (math.radians(50), math.radians(8), math.radians(-30))
    # fill light pointing into the recess
    fd = bpy.data.lights.new("F", 'AREA'); fd.energy = 4000; fd.size = 12
    fo = bpy.data.objects.new("F", fd); scene.collection.objects.link(fo)
    fo.location = Vector((tx, end_y + 18.0, bgw.TUBE_Z + 2.0))
    fo.rotation_euler = (math.radians(-90), 0, 0)

    if not scene.world:
        scene.world = bpy.data.worlds.new("W")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.5, 0.62, 0.78, 1.0); bg.inputs[1].default_value = 0.5
    try:
        scene.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = eng; break
        except TypeError:
            continue
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 750
    out = os.path.join(SCRIPT_DIR, f"CERN_tubeend_setback_{setback:.1f}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("RENDER", setback, out)


for sb in SETBACKS:
    render_one(sb)
