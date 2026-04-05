import bpy
import math

# Clear scene
for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)

# Wood material
wood = bpy.data.materials.new('Wood')
wood.use_nodes = True
_n = wood.node_tree.nodes; _l = wood.node_tree.links; _n.clear()
_out = _n.new('ShaderNodeOutputMaterial')
_bsdf = _n.new('ShaderNodeBsdfPrincipled')
_bsdf.inputs['Roughness'].default_value = 0.7
_tc = _n.new('ShaderNodeTexCoord')
_mp = _n.new('ShaderNodeMapping')
_mp.inputs['Scale'].default_value = (3, 3, 25)
_ns = _n.new('ShaderNodeTexNoise')
_ns.inputs['Scale'].default_value = 5
_ns.inputs['Detail'].default_value = 14
_ns.inputs['Roughness'].default_value = 0.8
_ramp = _n.new('ShaderNodeValToRGB')
_ramp.color_ramp.elements[0].position = 0.3
_ramp.color_ramp.elements[0].color = (0.6, 0.4, 0.2, 1)
_ramp.color_ramp.elements[1].position = 0.7
_ramp.color_ramp.elements[1].color = (0.85, 0.65, 0.4, 1)
_l.new(_tc.outputs['Object'], _mp.inputs['Vector'])
_l.new(_mp.outputs['Vector'], _ns.inputs['Vector'])
_l.new(_ns.outputs['Fac'], _ramp.inputs['Fac'])
_l.new(_ramp.outputs['Color'], _bsdf.inputs['Base Color'])
_l.new(_bsdf.outputs['BSDF'], _out.inputs['Surface'])

# Metal material
metal = bpy.data.materials.new('Metal')
metal.use_nodes = True
_n = metal.node_tree.nodes; _l = metal.node_tree.links; _n.clear()
_out = _n.new('ShaderNodeOutputMaterial')
_bsdf = _n.new('ShaderNodeBsdfPrincipled')
_bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
_bsdf.inputs['Metallic'].default_value = 1.0
_bsdf.inputs['Roughness'].default_value = 0.3
_l.new(_bsdf.outputs['BSDF'], _out.inputs['Surface'])

def box(x, y, z, w, d, h):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z), scale=(w, d, h))
    o = bpy.context.active_object
    bpy.ops.object.transform_apply(scale=True)
    return o

# Carcass panels
parts = []
parts.append(box(0.000000, 0.000000, 0.890000, 1.200000, 0.450000, 0.020000))
parts.append(box(0.000000, 0.000000, 0.160000, 1.200000, 0.450000, 0.020000))
parts.append(box(-0.590000, 0.000000, 0.525000, 0.020000, 0.450000, 0.750000))
parts.append(box(0.590000, 0.000000, 0.525000, 0.020000, 0.450000, 0.750000))
parts.append(box(0.000000, -0.215000, 0.525000, 1.200000, 0.020000, 0.750000))
parts.append(box(0.000000, 0.000000, 0.680000, 1.160000, 0.430000, 0.020000))
parts.append(box(-0.196667, 0.000000, 0.525000, 0.020000, 0.430000, 0.710000))
parts.append(box(0.196667, 0.000000, 0.525000, 0.020000, 0.430000, 0.710000))
# Legs
parts.append(box(-0.550000, -0.175000, 0.075000, 0.04, 0.04, 0.15))
parts.append(box(0.550000, -0.175000, 0.075000, 0.04, 0.04, 0.15))
parts.append(box(-0.550000, 0.175000, 0.075000, 0.04, 0.04, 0.15))
parts.append(box(0.550000, 0.175000, 0.075000, 0.04, 0.04, 0.15))

bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
carcass = bpy.context.active_object
carcass.name = 'Carcass'
carcass.data.materials.append(wood)
bpy.ops.object.shade_smooth()

# Row 0: Doors
box(-0.393333, 0.215000, 0.420000, 0.367333, 0.020000, 0.494000)
bpy.context.active_object.name = 'Door_0'
bpy.context.active_object.data.materials.append(wood)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012500, segments=16, ring_count=8, location=(-0.374667, 0.237000, 0.595000))
bpy.context.active_object.name = 'Knob_0'
bpy.context.active_object.data.materials.append(metal)
bpy.ops.object.shade_smooth()

box(0.000000, 0.215000, 0.420000, 0.367333, 0.020000, 0.494000)
bpy.context.active_object.name = 'Door_1'
bpy.context.active_object.data.materials.append(wood)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012500, segments=16, ring_count=8, location=(-0.018667, 0.237000, 0.595000))
bpy.context.active_object.name = 'Knob_1'
bpy.context.active_object.data.materials.append(metal)
bpy.ops.object.shade_smooth()

box(0.393333, 0.215000, 0.420000, 0.367333, 0.020000, 0.494000)
bpy.context.active_object.name = 'Door_2'
bpy.context.active_object.data.materials.append(wood)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012500, segments=16, ring_count=8, location=(0.412000, 0.237000, 0.595000))
bpy.context.active_object.name = 'Knob_2'
bpy.context.active_object.data.materials.append(metal)
bpy.ops.object.shade_smooth()

# Row 1: Drawers
# Drawer 0
_dp = []
_dp.append(box(-0.393333, 0.215000, 0.790000, 0.367333, 0.020000, 0.194000))
_dp.append(box(-0.393333, 0.032250, 0.699000, 0.343333, 0.345500, 0.012000))
_dp.append(box(-0.571000, 0.032250, 0.790000, 0.012000, 0.345500, 0.182000))
_dp.append(box(-0.215667, 0.032250, 0.790000, 0.012000, 0.345500, 0.182000))
_dp.append(box(-0.393333, -0.144500, 0.790000, 0.343333, 0.012000, 0.182000))
bpy.ops.object.select_all(action='DESELECT')
for p in _dp: p.select_set(True)
bpy.context.view_layer.objects.active = _dp[0]
bpy.ops.object.join()
bpy.context.active_object.name = 'Drawer_0'
bpy.context.active_object.data.materials.append(wood)
bpy.ops.object.shade_smooth()

box(-0.393333, 0.230000, 0.790000, 0.100000, 0.012, 0.015)
bpy.context.active_object.name = 'Handle_0'
bpy.context.active_object.data.materials.append(metal)
bpy.ops.object.shade_smooth()

# Drawer 1
_dp = []
_dp.append(box(0.000000, 0.215000, 0.790000, 0.367333, 0.020000, 0.194000))
_dp.append(box(0.000000, 0.032250, 0.699000, 0.343333, 0.345500, 0.012000))
_dp.append(box(-0.177667, 0.032250, 0.790000, 0.012000, 0.345500, 0.182000))
_dp.append(box(0.177667, 0.032250, 0.790000, 0.012000, 0.345500, 0.182000))
_dp.append(box(0.000000, -0.144500, 0.790000, 0.343333, 0.012000, 0.182000))
bpy.ops.object.select_all(action='DESELECT')
for p in _dp: p.select_set(True)
bpy.context.view_layer.objects.active = _dp[0]
bpy.ops.object.join()
bpy.context.active_object.name = 'Drawer_1'
bpy.context.active_object.data.materials.append(wood)
bpy.ops.object.shade_smooth()

box(0.000000, 0.230000, 0.790000, 0.100000, 0.012, 0.015)
bpy.context.active_object.name = 'Handle_1'
bpy.context.active_object.data.materials.append(metal)
bpy.ops.object.shade_smooth()

# Drawer 2
_dp = []
_dp.append(box(0.393333, 0.215000, 0.790000, 0.367333, 0.020000, 0.194000))
_dp.append(box(0.393333, 0.032250, 0.699000, 0.343333, 0.345500, 0.012000))
_dp.append(box(0.215667, 0.032250, 0.790000, 0.012000, 0.345500, 0.182000))
_dp.append(box(0.571000, 0.032250, 0.790000, 0.012000, 0.345500, 0.182000))
_dp.append(box(0.393333, -0.144500, 0.790000, 0.343333, 0.012000, 0.182000))
bpy.ops.object.select_all(action='DESELECT')
for p in _dp: p.select_set(True)
bpy.context.view_layer.objects.active = _dp[0]
bpy.ops.object.join()
bpy.context.active_object.name = 'Drawer_2'
bpy.context.active_object.data.materials.append(wood)
bpy.ops.object.shade_smooth()

box(0.393333, 0.230000, 0.790000, 0.100000, 0.012, 0.015)
bpy.context.active_object.name = 'Handle_2'
bpy.context.active_object.data.materials.append(metal)
bpy.ops.object.shade_smooth()

# Stats
all_objs = [o for o in bpy.data.objects]
tv = sum(len(o.data.vertices) for o in all_objs if hasattr(o.data, 'vertices'))
from mathutils import Vector
bmin = Vector((1e9,1e9,1e9)); bmax = Vector((-1e9,-1e9,-1e9))
for o in all_objs:
    if not hasattr(o.data, 'vertices'): continue
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        bmin = Vector((min(bmin.x,w.x), min(bmin.y,w.y), min(bmin.z,w.z)))
        bmax = Vector((max(bmax.x,w.x), max(bmax.y,w.y), max(bmax.z,w.z)))
d = bmax - bmin
print(f'Objects: {len(all_objs)}')
print(f'Vertices: {tv}')
print(f'Dims: {d.x:.3f} x {d.y:.3f} x {d.z:.3f} m')
for o in all_objs: print(f'  {o.name}: {[m.name for m in o.data.materials]}')
bpy.ops.wm.usd_export(filepath='/home/msi/IsaacLab/scripts/tools/simready_assets/cabinet_2/cabinet_2_asset.usd', export_materials=True)
bpy.ops.wm.save_as_mainfile(filepath='/home/msi/IsaacLab/scripts/tools/simready_assets/cabinet_2/cabinet_2.blend')
print('Saved')