"""Five alchemy traders and their market stands, facing Blender -Y."""
import math
from dataclasses import dataclass, replace

from mathutils import Vector

from .machines import bottle
from .meshkit import MeshBuilder, R, S, T

STYLES = {
    "selma": ("cloth_green", "pine", "wood_pale", "plaster_peach", "wood_red", 1.0, 1.0),
    "nyra": ("roof_purple", "roof_slate", "glass_light", "plaster_rose", "wood_grey", 0.93, 1.02),
    "lio": ("cloth_blue", "roof_teal", "wood_mid", "wood_light", "wood_dark", 0.94, 0.98),
    "aron": ("roof_red", "iron", "wood_red", "plaster_peach", "wood_dark", 1.23, 0.95),
    "esme": ("roof_teal", "leaf_dark", "wood_mid", "sand", "wood_red", 0.98, 1.07),
}


def sprig(mb, x, y, z, scale=1, color="leaf_green"):
    mb.beam((x, y, z), (x + 0.07 * scale, y, z + 0.9 * scale), 0.055 * scale, 0.055 * scale, "leaf_dark")
    for i in range(4):
        sign = 1 if i % 2 else -1
        with mb.at(T(x + sign * 0.15 * scale, y, z + (i + 1) * 0.19 * scale), R("Y", sign * 31)):
            mb.blob(0.23 * scale, color, scale=(0.65, 0.36, 1.22), level=0, noise=0.07,
                    grad=(0.38, 0.73))


def mushroom(mb, x, y, z, scale=1):
    mb.cyl(0.13 * scale, 0.11 * scale, 0.45 * scale, "plaster_cream", (x, y, z), segs=6, smooth=False)
    mb.lathe([(0.18 * scale, 0.34 * scale), (0.41 * scale, 0.40 * scale),
              (0.34 * scale, 0.62 * scale), (0.13 * scale, 0.73 * scale)],
             "roof_purple", segs=8, pos=(x, y, z), smooth=False)
    for dx, dy, dz in ((-0.16, -0.16, 0.59), (0.18, -0.12, 0.60), (0.0, 0.14, 0.67)):
        mb.blob(0.06 * scale, "flower_purple", (x + dx * scale, y + dy * scale, z + dz * scale),
                scale=(1, 1, 0.58), level=0, noise=0)


def crystal(mb, x, y, z, scale=1, color="glass_light"):
    with mb.at(T(x, y, z), R("Y", -12)):
        mb.lathe([(0.21 * scale, 0), (0.29 * scale, 0.3 * scale), (0.19 * scale, 0.82 * scale),
                  (0.04 * scale, 1.05 * scale)], color, segs=5, smooth=False, grad=(0.34, 0.86))


def flask_case(mb, x, y, z, scale=1):
    mb.box(0.8 * scale, 0.6 * scale, 0.10 * scale, "brass", (x, y, z))
    mb.box(0.59 * scale, 0.43 * scale, 0.58 * scale, "glass_lit", (x, y, z + 0.09 * scale))
    mb.box(0.8 * scale, 0.6 * scale, 0.12 * scale, "iron", (x, y, z + 0.62 * scale))
    for dx in (-0.32, 0.32):
        for dy in (-0.22, 0.22):
            mb.box(0.07 * scale, 0.07 * scale, 0.6 * scale, "iron",
                   (x + dx * scale, y + dy * scale, z + 0.09 * scale))


# The bare head is 0.83 studs high and the body is about six studs tall.
# All faces and costumes use the same -Y front as the village assets.
HEAD = (
    (5.21, 0.091, 0.122, -0.048),
    (5.27, 0.161, 0.173, -0.043),
    (5.34, 0.217, 0.203, -0.028),
    (5.43, 0.248, 0.223, -0.009),
    (5.51, 0.265, 0.232, 0.006),
    (5.60, 0.274, 0.228, 0.014),
    (5.67, 0.277, 0.234, 0.019),
    (5.74, 0.275, 0.247, 0.031),
    (5.81, 0.270, 0.257, 0.040),
    (5.91, 0.237, 0.238, 0.052),
    (6.00, 0.162, 0.171, 0.061),
    (6.04, 0.050, 0.060, 0.063),
)
@dataclass(frozen=True)
class Face:
    width: float
    jaw: float
    nose: float
    nose_width: float
    cheek: float
    eye_width: float
    eye_height: tuple
    gaze: tuple
    brow: tuple
    mouth: tuple


FACES = {
    "selma": Face(1.04, 0.96, 0.083, 0.055, 0.033, 0.066, (0.71, 0.76), (0.014, -0.009),
                  (0.022, 0.033), ((-0.082, 5.422), (-0.044, 5.404), (0.039, 5.397), (0.088, 5.436))),
    "nyra": Face(0.90, 0.88, 0.124, 0.041, 0.021, 0.061, (0.91, 1.06), (-0.015, 0.004),
                 (0.010, 0.034), ((-0.057, 5.406), (-0.027, 5.407), (0.031, 5.403), (0.062, 5.397))),
    "lio": Face(0.95, 0.92, 0.070, 0.046, 0.019, 0.066, (0.53, 0.86), (0.023, 0.005),
                (0.035, 0.011), ()),
    "aron": Face(1.12, 1.19, 0.098, 0.065, 0.029, 0.064, (0.84, 0.63), (0.004, 0.003),
                 (-0.009, 0.013), ((-0.091, 5.404), (-0.034, 5.400), (0.039, 5.407), (0.087, 5.429))),
    "esme": Face(0.97, 1.02, 0.078, 0.042, 0.025, 0.069, (0.67, 0.82), (-0.018, 0.004),
                 (0.009, 0.030), ((-0.080, 5.405), (-0.035, 5.398), (0.029, 5.405), (0.080, 5.420))),
}


@dataclass(frozen=True)
class Arm:
    elbow: tuple             # x, y, z in the figure's frame
    palm: tuple
    angles: tuple            # pitch, roll, heading in degrees
    fingers: str = "grip"


@dataclass(frozen=True)
class Leg:
    foot: tuple              # x, y, toe heading in degrees. Soles stay on the ground.
    knee: tuple


@dataclass(frozen=True)
class Pose:
    pelvis: tuple            # x, y offset
    chest: tuple             # x, y offset, drop at the neck
    twist: float
    shoulder_tilt: float
    head: tuple              # pitch, roll, heading in degrees
    arms: tuple
    legs: tuple


POSES = {
    # She stoops over a basket, picking out one sprig with her free hand.
    "selma": Pose((-0.11, 0.04), (0.10, -0.22, 0.15), 13, -0.12, (13, -10, 24), (
        Arm((-0.55, -0.46, 3.88), (0.21, -0.80, 3.88), (40, -37, -9), "pinch"),
        Arm((0.66, -0.35, 3.63), (0.55, -0.67, 3.60), (4, 7, 9)),
    ), (
        Leg((-0.31, 0.05, -11), (-0.30, -0.10, 1.76)),
        Leg((0.21, -0.22, 8), (0.21, -0.29, 1.60)),
    )),
    # She raises a crystal into the lantern light and cocks her head.
    "nyra": Pose((0.07, 0.04), (-0.14, -0.03, 0.06), -13, 0.08, (4, -17, -25), (
        Arm((-0.83, -0.35, 4.03), (-0.58, -0.84, 4.92), (5, -24, -13), "pinch"),
        Arm((0.60, -0.22, 3.96), (0.37, -0.82, 4.14), (5, -7, 9)),
    ), (
        Leg((-0.28, -0.15, -9), (-0.21, -0.20, 1.63)),
        Leg((0.28, 0.06, 14), (0.30, 0.08, 1.80)),
    )),
    # His gaze follows the glass while he blows into a diagonally held pipe.
    "lio": Pose((-0.09, 0.06), (0.10, -0.18, 0.14), 17, 0.12, (10, -6, 30), (
        Arm((-0.40, -0.21, 3.94), (0.17, -0.72, 4.62), (-49, -39, -7), "open"),
        Arm((0.79, -0.36, 4.17), (0.64, -0.76, 5.04), (-12, 9, 8)),
    ), (
        Leg((-0.32, -0.30, -16), (-0.28, -0.35, 1.66)),
        Leg((0.24, 0.22, 4), (0.24, 0.19, 1.80)),
    )),
    # A grounded, open stance, one hand on his hip and a hammer at his shoulder.
    "aron": Pose((-0.06, 0.02), (-0.16, 0.02, -0.03), -7, 0.14, (-5, 8, -9), (
        Arm((-0.88, -0.14, 3.88), (-0.50, -0.13, 3.46), (-28, 21, 65), "relaxed"),
        Arm((0.70, 0.02, 3.92), (0.73, -0.45, 4.71), (4, 2, -7)),
    ), (
        Leg((-0.42, -0.02, -19), (-0.42, -0.12, 1.71)),
        Leg((0.39, -0.10, 17), (0.36, -0.16, 1.69)),
    )),
    # She has just stepped over, lowering her axe and flicking out a folding rule.
    "esme": Pose((0.16, 0.07), (-0.06, -0.07, 0.03), 21, -0.15, (-3, -12, -28), (
        Arm((-0.82, -0.02, 3.62), (-0.79, -0.41, 3.20), (20, 80, -16)),
        Arm((0.67, -0.11, 3.90), (0.47, -0.73, 3.92), (-5, 18, -29)),
    ), (
        Leg((-0.18, 0.22, -5), (-0.13, 0.13, 1.82)),
        Leg((0.39, -0.43, 16), (0.39, -0.41, 1.56)),
    )),
}


def rotations(angles):
    pitch, roll, heading = angles
    return R("Z", heading) @ R("Y", roll) @ R("X", pitch)


def torso_point(v, pose):
    x, y, z = v
    t = min(1, max(0, (z - 3.04) / 1.97))
    angle = math.radians(pose.twist * t)
    x1, y1 = x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)
    hip_x, hip_y = pose.pelvis
    chest_x, chest_y, drop = pose.chest
    return Vector((x1 + (1 - t) * hip_x + t * chest_x,
                   y1 + (1 - t) * hip_y + t * chest_y,
                   z + t * (x * pose.shoulder_tilt - drop)))


def head_frame(pose):
    base = Vector((0, 0.03, 5.17))
    return T(*torso_point(base, pose)) @ rotations(pose.head) @ T(*(-base))


def sweep(mb, sections, color, segments=10, end_axis=None, **shading):
    """Smooth elliptical rings perpendicular to a curved sleeve, limb or lock of hair."""
    centers = [Vector(p) for p, _, _ in sections]
    rings = []
    for i, (p, rx, ry) in enumerate(sections):
        if end_axis is not None and i == len(centers) - 1:
            axis = end_axis
        else:
            axis = (centers[min(i + 1, len(centers) - 1)] - centers[max(i - 1, 0)]).normalized()
        side = Vector((1, 0, 0))
        if abs(axis.dot(side)) > 0.96:
            side = Vector((0, 0, 1))
        side = (side - axis * side.dot(axis)).normalized()
        across = axis.cross(side)
        rings.append([Vector(p) + side * (rx * math.cos(math.tau * j / segments))
                      + across * (ry * math.sin(math.tau * j / segments)) for j in range(segments)])
    mb.loft(rings, color, smooth=True, **shading)


def folds(mb, profile, color, depth=0.0, segments=20, phase=0.0, **shading):
    """A fitted horizontal profile, with most pleat depth concentrated at the hem."""
    rings = []
    for cx, cy, z, rx, ry, fullness in profile:
        ring = []
        for i in range(segments):
            a = math.tau * i / segments
            f = depth * fullness * (math.cos(5 * a + phase) + 0.36 * math.sin(8 * a - phase))
            ring.append((cx + (rx + f) * math.cos(a), cy + (ry + f) * math.sin(a),
                         z + 0.13 * fullness * math.sin(2 * a + phase)))
        rings.append(ring)
    mb.loft(rings, color, smooth=True, **shading)


def gaussian(x, scale):
    return math.exp(-(x / scale) ** 2)


def head_section(z, role):
    face = FACES[role]
    for low, high in zip(HEAD, HEAD[1:]):
        if z <= high[0]:
            t = (z - low[0]) / (high[0] - low[0])
            rx, ry, cy = (a + (b - a) * t for a, b in zip(low[1:], high[1:]))
            return rx * face.width * (1 + (face.jaw - 1) * gaussian(z - 5.33, 0.19)), ry, cy
    return HEAD[-1][1:]


def face_y(x, z, role):
    """Sculpt the bridge, sockets, cheeks and lips into the head surface."""
    rx, ry, cy = head_section(z, role)
    front = math.sqrt(max(0, 1 - (x / rx) ** 2))
    face = FACES[role]
    nose = face.nose * gaussian(x, face.nose_width) * gaussian(z - 5.531, 0.086)
    cheek = face.cheek * gaussian(abs(x) - 0.154, 0.074) * gaussian(z - 5.51, 0.071)
    socket = 0.022 * gaussian(abs(x) - 0.122, 0.064) * gaussian(z - 5.633, 0.042)
    muzzle = 0.022 * gaussian(x, 0.092) * gaussian(z - 5.413, 0.060)
    return cy - ry * front - (nose + cheek + muzzle - socket) * front


def face_curve(mb, outline, role, color, radius, offset=0.014):
    sections = [((x, face_y(x, z, role) - offset, z), radius * width, radius * 0.58)
                for x, z, width in outline]
    sweep(mb, sections, color, segments=6, grad=(0.50, 0.61))


def make_face(mb, role, skin, hair):
    face = FACES[role]
    rings = []
    for z, _, _, _ in HEAD:
        rx, ry, cy = head_section(z, role)
        ring = []
        for i in range(32):
            angle = math.tau * i / 32
            x = rx * math.sin(angle)
            y = face_y(x, z, role) if math.cos(angle) >= 0 else cy - ry * math.cos(angle)
            ring.append((x, y, z))
        rings.append(ring)
    mb.loft(rings, skin, smooth=True, grad=(0.45, 0.65))

    iris = {"selma": "leaf_dark", "nyra": "roof_slate", "lio": "wood_red",
            "aron": "glass_blue", "esme": "wood_dark"}[role]
    for i, side in enumerate((-1, 1)):
        mb.blob(0.093, skin, (side * 0.263 * face.width, 0.017, 5.574),
                scale=(0.47, 0.66, 1.18), level=1, noise=0, smooth=True)
        z, x = 5.633, side * (0.108 + 0.011 * face.width)
        half, opening = face.eye_width, face.eye_height[i]
        eye_shape = ((-1.0, 0.0), (-0.59, -0.017), (0.44, -0.017),
                     (0.94, 0.004), (0.42, 0.023), (-0.53, 0.021))
        outline = [(x + xx * half, z + zz * opening) for xx, zz in eye_shape]
        front = [(px, face_y(px, zz, role) - 0.012, zz) for px, zz in outline]
        mb.poly(front, "cloth_white", facing=(0, -1, 0), grad=(0.38, 0.45))

        pupil_x, pupil_z = x + face.gaze[0], z + face.gaze[1] * opening
        pupil_y = face_y(pupil_x, pupil_z, role) - 0.022
        mb.blob(0.023, iris, (pupil_x, pupil_y, pupil_z), scale=(1, 0.28, opening),
                level=0, noise=0, smooth=True)
        mb.blob(0.011, "iron", (pupil_x, pupil_y - 0.004, pupil_z),
                scale=(1, 0.25, opening), level=0, noise=0)
        face_curve(mb, [(x - half, z + 0.001, 0.35), (x - half * 0.52, z + 0.022 * opening, 1),
                        (x + half * 0.38, z + 0.025 * opening, 1), (x + half, z + 0.004, 0.35)],
                   role, hair, 0.009, 0.016)

        lift = face.brow[i]
        face_curve(mb, [(side * 0.052, 5.699 + lift * 0.76, 0.65), (side * 0.108, 5.712 + lift, 1.1),
                        (side * 0.164, 5.699 + lift, 0.91), (side * 0.194, 5.681 + lift * 0.69, 0.25)],
                   role, hair, 0.016 if role == "aron" else 0.010, 0.013)

        if role in ("nyra", "aron"):
            face_curve(mb, [(side * 0.139, 5.595, 0.25), (side * 0.173, 5.600, 0.65),
                            (side * 0.198, 5.614, 0.19)], role, "wood_mid", 0.004, 0.008)
        if role == "selma":
            for xx, zz in ((0.133, 5.568), (0.157, 5.574), (0.166, 5.551)):
                xx *= side
                mb.blob(0.0065, "wood_mid", (xx, face_y(xx, zz, role) - 0.012, zz),
                        scale=(1, 0.35, 0.86), level=0, noise=0)

    if face.mouth:
        outline = [(*point, width) for point, width in zip(face.mouth, (0.28, 1.0, 0.91, 0.31))]
        face_curve(mb, outline, role, "wood_red", 0.008, 0.014)
    else:
        # Narrow aperture around Lio's pipe. The dark inset and lip rim share the same contour.
        points = [(0.034 * math.cos(i * math.tau / 10), 5.406 + 0.019 * math.sin(i * math.tau / 10))
                  for i in range(10)]
        mb.poly([(x, face_y(x, z, role) - 0.017, z) for x, z in points], "wood_dark", facing=(0, -1, 0))
        face_curve(mb, [(*v, 0.55) for v in points + [points[0]]], role, "plaster_rose", 0.010, 0.018)
    if role == "esme":
        face_curve(mb, [(-0.154, 5.732, 0.24), (-0.146, 5.705, 0.76), (-0.132, 5.683, 0.21)],
                   role, "stone_light", 0.006, 0.028)


def scalp(mb, role, hair, hood=False):
    width = FACES[role].width
    rings = []
    for step, radii in enumerate(((0.290, 0.255), (0.303, 0.264), (0.288, 0.266), (0.239, 0.246),
                                 (0.163, 0.182), (0.056, 0.071))):
        rx, ry = radii
        sx, sy = (1.19, 1.18) if hood else (1, 1)
        ring = []
        for i in range(24):
            a = math.tau * i / 24
            f = (1 + math.cos(a)) / 2
            if hood:
                low = 4.94 + 0.54 * f + 0.30 * f ** 8
            else:
                low = 5.35 + 0.41 * f ** 1.8
            crown = 6.23 if hood else 6.07
            z = low + (crown - low) * step / 5
            z += 0.065 * math.sin(a) * (1 - step / 5)
            x = rx * sx * width * math.sin(a)
            # Pull the sides of the hood around the cheeks, leaving the face visible.
            y = 0.068 - ry * sy * math.cos(a)
            if hood:
                y += 0.102 * (1 - step / 5) * f + 0.095 * (step / 5) ** 1.7
                x += 0.14 * (step / 5) ** 2
            ring.append((x, y, z))
        rings.append(ring)
    mb.loft(rings, hair, smooth=True, hide0=True, grad=(0.33, 0.65))


def hair_and_beard(mb, role, hair):
    scalp(mb, role, hair)
    if role in ("selma", "nyra", "esme"):
        for side in (-1, 1):
            sweep(mb, [((side * 0.205, -0.074, 5.826), 0.053, 0.055),
                       ((side * 0.257, -0.114, 5.554), 0.051, 0.058),
                       ((side * 0.233, -0.217, 5.262), 0.049, 0.045),
                       ((side * 0.166, -0.209, 5.102), 0.009, 0.010)], hair, segments=8)
    if role == "selma":
        braid = [(-0.225 - 0.012 * i, 0.084 - 0.024 * i, 5.53 - 0.103 * i) for i in range(11)]
        for i, p in enumerate(braid):
            mb.blob(0.092 - i * 0.0035, hair, (p[0] + (0.016 if i % 2 else -0.016), p[1], p[2]),
                    scale=(0.85, 0.90, 1.15), level=0, noise=0, smooth=True, tone=0.025 * (i % 2))
    if role == "aron":
        folds(mb, [(0, -0.124, 5.071, 0.064, 0.058, 0.5), (0, -0.12, 5.18, 0.178, 0.115, 0.37),
                   (0, -0.124, 5.31, 0.242, 0.126, 0.21), (0, -0.094, 5.458, 0.277, 0.094, 0)],
              hair, 0.044, segments=16, grad=(0.35, 0.62))
        for side in (-1, 1):
            sweep(mb, [((side * 0.018, -0.249, 5.438), 0.017, 0.012),
                       ((side * 0.081, -0.266, 5.431), 0.037, 0.029),
                       ((side * 0.161, -0.226, 5.416), 0.006, 0.006)], hair, segments=8)
            sweep(mb, [((side * 0.104, -0.209, 5.28), 0.045, 0.043),
                       ((side * 0.097, -0.222, 5.12), 0.036, 0.034),
                       ((side * 0.089, -0.209, 5.018), 0.015, 0.015)], hair, segments=8)
            mb.cyl(0.038, 0.037, 0.039, "brass", (side * 0.097, -0.221, 5.11), segs=8)


def ellipse(mb, profile, color, segments=14, **shading):
    folds(mb, [(*row, 0) for row in profile], color, segments=segments, **shading)


def headwear(mb, role, cloth, trim):
    if role == "selma":
        folds(mb, [(0, 0, 5.895, 0.425, 0.377, 0), (0, 0, 5.884, 0.78, 0.63, 0.15),
                   (-0.025, 0.025, 5.956, 0.759, 0.622, 0.22),
                   (0, 0.013, 5.972, 0.309, 0.292, 0)], trim, 0.08)
        ellipse(mb, [(0, 0.022, 5.95, 0.307, 0.288), (0.025, 0.038, 6.143, 0.267, 0.243),
                    (0.115, 0.057, 6.365, 0.192, 0.179), (0.259, 0.075, 6.534, 0.099, 0.103),
                    (0.395, 0.042, 6.586, 0.014, 0.018)], cloth, grad=(0.36, 0.72))
        ellipse(mb, [(0, 0.024, 5.98, 0.315, 0.302), (0.008, 0.03, 6.088, 0.302, 0.288)], "wood_dark")
        sprig(mb, -0.22, -0.134, 5.99, 0.35, "leaf_lime")
        mb.blob(0.072, "flower_yellow", (-0.235, -0.267, 6.067), level=1, noise=0, smooth=True)
    elif role == "nyra":
        scalp(mb, role, trim, hood=True)
        crescent = [(-0.106, 0.096), (-0.008, 0.126), (0.087, 0.073), (0.112, -0.027),
                    (0.05, -0.103), (-0.061, -0.111), (0.01, -0.049), (0.031, 0.018),
                    (-0.01, 0.074)]
        with mb.at(T(0.075, -0.274, 5.887)):
            mb.prism(crescent, -0.012, 0.025, "brass")
    elif role == "lio":
        ellipse(mb, [(0, 0.062, 5.891, 0.272, 0.25), (-0.009, 0.068, 6.011, 0.27, 0.238),
                    (-0.08, 0.089, 6.13, 0.141, 0.121)], trim)
        ellipse(mb, [(0, 0.057, 5.883, 0.278, 0.258), (-0.005, 0.063, 5.956, 0.285, 0.259)], "wood_dark")
        for side in (-1, 1):
            with mb.at(T(side * 0.128, -0.211, 5.929), R("Z", side * 16), R("X", 91)):
                mb.cyl(0.099, 0.102, 0.064, "brass", segs=12)
                mb.cyl(0.076, 0.075, 0.015, "glass_light", (0, 0, 0.064), segs=12)
    elif role == "aron":
        ellipse(mb, [(0, 0.046, 5.859, 0.316, 0.276), (0.014, 0.062, 6.013, 0.298, 0.253),
                    (0.06, 0.112, 6.109, 0.132, 0.132)], trim)
        ellipse(mb, [(0, 0.044, 5.836, 0.321, 0.284), (0.011, 0.052, 5.897, 0.316, 0.279)], cloth)
    else:
        with mb.at(T(0, 0, 5.933), R("Y", -9)):
            folds(mb, [(0, -0.01, -0.04, 0.636, 0.482, 0.36), (0, -0.01, 0.02, 0.65, 0.491, 0.32),
                       (0, 0.012, 0.075, 0.282, 0.26, 0)], "wood_dark", 0.06)
            ellipse(mb, [(0, 0.02, 0.041, 0.312, 0.274), (0.047, 0.056, 0.209, 0.281, 0.231),
                        (0.102, 0.073, 0.297, 0.196, 0.179)], "wood_mid")
            ellipse(mb, [(0.012, 0.026, 0.059, 0.318, 0.280), (0.037, 0.046, 0.129, 0.307, 0.265)], cloth)
            with mb.at(T(-0.263, 0.102, 0.164), R("Y", -31)):
                sweep(mb, [((0, 0, 0), 0.012, 0.013), ((-0.031, 0.003, 0.240), 0.089, 0.019),
                           ((-0.011, 0.02, 0.428), 0.064, 0.018), ((0.052, 0.04, 0.581), 0.003, 0.004)],
                      "cloth_white", segments=8)


def boot(mb, x, y, leather, trim):
    ellipse(mb, [(x, y - 0.13, 0, 0.152, 0.286), (x, y - 0.14, 0.065, 0.157, 0.293),
                (x, y - 0.114, 0.106, 0.146, 0.27)], "wood_dark")
    ellipse(mb, [(x, y - 0.113, 0.072, 0.15, 0.284), (x, y - 0.089, 0.157, 0.148, 0.273),
                (x, y + 0.015, 0.226, 0.127, 0.176), (x, y + 0.046, 0.366, 0.114, 0.126),
                (x, y + 0.061, 0.68, 0.139, 0.139), (x, y + 0.055, 0.838, 0.153, 0.153)], leather)
    ellipse(mb, [(x, y + 0.057, 0.774, 0.152, 0.151), (x, y + 0.053, 0.864, 0.158, 0.157)], trim)


# The index through little fingers wrap around this cross-palm axis.
GRIP_Y, GRIP_Z = -0.076, -0.037
GRIP = Vector((0, GRIP_Y, GRIP_Z))
WRIST = Vector((0, 0.021, 0.157))
SLEEVE_SEGMENTS = 12
CUFF_SEGMENTS = 10


def grip_point(radius, angle, x):
    angle = math.radians(angle)
    return (x, GRIP_Y + radius * math.cos(angle), GRIP_Z - radius * math.sin(angle))


def finger(mb, x, radius, color, curl, x_tip=None):
    # Finger pads lie on the handle. The joint centres follow the same curve,
    # offset by the finger thickness so the finger does not cross the shaft.
    x_tip = x if x_tip is None else x_tip
    sections = [((x, 0.015, 0.034), 0.023, 0.024)]
    for t, thickness in ((0, 0.022), (0.26, 0.021), (0.58, 0.019), (0.84, 0.017), (1, 0.014)):
        p = grip_point(radius + thickness - 0.001, 35 + t * curl, x + (x_tip - x) * t)
        sections.append((p, thickness, thickness))
    sweep(mb, sections, color, segments=6)


def hand(mb, skin, side, fingers, radius):
    # Wrist, heel of the palm, then the knuckle line. The narrower palm leaves
    # the handle, fingertips and thumb individually readable in silhouette.
    sweep(mb, [((0, 0.021, 0.181), 0.050, 0.041), (WRIST, 0.054, 0.045),
               ((0.003 * side, 0.019, 0.094), 0.074, 0.051),
               ((0.005 * side, 0.013, 0.040), 0.083, 0.045),
               ((0.006 * side, 0.010, 0.016), 0.073, 0.029)], skin, segments=8)
    # The thumb is on the index-finger side. Pinch grips bring those two pads
    # together, while the other fingers curl loosely behind the object.
    for i, (x, curl) in enumerate(((0.059, 185), (0.018, 180), (-0.023, 165), (-0.060, 148))):
        x *= side
        if fingers == "pinch" and i == 0:
            finger(mb, x, radius, skin, 143, 0.0)
        elif fingers in ("pinch", "relaxed"):
            end_x = x * 1.05
            sweep(mb, [((x, 0.014, 0.038), 0.022, 0.023),
                       ((end_x, -0.005, -0.034), 0.020, 0.021),
                       ((end_x, -0.031, -0.077 + 0.007 * i), 0.016, 0.017),
                       ((end_x, -0.048, -0.078 + 0.007 * i), 0.012, 0.013)], skin, segments=6)
        else:
            finger(mb, x, radius, skin, curl)

    thumb_target = grip_point(radius + 0.014, 233, 0.0 if fingers == "pinch" else 0.038 * side)
    if fingers == "relaxed":
        thumb_target = (0.087 * side, -0.034, -0.012)
    sweep(mb, [((0.051 * side, 0.011, 0.095), 0.032, 0.029),
               ((0.082 * side, -0.017, 0.059), 0.028, 0.026),
               ((0.073 * side, -0.066, 0.016), 0.022, 0.023),
               (thumb_target, 0.015, 0.016)], skin, segments=6)


def coat_front(profile, x, z):
    """Conservative front of the pleated fabric, in the unposed torso frame."""
    z = max(profile[0][2], min(profile[-1][2], z - 0.04))
    for lo, hi in zip(profile, profile[1:]):
        if z <= hi[2]:
            weight = (z - lo[2]) / (hi[2] - lo[2])
            cx, cy, _, rx, ry, fullness = (a + (b - a) * weight for a, b in zip(lo, hi))
            pleat = 0.1496 * fullness
            front = math.sqrt(max(0, 1 - ((x - cx) / (rx + pleat)) ** 2))
            return cy - (ry + pleat) * front
    raise ValueError("Coat profile must be ordered by height")


def apron_panel(mb, role, color, coat):
    short = 2.39 if role == "lio" else 2.12
    rows = []
    for z, width, y in ((short, 0.475, -0.398), (short + 0.15, 0.489, -0.397),
                        (3.14, 0.438, -0.371), (3.61, 0.372, -0.304),
                        (3.93, 0.28, -0.352), (4.43, 0.255, -0.382)):
        ring = []
        for i in range(9):
            across = i / 4 - 1
            xx, zz = across * width, z + 0.027 * math.sin(i * 1.1)
            yy = y + 0.112 * across ** 2 - 0.021 * math.cos(i * 2.4) * (4.55 - z)
            ring.append((xx, min(yy, coat_front(coat, xx, zz) - 0.031), zz))
        rows.append(ring)
    mb.sheet(rows, color, up=(0, -1, 0), smooth=True, grad=(0.36, 0.67))
    for side in (-1, 1):
        sweep(mb, [((side * 0.227, -0.359, 4.41), 0.042, 0.009),
                   ((side * 0.322, -0.259, 4.65), 0.042, 0.010),
                   ((side * 0.369, -0.109, 4.837), 0.043, 0.011)], color, segments=8)
    if role == "selma":
        pocket_y = min(-0.402, coat_front(coat, -0.17, 2.86) - 0.052)
        folds(mb, [(-0.17, pocket_y, 2.74, 0.126, 0.043, 0.4),
                   (-0.17, pocket_y - 0.006, 2.96, 0.141, 0.053, 0.4),
                   (-0.17, pocket_y, 2.994, 0.136, 0.043, 0.4)],
              color, 0.015, segments=12, tone=-0.095)


def section_at(profile, height):
    for (a, rx0, ry0), (b, rx1, ry1) in zip(profile, profile[1:]):
        if a.z <= height <= b.z:
            t = (height - a.z) / (b.z - a.z)
            return a.lerp(b, t), rx0 + (rx1 - rx0) * t, ry0 + (ry1 - ry0) * t
    raise ValueError(f"Height {height} is outside the leg profile")


def outfit(mb, role, cloth, trim, apron, skin):
    pose = POSES[role]
    hem = {"selma": 1.69, "nyra": 0.98, "lio": 2.29, "aron": 2.44, "esme": 2.22}[role]
    hems = []
    for side, leg in zip((-1, 1), pose.legs):
        x, y, toe_heading = leg.foot
        with mb.at(T(x, y, 0), R("Z", toe_heading)):
            boot(mb, 0, 0, "wood_mid" if role == "esme" else "wood_dark", trim)
        ankle = Vector((x, y + 0.059, 0.76))
        knee = Vector(leg.knee)
        hip = torso_point((0.208 * side, 0.05, 3.18), pose)
        leg_profile = [(ankle, 0.122, 0.123), (ankle.lerp(knee, 0.48), 0.149, 0.139),
                       (knee, 0.144, 0.135), (knee.lerp(hip, 0.24), 0.167, 0.16),
                       (knee.lerp(hip, 0.67), 0.201, 0.175), (hip, 0.202, 0.194)]
        # The hidden portion ends underneath the coat, so a bent knee can never
        # leave an isolated patch of trouser mesh halfway up the coat.
        knee_cover = hem + 0.20
        hems.append(section_at(leg_profile, hem + 0.08))
        visible = [ring for ring in leg_profile if ring[0].z < knee_cover]
        sweep(mb, visible + [section_at(leg_profile, knee_cover)], trim, segments=12)

    leg_mid = (hems[0][0] + hems[1][0]) * 0.5
    hem_x, hem_y = leg_mid.x - pose.pelvis[0], leg_mid.y - pose.pelvis[1]
    hem_width = max(0.53, abs(hems[0][0].x - hems[1][0].x) / 2 + max(h[1] for h in hems) + 0.14)
    hem_depth = max(0.38, abs(hems[0][0].y - hems[1][0].y) / 2 + max(h[2] for h in hems) + 0.12)

    torso = len(mb.verts)
    coat = [(hem_x, hem_y, hem, hem_width, hem_depth, 0.43),
               (hem_x * 0.8, hem_y * 0.71, hem + 0.16, hem_width - 0.006, hem_depth - 0.008, 0.32),
               (0.019, 0.073, 2.79, 0.502, 0.321, 0.25), (0, 0.053, 3.18, 0.453, 0.296, 0.12),
               (0, 0.049, 3.59, 0.381, 0.271, 0.03), (0, 0.043, 3.85, 0.407, 0.279, 0.02),
               (0, 0.029, 4.254, 0.465, 0.333, 0), (0, 0.024, 4.570, 0.544, 0.311, 0),
               (0, 0.026, 4.753, 0.518, 0.264, 0), (0, 0.035, 4.867, 0.252, 0.213, 0),
               (0, 0.053, 4.954, 0.152, 0.159, 0)]
    folds(mb, coat, cloth, depth=0.11, phase=0.8 if role == "nyra" else 0.2)
    ellipse(mb, [(0, 0.049, 4.819, 0.163, 0.168), (0, 0.029, 4.985, 0.143, 0.147),
                (0, 0.009, 5.294, 0.145, 0.139)], skin)
    ellipse(mb, [(0, 0.044, 3.47, 0.398, 0.286), (0, 0.041, 3.55, 0.392, 0.288)], "wood_dark")
    ellipse(mb, [(0, 0.042, 4.889, 0.234, 0.235), (0, 0.044, 5.051, 0.183, 0.193)], trim)
    if role in ("selma", "lio", "aron"):
        apron_panel(mb, role, apron, coat)
    else:
        folds(mb, [(0, 0.034, 4.10, 0.599, 0.415, 0.34), (0, 0.033, 4.28, 0.602, 0.411, 0.29),
                   (0, 0.026, 4.475, 0.586, 0.386, 0.13), (0, 0.027, 4.718, 0.56, 0.332, 0.04),
                   (0, 0.033, 4.852, 0.382, 0.281, 0.01), (0, 0.036, 4.954, 0.227, 0.231, 0)],
              trim, depth=0.058, segments=20, grad=(0.36, 0.64))
        with mb.at(T(0.096, -0.367, 4.430), R("X", 90)):
            mb.cyl(0.074, 0.078, 0.038, "brass", segs=10)
    mb.blob(0.185, "wood_mid", (-0.389, 0.065, 3.388), scale=(0.92, 0.62, 1.25),
            level=1, noise=0, smooth=True)
    if role == "lio":
        for i in range(3):
            bottle(mb, -0.213 + i * 0.151, -0.366, 3.115, "glass_light", 0.34)
    frame = mb.matrix.copy()
    inverse = frame.inverted()
    mb.deform(lambda v: frame @ torso_point(inverse @ v, pose), torso)

def grip_frame(arm):
    return T(*arm.palm) @ rotations(arm.angles) @ T(*GRIP)


def palm_frame(arm):
    grip = grip_frame(arm)
    # Roll the hand around the handle while keeping the contact point and
    # handle axis fixed. The wrist then approaches the elbow from the grip.
    elbow = grip.inverted() @ Vector(arm.elbow)
    wrist = WRIST - GRIP
    roll = math.degrees(math.atan2(elbow.z, elbow.y) - math.atan2(wrist.z, wrist.y))
    return grip @ R("X", roll) @ T(*(-GRIP))


def build_arm(mb, role, side, arm, cloth, trim, skin, radius):
    frame = palm_frame(arm)
    wrist = frame @ WRIST
    elbow = Vector(arm.elbow)
    wrist_axis = (frame.to_3x3() @ Vector((0, 0, -1))).normalized()
    shoulder = shoulder_point(role, side)
    sweep(mb, [(shoulder, 0.179, 0.183), (shoulder.lerp(elbow, 0.25), 0.194, 0.187),
               (shoulder.lerp(elbow, 0.70), 0.149, 0.154), (elbow, 0.133, 0.137),
               (elbow.lerp(wrist, 0.32), 0.122, 0.127), (elbow.lerp(wrist, 0.71), 0.103, 0.104),
               (wrist, 0.062, 0.057)], cloth, segments=SLEEVE_SEGMENTS, end_axis=wrist_axis)
    sleeve_end = len(mb.verts)
    sweep(mb, [(elbow.lerp(wrist, 0.79), 0.101, 0.103),
               (elbow.lerp(wrist, 0.88), 0.084, 0.084),
               (wrist, 0.067, 0.060)], trim, segments=CUFF_SEGMENTS, end_axis=wrist_axis)
    with mb.at(frame):
        hand(mb, "wood_dark" if role in ("lio", "aron") else skin, side, arm.fingers, radius)
    return sleeve_end


def shoulder_point(role, side):
    return torso_point((side * 0.401, 0.021, 4.655), POSES[role])


GRIP_RADIUS = {"selma": (0.011, 0.021), "nyra": (0.018, 0.019),
               "lio": (0.022, 0.027), "aron": (0.0, 0.043), "esme": (0.035, 0.028)}
LIO_SUPPORT_DISTANCE = -0.25


def align_lio_support():
    pose = POSES["lio"]
    left, right = pose.arms
    contact = grip_frame(right) @ Vector((LIO_SUPPORT_DISTANCE, 0, 0))
    palm = contact - rotations(right.angles).to_3x3() @ GRIP
    support = replace(left, elbow=(-0.42, -0.60, 4.39), palm=tuple(palm),
                      angles=right.angles, fingers="grip")
    POSES["lio"] = replace(pose, arms=(support, right))


align_lio_support()


def tool(mb, role, side, arm):
    radius = GRIP_RADIUS[role][int(side > 0)]
    if not radius:
        return
    frame = grip_frame(arm)
    contact = frame.translation
    with mb.at(frame):
        if role == "esme" and side < 0:
            # The long axis runs underneath all four curled fingers, with a flared
            # butt stop just past the fist and the axe head hanging below the wrist.
            sweep(mb, [((-0.20, 0.01, 0), 0.046, 0.043), ((-0.136, 0.003, 0), radius, radius),
                       ((0.16, 0, 0), radius, radius), ((0.55, -0.025, 0.03), 0.039, 0.044)],
                  "wood_mid", segments=12)
            # The axe eye sleeves the end of the haft and joins the blade.
            sweep(mb, [((0.475, -0.022, 0.024), 0.047, 0.050),
                       ((0.564, -0.024, 0.029), 0.044, 0.049)], "iron", segments=10)
            edge = [(0.47, 0.009), (0.57, 0.006), (0.77, -0.23), (0.71, -0.34),
                    (0.59, -0.40), (0.43, -0.15)]
            mb.prism(edge, -0.051, 0.051, "iron")
            mb.prism([(0.77, -0.23), (0.71, -0.34), (0.59, -0.40),
                      (0.59, -0.356), (0.695, -0.317), (0.738, -0.229)], -0.054, 0.054, "stone_light")
        elif role == "esme":
            mb.box(0.70, 0.044, 0.038, "wood_pale", (0.11, 0, 0))
            with mb.at(T(0.41, 0, -0.012), R("Z", -26)):
                mb.box(0.33, 0.044, 0.035, "wood_light", (0.144, 0, -0.008))
            for x in (-0.19, 0.17, 0.23, 0.29, 0.35, 0.41):
                mb.box(0.008, 0.002, 0.023, "wood_dark", (x, -0.023, 0.005))
            with mb.at(T(0.415, 0, 0.019), R("X", 90)):
                mb.cyl(0.015, 0.015, 0.047, "brass", segs=8)
        elif role == "aron":
            sweep(mb, [((-0.18, 0, 0), 0.049, 0.048), ((0.15, 0, 0), radius, radius),
                       ((0.65, 0.021, 0.017), 0.037, 0.041)], "wood_mid", segments=10)
            with mb.at(T(0.59, 0.017, 0.019)):
                sweep(mb, [((0, 0, -0.20), 0.103, 0.119), ((0, 0, -0.14), 0.112, 0.127),
                           ((0, 0, 0.18), 0.115, 0.129), ((0, 0, 0.23), 0.102, 0.115)], "iron", segments=10)
        elif role == "nyra" and side < 0:
            # The pointed heel is pinched between the pads, with the facets
            # widening beyond the fingertips.
            with mb.at(R("Y", 90)):
                mb.lathe([(0.012, -0.047), (radius, 0.015), (0.043, 0.105),
                          (0.078, 0.21), (0.055, 0.307), (0.008, 0.389)],
                         "glass_light", segs=5, smooth=False)
        elif role == "selma" and side < 0:
            sweep(mb, [((-0.068, 0, 0), radius, radius), ((0.133, 0, 0), radius, radius)],
                  "leaf_dark", segments=6)
            with mb.at(T(0.119, 0, 0), R("Y", 72)):
                sprig(mb, 0, 0, 0, 0.41, "leaf_teal")

    if role in ("nyra", "selma") and side > 0:
        # Pendants stay upright in the rest pose. Their handle passes through the
        # same contact point and follows the fist axis where the fingers close.
        direction = (frame.to_3x3() @ Vector((1, 0, 0)))
        points = [contact + direction * dx for dx in (-0.107, 0.107)]
        ends = [contact + Vector((sign * 0.244, 0, -0.205 if role == "selma" else -0.134)) for sign in (-1, 1)]
        sweep(mb, [(ends[0], radius, radius), (points[0], radius, radius),
                   (points[1], radius, radius), (ends[1], radius, radius)],
              "wood_mid" if role == "selma" else "iron", segments=9)
        with mb.at(T(*contact)):
            if role == "selma":
                mb.lathe([(0.202, -0.436), (0.256, -0.201), (0.261, -0.179),
                          (0.23, -0.173), (0.185, -0.405)], "wood_light", segs=11)
                for i in range(4):
                    sprig(mb, -0.13 + i * 0.087, 0.09 * (i % 2), -0.202, 0.43, "leaf_lime")
            else:
                flask_case(mb, 0, 0, -0.545, 0.64)
    if role == "lio" and side > 0:
        axis = frame.to_3x3() @ Vector((1, 0, 0))
        tip = contact + axis * 0.64
        sweep(mb, [(contact - axis * 0.44, 0.021, 0.021),
                   (contact, radius, radius), (tip, 0.023, 0.023)], "iron", segments=10)
        mb.blob(0.144, "glass_light", tip + axis * 0.09,
                scale=(1.17, 0.88, 0.96), level=1, noise=0, smooth=True)


def merchant_parts(role, seed):
    cloth, trim, apron, skin, hair, width, height = STYLES[role]
    scale = S(width, 1, height)
    pose = POSES[role]
    parts = {name: MeshBuilder(seed=seed + i) for i, name in enumerate(("body", "head", "left", "right"))}
    with parts["body"].at(scale):
        outfit(parts["body"], role, cloth, trim, apron, skin)
    with parts["head"].at(scale, head_frame(pose)):
        make_face(parts["head"], role, skin, hair)
        hair_and_beard(parts["head"], role, hair)
        headwear(parts["head"], role, cloth, trim)
    sleeves = {}
    for side, name, arm in zip((-1, 1), ("left", "right"), pose.arms):
        with parts[name].at(scale):
            sleeves[name] = build_arm(parts[name], role, side, arm, cloth, trim, skin, GRIP_RADIUS[role][int(side > 0)])
        prop = MeshBuilder(seed=seed + 8 + int(side > 0))
        with prop.at(scale):
            tool(prop, role, side, arm)
        if prop.verts:
            parts["tool_" + name] = prop

    return parts, sleeves



def goods(mb, role, z=3):
    for x in (-2.55, 0, 2.55):
        mb.box(2.11, 1.45, 0.21, "wood_mid", (x, -0.6, z), taper=1.08)
    if role == "selma":
        for i in range(8):
            sprig(mb, -3.3 + i * 0.49, -0.73 + i % 2 * 0.38, z + 0.21,
                  0.75 + i % 3 * 0.17, "leaf_lime" if i < 4 else "leaf_teal")
        for i in range(5):
            mb.blob(0.20, "flower_red", (1.78 + i * 0.35, -0.63, z + 0.35), level=0, noise=0.04)
        for i in range(2):
            mb.lathe([(0.27, 0), (0.31, 0.26), (0.18, 0.54), (0.20, 0.58)], "cloth_white",
                     segs=7, pos=(2.2 + i * 0.58, -0.18, z + 0.20), smooth=False)
    elif role == "nyra":
        for i in range(5):
            mushroom(mb, -3.30 + i * 0.46, -0.69 + i % 2 * 0.37, z + 0.2, 0.83 + i % 3 * 0.28)
        for i in range(5):
            crystal(mb, 1.8 + i * 0.36, -0.70 + i % 2 * 0.35, z + 0.2,
                    0.67 + i % 3 * 0.25, "flower_purple" if i % 2 else "glass_light")
        for i in range(3):
            sprig(mb, -0.49 + i * 0.43, -0.65, z + 0.21, 0.69, "glass_light")
    elif role == "lio":
        for i in range(9):
            bottle(mb, -0.71 + i % 3 * 0.61 + (2.55 if i > 4 else 0), -1.01 + i // 3 * 0.42,
                   z + 0.22, "glass_light", 0.81 + i % 3 * 0.25)
        mb.blob(0.77, "sand", (-2.56, -0.55, z + 0.23), scale=(1, 0.61, 0.47), level=1, noise=0.07)
    elif role == "aron":
        for i, color in enumerate(("iron", "brick", "stone_grey")):
            for j in range(5):
                mb.blob(0.37 + 0.08 * (j % 2), color,
                        (2.55 * (i - 1) + (j % 3 - 1) * 0.55, -0.93 + 0.59 * (j // 3), z + 0.38),
                        scale=(1, 0.83, 0.79), level=0, noise=0.26)
        mb.box(1.13, 0.49, 0.23, "brass", (0.10, -0.22, z + 0.3), taper=0.74)
    else:
        for i in range(5):
            with mb.at(T(-3.2 + 0.57 * (i % 3), -0.45, z + 0.4 + 0.36 * (i // 3)), R("X", 90)):
                mb.cyl(0.26, 0.25, 1.21, "bark", segs=7, smooth=False)
                mb.cyl(0.217, 0.217, 0.03, "wood_pale", (0, 0, 1.21), segs=7, smooth=False)
        for i in range(6):
            mb.blob(0.41, "stone_warm" if i % 2 else "stone_grey",
                    (1.93 + 0.53 * (i % 3), -1.03 + 0.52 * (i // 3), z + 0.35),
                    scale=(1.1, 0.85, 0.73), level=0, noise=0.19)
        mb.box(1.54, 0.36, 0.22, "wood_light", (0, -0.73, z + 0.22), taper=0.86)


def stall(mb, role):
    cloth, trim, *_ = STYLES[role]
    mb.box(7.8, 2.03, 2.78, "wood_mid", (0, -0.45, 0))
    mb.box(8.2, 2.25, 0.25, "wood_light", (0, -0.45, 2.75))
    for i in range(10):
        mb.box(0.734, 0.075, 2.30, "wood_dark" if i % 3 == 0 else "wood_mid",
               ((i - 4.5) * 0.758, -1.50, 0.2), tone=mb.jitter(0.055))
    mb.box(7.9, 0.16, 0.38, "wood_dark", (0, -1.55, 0.19))
    for sign in (-1, 1):
        for y, top in ((-2.06, 8.16), (2.05, 8.96)):
            mb.box(0.38, 0.38, top, "wood_dark", (sign * 4.15, y, 0))
            mb.beam((sign * 4.15, y, top - 1.47), (sign * 2.52, y, top - 0.17),
                    0.19, 0.22, "wood_mid")
    for i in range(8):
        x = (i - 3.5) * 1.12
        color = cloth if i % 2 else "cloth_white"
        mb.beam((x, 2.55, 9.05), (x, -2.94, 8.14), 1.12, 0.18, color)
        mb.box(1.095, 0.13, 0.51 + (i % 2) * 0.12, color, (x, -2.91, 7.52 + (i % 2) * 0.06))
    mb.box(1.75, 0.14, 1.02, trim, (0, -1.67, 1.22))
    mb.box(1.93, 0.065, 0.11, "brass", (0, -1.75, 1.16))
    mb.box(1.93, 0.065, 0.11, "brass", (0, -1.75, 2.24))
    with mb.at(T(0, -1.82, 1.35)):
        if role == "selma":
            sprig(mb, -0.1, 0, 0, 0.87, "leaf_lime")
        elif role == "nyra":
            crystal(mb, 0.08, 0, 0, 0.7)
        elif role == "lio":
            bottle(mb, 0, 0, 0, "glass_light", 0.83)
        elif role == "aron":
            mb.beam((-0.24, 0, 0.08), (0.19, 0, 0.68), 0.11, 0.10, "wood_light")
            mb.box(0.66, 0.16, 0.29, "brass", (0.11, 0, 0.56))
        else:
            for side in (-1, 1):
                mb.beam((side * 0.35, 0, 0.12), (-side * 0.30, 0, 0.73), 0.18, 0.14, "wood_pale")
    goods(mb, role)
