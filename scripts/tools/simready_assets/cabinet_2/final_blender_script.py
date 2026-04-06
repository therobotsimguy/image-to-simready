import bpy
import bmesh
import math
from mathutils import Vector

# ─────────────────────────────────────────────────
# 0. CLEAR SCENE
# ─────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)
for c in list(bpy.data.collections):
    if c.name != 'Collection':
        bpy.data.collections.remove(c)

# ─────────────────────────────────────────────────
# 1. HELPER FUNCTIONS
# ─────────────────────────────────────────────────
def set_origin_keep_visual(obj, new_origin_x, new_origin_y, new_origin_z):
    new_origin = Vector((new_origin_x, new_origin_y, new_origin_z))
    offset = new_origin - obj.location
    obj.location = new_origin
    for v in obj.data.vertices:
        v.co -= offset


def create_box(name, sx, sy, sz, loc, mat=None):
    """Create a box at loc with dimensions sx, sy, sz (full extents)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj


def create_cylinder(name, radius, depth, loc, rot=(0,0,0), mat=None, segments=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=segments)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    if mat:
        obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj


def create_sphere(name, radius, loc, mat=None, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=segments, ring_count=rings)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj


def join_objects(objects):
    """Join a list of objects into one."""
    if not objects:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    return bpy.context.active_object


# ─────────────────────────────────────────────────
# 2. MATERIALS
# ─────────────────────────────────────────────────
def make_wood_material():
    mat = bpy.data.materials.new(name="Teak_Wood")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.72, 0.50, 0.30, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.55
    bsdf.inputs['Metallic'].default_value = 0.0
    # Add subtle wood grain via noise -> color ramp
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.location = (-600, 0)
    noise.inputs['Scale'].default_value = 20.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Distortion'].default_value = 3.0
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.location = (-800, 0)
    mapping.inputs['Scale'].default_value = (1.0, 15.0, 1.0)
    texcoord = tree.nodes.new('ShaderNodeTexCoord')
    texcoord.location = (-1000, 0)
    tree.links.new(texcoord.outputs['Object'], mapping.inputs['Vector'])
    tree.links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
    ramp = tree.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-300, 0)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.65, 0.42, 0.22, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.80, 0.58, 0.38, 1.0)
    tree.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    tree.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    # Bump for wood grain
    bump = tree.nodes.new('ShaderNodeBump')
    bump.location = (-150, -200)
    bump.inputs['Strength'].default_value = 0.05
    tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def make_metal_material():
    mat = bpy.data.materials.new(name="Brushed_Nickel")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.75, 0.75, 0.75, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.35
    bsdf.inputs['Metallic'].default_value = 1.0
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


wood_mat = make_wood_material()
metal_mat = make_metal_material()

# ─────────────────────────────────────────────────
# 3. DIMENSIONS (all in meters)
# ─────────────────────────────────────────────────
# Overall dimensions
W = 1.20    # total width
D = 0.46    # total depth
H = 0.88    # total height (to top of top panel)

# Top panel
top_thick = 0.025
top_overhang_front = 0.020
top_overhang_side = 0.020

# Legs
leg_w = 0.045
leg_d = 0.045
leg_height = H - top_thick  # legs go from ground to underside of top

# Leg positions (outer corners of the cabinet body)
body_w = W - 2 * top_overhang_side  # 1.16
body_d = D - 2 * top_overhang_front  # 0.42 approx, use 0.42

# Side panels
side_thick = 0.019
side_h = 0.70  # height of side panel (between top and bottom rail above legs)
side_d_inner = body_d - 2 * leg_d  # inner depth

# Bottom of cabinet body is at leg exposure height
leg_exposed = 0.08  # how much leg shows below cabinet body
body_bottom_z = leg_exposed
body_top_z = H - top_thick

# Drawer and door layout
gap = 0.004  # gap between components
stile_w = 0.022  # vertical divider width between bays
n_bays = 3
total_stile_w = 2 * stile_w
total_gap_w = 0  # gaps included in bay calc
avail_w = body_w - 2 * side_thick - total_stile_w - 2 * leg_w
bay_w = avail_w / n_bays  # width per bay

# Row heights
drawer_ratio = 0.22
door_ratio = 0.62
rail_h = 0.022  # horizontal rail between drawers and doors

drawer_h = 0.155
door_h = body_top_z - body_bottom_z - drawer_h - rail_h - gap * 3
# Adjust door_h to use available space
total_front_h = body_top_z - body_bottom_z
door_h = total_front_h - drawer_h - rail_h - gap * 4

# Correct door_h if needed
if door_h < 0.3:
    door_h = 0.42

# Front face Z position (front of legs)
front_z_y = -body_d / 2 + leg_d  # actually let's work in a coordinate system

# ─── Coordinate System ───
# Origin at bottom center of cabinet (between legs, on ground)
# X = left-right, Y = front-back (negative = front), Z = up

# Leg positions
fl_x = -body_w/2 + leg_w/2   # front left
fr_x = body_w/2 - leg_w/2    # front right
front_y = -body_d/2 + leg_d/2
back_y = body_d/2 - leg_d/2
leg_cz = leg_height / 2

# Side panel positions
left_side_x = -body_w/2 + leg_w + side_thick/2
right_side_x = body_w/2 - leg_w - side_thick/2
side_panel_inner_d = body_d - 2 * leg_d
side_panel_z = body_bottom_z + side_h / 2

# Back panel
back_thick = 0.010
back_x = 0
back_panel_y = body_d/2 - leg_d + back_thick/2  # inner face of back legs
back_panel_w = body_w - 2 * leg_w
back_panel_h = side_h

# Bottom shelf
shelf_thick = 0.019
shelf_z = body_bottom_z + shelf_thick / 2
shelf_w = body_w - 2 * leg_w - 2 * side_thick
shelf_d = body_d - 2 * leg_d

# Front face Y (the front plane of the cabinet body)
front_face_y = -body_d / 2 + leg_d

# Bay X positions (left edge of each bay)
inner_left = -body_w/2 + leg_w + side_thick
inner_right = body_w/2 - leg_w - side_thick
# Three bays separated by two stiles
bay_total_w = inner_right - inner_left
bay_w = (bay_total_w - 2 * stile_w) / 3.0

bay_centers_x = []
bay_lefts_x = []
x_cursor = inner_left
for i in range(3):
    bay_lefts_x.append(x_cursor)
    bay_centers_x.append(x_cursor + bay_w / 2)
    x_cursor += bay_w
    if i < 2:
        x_cursor += stile_w

# Drawer dimensions
drawer_front_thick = 0.020
drawer_front_h = drawer_h - 2 * gap
drawer_front_w = bay_w - 2 * gap

# Drawer front positions (Z)
drawer_front_cz = body_top_z - gap - drawer_front_h / 2

# Door dimensions
door_front_thick = 0.020
door_front_h = door_h
door_front_w = bay_w - 2 * gap

# Rail between drawers and doors
rail_z = drawer_front_cz - drawer_front_h / 2 - gap - rail_h / 2

# Door Z center
door_cz = rail_z - rail_h / 2 - gap - door_front_h / 2

# Recalc to make sure doors don't go below body bottom
door_bottom = door_cz - door_front_h / 2
if door_bottom < body_bottom_z + gap:
    door_front_h = (rail_z - rail_h / 2 - gap) - (body_bottom_z + gap)
    door_cz = body_bottom_z + gap + door_front_h / 2

# Drawer box dimensions
drawer_box_wall = 0.012
drawer_box_depth = (body_d - 2 * leg_d) * 0.78
drawer_box_inner_w = drawer_front_w - 2 * drawer_box_wall
drawer_box_inner_h = drawer_front_h - drawer_box_wall - 0.01  # slightly less than front

print(f"Body W: {body_w:.3f}, Body D: {body_d:.3f}")
print(f"Bay W: {bay_w:.3f}, Drawer H: {drawer_front_h:.3f}, Door H: {door_front_h:.3f}")
print(f"Drawer CZ: {drawer_front_cz:.3f}, Rail Z: {rail_z:.3f}, Door CZ: {door_cz:.3f}")

# ─────────────────────────────────────────────────
# 4. BUILD FRAME PARTS
# ─────────────────────────────────────────────────
frame_parts = []

# 4a. Four legs (slightly tapered)
def create_tapered_leg(name, cx, cy, mat):
    """Create a tapered leg. Top is leg_w x leg_d, bottom is slightly smaller."""
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    top_w = leg_w / 2
    top_d = leg_d / 2
    bot_w = leg_w / 2 * 0.75
    bot_d = leg_d / 2 * 0.75
    tz = leg_height
    # Vertices: bottom 4, top 4
    v0 = bm.verts.new((-bot_w, -bot_d, 0))
    v1 = bm.verts.new((bot_w, -bot_d, 0))
    v2 = bm.verts.new((bot_w, bot_d, 0))
    v3 = bm.verts.new((-bot_w, bot_d, 0))
    v4 = bm.verts.new((-top_w, -top_d, tz))
    v5 = bm.verts.new((top_w, -top_d, tz))
    v6 = bm.verts.new((top_w, top_d, tz))
    v7 = bm.verts.new((-top_w, top_d, tz))
    # Faces
    bm.faces.new([v0, v1, v2, v3])  # bottom
    bm.faces.new([v7, v6, v5, v4])  # top
    bm.faces.new([v0, v4, v5, v1])  # front
    bm.faces.new([v1, v5, v6, v2])  # right
    bm.faces.new([v2, v6, v7, v3])  # back
    bm.faces.new([v3, v7, v4, v0])  # left
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (cx, cy, 0)
    if mat:
        obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    return obj

leg_fl = create_tapered_leg("Leg_FL", fl_x, front_y, wood_mat)
leg_fr = create_tapered_leg("Leg_FR", fr_x, front_y, wood_mat)
leg_bl = create_tapered_leg("Leg_BL", fl_x, back_y, wood_mat)
leg_br = create_tapered_leg("Leg_BR", fr_x, back_y, wood_mat)
frame_parts.extend([leg_fl, leg_fr, leg_bl, leg_br])

# 4b. Top panel
top_obj = create_box("Top_Panel", W, D, top_thick,
                     (0, 0, H - top_thick / 2), wood_mat)
frame_parts.append(top_obj)

# 4c. Side panels
left_panel = create_box("Left_Side", side_thick, side_panel_inner_d, side_h,
                        (left_side_x, 0, side_panel_z), wood_mat)
right_panel = create_box("Right_Side", side_thick, side_panel_inner_d, side_h,
                         (right_side_x, 0, side_panel_z), wood_mat)
frame_parts.extend([left_panel, right_panel])

# 4d. Back panel
back_panel = create_box("Back_Panel", back_panel_w, back_thick, back_panel_h,
                        (0, body_d/2 - leg_d/2, side_panel_z), wood_mat)
frame_parts.append(back_panel)

# 4e. Bottom shelf
shelf_obj = create_box("Bottom_Shelf", shelf_w, shelf_d, shelf_thick,
                       (0, 0, shelf_z), wood_mat)
frame_parts.append(shelf_obj)

# 4f. Horizontal rail between drawers and doors (set back behind front face)
rail_depth = side_panel_inner_d
h_rail = create_box("Horizontal_Rail", shelf_w, rail_depth, rail_h,
                    (0, 0, rail_z), wood_mat)
frame_parts.append(h_rail)

# 4g. Vertical stiles between bays (face frame members)
stile_depth = 0.019  # thin face frame
for i in range(2):
    stile_x = bay_lefts_x[i] + bay_w + stile_w / 2
    # Drawer stile
    ds = create_box(f"Stile_Drawer_{i}", stile_w, stile_depth,
                    drawer_front_h + 2 * gap,
                    (stile_x, front_face_y - stile_depth / 2,
                     drawer_front_cz), wood_mat)
    frame_parts.append(ds)
    # Door stile
    dos = create_box(f"Stile_Door_{i}", stile_w, stile_depth,
                     door_front_h + 2 * gap,
                     (stile_x, front_face_y - stile_depth / 2,
                      door_cz), wood_mat)
    frame_parts.append(dos)

# 4h. Bottom front rail
bottom_rail_h = 0.025
bottom_rail_z = body_bottom_z + bottom_rail_h / 2
bfr = create_box("Bottom_Front_Rail", shelf_w, stile_depth, bottom_rail_h,
                 (0, front_face_y - stile_depth / 2, bottom_rail_z), wood_mat)
frame_parts.append(bfr)

# 4i. Top front rail (above drawers, below top)
top_rail_h = 0.020
top_rail_z = body_top_z - top_rail_h / 2
tfr = create_box("Top_Front_Rail", shelf_w, stile_depth, top_rail_h,
                 (0, front_face_y - stile_depth / 2, top_rail_z), wood_mat)
frame_parts.append(tfr)

# 4j. Raised back tray lip on top
tray_lip_h = 0.030
tray_lip_thick = 0.015
tray_lip = create_box("Tray_Lip", W, tray_lip_thick, tray_lip_h,
                      (0, D/2 - tray_lip_thick/2, H + tray_lip_h/2), wood_mat)
frame_parts.append(tray_lip)

# Side tray lips (short)
tray_lip_side_len = 0.15
for side in [-1, 1]:
    tsl = create_box(f"Tray_Lip_Side_{side}", tray_lip_thick, tray_lip_side_len, tray_lip_h,
                     (side * (W/2 - tray_lip_thick/2), D/2 - tray_lip_side_len/2,
                      H + tray_lip_h/2), wood_mat)
    frame_parts.append(tsl)

# Join all frame parts
frame_obj = join_objects(frame_parts)
frame_obj.name = "Main_Frame"

# Add bevel modifier to frame
bev = frame_obj.modifiers.new(name="Bevel", type='BEVEL')
bev.width = 0.002
bev.segments = 2
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(50)

# ─────────────────────────────────────────────────
# 5. BUILD DRAWERS (each as separate object with box)
# ─────────────────────────────────────────────────
def create_drawer(name, cx, cz, width, height, mat):
    """Create a drawer as a 5-sided open-top box with decorative front."""
    parts = []
    
    # Front panel (decorative face) - positioned at front face
    front_y_pos = front_face_y - drawer_front_thick / 2
    fp = create_box(f"{name}_front", width, drawer_front_thick, height,
                    (cx, front_y_pos, cz), mat)
    parts.append(fp)
    
    # Drawer box behind front panel
    box_w = width - 0.010  # slightly narrower than front
    box_h = height - 0.015  # slightly shorter
    box_depth = drawer_box_depth
    box_wall = drawer_box_wall
    box_bottom_thick = 0.008
    
    box_cy = front_face_y + box_depth / 2  # extends backward from front
    box_cz = cz - (height - box_h) / 2 + 0.005  # slightly lower
    
    # Bottom panel
    bp = create_box(f"{name}_bottom", box_w, box_depth, box_bottom_thick,
                    (cx, box_cy, box_cz - box_h / 2 + box_bottom_thick / 2), mat)
    parts.append(bp)
    
    # Left wall
    lw = create_box(f"{name}_lwall", box_wall, box_depth, box_h,
                    (cx - box_w / 2 + box_wall / 2, box_cy, box_cz), mat)
    parts.append(lw)
    
    # Right wall
    rw = create_box(f"{name}_rwall", box_wall, box_depth, box_h,
                    (cx + box_w / 2 - box_wall / 2, box_cy, box_cz), mat)
    parts.append(rw)
    
    # Back wall
    bw = create_box(f"{name}_back", box_w, box_wall, box_h,
                    (cx, box_cy + box_depth / 2 - box_wall / 2, box_cz), mat)
    parts.append(bw)
    
    # Join all parts
    drawer_obj = join_objects(parts)
    drawer_obj.name = name
    return drawer_obj


drawer_names = ["Drawer_Left", "Drawer_Center", "Drawer_Right"]
drawer_objects = []
for i in range(3):
    d = create_drawer(drawer_names[i], bay_centers_x[i], drawer_front_cz,
                      drawer_front_w, drawer_front_h, wood_mat)
    # Add bevel
    bev = d.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = 0.0015
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(50)
    drawer_objects.append(d)

# ─────────────────────────────────────────────────
# 6. BUILD DOORS (each as separate object)
# ─────────────────────────────────────────────────
def create_door_panel(name, cx, cz, width, height, mat):
    """Create a door with frame-and-panel construction."""
    # Main door panel
    door_y = front_face_y - door_front_thick / 2
    
    # Create using bmesh for panel detail
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    
    hw = width / 2
    hh = height / 2
    hd = door_front_thick / 2
    
    # Outer frame vertices (front and back faces)
    # We'll create a simple box first, then add panel detail
    # Front face
    frame_border = 0.045  # frame border width
    panel_recess = 0.004  # how much the panel is recessed
    
    # Create outer box
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= width
        v.co.y *= door_front_thick
        v.co.z *= height
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (cx, door_y, cz)
    
    if mat:
        obj.data.materials.append(mat)
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    
    return obj


door_objects = []
# Hinge sides: left door hinges on left, center can hinge on left, right hinges on right
hinge_sides = ['left', 'left', 'right']

for i in range(3):
    door = create_door_panel(f"Door_{['Left','Center','Right'][i]}",
                             bay_centers_x[i], door_cz,
                             door_front_w, door_front_h, wood_mat)
    
    # Add bevel
    bev = door.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = 0.0015
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(50)
    
    # Set origin to hinge edge
    door_y_pos = front_face_y - door_front_thick / 2
    if hinge_sides[i] == 'left':
        hinge_x = bay_centers_x[i] - door_front_w / 2
    else:
        hinge_x = bay_centers_x[i] + door_front_w / 2
    
    set_origin_keep_visual(door, hinge_x, door_y_pos, door_cz)
    
    door_objects.append(door)

# ─────────────────────────────────────────────────
# 7. DRAWER HANDLES (bar pulls)
# ─────────────────────────────────────────────────
handle_objects = []
handle_width = 0.095
handle_radius = 0.004
handle_standoff = 0.015  # distance from drawer face
post_radius = 0.005
post_height = handle_standoff

for i in range(3):
    cx = bay_centers_x[i]
    cz = drawer_front_cz
    handle_y = front_face_y - drawer_front_thick - handle_standoff / 2
    
    handle_parts = []
    
    # Bar (horizontal cylinder)
    bar = create_cylinder(f"Handle_Bar_{i}", handle_radius, handle_width,
                         (cx, handle_y - handle_standoff / 2, cz),
                         rot=(0, 0, math.pi / 2), mat=metal_mat)
    handle_parts.append(bar)
    
    # Left post
    lp = create_cylinder(f"Handle_LPost_{i}", post_radius, post_height,
                        (cx - handle_width / 2 + 0.008, front_face_y - post_height / 2, cz),
                        rot=(math.pi / 2, 0, 0), mat=metal_mat, segments=16)
    handle_parts.append(lp)
    
    # Right post
    rp = create_cylinder(f"Handle_RPost_{i}", post_radius, post_height,
                        (cx + handle_width / 2 - 0.008, front_face_y - post_height / 2, cz),
                        rot=(math.pi / 2, 0, 0), mat=metal_mat, segments=16)
    handle_parts.append(rp)
    
    handle_obj = join_objects(handle_parts)
    handle_obj.name = f"Handle_Drawer_{['Left','Center','Right'][i]}"
    handle_objects.append(handle_obj)

# ─────────────────────────────────────────────────
# 8. DOOR KNOBS
# ─────────────────────────────────────────────────
knob_objects = []
knob_radius = 0.013
knob_stem_radius = 0.005
knob_stem_height = 0.018

# Knobs are between the doors: 2 knobs (at stile positions between center-left, center-right)
# Actually from the image there are 2 round knobs between the 3 doors
# Left door knob on right edge, center door has no knob (shared), right door knob on left edge
# Let's place knobs: one between left-center doors, one between center-right doors

# Looking at image more carefully: there appear to be round knobs on the center door
# at both its left edge and right edge area
# Actually the knobs appear to be: one on center door near left stile, one on center door near right stile

knob_positions = []
for i in range(2):
    stile_x = bay_lefts_x[i] + bay_w + stile_w / 2
    # Knob slightly offset from stile toward center
    if i == 0:
        kx = stile_x + 0.015  # just right of left stile
    else:
        kx = stile_x - 0.015  # just left of right stile
    knob_positions.append(kx)

for i, kx in enumerate(knob_positions):
    parts = []
    knob_y = front_face_y - door_front_thick - knob_stem_height
    
    # Stem
    stem = create_cylinder(f"Knob_Stem_{i}", knob_stem_radius, knob_stem_height,
                          (kx, front_face_y - knob_stem_height / 2, door_cz),
                          rot=(math.pi / 2, 0, 0), mat=metal_mat, segments=16)
    parts.append(stem)
    
    # Knob sphere
    knob = create_sphere(f"Knob_Head_{i}", knob_radius,
                        (kx, front_face_y - knob_stem_height - knob_radius * 0.5, door_cz),
                        mat=metal_mat)
    # Flatten knob slightly
    knob.scale = (1.0, 0.6, 1.0)
    bpy.context.view_layer.objects.active = knob
    knob.select_set(True)
    bpy.ops.object.transform_apply(scale=True)
    knob.select_set(False)
    parts.append(knob)
    
    knob_obj = join_objects(parts)
    knob_obj.name = f"Knob_Door_{['Left','Right'][i]}"
    knob_objects.append(knob_obj)

# Third knob - actually looking at image description says 3 knobs
# Add a third knob on the left door's right edge and right door's left edge
# Wait - the vision data says 3 knobs. Let me add one more.
# Looking at image: there seem to be knobs between each pair of doors

# Actually let's check: the center door appears to have 2 knobs (one on each side).
# But the vision says knob count = 3. Let me interpret: 
# One knob per door bay, but the center shares. 
# Actually: left door has knob near right, center has knob near left (shared position), right has knob near left
# That gives us 2 positions but 3 is from the vision stack.
# Let me add a third knob for the right side
third_knob_parts = []
kx3 = bay_centers_x[1]  # center of center door
stem3 = create_cylinder("Knob_Stem_2", knob_stem_radius, knob_stem_height,
                       (kx3, front_face_y - knob_stem_height / 2, door_cz),
                       rot=(math.pi / 2, 0, 0), mat=metal_mat, segments=16)
third_knob_parts.append(stem3)
knob3 = create_sphere("Knob_Head_2", knob_radius,
                     (kx3, front_face_y - knob_stem_height - knob_radius * 0.5, door_cz),
                     mat=metal_mat)
knob3.scale = (1.0, 0.6, 1.0)
bpy.context.view_layer.objects.active = knob3
knob3.select_set(True)
bpy.ops.object.transform_apply(scale=True)
knob3.select_set(False)
third_knob_parts.append(knob3)
knob_obj3 = join_objects(third_knob_parts)
knob_obj3.name = "Knob_Door_Center"
knob_objects.append(knob_obj3)

# ─────────────────────────────────────────────────
# 9. RAISED PANEL DETAIL ON DOORS (using bmesh inset on front face)
# ─────────────────────────────────────────────────
# We'll add panel detail by creating a slightly raised inner panel on each door
# This is done by creating additional geometry on each door

for door in door_objects:
    # Add a solidify modifier for thickness, then manual panel detail
    pass  # The box shape with bevel already gives a good look
    # For more detail, we could use boolean or inset, but keeping it clean

# ─────────────────────────────────────────────────
# 10. ADD RAISED PANEL DETAIL BOXES (decorative overlays)
# ─────────────────────────────────────────────────
# Add raised center panels on drawer fronts
for i, drawer in enumerate(drawer_objects):
    panel_w = drawer_front_w - 0.08  # 40mm border on each side
    panel_h = drawer_front_h - 0.05  # 25mm border top/bottom
    panel_thick = 0.006
    panel_y = front_face_y - drawer_front_thick - panel_thick / 2
    
    panel = create_box(f"Drawer_Panel_{i}", panel_w, panel_thick, panel_h,
                      (bay_centers_x[i], panel_y, drawer_front_cz), wood_mat)
    
    # Select both drawer and panel, join
    bpy.ops.object.select_all(action='DESELECT')
    panel.select_set(True)
    drawer.select_set(True)
    bpy.context.view_layer.objects.active = drawer
    bpy.ops.object.join()
    drawer_objects[i] = bpy.context.active_object
    drawer_objects[i].name = f"Drawer_{['Left','Center','Right'][i]}"

# Add raised center panels on door fronts
for i, door in enumerate(door_objects):
    panel_w = door_front_w - 0.09
    panel_h = door_front_h - 0.09
    panel_thick = 0.006
    
    # Door location (origin is at hinge edge)
    door_cx = bay_centers_x[i]
    door_cy = front_face_y - door_front_thick / 2
    panel_y = front_face_y - door_front_thick - panel_thick / 2
    
    panel = create_box(f"Door_Panel_{i}", panel_w, panel_thick, panel_h,
                      (door_cx, panel_y, door_cz), wood_mat)
    
    bpy.ops.object.select_all(action='DESELECT')
    panel.select_set(True)
    door.select_set(True)
    bpy.context.view_layer.objects.active = door
    bpy.ops.object.join()
    door_objects[i] = bpy.context.active_object
    door_objects[i].name = f"Door_{['Left','Center','Right'][i]}"

# ─────────────────────────────────────────────────
# 11. FINAL CLEANUP AND EXPORT
# ─────────────────────────────────────────────────

# Apply smooth shading to all objects
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth()
        obj.select_set(False)

# Print stats
print("\n" + "=" * 50)
print("SIDEBOARD CABINET - BUILD COMPLETE")
print("=" * 50)
obj_count = len([o for o in bpy.data.objects if o.type == 'MESH'])
total_verts = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
print(f"Total objects: {obj_count}")
print(f"Total vertices: {total_verts}")

# Get bounding box
all_coords = []
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        for v in obj.data.vertices:
            world_co = obj.matrix_world @ v.co
            all_coords.append(world_co)

if all_coords:
    xs = [c.x for c in all_coords]
    ys = [c.y for c in all_coords]
    zs = [c.z for c in all_coords]
    dim_x = max(xs) - min(xs)
    dim_y = max(ys) - min(ys)
    dim_z = max(zs) - min(zs)
    print(f"Bounding box: {dim_x:.3f} x {dim_y:.3f} x {dim_z:.3f} m")
    print(f"  Width (X): {dim_x:.3f} m ({dim_x*1000:.0f} mm)")
    print(f"  Depth (Y): {dim_y:.3f} m ({dim_y*1000:.0f} mm)")
    print(f"  Height (Z): {dim_z:.3f} m ({dim_z*1000:.0f} mm)")

# List all objects
print("\nObjects:")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"  {obj.name}: {len(obj.data.vertices)} verts, loc=({obj.location.x:.3f}, {obj.location.y:.3f}, {obj.location.z:.3f})")

# Save paths
import os
output_dir = "/home/msi/IsaacLab/scripts/tools/simready_assets/cabinet_2"
os.makedirs(output_dir, exist_ok=True)

blend_path = os.path.join(output_dir, "cabinet_2.blend")
usd_path = os.path.join(output_dir, "cabinet_2_asset.usd")

# Save .blend
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"\nSaved .blend to: {blend_path}")

# Export USD
bpy.ops.wm.usd_export(filepath=usd_path, selected_objects_only=False)
print(f"Saved .usd to: {usd_path}")

print("\nDONE!")