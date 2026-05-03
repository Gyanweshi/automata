import math

import bpy
from mathutils import Vector


def material(name, color, roughness=0.65, metallic=0.15):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def beam(name, points, radius, mat, resolution=3):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 3 if radius > 0.08 else 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (co[0], co[1], co[2], 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def cube(name, location, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def sphere(name, location, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=5, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def half_width_at(z):
    # Approximate measured outline: wide arched base, narrow upper shaft, spire.
    widths = {
        0.0: 62.5,
        25.0: 52.0,
        57.6: 35.0,
        90.0: 25.0,
        115.7: 18.0,
        170.0: 13.0,
        230.0: 8.0,
        276.1: 4.8,
        300.0: 2.4,
        330.0: 0.35,
    }
    keys = sorted(widths)
    for low, high in zip(keys[:-1], keys[1:]):
        if low <= z <= high:
            t = (z - low) / (high - low)
            return widths[low] * (1.0 - t) + widths[high] * t
    return widths[keys[-1]]


def corner(z, index):
    w = half_width_at(z)
    pts = [
        Vector((w, w, z)),
        Vector((-w, w, z)),
        Vector((-w, -w, z)),
        Vector((w, -w, z)),
    ]
    return pts[index]


def side_point(z, side, t):
    a = corner(z, side)
    b = corner(z, (side + 1) % 4)
    return a.lerp(b, t)


def radial_tangent_offset(point, radial_amount, tangent_amount):
    radial = Vector((point.x, point.y, 0))
    if radial.length == 0:
        radial = Vector((1, 0, 0))
    radial.normalize()
    tangent = Vector((-radial.y, radial.x, 0))
    return radial * radial_amount + tangent * tangent_amount


def build_model():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    iron = material("aged Eiffel brown iron paint", (0.36, 0.20, 0.10, 1), 0.78, 0.25)
    dark_iron = material("deep shadow ironwork", (0.16, 0.08, 0.04, 1), 0.82, 0.2)
    edge_iron = material("worn highlighted iron edges", (0.52, 0.33, 0.18, 1), 0.7, 0.22)
    deck_mat = material("dark enclosed deck structures", (0.11, 0.09, 0.075, 1), 0.6, 0.1)
    glass_mat = material("smoky observation glazing", (0.07, 0.09, 0.10, 0.48), 0.2, 0.0)
    concrete = material("subtle stone foundations", (0.36, 0.34, 0.30, 1), 0.85, 0.0)
    ground_mat = material("muted plaza ground", (0.24, 0.23, 0.20, 1), 0.9, 0.0)

    # Main four arched legs are built as bundled chords with small internal trusses.
    main_levels = [0, 12, 24, 36, 48, 57.6, 72, 88, 104, 115.7, 136, 158, 182, 206, 230, 252, 276.1, 288, 300]
    for leg in range(4):
        chords = []
        for radial in (-1.15, 1.15):
            for tangent in (-1.15, 1.15):
                pts = []
                for z in main_levels:
                    p = corner(z, leg)
                    amount = max(0.35, 1.4 - z / 330.0)
                    pts.append(p + radial_tangent_offset(p, radial * amount, tangent * amount))
                chords.append(pts)
                beam(f"bundled leg chord {leg + 1}", pts, 0.36 if radial > 0 else 0.28, iron)

        for idx in range(len(main_levels) - 1):
            radius = 0.16 if main_levels[idx + 1] < 125 else 0.095
            for a, b in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]:
                beam(f"leg micro lattice {leg + 1}", [chords[a][idx], chords[b][idx + 1]], radius, dark_iron)

    # Face lattice: many horizontal rings, vertical subdivisions, and X-braces.
    z_faces = [0, 8, 16, 24, 32, 40, 48, 57.6, 66, 74, 82, 90, 98, 106, 115.7,
               128, 141, 154, 167, 180, 193, 206, 219, 232, 244, 256, 268, 276.1, 288, 300]
    for side in range(4):
        for z in z_faces:
            radius = 0.24 if z < 125 else 0.12
            beam(f"thin horizontal face rail side {side + 1}", [side_point(z, side, 0), side_point(z, side, 1)], radius, iron)
            for t in (0.2, 0.4, 0.6, 0.8):
                p = side_point(z, side, t)
                sphere("small riveted node", p, 0.32 if z < 125 else 0.18, edge_iron)

        for low, high in zip(z_faces[:-1], z_faces[1:]):
            radius = 0.13 if high < 125 else 0.075
            divisions = 6 if high < 125 else 4
            for i in range(divisions):
                t0 = i / divisions
                t1 = (i + 1) / divisions
                beam(f"dense x lattice side {side + 1}", [side_point(low, side, t0), side_point(high, side, t1)], radius, dark_iron)
                beam(f"counter x lattice side {side + 1}", [side_point(low, side, t1), side_point(high, side, t0)], radius, dark_iron)
            for t in [i / divisions for i in range(1, divisions)]:
                beam(f"vertical face lattice side {side + 1}", [side_point(low, side, t), side_point(high, side, t)], radius * 0.85, iron)

    # Observation decks: layered enclosed floors, balconies, undersides, railings, posts.
    decks = [
        ("first", 57.6, 82, 9.0, 2.8),
        ("second", 115.7, 46, 7.0, 2.2),
        ("summit", 276.1, 16, 8.0, 1.4),
    ]
    for name, z, size, building_height, rail_radius in decks:
        cube(f"{name} lower iron platform slab", (0, 0, z - 1.4), (size, size, 2.2), deck_mat)
        cube(f"{name} enclosed observation rooms", (0, 0, z + building_height * 0.35), (size * 0.82, size * 0.82, building_height), glass_mat)
        cube(f"{name} upper cornice band", (0, 0, z + building_height + 1.6), (size * 0.92, size * 0.92, 1.2), deck_mat)

        half = size * 0.5
        for dz in (1.2, 3.0, building_height + 2.8):
            corners = [
                Vector((half, half, z + dz)),
                Vector((-half, half, z + dz)),
                Vector((-half, -half, z + dz)),
                Vector((half, -half, z + dz)),
            ]
            for side in range(4):
                beam(f"{name} balcony rail", [corners[side], corners[(side + 1) % 4]], 0.09 * rail_radius, edge_iron)

        post_count = 22 if name == "first" else 16 if name == "second" else 8
        for side in range(4):
            for i in range(post_count + 1):
                t = i / post_count
                p0 = Vector((half, half, z + 1.0)).lerp(Vector((-half, half, z + 1.0)), t)
                if side == 1:
                    p0 = Vector((-half, half, z + 1.0)).lerp(Vector((-half, -half, z + 1.0)), t)
                elif side == 2:
                    p0 = Vector((-half, -half, z + 1.0)).lerp(Vector((half, -half, z + 1.0)), t)
                elif side == 3:
                    p0 = Vector((half, -half, z + 1.0)).lerp(Vector((half, half, z + 1.0)), t)
                beam(f"{name} fine rail post", [p0, p0 + Vector((0, 0, building_height + 2.4))], 0.055 * rail_radius, edge_iron)

    # Base arches with multiple ribs and ornamental under-arch bracing.
    for side in range(4):
        a = corner(0, side)
        b = corner(0, (side + 1) % 4)
        midpoint = (a + b) * 0.5
        inward = Vector((-midpoint.x, -midpoint.y, 0))
        inward.normalize()
        for rib in (-3.2, -1.2, 1.2, 3.2):
            pts = []
            for step in range(33):
                t = step / 32
                base = a.lerp(b, t)
                z = 7 + 34 * math.sin(math.pi * t)
                pts.append(Vector((base.x, base.y, z)) + inward * rib)
            beam(f"layered base arch rib side {side + 1}", pts, 0.34, iron)
            for step in range(0, 32, 2):
                beam(f"arch webbing side {side + 1}", [pts[step], pts[min(step + 2, 32)] + Vector((0, 0, -3.0))], 0.075, dark_iron)

    # Elevator rails and stair-like zigzags running inside each face.
    for side in range(4):
        for t in (0.43, 0.57):
            pts = [side_point(z, side, t) * Vector((0.92, 0.92, 1.0)) for z in main_levels]
            beam(f"straight elevator guide rail side {side + 1}", pts, 0.12, edge_iron)
        for low, high in [(0, 57.6), (57.6, 115.7), (115.7, 276.1)]:
            steps = 18
            zig = []
            for i in range(steps + 1):
                z = low + (high - low) * i / steps
                t = 0.46 if i % 2 == 0 else 0.54
                zig.append(side_point(z, side, t) * Vector((0.82, 0.82, 1.0)))
            beam(f"visible zigzag stair suggestion side {side + 1}", zig, 0.07, dark_iron)

    # Summit lantern, tapered mast, antenna stack, and small antenna rings.
    for z, width, height in [(286, 9.0, 8), (296, 5.6, 7), (305, 3.2, 8)]:
        cube("stacked summit mechanical room", (0, 0, z), (width, width, height), deck_mat)
        for side in range(4):
            w = width * 0.5
            pts = [Vector((w, w, z + height * 0.5)), Vector((-w, w, z + height * 0.5)),
                   Vector((-w, -w, z + height * 0.5)), Vector((w, -w, z + height * 0.5))]
            beam("summit balcony trim", [pts[side], pts[(side + 1) % 4]], 0.055, edge_iron)

    mast_levels = [300, 308, 316, 324, 330]
    for low, high in zip(mast_levels[:-1], mast_levels[1:]):
        beam("segmented radio mast core", [Vector((0, 0, low)), Vector((0, 0, high))], 0.18 if high < 324 else 0.08, edge_iron)
        for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
            offset = Vector((math.cos(angle), math.sin(angle), 0)) * (1.0 - low / 400.0)
            beam("mast side strut", [Vector((0, 0, low)) + offset, Vector((0, 0, high))], 0.045, dark_iron)
    for z in (309, 317, 324):
        ring = []
        for i in range(33):
            angle = math.tau * i / 32
            ring.append(Vector((math.cos(angle) * 1.35, math.sin(angle) * 1.35, z)))
        beam("circular antenna service ring", ring, 0.035, edge_iron)

    for index in range(4):
        p = corner(0, index)
        cube("stone footing block", (p.x, p.y, -1.0), (20, 20, 2.0), concrete)

    bpy.ops.mesh.primitive_plane_add(size=190, location=(0, 0, -2.1))
    ground = bpy.context.object
    ground.name = "simple plaza ground plane"
    ground.data.materials.append(ground_mat)

    bpy.ops.object.light_add(type="SUN", location=(80, -120, 240))
    sun = bpy.context.object
    sun.name = "warm directional sun"
    sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(44), 0, math.radians(34))

    bpy.ops.object.light_add(type="AREA", location=(-70, -120, 125))
    fill = bpy.context.object
    fill.name = "large soft fill"
    fill.data.energy = 700
    fill.data.size = 95

    bpy.ops.object.camera_add(location=(155, -245, 130))
    camera = bpy.context.object
    camera.name = "portrait camera realistic full tower"
    bpy.context.scene.camera = camera
    direction = Vector((0, 0, 150)) - Vector(camera.location)
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 34
    camera.data.clip_end = 1200

    try:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 96
    except Exception:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.view_settings.view_transform = "Filmic"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 2200
    scene["model_note"] = "Detailed procedural Eiffel Tower visual model. Diagram scale labels removed."


if __name__ == "__main__":
    build_model()
