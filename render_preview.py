"""
render_preview.py
Runs the CERN Science Gateway builder, then renders a 3/4 preview PNG.

Usage:
    blender --background --python render_preview.py
Outputs:
    CERN_ScienceGateway.fbx          (from the builder)
    CERN_ScienceGateway_preview.png  (this script)
"""
import bpy, os, sys, math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import build_cern_gateway as bgw

# Build + export the asset.
bgw.main()

scene = bpy.context.scene

# Load the BaseColor atlas onto the main material so panels/concrete show.
_mat = bpy.data.materials.get("CERN_ScienceGateway")
_bc = os.path.join(SCRIPT_DIR, "CERN_ScienceGateway_BaseColor.png")
if _mat and os.path.exists(_bc):
    _nt = _mat.node_tree
    _bsdf = _nt.nodes.get("Principled BSDF")
    _tex = _nt.nodes.new("ShaderNodeTexImage")
    _tex.image = bpy.data.images.load(_bc)
    _nt.links.new(_tex.outputs["Color"], _bsdf.inputs["Base Color"])

# --- Frame target: centre of the massing, a bit above ground ---
target = Vector((0.0, 0.0, 6.0))

# --- Camera (3/4 hero angle) ---
cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.lens = 42
cam = bpy.data.objects.new("PreviewCam", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((120.0, -280.0, 140.0))
direction = (target - cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# --- Sun ---
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), math.radians(15), math.radians(35))

# --- Sky-ish world ---
world = bpy.data.worlds.new("W") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.50, 0.62, 0.78, 1.0)
    bg.inputs[1].default_value = 0.35     # dimmer sky -> sun creates real contrast

# Clearer colours than the default AgX (which washes pale greys out)
try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass

# --- Render settings (EEVEE for speed; name differs across versions) ---
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        continue
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.film_transparent = False
out = os.path.join(SCRIPT_DIR, "CERN_ScienceGateway_preview.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("PREVIEW:", out)
