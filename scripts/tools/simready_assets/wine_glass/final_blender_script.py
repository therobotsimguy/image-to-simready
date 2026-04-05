import bpy
import bmesh
import mathutils
from mathutils import Vector
import math

def clear_scene():
    # Remove all objects
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    
    # Remove all meshes
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    
    # Remove all materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    
    # Remove all curves
    for curve in bpy.data.curves:
        bpy.data.curves.remove(curve)

def create_wine_glass():
    # Create wine glass using body of revolution approach
    
    # Define profile points (radius, z) from bottom to top
    outer_profile = [
        (0.0, 0.0),          # Foot center bottom
        (0.036, 0.0),        # Foot outer bottom edge
        (0.036, 0.0025),     # Foot outer top edge
        (0.030, 0.008),      # Foot to stem fillet start
        (0.003, 0.020),      # Stem start after fillet
        (0.003, 0.075),      # Stem top before bowl fillet
        (0.009, 0.0975),     # Bowl base after fillet
        (0.033, 0.1475),     # Bowl maximum diameter
        (0.0315, 0.185),     # Bowl rim outer
    ]
    
    inner_profile = [
        (0.0303, 0.185),     # Bowl rim inner (1.2mm wall)
        (0.032, 0.1475),     # Bowl max inner (1.0mm wall)
        (0.007, 0.0975),     # Bowl base inner (2.0mm wall)
        (0.0, 0.0875),       # Stem top (solid)
        (0.0, 0.0025),       # Foot top (solid)
        (0.0, 0.0),          # Back to center
    ]
    
    # Combine profiles to create closed loop
    profile_points = outer_profile + inner_profile
    
    # Create vertices and faces for revolution
    vertices = []
    faces = []
    segments = 64  # Number of rotational segments
    
    # Generate vertices by rotating profile around Z-axis
    for i in range(segments):
        angle = (2 * math.pi * i) / segments
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        for radius, z in profile_points:
            x = radius * cos_a
            y = radius * sin_a
            vertices.append((x, y, z))
    
    # Generate faces
    num_profile_points = len(profile_points)
    
    # Side faces (quads between segments)
    for i in range(segments):
        next_i = (i + 1) % segments
        
        for j in range(num_profile_points - 1):
            v1 = i * num_profile_points + j
            v2 = i * num_profile_points + (j + 1)
            v3 = next_i * num_profile_points + (j + 1)
            v4 = next_i * num_profile_points + j
            
            faces.append([v1, v2, v3, v4])
    
    # Create mesh
    mesh = bpy.data.meshes.new("WineGlass")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    
    # Create object
    wine_glass = bpy.data.objects.new("WineGlass", mesh)
    bpy.context.collection.objects.link(wine_glass)
    bpy.context.view_layer.objects.active = wine_glass
    wine_glass.select_set(True)
    
    # Enter edit mode to clean up
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Remove doubles
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    
    # Recalculate normals
    bpy.ops.mesh.normals_make_consistent(inside=False)
    
    # Select rim edges for fire-polished bevel
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Add bevel modifier for fire-polished edges
    bevel_mod = wine_glass.modifiers.new(name="FirePolish", type='BEVEL')
    bevel_mod.width = 0.0008
    bevel_mod.segments = 3
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # Apply smooth shading
    bpy.ops.object.shade_smooth()
    
    return wine_glass

def create_glass_material():
    # Create crystal glass material
    material = bpy.data.materials.new(name="CrystalGlass")
    material.use_nodes = True
    
    # Clear default nodes
    material.node_tree.nodes.clear()
    
    # Add Principled BSDF
    principled = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    # Glass properties
    principled.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    principled.inputs['Metallic'].default_value = 0.0
    principled.inputs['Roughness'].default_value = 0.0
    principled.inputs['Transmission Weight'].default_value = 1.0
    principled.inputs['IOR'].default_value = 1.52  # Crystal glass
    
    # Add output node
    output = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Link nodes
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def main():
    # Clear scene
    clear_scene()
    
    # Create wine glass
    wine_glass = create_wine_glass()
    
    # Create and apply material
    glass_material = create_glass_material()
    wine_glass.data.materials.append(glass_material)
    
    # Set origin to center of mass
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
    
    # Apply transforms
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    # Final cleanup in edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get bounding box dimensions
    bbox = wine_glass.bound_box
    min_coords = [min(coord[i] for coord in bbox) for i in range(3)]
    max_coords = [max(coord[i] for coord in bbox) for i in range(3)]
    dimensions = [max_coords[i] - min_coords[i] for i in range(3)]
    
    # Get vertex count
    vertex_count = len(wine_glass.data.vertices)
    
    # Print info
    print(f"Wine Glass Created:")
    print(f"Object Name: {wine_glass.name}")
    print(f"Dimensions (m): X={dimensions[0]:.3f}, Y={dimensions[1]:.3f}, Z={dimensions[2]:.3f}")
    print(f"Vertex Count: {vertex_count}")
    print(f"Material: {glass_material.name}")
    
    # Export to USD
    try:
        bpy.ops.wm.usd_export(
            filepath="/home/msi/IsaacLab/scripts/tools/simready_assets/wine_glass/wine_glass_asset.usd",
            export_materials=True,
            selected_objects_only=True
        )
        print("Successfully exported to USD format")
    except Exception as e:
        print(f"Export error: {e}")

main()