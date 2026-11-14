"""Scene, lighting, camera and render helpers (Cycles on CPU, headless)."""
import math
import os

import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEXTURE_PATH = os.path.join(ROOT, "exports", "textures", "village_palette.png")


def path(*parts):
    return os.path.join(ROOT, *parts)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def setup_render(scene, res=(1600, 900), samples=48):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 1
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.render.threads_mode = "AUTO"


def setup_light(scene, sun_az=215.0, sun_el=42.0, sun_strength=3.4, sky=(0.60, 0.78, 1.0),
                sky_strength=0.85):
    """Warm sun + uniform sky light. Azimuth measured from +X towards +Y."""
    world = bpy.data.worlds.new("VillageSky")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*sky, 1.0)
    bg.inputs["Strength"].default_value = sky_strength
    scene.world = world
    light = bpy.data.lights.new("Sun", "SUN")
    light.energy = sun_strength
    light.color = (1.0, 0.95, 0.84)
    light.angle = math.radians(3.0)
    sun = bpy.data.objects.new("Sun", light)
    scene.collection.objects.link(sun)
    az, el = math.radians(sun_az), math.radians(sun_el)
    direction = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    sun.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return sun


def add_camera(scene, name="Camera"):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.clip_start = 0.5
    cam.data.clip_end = 5000
    return cam


def aim(cam, eye, target):
    eye, target = Vector(eye), Vector(target)
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()


def orbit(cam, target, az, el, dist):
    az, el = math.radians(az), math.radians(el)
    t = Vector(target)
    eye = t + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * dist
    aim(cam, eye, t)


def frame_bounds(cam, bmin, bmax, az=-60.0, el=22.0, lens=50.0, margin=0.78, aspect=16 / 9):
    """Perspective camera that frames an axis-aligned box."""
    cam.data.type = "PERSP"
    cam.data.lens = lens
    centre = (Vector(bmin) + Vector(bmax)) / 2
    radius = (Vector(bmax) - Vector(bmin)).length / 2
    fov_h = 2 * math.atan(36 / (2 * lens))
    fov_v = 2 * math.atan(math.tan(fov_h / 2) / aspect)
    dist = radius / math.sin(min(fov_h, fov_v) / 2) * margin
    orbit(cam, centre, az, el, dist)
    return dist


def ground_plane(scene, size=400.0, color="grass", z=0.0):
    from . import palette
    mesh = bpy.data.meshes.new("PreviewGround")
    s = size / 2
    mesh.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [], [(0, 1, 2, 3)])
    uvl = mesh.uv_layers.new(name="UVMap")
    u, v = palette.uv(color, 0.5)
    uvl.data.foreach_set("uv", [u, v] * 4)
    mesh.materials.append(palette.get_material(TEXTURE_PATH))
    obj = bpy.data.objects.new("PreviewGround", mesh)
    scene.collection.objects.link(obj)
    return obj


def render(scene, filepath):
    filepath = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    return filepath
