import bpy
import bmesh
import math
import os
from mathutils import Vector

# ─── 1. CLEAR SCENE ─────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=True)

for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh)
for mat in bpy.data.materials:
    bpy.data.materials.remove(mat)
for curve in bpy.data.curves:
    bpy.data.curves.remove(curve)

# ─── 2. DIMENSIONS (in meters) ──────────────────────────────────────────────
head_across_flats = 0.024  # 24mm across flats (M16-ish hex)
head_across_corners = head_across_flats / math.cos(math.radians(30))  # ~27.7mm
head_height = 0.010  # 10mm
shank_diameter = 0.016  # 16mm
shank_radius = shank_diameter / 2.0
total_length = 0.075  # 75mm total bolt length
shank_length = 0.025  # smooth shank portion (25mm)
thread_length = total_length - head_height - shank_length  # ~40mm threaded
thread_pitch = 0.002  # 2mm pitch (M16 coarse)
thread_depth = 0.00125  # ~1.25mm thread depth (slightly less for galvanized)
thread_major_radius = shank_radius
thread_minor_radius = shank_radius - thread_depth
num_turns = int(thread_length / thread_pitch)
segments_per_turn = 32
chamfer_length = 0.003  # 3mm tip chamfer
head_chamfer = 0.001  # 1mm top edge chamfer on head

# ─── 3. CREATE BOLT MESH USING BMESH ────────────────────────────────────────
mesh = bpy.data.meshes.new("HexBolt")
bm = bmesh.new()

# ─── 3a. Hex Head ────────────────────────────────────────────────────────────
# Build hex head as a 6-sided prism
hex_radius = head_across_corners / 2.0
hex_verts_bottom = []
hex_verts_top = []

for i in range(6):
    angle = math.radians(60 * i + 30)  # +30 to align flats
    x = hex_radius * math.cos(angle)
    y = hex_radius * math.sin(angle)
    hex_verts_bottom.append(bm.verts.new((x, y, 0.0)))
    hex_verts_top.append(bm.verts.new((x, y, head_height)))

bm.verts.ensure_lookup_table()

# Bottom face
bm.faces.new(hex_verts_bottom[::-1])

# Top face
bm.faces.new(hex_verts_top)

# Side faces
for i in range(6):
    ni = (i + 1) % 6
    bm.faces.new([hex_verts_bottom[i], hex_verts_bottom[ni],
                   hex_verts_top[ni], hex_verts_top[i]])

# ─── 3b. Chamfer on top of hex head ─────────────────────────────────────────
# We'll add a beveled ring on top to simulate the chamfer
# Create inner chamfered ring on top
chamfer_hex_verts = []
chamfer_factor = 0.85  # slightly smaller radius
for i in range(6):
    angle = math.radians(60 * i + 30)
    x = hex_radius * chamfer_factor * math.cos(angle)
    y = hex_radius * chamfer_factor * math.sin(angle)
    chamfer_hex_verts.append(bm.verts.new((x, y, head_height + head_chamfer * 0.3)))

bm.verts.ensure_lookup_table()

# Remove old top face and create chamfered version
# Find and remove the top face
top_face = None
for f in bm.faces:
    if all(v in hex_verts_top for v in f.verts):
        top_face = f
        break
if top_face:
    bm.faces.remove(top_face)

# Connect outer top ring to chamfered ring
for i in range(6):
    ni = (i + 1) % 6
    bm.faces.new([hex_verts_top[i], hex_verts_top[ni],
                   chamfer_hex_verts[ni], chamfer_hex_verts[i]])

# Close the chamfered top
bm.faces.new(chamfer_hex_verts)

# ─── 3c. Washer face (circular bearing surface under head) ───────────────────
# Transition from hex bottom to circular shank
washer_segments = 32
washer_radius = shank_radius + 0.001  # slightly larger than shank
washer_height = -0.001  # 1mm below head bottom
washer_verts = []
for i in range(washer_segments):
    angle = 2 * math.pi * i / washer_segments
    x = washer_radius * math.cos(angle)
    y = washer_radius * math.sin(angle)
    washer_verts.append(bm.verts.new((x, y, washer_height)))

bm.verts.ensure_lookup_table()

# Remove bottom hex face and bridge to washer circle
bottom_face = None
for f in bm.faces:
    if all(v in hex_verts_bottom for v in f.verts):
        bottom_face = f
        break
if bottom_face:
    bm.faces.remove(bottom_face)

# Create transition faces from hex bottom to washer circle
# We need to triangulate between the 6 hex verts and 32 washer verts
# Simple approach: fan triangles from hex corners to washer segments
verts_per_hex_side = washer_segments // 6  # ~5 washer verts per hex side

for i in range(6):
    ni = (i + 1) % 6
    start_w = i * verts_per_hex_side
    end_w = (i + 1) * verts_per_hex_side
    if i == 5:
        end_w = washer_segments

    # Create triangle fan from hex edge to washer arc
    w_indices = list(range(start_w, end_w + 1))
    if w_indices[-1] >= washer_segments:
        w_indices[-1] = w_indices[-1] % washer_segments

    # First triangle
    bm.faces.new([hex_verts_bottom[i], washer_verts[w_indices[0]], hex_verts_bottom[ni]])

    # Middle triangles along the washer arc
    for j in range(len(w_indices) - 1):
        wi_cur = w_indices[j]
        wi_next = w_indices[j + 1]
        try:
            bm.faces.new([hex_verts_bottom[ni], washer_verts[wi_cur], washer_verts[wi_next]])
        except:
            pass

    # Last triangle connecting back
    if w_indices[-1] != (ni * verts_per_hex_side) % washer_segments:
        last_w = w_indices[-1]
        next_start = ((i + 1) * verts_per_hex_side) % washer_segments
        if last_w != next_start:
            try:
                bm.faces.new([hex_verts_bottom[ni], washer_verts[last_w], washer_verts[next_start]])
            except:
                pass

bm.to_mesh(mesh)
bm.free()

# ─── APPROACH: Build bolt body as separate clean mesh, then join ─────────────
# The hex head bridging is complex. Let's use a cleaner approach.
# Clear and rebuild properly.

bpy.data.meshes.remove(mesh)

# ═══════════════════════════════════════════════════════════════════════════════
# FRESH START - Build bolt using primitives and boolean operations
# ═══════════════════════════════════════════════════════════════════════════════

# ─── HEX HEAD ────────────────────────────────────────────────────────────────
bpy.ops.mesh.primitive_cylinder_add(
    vertices=6,
    radius=head_across_corners / 2.0,
    depth=head_height,
    location=(0, 0, head_height / 2.0),
    rotation=(0, 0, math.radians(30))
)
head_obj = bpy.context.active_object
head_obj.name = "BoltHead"
bpy.ops.object.transform_apply(rotation=True)

# Add chamfer to top of hex head using a cone boolean subtraction
# Create a cone that cuts the top edges
cone_radius = head_across_corners / 2.0 + 0.005
cone_height = head_chamfer * 4
bpy.ops.mesh.primitive_cone_add(
    vertices=64,
    radius1=cone_radius,
    radius2=0,
    depth=cone_height,
    location=(0, 0, head_height + cone_height / 2.0 - head_chamfer * 1.2)
)
cone_cutter = bpy.context.active_object
cone_cutter.name = "ConeCutter"

# Invert the cone: we want to cut the corners
# Actually, use a cylinder slightly larger minus a cone to create the chamfer
# Better approach: use a large cylinder minus the inverted cone shape

# Remove cone cutter, use bmesh bevel instead
bpy.data.objects.remove(cone_cutter, do_unlink=True)

# Select head and enter edit mode for bevel
bpy.context.view_layer.objects.active = head_obj
head_obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

bm = bmesh.from_edit_mesh(head_obj.data)
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()

# Find top edges (edges where both verts have z close to head_height)
top_edges = []
for e in bm.edges:
    if all(abs(v.co.z - head_height) < 0.0001 for v in e.verts):
        top_edges.append(e)

# Bevel top edges
if top_edges:
    result = bmesh.ops.bevel(bm, geom=top_edges, offset=head_chamfer,
                              segments=2, affect='EDGES')

bmesh.update_edit_mesh(head_obj.data)
bpy.ops.object.mode_set(mode='OBJECT')

# ─── SMOOTH SHANK ────────────────────────────────────────────────────────────
bpy.ops.mesh.primitive_cylinder_add(
    vertices=32,
    radius=shank_radius,
    depth=shank_length,
    location=(0, 0, -shank_length / 2.0)
)
shank_obj = bpy.context.active_object
shank_obj.name = "BoltShank"

# ─── THREADED SECTION ────────────────────────────────────────────────────────
# Build threaded section using from_pydata with helical thread profile
thread_verts = []
thread_faces = []

total_thread_segments = num_turns * segments_per_turn
thread_start_z = -(shank_length + thread_length)
thread_end_z = -shank_length

# For each segment along the helix, create a ring of vertices
# Ring consists of: inner radius, outer radius (thread crest)
# We use a simple approach: each cross-section has points for the thread profile

# Simplified approach: cylinder with sinusoidal radius variation
ring_verts_count = 4  # vertices per radial ring for thread profile (inner, mid-rise, crest, mid-fall)

# Actually, let's create the thread as a proper mesh with variable radius
# Each "slice" along z has a ring of vertices at the appropriate radius

verts_per_ring = 32  # circumferential resolution

for i in range(total_thread_segments + 1):
    t = i / total_thread_segments  # 0 to 1 along thread length
    z = thread_end_z - t * thread_length  # goes from shank bottom downward

    # Thread phase at this height
    z_in_thread = t * thread_length
    phase = (z_in_thread / thread_pitch) * 2 * math.pi

    for j in range(verts_per_ring):
        angle = 2 * math.pi * j / verts_per_ring

        # Thread profile: radius varies with angle - phase to create helix
        helix_phase = angle - phase
        # Triangular thread profile approximation using cosine
        thread_factor = max(0, math.cos(helix_phase))
        thread_factor = thread_factor ** 0.5  # sharpen the profile a bit

        # Chamfer at tip
        tip_factor = 1.0
        dist_from_tip = thread_length - z_in_thread  # distance from bolt tip
        if dist_from_tip < chamfer_length:
            tip_factor = dist_from_tip / chamfer_length
            tip_factor = max(0.3, tip_factor)

        # Thread runout near shank
        runout_length = thread_pitch * 2
        if z_in_thread < runout_length:
            runout_factor = z_in_thread / runout_length
        else:
            runout_factor = 1.0

        radius = thread_minor_radius + thread_depth * thread_factor * runout_factor
        # Apply tip chamfer to overall radius
        if dist_from_tip < chamfer_length:
            radius *= tip_factor

        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        thread_verts.append((x, y, z))

# Create faces connecting adjacent rings
for i in range(total_thread_segments):
    for j in range(verts_per_ring):
        nj = (j + 1) % verts_per_ring
        v0 = i * verts_per_ring + j
        v1 = i * verts_per_ring + nj
        v2 = (i + 1) * verts_per_ring + nj
        v3 = (i + 1) * verts_per_ring + j
        thread_faces.append((v0, v1, v2, v3))

# Cap the top of threads (connects to shank)
top_ring = list(range(verts_per_ring))
thread_faces.append(tuple(top_ring))

# Cap the bottom (bolt tip)
bottom_start = total_thread_segments * verts_per_ring
bottom_ring = list(range(bottom_start, bottom_start + verts_per_ring))
thread_faces.append(tuple(reversed(bottom_ring)))

thread_mesh = bpy.data.meshes.new("ThreadMesh")
thread_mesh.from_pydata(thread_verts, [], thread_faces)
thread_mesh.update()

thread_obj = bpy.data.objects.new("BoltThread", thread_mesh)
bpy.context.collection.objects.link(thread_obj)

# ─── JOIN ALL PARTS ──────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
head_obj.select_set(True)
shank_obj.select_set(True)
thread_obj.select_set(True)
bpy.context.view_layer.objects.active = head_obj
bpy.ops.object.join()

bolt_obj = bpy.context.active_object
bolt_obj.name = "HexBolt"

# Apply transforms
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# ─── FIX NORMALS ─────────────────────────────────────────────────────────────
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
# Remove doubles at junction points
bpy.ops.mesh.remove_doubles(threshold=0.0003)
bpy.ops.object.mode_set(mode='OBJECT')

# ─── SMOOTH SHADING ─────────────────────────────────────────────────────────
bpy.ops.object.shade_smooth()

# Add sharp edges on hex head flats using split normals / auto smooth via geometry nodes
# In Blender 4.3, we use mesh attribute or edge split modifier
# Use edge split modifier for hex head sharp edges
mod = bolt_obj.modifiers.new(name="EdgeSplit", type='EDGE_SPLIT')
mod.split_angle = math.radians(40)
bpy.ops.object.modifier_apply(modifier="EdgeSplit")
bpy.ops.object.shade_smooth()

# ─── 4. MATERIAL: Hot-Dip Galvanized Steel ──────────────────────────────────
mat = bpy.data.materials.new(name="GalvanizedSteel")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
for node in nodes:
    nodes.remove(node)

# Output
output_node = nodes.new('ShaderNodeOutputMaterial')
output_node.location = (800, 0)

# Principled BSDF
principled = nodes.new('ShaderNodeBsdfPrincipled')
principled.location = (400, 0)
principled.inputs['Base Color'].default_value = (0.55, 0.56, 0.57, 1.0)
principled.inputs['Metallic'].default_value = 0.85
principled.inputs['Roughness'].default_value = 0.6

links.new(principled.outputs['BSDF'], output_node.inputs['Surface'])

# Noise texture for roughness variation (spangle pattern)
tex_coord = nodes.new('ShaderNodeTexCoord')
tex_coord.location = (-600, 200)

mapping = nodes.new('ShaderNodeMapping')
mapping.location = (-400, 200)
mapping.inputs['Scale'].default_value = (50, 50, 50)
links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

noise1 = nodes.new('ShaderNodeTexNoise')
noise1.location = (-200, 200)
noise1.inputs['Scale'].default_value = 80.0
noise1.inputs['Detail'].default_value = 8.0
noise1.inputs['Roughness'].default_value = 0.7
links.new(mapping.outputs['Vector'], noise1.inputs['Vector'])

# Color ramp for roughness variation
ramp_rough = nodes.new('ShaderNodeMapRange')
ramp_rough.location = (0, 200)
ramp_rough.inputs['From Min'].default_value = 0.0
ramp_rough.inputs['From Max'].default_value = 1.0
ramp_rough.inputs['To Min'].default_value = 0.45
ramp_rough.inputs['To Max'].default_value = 0.7
links.new(noise1.outputs['Fac'], ramp_rough.inputs['Value'])
links.new(ramp_rough.outputs['Result'], principled.inputs['Roughness'])

# Second noise for color variation
noise2 = nodes.new('ShaderNodeTexNoise')
noise2.location = (-200, -100)
noise2.inputs['Scale'].default_value = 30.0
noise2.inputs['Detail'].default_value = 4.0
links.new(mapping.outputs['Vector'], noise2.inputs['Vector'])

# Mix base color with slight variation
color_mix = nodes.new('ShaderNodeMix')
color_mix.location = (200, -100)
color_mix.data_type = 'RGBA'
color_mix.inputs['Factor'].default_value = 0.15
color_mix.inputs[6].default_value = (0.55, 0.56, 0.57, 1.0)  # A color
color_mix.inputs[7].default_value = (0.62, 0.61, 0.55, 1.0)  # B color (slight warm tint)
links.new(noise2.outputs['Fac'], color_mix.inputs['Factor'])
links.new(color_mix.outputs[2], principled.inputs['Base Color'])

# Bump map for surface texture
noise3 = nodes.new('ShaderNodeTexNoise')
noise3.location = (-200, -300)
noise3.inputs['Scale'].default_value = 200.0
noise3.inputs['Detail'].default_value = 10.0
noise3.inputs['Roughness'].default_value = 0.5
links.new(mapping.outputs['Vector'], noise3.inputs['Vector'])

bump = nodes.new('ShaderNodeBump')
bump.location = (200, -300)
bump.inputs['Strength'].default_value = 0.05
bump.inputs['Distance'].default_value = 0.001
links.new(noise3.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], principled.inputs['Normal'])

# Assign material to bolt
bolt_obj.data.materials.append(mat)

# ─── 5. ORIENT BOLT - lay it on its side like in the reference image ────────
# The reference shows the bolt lying horizontally with head on the left
# Bolt is currently vertical (along Z). Rotate to lie along X axis.
# Actually, let's keep it vertical for simulation purposes. The image orientation
# is just for display. For SimReady assets, vertical is standard.

# Move origin to center of head bearing surface (bottom of head)
# The head bottom is at z=0 currently
bpy.context.scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# ─── 6. EXPORT ───────────────────────────────────────────────────────────────
output_dir = "/home/msi/IsaacLab/scripts/tools/simready_assets/bolt"
os.makedirs(output_dir, exist_ok=True)

usd_path = os.path.join(output_dir, "bolt_asset.usd")
blend_path = os.path.join(output_dir, "bolt.blend")

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# Export USD
bpy.ops.wm.usd_export(
    filepath=usd_path,
    selected_objects_only=False,
    export_materials=True
)

# ─── 7. VERIFICATION ────────────────────────────────────────────────────────
print("=" * 60)
print("BOLT GENERATION COMPLETE")
print("=" * 60)

obj_count = len([o for o in bpy.data.objects if o.type == 'MESH'])
print(f"Object count: {obj_count}")

vert_count = len(bolt_obj.data.vertices)
print(f"Vertex count: {vert_count}")

# Compute bounding box dimensions
bbox = bolt_obj.bound_box
xs = [v[0] for v in bbox]
ys = [v[1] for v in bbox]
zs = [v[2] for v in bbox]
width = max(xs) - min(xs)
depth = max(ys) - min(ys)
height = max(zs) - min(zs)
print(f"Dimensions: {width*1000:.1f}mm x {depth*1000:.1f}mm x {height*1000:.1f}mm")
print(f"  Width (X): {width*1000:.1f}mm")
print(f"  Depth (Y): {depth*1000:.1f}mm")
print(f"  Height (Z): {height*1000:.1f}mm")
print(f"Materials: {len(bolt_obj.data.materials)}")
print(f"Saved: {blend_path}")
print(f"Exported: {usd_path}")
print("=" * 60)