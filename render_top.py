"""Top-down orthographic plan render. Run: blender --background --python render_top.py"""
import bpy, os, sys, math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import build_cern_gateway as bgw
bgw.main()

scene = bpy.context.scene

_mat = bpy.data.materials.get("CERN_ScienceGateway")
_bc = os.path.join(SCRIPT_DIR, "CERN_ScienceGateway_BaseColor.png")
if _mat and os.path.exists(_bc):
    _nt = _mat.node_tree
    _bsdf = _nt.nodes.get("Principled BSDF")
    _tex = _nt.nodes.new("ShaderNodeTexImage")
    _tex.image = bpy.data.images.load(_bc)
    _nt.links.new(_tex.outputs["Color"], _bsdf.inputs["Base Color"])
cam_data = bpy.data.cameras.new("Top")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 245
cam = bpy.data.objects.new("Top", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((0, 0, 220))
cam.rotation_euler = (0, 0, 0)
scene.camera = cam

sun_d = bpy.data.lights.new("S", 'SUN'); sun_d.energy = 3.0
sun = bpy.data.objects.new("S", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(35), math.radians(20), math.radians(40))

if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.5, 0.62, 0.78, 1.0); bg.inputs[1].default_value = 0.4
try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = eng; break
    except TypeError:
        continue
scene.render.resolution_x = 1500
scene.render.resolution_y = 640
out = os.path.join(SCRIPT_DIR, "CERN_ScienceGateway_top.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("TOP:", out)
