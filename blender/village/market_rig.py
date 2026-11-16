"""Skin the market characters and bake analytic two-bone IK into GLB joints."""
import math

import bpy
from mathutils import Matrix, Vector

from . import market, market_motion, scene
from .meshkit import MeshBuilder, S

SIDES = ((-1, "left"), (1, "right"))
STEP = 4
SLEEVE = ((1, 0), (1, 0), (0.85, 0), (0.50, 0), (0.05, 0), (0, 0.15), (0, 1))
CUFF = ((0, 0.37), (0, 0.58), (0, 1))


def arm_points(role, side, arm, scale):
    wrist = market.palm_frame(arm) @ market.WRIST
    return tuple(scale @ v for v in (market.shoulder_point(role, side), Vector(arm.elbow), wrist))


def bones(role):
    width, height = market.STYLES[role][-2:]
    scale = S(width, 1, height)
    pose = market.POSES[role]
    result = {"root": (None, Vector((0, 0, 0))),
              "head": ("root", scale @ market.torso_point((0, 0.03, 5.17), pose))}
    for (sign, side), arm in zip(SIDES, pose.arms):
        shoulder, elbow, wrist = arm_points(role, sign, arm, scale)
        result[side + "_upper"] = ("root", shoulder)
        result[side + "_fore"] = (side + "_upper", elbow)
        result[side + "_hand"] = (side + "_fore", wrist)
    return result


def solve_arm(start, rest_elbow, rest_end, target):
    upper, lower = (rest_elbow - start).length, (rest_end - rest_elbow).length
    direction = (target - start).normalized()
    distance = min(upper + lower - 0.001, max(abs(upper - lower) + 0.001, (target - start).length))
    reach = start + direction * distance
    bend = rest_elbow - start
    pole = (bend - direction * bend.dot(direction)).normalized()
    along = (upper * upper - lower * lower + distance * distance) / (2 * distance)
    elbow = start + direction * along + pole * math.sqrt(max(0, upper * upper - along * along))
    return elbow, reach


def skin_keys(role, rest):
    tracks = market_motion.TRACKS[role]
    names = [name for name in rest if name != "root"]
    channels = {name: [] for name in names}
    for frame in range(1, market_motion.DURATION * 24 + 2, STEP):
        seconds = (frame - 1) / 24
        local = {"head": market.rotations(market_motion.sample(tracks["head"], seconds)).to_3x3()}
        hand_motion = {}
        for side in ("right", "left"):
            start, elbow, wrist = (rest[side + "_" + key][1] for key in ("upper", "fore", "hand"))
            angles = market_motion.sample(tracks[side], seconds)
            aim = market.rotations(angles).to_3x3()
            if role == "lio" and side == "left":
                # Follow the same rigid pipe transform, including wrist orientation.
                right_rest, right_wrist, aim = hand_motion["right"]
                target = right_wrist + aim @ (wrist - right_rest)
            else:
                # Tip and draw the wrist in slightly, so the elbow flexes during the gesture.
                pull = min(0.094, math.radians(sum(abs(a) for a in angles)) * 0.23)
                target = start + aim @ (wrist - start) * (1 - pull)
            new_elbow, new_wrist = solve_arm(start, elbow, wrist, target)
            if role == "lio" and side == "left":
                assert (new_wrist - target).length < 0.006, (seconds, "support hand loses pipe contact")
            upper = (elbow - start).rotation_difference(new_elbow - start).to_matrix()
            fore = (wrist - elbow).rotation_difference(new_wrist - new_elbow).to_matrix()
            palm = aim if role == "lio" else market.rotations(tuple(a * 1.4 for a in angles)).to_3x3()
            hand_motion[side] = (wrist, new_wrist, palm)
            local[side + "_upper"] = upper
            local[side + "_fore"] = upper.inverted() @ fore
            local[side + "_hand"] = fore.inverted() @ palm
        for name in names:
            channels[name].append((frame, local[name].to_quaternion()))
    return channels


def new_armature(group, name, rest):
    data = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, data)
    group.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for joint, (parent, head) in rest.items():
        bone = data.edit_bones.new(joint)
        # Match the armature axes in every rest bone. The offsets lay out the limb.
        bone.head, bone.tail = head, head + Vector((0, 0.28, 0))
        if parent:
            bone.parent = data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.show_in_front = True
    return rig


def animate(rig, channels):
    for name, keys in channels.items():
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        previous = None
        for frame, value in keys:
            value = value.copy()
            if previous is not None:
                value.make_compatible(previous)
            bone.rotation_quaternion = value
            bone.keyframe_insert("rotation_quaternion", frame=frame, group=name)
            previous = value
        bone.rotation_quaternion = keys[0][1]
    for curve in rig.animation_data.action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = "LINEAR"


def weights(part, count, sleeve_end):
    if part in ("body", "head"):
        return [[("root" if part == "body" else "head", 1)]] * count
    if part.startswith("tool_"):
        return [[(part.removeprefix("tool_") + "_hand", 1)]] * count
    assert sleeve_end == len(SLEEVE) * market.SLEEVE_SEGMENTS
    cuff_end = sleeve_end + len(CUFF) * market.CUFF_SEGMENTS
    out = []
    for j in range(count):
        if j < sleeve_end:
            upper, hand = SLEEVE[j // market.SLEEVE_SEGMENTS]
        elif j < cuff_end:
            upper, hand = CUFF[(j - sleeve_end) // market.CUFF_SEGMENTS]
        else:
            upper, hand = 0, 1
        out.append([(part + "_" + key, value) for key, value in
                    (("upper", upper), ("fore", 1 - upper - hand), ("hand", hand)) if value > 0])
    return out


def bind(obj, rig, assignments):
    groups = {name: obj.vertex_groups.new(name=name) for name in rig.data.bones.keys()}
    for i, entries in enumerate(assignments):
        for name, value in entries:
            groups[name].add([i], value, "REPLACE")
    modifier = obj.modifiers.new("Merchant armature", "ARMATURE")
    modifier.object = rig
    obj.parent = rig


def create(group, role, seed, merged=False):
    parts, sleeves = market.merchant_parts(role, seed)
    rest = bones(role)
    channels = skin_keys(role, rest)
    name = "merchant_" + role
    rig = new_armature(group, name + "_rig", rest)
    whole = MeshBuilder()
    combined_weights = []
    models = []
    for part, mesh in parts.items():
        entries = weights(part, len(mesh.verts), sleeves.get(part))
        whole.merge(mesh)
        combined_weights.extend(entries)
        if not merged:
            obj = mesh.to_object(name + "_" + part, scene.TEXTURE_PATH, group)
            bind(obj, rig, entries)
            models.append(obj)
    if merged:
        obj = whole.to_object(name, scene.TEXTURE_PATH, group)
        bind(obj, rig, combined_weights)
        models.append(obj)
    animate(rig, channels)
    return rig, models, whole, channels
