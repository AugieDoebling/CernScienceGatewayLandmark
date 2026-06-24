"""Close-up of one tube end to check the recessed glass offset.
Run: blender --background --python render_tubeend.py"""
import bpy, os, sys, math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import build_cern_gateway as bgw
bgw.main()

scene = bpy.context.scene

# BaseColor onto the material
_mat = bpy.data.materials.get("CERN_ScienceGateway")
_bc = os.path.join(SCRIPT_DIR, "CERN_ScienceGateway_BaseColor.png")
if _mat and os.path.exists(_bc):
    nt = _mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(_bc)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

# Frame the +Y end of tube 1 (x=10.5, ends at y=+45, axis z=10)
tx = bgw.TUBES[0]["x"]
end_y = bgw.TUBES[0]["length"] / 2.0
target = Vector((tx, end_y - 4.0, bgw.TUBE_Z))

cam_data = bpy.data.cameras.new("C"); cam_data.lens = 45
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam)
cam.location = Vector((tx - 24.0, end_y + 34.0, bgw.TUBE_Z + 7.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

sun_d = bpy.data.lights.new("S", 'SUN'); sun_d.energy = 3.5; sun_d.use_shadow = True
sun = bpy.data.objects.new("S", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(10), math.radians(-25))

if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.5, 0.62, 0.78, 1.0); bg.inputs[1].default_value = 0.45
try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = eng; break
    except TypeError:
        continue
scene.render.resolution_x = 1280
scene.render.resolution_y = 800
out = os.path.join(SCRIPT_DIR, "CERN_ScienceGateway_tubeend.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("TUBEEND:", out, "SETBACK=", bgw.TUBE_SETBACK)
