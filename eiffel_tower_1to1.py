import math

import bpy
from mathutils import Vector


def make_material(name, color, roughness=0.55, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def cylinder_between(name, start, end, radius, material, vertices=10):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    length = direction.length
    if length <= 0.0001:
        return None

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=length,
        location=(start + end) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return obj


def cube(name, location, dimensions, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    iron = make_material("Eiffel Tower warm brown painted iron", (0.42, 0.25, 0.13, 1), 0.72, 0.2)
    dark_iron = make_material("Darker iron bracing", (0.22, 0.12, 0.07, 1), 0.78, 0.15)
    deck_mat = make_material("Observation platform decking", (0.18, 0.14, 0.10, 1), 0.65, 0.1)
    label_mat = make_material("Scale label off white", (0.92, 0.88, 0.78, 1), 0.5, 0.0)
    ground_mat = make_material("Champ de Mars scale ground", (0.18, 0.30, 0.17, 1), 0.9, 0.0)

    # 1 Blender unit is 1 meter. Eiffel Tower height is modeled as 330 m including antenna.
    half_widths = {
        0.0: 62.5,
        57.6: 35.0,
        115.7: 18.0,
        276.1: 4.5,
        300.0: 2.3,
        330.0: 0.45,
    }

    def half_width_at(z):
        levels = sorted(half_widths)
        for low, high in zip(levels[:-1], levels[1:]):
            if low <= z <= high:
                t = (z - low) / (high - low)
                return half_widths[low] * (1.0 - t) + half_widths[high] * t
        return half_widths[levels[-1]]

    def corners(z):
        width = half_width_at(z)
        return [
            Vector((width, width, z)),
            Vector((-width, width, z)),
            Vector((-width, -width, z)),
            Vector((width, -width, z)),
        ]

    z_steps = [0, 18, 36, 57.6, 80, 100, 115.7, 150, 190, 230, 276.1, 300]

    for corner_index in range(4):
        previous = corners(z_steps[0])[corner_index]
        for z in z_steps[1:]:
            current = corners(z)[corner_index]
            radius = max(0.75, 2.2 - z * 0.0045)
            cylinder_between(f"primary curved leg {corner_index + 1} z{z:.1f}", previous, current, radius, iron, 14)
            previous = current

    for z in [18, 36, 57.6, 80, 100, 115.7, 150, 190, 230, 276.1, 300]:
        points = corners(z)
        radius = 1.05 if z < 120 else 0.62
        for side in range(4):
            cylinder_between(f"horizontal square frame z{z:.1f} side {side + 1}", points[side], points[(side + 1) % 4], radius, iron, 10)

    brace_bays = [
        (0, 18),
        (18, 36),
        (36, 57.6),
        (57.6, 80),
        (80, 100),
        (100, 115.7),
        (115.7, 150),
        (150, 190),
        (190, 230),
        (230, 276.1),
        (276.1, 300),
    ]
    for z0, z1 in brace_bays:
        lower = corners(z0)
        upper = corners(z1)
        radius = 0.45 if z1 <= 120 else 0.25
        for side in range(4):
            a0 = lower[side]
            b0 = lower[(side + 1) % 4]
            a1 = upper[side]
            b1 = upper[(side + 1) % 4]
            cylinder_between(f"x brace {z0:.1f}-{z1:.1f} side {side + 1} a", a0, b1, radius, dark_iron, 8)
            cylinder_between(f"x brace {z0:.1f}-{z1:.1f} side {side + 1} b", b0, a1, radius, dark_iron, 8)
            cylinder_between(
                f"secondary side upright {z0:.1f}-{z1:.1f} side {side + 1}",
                (a0 + b0) * 0.5,
                (a1 + b1) * 0.5,
                radius * 0.65,
                iron,
                8,
            )

    for z0, z1 in [(115.7, 150), (150, 190), (190, 230), (230, 276.1), (276.1, 300)]:
        for index in range(4):
            p0 = corners(z0)[index]
            p1 = corners(z1)[index]
            p0 = Vector((p0.x * 0.55, p0.y * 0.55, p0.z))
            p1 = Vector((p1.x * 0.55, p1.y * 0.55, p1.z))
            cylinder_between(f"inner shaft upright {index + 1} {z0:.1f}-{z1:.1f}", p0, p1, 0.34, iron, 8)

    for name, z, size, thickness in [
        ("First observation deck 57.6m", 57.6, 78, 3.0),
        ("Second observation deck 115.7m", 115.7, 42, 2.6),
        ("Top observation deck 276.1m", 276.1, 14, 2.2),
    ]:
        cube(name, (0, 0, z), (size, size, thickness), deck_mat)
        rail_z = z + 2.2
        half = size * 0.5
        rail = [
            Vector((half, half, rail_z)),
            Vector((-half, half, rail_z)),
            Vector((-half, -half, rail_z)),
            Vector((half, -half, rail_z)),
        ]
        for side in range(4):
            cylinder_between(f"{name} railing {side + 1}", rail[side], rail[(side + 1) % 4], 0.25, iron, 8)

    for side in range(4):
        p_a = corners(0)[side]
        p_b = corners(0)[(side + 1) % 4]
        midpoint = (p_a + p_b) * 0.5
        for inset in [-2.0, 2.0]:
            arch_points = []
            for step in range(17):
                t = step / 16
                base = p_a.lerp(p_b, t)
                z = 8 + 31 * math.sin(math.pi * t)
                point = Vector((base.x, base.y, z))
                inward = Vector((-midpoint.x, -midpoint.y, 0))
                if inward.length > 0:
                    inward.normalize()
                    point.x += inward.x * inset
                    point.y += inward.y * inset
                arch_points.append(point)
            for start, end in zip(arch_points[:-1], arch_points[1:]):
                cylinder_between(f"base arch side {side + 1}", start, end, 0.85, iron, 12)

    cylinder_between("upper spire 300m to 324m", (0, 0, 300), (0, 0, 324), 1.0, iron, 16)
    cylinder_between("broadcast antenna to 330m total height", (0, 0, 324), (0, 0, 330), 0.32, dark_iron, 12)

    for index, point in enumerate(corners(0)):
        cube(f"foundation pad {index + 1}", (point.x, point.y, -1.0), (16, 16, 2), deck_mat)

    bpy.ops.mesh.primitive_plane_add(size=180, location=(0, 0, -2.05))
    ground = bpy.context.object
    ground.name = "180m ground plane for scale"
    ground.data.materials.append(ground_mat)

    cylinder_between("330 meter height reference line", (82, -82, 0), (82, -82, 330), 0.22, label_mat, 8)
    for z, text in [
        (0, "0 m"),
        (57.6, "1st deck 57.6 m"),
        (115.7, "2nd deck 115.7 m"),
        (276.1, "top deck 276.1 m"),
        (330, "330 m total"),
    ]:
        bpy.ops.object.text_add(location=(86, -82, z), rotation=(math.radians(90), 0, math.radians(90)))
        label = bpy.context.object
        label.name = f"scale label {text}"
        label.data.body = text
        label.data.size = 5 if z < 300 else 4
        label.data.align_x = "LEFT"
        label.data.align_y = "CENTER"
        label.data.materials.append(label_mat)

    bpy.ops.object.text_add(location=(0, -78, 8), rotation=(math.radians(75), 0, 0))
    plaque = bpy.context.object
    plaque.name = "model label"
    plaque.data.body = "Eiffel Tower - 1:1 scale (meters)"
    plaque.data.size = 7
    plaque.data.align_x = "CENTER"
    plaque.data.materials.append(label_mat)

    bpy.ops.object.light_add(type="SUN", location=(100, -120, 200))
    sun = bpy.context.object
    sun.name = "late afternoon sun"
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(45), 0, math.radians(35))

    bpy.ops.object.light_add(type="AREA", location=(0, -140, 120))
    area = bpy.context.object
    area.name = "soft front fill"
    area.data.energy = 450
    area.data.size = 85

    bpy.ops.object.camera_add(location=(170, -230, 165))
    camera = bpy.context.object
    camera.name = "camera full tower view"
    bpy.context.scene.camera = camera
    direction = Vector((0, 0, 150)) - Vector(camera.location)
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 28
    camera.data.clip_end = 1000

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.view_settings.view_transform = "Filmic"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1400
    scene["model_note"] = (
        "Procedural Eiffel Tower approximation: 330m total height, 125m footprint, "
        "decks at 57.6m, 115.7m, 276.1m. 1 Blender unit = 1 meter."
    )


if __name__ == "__main__":
    main()
