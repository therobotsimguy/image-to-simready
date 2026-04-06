import bpy
import bmesh
import os
from mathutils import Vector

# ============================================================
# CLEAR SCENE
# ============================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh)
for mat in bpy.data.materials:
    bpy.data.materials.remove(mat)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def create_box(name, cx, cy, cz, sx, sy, sz):
    """Create a box at center (cx,cy,cz) with full size (sx,sy,sz)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    return obj

def set_origin_keep_visual(obj, new_origin_x, new_origin_y, new_origin_z):
    new_origin = Vector((new_origin_x, new_origin_y, new_origin_z))
    offset = new_origin - obj.location
    obj.location = new_origin
    for v in obj.data.vertices:
        v.co -= offset

def set_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True

def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def add_bevel_modifier(obj, width=0.002, segments=2):
    mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = 0.785

def join_objects(objects):
    """Join a list of objects into one."""
    if not objects:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def create_drawer_box(name, front_cx, front_cy, front_cz, front_sx, front_sy, front_sz, carcass_depth, wall_thickness=0.012):
    """Create a 5-sided open-top drawer box."""
    parts = []
    
    # Front panel (decorative face)
    front = create_box(name + "_front", front_cx, front_cy, front_cz, front_sx, front_sy, front_sz)
    parts.append(front)
    
    # Internal box dimensions
    inner_width = front_sx - 2 * wall_thickness
    inner_depth = carcass_depth * 0.75
    inner_height = front_sz - wall_thickness  # slightly shorter than front
    
    box_center_y = front_cy - front_sy / 2 - inner_depth / 2
    box_center_z = front_cz - (front_sz - inner_height) / 2
    
    # Bottom panel
    bottom = create_box(name + "_bottom",
                        front_cx,
                        box_center_y,
                        front_cz - front_sz / 2 + wall_thickness / 2,
                        inner_width,
                        inner_depth,
                        wall_thickness)
    parts.append(bottom)
    
    # Left side wall
    left_wall = create_box(name + "_left_wall",
                           front_cx - front_sx / 2 + wall_thickness / 2,
                           box_center_y,
                           box_center_z,
                           wall_thickness,
                           inner_depth,
                           inner_height)
    parts.append(left_wall)
    
    # Right side wall
    right_wall = create_box(name + "_right_wall",
                            front_cx + front_sx / 2 - wall_thickness / 2,
                            box_center_y,
                            box_center_z,
                            wall_thickness,
                            inner_depth,
                            inner_height)
    parts.append(right_wall)
    
    # Back wall
    back_wall = create_box(name + "_back_wall",
                           front_cx,
                           box_center_y - inner_depth / 2 + wall_thickness / 2,
                           box_center_z,
                           inner_width,
                           wall_thickness,
                           inner_height)
    parts.append(back_wall)
    
    # Join all into one object
    joined = join_objects(parts)
    joined.name = name
    return joined

def create_raised_panel_door(name, cx, cy, cz, sx, sy, sz, frame_width=0.03, recess_depth=0.005):
    """Create a door with raised panel (frame-and-panel) look using bmesh."""
    # Create base door panel
    door = create_box(name, cx, cy, cz, sx, sy, sz)
    
    # Use bmesh to create the raised panel effect
    bm = bmesh.new()
    bm.from_mesh(door.data)
    bm.faces.ensure_lookup_table()
    
    # Find the front face (max Y normal)
    front_face = None
    for f in bm.faces:
        if f.normal.y > 0.9:
            front_face = f
            break
    
    if front_face:
        # Inset the front face
        result = bmesh.ops.inset_individual(bm, faces=[front_face], thickness=frame_width, depth=0)
        bm.faces.ensure_lookup_table()
        
        # Find the new inner face and extrude it inward
        for f in bm.faces:
            if f.normal.y > 0.9:
                # Check if this face is smaller (the inset face)
                area = f.calc_area()
                if area < sx * sz * 0.8:
                    bmesh.ops.translate(bm, verts=f.verts, vec=(0, -recess_depth, 0))
                    break
    
    bm.to_mesh(door.data)
    bm.free()
    door.data.update()
    
    return door

def create_bar_handle(name, cx, cy, cz, handle_width=0.10, handle_height=0.015, handle_depth=0.02):
    """Create a U-shaped bar pull handle."""
    parts = []
    
    # Main horizontal bar
    bar = create_box(name + "_bar", cx, cy + handle_depth, cz, handle_width, 0.008, 0.008)
    parts.append(bar)
    
    # Left mounting post
    left_post = create_box(name + "_left_post",
                           cx - handle_width / 2 + 0.004,
                           cy + handle_depth / 2,
                           cz,
                           0.008, handle_depth, 0.008)
    parts.append(left_post)
    
    # Right mounting post
    right_post = create_box(name + "_right_post",
                            cx + handle_width / 2 - 0.004,
                            cy + handle_depth / 2,
                            cz,
                            0.008, handle_depth, 0.008)
    parts.append(right_post)
    
    joined = join_objects(parts)
    joined.name = name
    return joined

def create_round_knob(name, cx, cy, cz, radius=0.015):
    """Create a round door knob."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=16, ring_count=8, location=(cx, cy + radius * 0.6, cz))
    knob = bpy.context.active_object
    knob.name = name
    bpy.ops.object.transform_apply(scale=True)
    return knob


# ============================================================
# MATERIALS
# ============================================================
# Teak/Oak wood material
mat_wood = bpy.data.materials.new(name="Teak_Wood")
mat_wood.use_nodes = True
nodes_w = mat_wood.node_tree.nodes
links_w = mat_wood.node_tree.links
nodes_w.clear()

output_w = nodes_w.new('ShaderNodeOutputMaterial')
output_w.location = (400, 0)
bsdf_w = nodes_w.new('ShaderNodeBsdfPrincipled')
bsdf_w.location = (0, 0)
bsdf_w.inputs['Base Color'].default_value = (0.75, 0.55, 0.35, 1.0)
bsdf_w.inputs['Roughness'].default_value = 0.55
bsdf_w.inputs['Metallic'].default_value = 0.0
links_w.new(bsdf_w.outputs['BSDF'], output_w.inputs['Surface'])

# Brushed nickel metal material
mat_metal = bpy.data.materials.new(name="Brushed_Nickel")
mat_metal.use_nodes = True
nodes_m = mat_metal.node_tree.nodes
links_m = mat_metal.node_tree.links
nodes_m.clear()

output_m = nodes_m.new('ShaderNodeOutputMaterial')
output_m.location = (400, 0)
bsdf_m = nodes_m.new('ShaderNodeBsdfPrincipled')
bsdf_m.location = (0, 0)
bsdf_m.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
bsdf_m.inputs['Roughness'].default_value = 0.4
bsdf_m.inputs['Metallic'].default_value = 1.0
links_m.new(bsdf_m.outputs['BSDF'], output_m.inputs['Surface'])


# ============================================================
# PRE-COMPUTED COORDINATES (EXACT from math engine)
# ============================================================

# Carcass panels
carcass_data = [
    {"name": "Top",    "center": (0, 0, 0.904),    "size": (1.371, 0.457, 0.02)},
    {"name": "Bottom", "center": (0, 0, 0.01),     "size": (1.371, 0.457, 0.02)},
    {"name": "Left",   "center": (-0.6755, 0, 0.457), "size": (0.02, 0.457, 0.914)},
    {"name": "Right",  "center": (0.6755, 0, 0.457),  "size": (0.02, 0.457, 0.914)},
    {"name": "Back",   "center": (0, -0.2185, 0.457), "size": (1.371, 0.02, 0.914)},
    {"name": "HDiv_0", "center": (0, 0, 0.6082),   "size": (1.331, 0.437, 0.02)},
    {"name": "VStile_0", "center": (-0.2252, 0, 0.457), "size": (0.02, 0.437, 0.874)},
    {"name": "VStile_1", "center": (0.2252, 0, 0.457),  "size": (0.02, 0.437, 0.874)},
]

# Leg data - these have height 0 in precomputed, we need to create visible legs
# The cabinet has legs that extend below. Looking at the image, the legs are part of the frame
# and the bottom panel sits above. Let me use the leg positions as reference.
leg_data = [
    {"name": "Leg_FL", "center": (-0.6355, 0.1785, 0.0), "size": (0.05, 0.05, 0.0)},
    {"name": "Leg_FR", "center": (0.6355, 0.1785, 0.0),  "size": (0.05, 0.05, 0.0)},
    {"name": "Leg_BL", "center": (-0.6355, -0.1785, 0.0), "size": (0.05, 0.05, 0.0)},
    {"name": "Leg_BR", "center": (0.6355, -0.1785, 0.0),  "size": (0.05, 0.05, 0.0)},
]

# Cell data for doors (row 0) and drawers (row 1)
# Row 0 = doors (bottom), Row 1 = drawers (top)
doors_data = [
    {"name": "Cell_r0_c0", "center": (-0.4503, 0.2185, 0.3091), "size": (0.4243, 0.02, 0.5722),
     "knob_pos": (-0.5149, 0.2405, 0.338)},
    {"name": "Cell_r0_c1", "center": (0.0, 0.2185, 0.3091), "size": (0.4243, 0.02, 0.5722),
     "knob_pos": (-0.0646, 0.2405, 0.338)},
    {"name": "Cell_r0_c2", "center": (0.4503, 0.2185, 0.3091), "size": (0.4243, 0.02, 0.5722),
     "knob_pos": (0.3858, 0.2405, 0.338)},
]

drawers_data = [
    {"name": "Cell_r1_c0", "center": (-0.4503, 0.2185, 0.7561), "size": (0.4243, 0.02, 0.2698),
     "pull_pos": (-0.4503, 0.2335, 0.7561)},
    {"name": "Cell_r1_c1", "center": (0.0, 0.2185, 0.7561), "size": (0.4243, 0.02, 0.2698),
     "pull_pos": (0.0, 0.2335, 0.7561)},
    {"name": "Cell_r1_c2", "center": (0.4503, 0.2185, 0.7561), "size": (0.4243, 0.02, 0.2698),
     "pull_pos": (0.4503, 0.2335, 0.7561)},
]


# ============================================================
# CREATE CARCASS / FRAME
# ============================================================
frame_parts = []

for panel in carcass_data:
    c = panel["center"]
    s = panel["size"]
    obj = create_box("Frame_" + panel["name"], c[0], c[1], c[2], s[0], s[1], s[2])
    assign_material(obj, mat_wood)
    set_smooth(obj)
    frame_parts.append(obj)

# Create legs - the precomputed has height=0, but the image shows legs
# Looking at the cabinet, the legs are the corner posts that are part of the side panels
# The bottom of the cabinet is at z=0, legs are incorporated into the frame
# Actually, from the image, the cabinet has 4 visible legs extending below the main body
# The precomputed bottom panel is at z=0.01, so legs must go from below that down
# But the precomputed leg height is 0, suggesting legs are integrated into the frame
# The image clearly shows legs. Let me create them as extensions below the bottom panel

# Actually, looking more carefully at the precomputed data:
# Bottom panel center z=0.01, so bottom face is at z=0 (ground level)
# The legs in the image appear to be part of the corner structure
# Since leg_h_m = 0.0 in grid data, the cabinet sits directly on the ground
# But the image shows visible legs! Let me look at the overall height = 0.914m
# and the carcass = 0.914m, so there are no separate legs below.
# The "legs" visible in the image are actually the corner posts of the frame.

# Let me create visible leg-like corner posts (slightly proud of the carcass)
# These are the front legs visible in the image, extending from bottom to top
leg_height = 0.914
leg_width = 0.05
leg_depth = 0.05

# Front left leg
fl = create_box("Frame_Leg_FL", -0.6555, 0.2035, 0.457, leg_width, leg_depth, leg_height)
assign_material(fl, mat_wood)
set_smooth(fl)
frame_parts.append(fl)

# Front right leg
fr = create_box("Frame_Leg_FR", 0.6555, 0.2035, 0.457, leg_width, leg_depth, leg_height)
assign_material(fr, mat_wood)
set_smooth(fr)
frame_parts.append(fr)

# Back left leg
bl = create_box("Frame_Leg_BL", -0.6555, -0.2035, 0.457, leg_width, leg_depth, leg_height)
assign_material(bl, mat_wood)
set_smooth(bl)
frame_parts.append(bl)

# Back right leg
br = create_box("Frame_Leg_BR", 0.6555, -0.2035, 0.457, leg_width, leg_depth, leg_height)
assign_material(br, mat_wood)
set_smooth(br)
frame_parts.append(br)

# Create a top surface with slight overhang
top_surface = create_box("Frame_TopSurface", 0, 0, 0.914 + 0.0125, 1.40, 0.48, 0.025)
assign_material(top_surface, mat_wood)
set_smooth(top_surface)
frame_parts.append(top_surface)

# Add front horizontal rail between drawer row and door row (behind the front faces)
# This rail is at z=0.6082, but it must be behind the drawer/door fronts
# front_y of cells = 0.2185, panel thickness = 0.02, so front face at 0.2185 + 0.01 = 0.2285
# Rail should be recessed behind the front panels
rail_y = 0.2185 - 0.02  # behind the front panel faces
front_rail_mid = create_box("Frame_FrontRailMid", 0, rail_y, 0.6082, 1.331, 0.02, 0.02)
assign_material(front_rail_mid, mat_wood)
set_smooth(front_rail_mid)
frame_parts.append(front_rail_mid)

# Front top rail (below the top)
front_rail_top = create_box("Frame_FrontRailTop", 0, rail_y, 0.894, 1.331, 0.02, 0.02)
assign_material(front_rail_top, mat_wood)
set_smooth(front_rail_top)
frame_parts.append(front_rail_top)

# Front bottom rail
front_rail_bottom = create_box("Frame_FrontRailBottom", 0, rail_y, 0.02, 1.331, 0.02, 0.02)
assign_material(front_rail_bottom, mat_wood)
set_smooth(front_rail_bottom)
frame_parts.append(front_rail_bottom)

# Front vertical stiles between doors (behind front faces)
vstile_left = create_box("Frame_FVStile_L", -0.2252, rail_y, 0.457, 0.02, 0.02, 0.874)
assign_material(vstile_left, mat_wood)
set_smooth(vstile_left)
frame_parts.append(vstile_left)

vstile_right = create_box("Frame_FVStile_R", 0.2252, rail_y, 0.457, 0.02, 0.02, 0.874)
assign_material(vstile_right, mat_wood)
set_smooth(vstile_right)
frame_parts.append(vstile_right)

# Join all frame parts
frame_obj = join_objects(frame_parts)
frame_obj.name = "Main_Frame"
add_bevel_modifier(frame_obj, width=0.002, segments=2)


# ============================================================
# CREATE DOORS (Row 0 - bottom row)
# ============================================================
door_names = ["Door_Left", "Door_Center", "Door_Right"]
door_hinge_sides = ["left", "left", "right"]  # left door hinges left, center hinges left, right hinges right

carcass_depth_for_reference = 0.457

for i, dd in enumerate(doors_data):
    c = dd["center"]
    s = dd["size"]
    kp = dd["knob_pos"]
    
    # Create raised panel door
    door = create_raised_panel_door(
        door_names[i],
        c[0], c[1], c[2],
        s[0], s[1], s[2],
        frame_width=0.035,
        recess_depth=0.004
    )
    assign_material(door, mat_wood)
    set_smooth(door)
    add_bevel_modifier(door, width=0.001, segments=1)
    
    # Set origin to hinge edge
    hinge_side = door_hinge_sides[i]
    if hinge_side == "left":
        hinge_x = c[0] - s[0] / 2
    else:
        hinge_x = c[0] + s[0] / 2
    
    set_origin_keep_visual(door, hinge_x, c[1], c[2])


# ============================================================
# CREATE DOOR KNOBS
# ============================================================
# From the image, there appear to be 2 knobs visible between the doors
# The precomputed data shows knob positions for each door
# Looking at the image more carefully: left door has a knob on its right side,
# center and right doors share knobs near their meeting edges
# Actually the vision data says 3 knobs but looking at image there are 2 round knobs
# between the doors. Let me follow the precomputed knob positions.

# Left door knob - on right side of left door
knob_left = create_round_knob("Knob_Door_Left",
                               doors_data[0]["knob_pos"][0],
                               doors_data[0]["knob_pos"][1],
                               doors_data[0]["knob_pos"][2],
                               radius=0.012)
assign_material(knob_left, mat_metal)
set_smooth(knob_left)

# Center door knob - between center and right door
# Actually from image, knobs appear between left-center and center-right doors
# The precomputed knob for center door is at its left edge
knob_center = create_round_knob("Knob_Door_Center",
                                 doors_data[1]["knob_pos"][0],
                                 doors_data[1]["knob_pos"][1],
                                 doors_data[1]["knob_pos"][2],
                                 radius=0.012)
assign_material(knob_center, mat_metal)
set_smooth(knob_center)

# Right door knob
knob_right = create_round_knob("Knob_Door_Right",
                                doors_data[2]["knob_pos"][0],
                                doors_data[2]["knob_pos"][1],
                                doors_data[2]["knob_pos"][2],
                                radius=0.012)
assign_material(knob_right, mat_metal)
set_smooth(knob_right)


# ============================================================
# CREATE DRAWERS (Row 1 - top row)
# ============================================================
drawer_names = ["Drawer_Left", "Drawer_Center", "Drawer_Right"]

for i, drd in enumerate(drawers_data):
    c = drd["center"]
    s = drd["size"]
    
    drawer = create_drawer_box(
        drawer_names[i],
        c[0], c[1], c[2],
        s[0], s[1], s[2],
        carcass_depth=carcass_depth_for_reference,
        wall_thickness=0.012
    )
    assign_material(drawer, mat_wood)
    set_smooth(drawer)
    add_bevel_modifier(drawer, width=0.001, segments=1)
    
    # Add raised panel effect to front face using bmesh
    # We need to find the front face of the front panel portion
    # The front panel is the first created piece, front face at max Y
    bm = bmesh.new()
    bm.from_mesh(drawer.data)
    bm.faces.ensure_lookup_table()
    
    # Find the front-most face that's large enough to be the drawer front
    front_faces = []
    max_y = -999
    for f in bm.faces:
        for v in f.verts:
            if v.co.y > max_y:
                max_y = v.co.y
    
    for f in bm.faces:
        if f.normal.y > 0.9:
            # Check if face center is near the front
            fc = f.calc_center_median()
            if abs(fc.y - max_y) < 0.005:
                area = f.calc_area()
                if area > 0.01:  # large enough to be the main front face
                    front_faces.append(f)
    
    if front_faces:
        result = bmesh.ops.inset_individual(bm, faces=front_faces, thickness=0.025, depth=0)
        bm.faces.ensure_lookup_table()
        # Find the inset face and recess it
        for f in bm.faces:
            if f.normal.y > 0.9:
                fc = f.calc_center_median()
                if abs(fc.y - max_y) < 0.005:
                    area = f.calc_area()
                    if area < s[0] * s[2] * 0.8 and area > 0.005:
                        bmesh.ops.translate(bm, verts=f.verts, vec=(0, -0.003, 0))
                        break
    
    bm.to_mesh(drawer.data)
    bm.free()
    drawer.data.update()


# ============================================================
# CREATE DRAWER HANDLES
# ============================================================
handle_names = ["Handle_Drawer_Left", "Handle_Drawer_Center", "Handle_Drawer_Right"]

for i, drd in enumerate(drawers_data):
    pp = drd["pull_pos"]
    handle = create_bar_handle(
        handle_names[i],
        pp[0], pp[1], pp[2],
        handle_width=0.10,
        handle_height=0.012,
        handle_depth=0.018
    )
    assign_material(handle, mat_metal)
    set_smooth(handle)


# ============================================================
# APPLY BEVEL MODIFIERS
# ============================================================
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        for mod in obj.modifiers:
            if mod.type == 'BEVEL':
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    pass


# ============================================================
# FINAL SMOOTH SHADING
# ============================================================
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        set_smooth(obj)


# ============================================================
# PRINT STATS
# ============================================================
total_verts = 0
total_objects = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        total_objects += 1
        total_verts += len(obj.data.vertices)

print(f"Total objects: {total_objects}")
print(f"Total vertices: {total_verts}")

# Get bounding box of all objects
min_coords = [999, 999, 999]
max_coords = [-999, -999, -999]
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        for v in obj.data.vertices:
            world_co = obj.matrix_world @ v.co
            for i_ax in range(3):
                min_coords[i_ax] = min(min_coords[i_ax], world_co[i_ax])
                max_coords[i_ax] = max(max_coords[i_ax], world_co[i_ax])

dims = [max_coords[i_ax] - min_coords[i_ax] for i_ax in range(3)]
print(f"Dimensions (W x D x H): {dims[0]:.3f} x {dims[1]:.3f} x {dims[2]:.3f} m")


# ============================================================
# SAVE FILES
# ============================================================
output_dir = "/home/msi/IsaacLab/scripts/tools/simready_assets/cabinet_2"
os.makedirs(output_dir, exist_ok=True)

# Save .blend file
blend_path = os.path.join(output_dir, "cabinet_2.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"Saved .blend to: {blend_path}")

# Export to USD
usd_path = os.path.join(output_dir, "cabinet_2_asset.usd")
bpy.ops.wm.usd_export(filepath=usd_path, selected_objects_only=False)
print(f"Exported USD to: {usd_path}")