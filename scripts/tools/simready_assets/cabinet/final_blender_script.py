import bpy
import bmesh
import math
from mathutils import Vector

def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for curve in list(bpy.data.curves):
        bpy.data.curves.remove(curve, do_unlink=True)

def create_walnut_material():
    mat = bpy.data.materials.new(name="Walnut_Wood")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.35, 0.22, 0.14, 1.0)
    principled.inputs['Roughness'].default_value = 0.4
    principled.inputs['Metallic'].default_value = 0.0

    # Wood grain via stretched noise
    texcoord = nodes.new('ShaderNodeTexCoord')
    texcoord.location = (-800, 0)

    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-600, 0)
    mapping.inputs['Scale'].default_value = (1.0, 1.0, 15.0)  # Stretch along Z for grain
    links.new(texcoord.outputs['Object'], mapping.inputs['Vector'])

    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, 0)
    noise.inputs['Scale'].default_value = 8.0
    noise.inputs['Detail'].default_value = 10.0
    noise.inputs['Roughness'].default_value = 0.7
    links.new(mapping.outputs['Vector'], noise.inputs['Vector'])

    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].position = 0.3
    color_ramp.color_ramp.elements[0].color = (0.25, 0.15, 0.08, 1.0)  # Dark walnut
    color_ramp.color_ramp.elements[1].position = 0.7
    color_ramp.color_ramp.elements[1].color = (0.45, 0.30, 0.18, 1.0)  # Light walnut
    links.new(noise.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], principled.inputs['Base Color'])

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return mat

def create_brass_material():
    mat = bpy.data.materials.new(name="Brushed_Brass")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.78, 0.57, 0.11, 1.0)
    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 0.3

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    mat.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return mat

def add_box(name, location, scale):
    """Helper: create a box at location with given scale (half-extents)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return obj

def main():
    clear_scene()

    walnut = create_walnut_material()
    brass = create_brass_material()

    # ═══ DIMENSIONS ═══
    W = 1.52    # total width
    D = 0.45    # total depth
    H = 0.67    # carcass height (without legs)
    T = 0.018   # panel thickness
    LEG_H = 0.14
    LEG_R_TOP = 0.020
    LEG_R_BOT = 0.013

    # Carcass bottom sits at Z = LEG_H
    carcass_bottom = LEG_H

    # ═══ CARCASS (built from panels — like real furniture) ═══
    panels = []

    # Top panel
    panels.append(add_box("Top", (0, 0, carcass_bottom + H - T/2), (W/2, D/2, T/2)))
    # Bottom panel
    panels.append(add_box("Bottom", (0, 0, carcass_bottom + T/2), (W/2, D/2, T/2)))
    # Left side
    panels.append(add_box("Left", (-W/2 + T/2, 0, carcass_bottom + H/2), (T/2, D/2, H/2)))
    # Right side
    panels.append(add_box("Right", (W/2 - T/2, 0, carcass_bottom + H/2), (T/2, D/2, H/2)))
    # Back panel
    panels.append(add_box("Back", (0, -D/2 + T/2, carcass_bottom + H/2), (W/2, T/2, H/2)))
    # Center vertical divider
    panels.append(add_box("Divider_V", (0, 0, carcass_bottom + H/2), (T/2, D/2 - T, H/2 - T)))
    # Horizontal dividers (2 shelves creating 3 rows)
    row_h = (H - 2*T) / 3  # interior height per row
    for i in range(1, 3):
        z = carcass_bottom + T + row_h * i
        panels.append(add_box(f"Divider_H_{i}", (0, 0, z), (W/2 - T, D/2 - T, T/2)))

    # Join all panels into one carcass
    bpy.ops.object.select_all(action='DESELECT')
    for p in panels:
        p.select_set(True)
    bpy.context.view_layer.objects.active = panels[0]
    bpy.ops.object.join()
    carcass = bpy.context.active_object
    carcass.name = "Carcass"
    carcass.data.materials.append(walnut)
    bpy.ops.object.shade_smooth()

    # ═══ 6 DRAWERS (each is a separate body — they slide!) ═══
    drawer_w = (W/2 - T) - T/2 - 0.004  # half-width minus divider minus clearance
    drawer_h = row_h - 0.006              # row height minus clearance
    drawer_d = D - 2*T - 0.01            # depth minus walls minus clearance
    front_thickness = 0.018

    drawers = []
    for row in range(3):
        for col in range(2):
            x = -W/4 + col * W/2  # center of left/right column
            z = carcass_bottom + T + row_h * row + row_h/2

            # Drawer front (visible face)
            front = add_box(f"Drawer_{row}_{col}", (x, D/2 - front_thickness/2, z),
                           (drawer_w/2, front_thickness/2, drawer_h/2))
            front.data.materials.append(walnut)
            bpy.ops.object.shade_smooth()
            drawers.append(front)

    # ═══ 6 BRASS HANDLES ═══
    handle_w = 0.180   # 180mm wide
    handle_h = 0.012
    handle_d = 0.008

    handles = []
    for row in range(3):
        for col in range(2):
            x = -W/4 + col * W/2
            z = carcass_bottom + T + row_h * row + row_h/2 + drawer_h/2 - 0.025
            y = D/2 + handle_d/2

            handle = add_box(f"Handle_{row}_{col}", (x, y, z),
                            (handle_w/2, handle_d/2, handle_h/2))
            handle.data.materials.append(brass)
            bpy.ops.object.shade_smooth()
            handles.append(handle)

    # ═══ 4 LEGS (tapered cones, splayed outward) ═══
    leg_positions = [
        (-W/2 + 0.06, -D/2 + 0.05, LEG_H/2),   # Back left
        ( W/2 - 0.06, -D/2 + 0.05, LEG_H/2),   # Back right
        (-W/2 + 0.06,  D/2 - 0.05, LEG_H/2),   # Front left
        ( W/2 - 0.06,  D/2 - 0.05, LEG_H/2),   # Front right
    ]
    splay_angles = [
        (math.radians(10), math.radians(-8), 0),    # Back left
        (math.radians(10), math.radians(8), 0),     # Back right
        (math.radians(-3), math.radians(-8), 0),    # Front left
        (math.radians(-3), math.radians(8), 0),     # Front right
    ]

    legs = []
    for i, (pos, angles) in enumerate(zip(leg_positions, splay_angles)):
        bpy.ops.mesh.primitive_cone_add(
            vertices=32, radius1=LEG_R_BOT, radius2=LEG_R_TOP,
            depth=LEG_H, location=pos, end_fill_type="NGON"
        )
        leg = bpy.context.active_object
        leg.name = f"Leg_{i}"
        leg.rotation_euler = angles
        leg.data.materials.append(walnut)
        bpy.ops.object.shade_smooth()
        legs.append(leg)

    # Join all 4 legs into one assembly
    bpy.ops.object.select_all(action='DESELECT')
    for leg in legs:
        leg.select_set(True)
    bpy.context.view_layer.objects.active = legs[0]
    bpy.ops.object.join()
    leg_assembly = bpy.context.active_object
    leg_assembly.name = "Legs"

    # ═══ STATS ═══
    all_objects = [carcass] + drawers + handles + [leg_assembly]
    total_verts = sum(len(o.data.vertices) for o in all_objects)

    # Scene bounding box
    bbox_min = [float('inf')] * 3
    bbox_max = [float('-inf')] * 3
    for obj in all_objects:
        for v in obj.data.vertices:
            wv = obj.matrix_world @ v.co
            for i in range(3):
                bbox_min[i] = min(bbox_min[i], wv[i])
                bbox_max[i] = max(bbox_max[i], wv[i])
    dims = [bbox_max[i] - bbox_min[i] for i in range(3)]

    print(f"=== MID-CENTURY DRESSER ===")
    print(f"Objects: {len(all_objects)} (1 carcass + 6 drawers + 6 handles + 1 leg assembly)")
    print(f"Vertices: {total_verts}")
    print(f"Dimensions: {dims[0]:.3f} x {dims[1]:.3f} x {dims[2]:.3f} m (WxDxH)")

    for obj in all_objects:
        print(f"  {obj.name}: {len(obj.data.vertices)} verts, mats={[m.name for m in obj.data.materials]}")

    # Export
    bpy.ops.wm.usd_export(
        filepath="/home/msi/IsaacLab/scripts/tools/simready_assets/cabinet/cabinet_asset.usd",
        export_materials=True
    )
    print("USD exported")

    # Save .blend
    bpy.ops.wm.save_as_mainfile(
        filepath="/home/msi/IsaacLab/scripts/tools/simready_assets/cabinet/cabinet.blend"
    )
    print("Blend saved")

main()
