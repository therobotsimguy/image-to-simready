import bpy
import bmesh
import mathutils
from mathutils import Vector
import math

def clear_scene():
    """Remove all objects, meshes, materials, and curves from scene"""
    # Remove all objects
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    
    # Remove all meshes
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    
    # Remove all materials
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    
    # Remove all curves
    for curve in bpy.data.curves:
        bpy.data.curves.remove(curve)

def create_hex_head():
    """Create hex head with top chamfer"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.01215, depth=0.0101, location=(0, 0, 0.07505))
    hex_head = bpy.context.active_object
    hex_head.name = "HexHead"

    # Bevel top outer edges for chamfer
    bpy.context.view_layer.objects.active = hex_head
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bm = bmesh.from_edit_mesh(hex_head.data)
    bm.edges.ensure_lookup_table()

    top_z = max(v.co.z for v in bm.verts)
    for edge in bm.edges:
        v1, v2 = edge.verts
        if abs(v1.co.z - top_z) < 0.0005 and abs(v2.co.z - top_z) < 0.0005:
            r1 = math.sqrt(v1.co.x**2 + v1.co.y**2)
            r2 = math.sqrt(v2.co.x**2 + v2.co.y**2)
            if r1 > 0.008 or r2 > 0.008:
                edge.select = True

    bmesh.update_edit_mesh(hex_head.data)
    bpy.ops.mesh.bevel(offset=0.0015, segments=2)

    bpy.ops.object.mode_set(mode='OBJECT')
    return hex_head

def create_washer_face():
    """Create washer face bearing surface"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.0116, depth=0.001, location=(0, 0, 0.0695))
    washer_face = bpy.context.active_object
    washer_face.name = "WasherFace"
    return washer_face

def create_shank():
    """Create unthreaded shank section"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.0081, depth=0.042, location=(0, 0, 0.048))
    shank = bpy.context.active_object
    shank.name = "Shank"
    return shank

def create_thread_profile():
    """Create thread profile curve for helix bevel"""
    # Create triangular thread profile
    profile_points = [
        (0.0, 0.0, 0.0),      # Root
        (0.001, 0.0006, 0.0), # Peak
        (0.002, 0.0, 0.0),    # Root
        (0.0, 0.0, 0.0)       # Close curve
    ]
    
    # Create curve from points
    curve_data = bpy.data.curves.new('ThreadProfile', 'CURVE')
    curve_data.dimensions = '2D'
    curve_data.fill_mode = 'BOTH'
    
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(profile_points) - 1)
    
    for i, point in enumerate(profile_points):
        spline.points[i].co = (*point, 1.0)
    
    spline.use_cyclic_u = True
    
    profile_obj = bpy.data.objects.new('ThreadProfile', curve_data)
    bpy.context.collection.objects.link(profile_obj)
    
    return profile_obj

def create_helix_threads():
    """Create helical threads using curve with bevel profile"""
    # Thread parameters
    radius = 0.00815
    pitch = 0.002
    thread_length = 0.038
    turns = thread_length / pitch
    points_per_turn = 32
    total_points = int(turns * points_per_turn)

    # Create helix curve from scratch (not from operator)
    curve_data = bpy.data.curves.new(name="helix_curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 32

    spline = curve_data.splines.new("NURBS")
    spline.points.add(total_points - 1)

    for i in range(total_points):
        angle = (i / points_per_turn) * 2 * math.pi
        z = (i / total_points) * thread_length
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        spline.points[i].co = (x, y, z, 1.0)

    helix_obj = bpy.data.objects.new("ThreadHelix", curve_data)
    bpy.context.collection.objects.link(helix_obj)

    # Create thread profile and assign as bevel
    profile_obj = create_thread_profile()
    curve_data.bevel_object = profile_obj
    curve_data.use_fill_caps = True

    # Convert curve to mesh
    bpy.context.view_layer.objects.active = helix_obj
    bpy.ops.object.select_all(action="DESELECT")
    helix_obj.select_set(True)
    bpy.ops.object.convert(target="MESH")

    # Position at bottom of bolt (thread section)
    helix_obj.location = (0, 0, 0.0)

    # Clean up profile object
    bpy.data.objects.remove(profile_obj, do_unlink=True)

    return helix_obj

def create_tip():
    """Create bolt tip — cone chamfer at the bottom"""
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.0081, radius2=0.0003, depth=0.004, location=(0, 0, -0.002))
    tip = bpy.context.active_object
    tip.name = "Tip"
    return tip

def join_sections(sections):
    """Join all sections into single mesh"""
    # Select all sections
    bpy.ops.object.select_all(action='DESELECT')
    for section in sections:
        section.select_set(True)
    
    # Set active object
    bpy.context.view_layer.objects.active = sections[0]
    
    # Join objects
    bpy.ops.object.join()
    
    bolt = bpy.context.active_object
    bolt.name = "HexBolt_M16x80_HDG"
    
    return bolt

def clean_mesh(obj):
    """Clean up mesh geometry"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    # Remove doubles
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)

    # Recalculate normals
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply smooth shading
    bpy.ops.object.shade_smooth()

def create_hdg_material():
    """Create hot-dip galvanized steel material"""
    mat = bpy.data.materials.new(name="HDG_Steel")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear existing nodes
    nodes.clear()
    
    # Add Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # Add Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Add Noise Texture for surface variation
    noise = nodes.new(type='ShaderNodeTexNoise')
    noise.location = (-400, -200)
    noise.inputs['Scale'].default_value = 50.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.7
    
    # Add ColorRamp for roughness variation
    ramp = nodes.new(type='ShaderNodeValToRGB')
    ramp.location = (-200, -200)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.4, 0.4, 0.4, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.8, 0.8, 0.8, 1.0)
    
    # Add Texture Coordinate
    texcoord = nodes.new(type='ShaderNodeTexCoord')
    texcoord.location = (-600, -200)
    
    # Connect nodes
    links.new(texcoord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Roughness'])
    
    # Set material properties
    bsdf.inputs['Base Color'].default_value = (0.48, 0.48, 0.50, 1.0)  # HDG color
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.6  # Default value
    
    return mat

def main():
    """Main function to create hex bolt"""
    print("Creating Hex Head Bolt (M16x80 HDG)...")
    
    # Clear scene
    clear_scene()
    
    # Create sections from tip to head
    print("Creating sections...")
    tip = create_tip()
    threads = create_helix_threads()
    shank = create_shank()
    washer_face = create_washer_face()
    hex_head = create_hex_head()
    
    sections = [tip, threads, shank, washer_face, hex_head]
    
    # Join all sections
    print("Joining sections...")
    bolt = join_sections(sections)
    
    # Clean mesh
    print("Cleaning mesh...")
    clean_mesh(bolt)
    
    # Apply material
    print("Applying HDG material...")
    hdg_material = create_hdg_material()
    bolt.data.materials.append(hdg_material)
    
    # Set origin and apply transforms
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    # Get final stats
    vertex_count = len(bolt.data.vertices)
    dimensions = bolt.dimensions
    
    print(f"Final bolt: {bolt.name}")
    print(f"Vertices: {vertex_count}")
    print(f"Dimensions (m): X={dimensions.x:.4f}, Y={dimensions.y:.4f}, Z={dimensions.z:.4f}")
    
    # Export USD
    export_path = "/home/msi/IsaacLab/scripts/tools/simready_assets/bolt/bolt_asset.usd"
    bpy.ops.wm.usd_export(filepath=export_path, export_materials=True)
    print(f"Exported to: {export_path}")
    
    print("Hex bolt creation complete!")

main()