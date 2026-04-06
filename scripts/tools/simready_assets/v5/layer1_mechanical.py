#!/usr/bin/env python3
"""V5 Layer 1: Mechanical Extraction — "What CAN this object do?"

Extracts mechanical properties from the Blender scene:
  - Objects, names, vertices, bounding boxes
  - Materials
  - Hierarchy / parent-child relationships
  - Origins

Populates the BehaviorContract with PartContract entries.
"""

import json
import os
import sys
import socket

_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.dirname(_DIR)
sys.path.insert(0, _ASSETS_DIR)

from v5.behavior_contract import BehaviorContract, PartContract


def send_to_blender(script, port=9876):
    """Send script to Blender MCP and get result."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(180)
    sock.connect(("localhost", port))
    sock.sendall(json.dumps({"type": "execute_code", "params": {"code": script}}).encode())
    response = b""
    while True:
        try:
            chunk = sock.recv(8192)
            if not chunk:
                break
            response += chunk
            try:
                json.loads(response.decode())
                break
            except:
                continue
        except socket.timeout:
            break
    sock.close()
    if not response:
        raise RuntimeError("No response from Blender")
    return json.loads(response.decode())


def load_obj_in_blender(obj_path, port=9876):
    """Load an OBJ file into Blender, apply transforms."""
    script = f'''
import bpy
from mathutils import Vector

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)

# Import OBJ
bpy.ops.wm.obj_import(filepath="{obj_path}")

# Apply transforms (OBJ Y-up → Blender Z-up)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

print(f"Loaded {{len([o for o in bpy.data.objects if o.type=='MESH'])}} meshes")
'''
    result = send_to_blender(script, port)
    return result


def extract_scene_data(port=9876):
    """Query Blender for complete scene data."""
    script = '''
import bpy
import json
from mathutils import Vector

scene_data = {"objects": []}

for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    if obj.type != 'MESH':
        continue

    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]

    mats = [m.name for m in obj.data.materials if m]

    # Count face types
    tris = sum(1 for p in obj.data.polygons if len(p.vertices) == 3)
    quads = sum(1 for p in obj.data.polygons if len(p.vertices) == 4)

    # Check for front-facing faces that might block openings
    front_faces = 0
    for p in obj.data.polygons:
        if p.normal.y < -0.9:
            vs = [obj.matrix_world @ obj.data.vertices[v].co for v in p.vertices]
            x_span = max(v.x for v in vs) - min(v.x for v in vs)
            z_span = max(v.z for v in vs) - min(v.z for v in vs)
            if x_span > 0.1 and z_span > 0.1:
                front_faces += 1

    obj_data = {
        "name": obj.name,
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "tris": tris,
        "quads": quads,
        "origin": [round(obj.location.x, 4), round(obj.location.y, 4), round(obj.location.z, 4)],
        "bbox_min": [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
        "bbox_max": [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)],
        "dims_mm": [
            round((max(xs) - min(xs)) * 1000, 1),
            round((max(ys) - min(ys)) * 1000, 1),
            round((max(zs) - min(zs)) * 1000, 1),
        ],
        "materials": mats,
        "front_blocking_faces": front_faces,
        "parent": obj.parent.name if obj.parent else None,
    }
    scene_data["objects"].append(obj_data)

# Overall bounding box
if scene_data["objects"]:
    all_min = [min(o["bbox_min"][i] for o in scene_data["objects"]) for i in range(3)]
    all_max = [max(o["bbox_max"][i] for o in scene_data["objects"]) for i in range(3)]
    scene_data["overall_dims_mm"] = [round((all_max[i] - all_min[i]) * 1000, 1) for i in range(3)]
else:
    scene_data["overall_dims_mm"] = [0, 0, 0]

print(json.dumps(scene_data))
'''
    result = send_to_blender(script, port)
    output = result.get("result", {}).get("result", "")
    if isinstance(output, str) and output.strip().startswith("{"):
        return json.loads(output)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# MASS ESTIMATION from geometry + material
# ═══════════════════════════════════════════════════════════════════════════════

MATERIAL_DENSITY = {
    # material name keywords → density kg/m³
    "stainless": 8000,
    "steel": 7800,
    "chrome": 7190,
    "metal": 7800,
    "wood": 600,
    "glass": 2500,
    "enamel": 2500,
    "plastic": 1200,
    "rubber": 1100,
}


def estimate_mass(dims_mm, materials):
    """Estimate mass from bounding box volume and material."""
    vol_m3 = (dims_mm[0] / 1000) * (dims_mm[1] / 1000) * (dims_mm[2] / 1000)

    # Find best density match
    density = 1000  # default: water
    for mat_name in materials:
        mat_lower = mat_name.lower()
        for keyword, d in MATERIAL_DENSITY.items():
            if keyword in mat_lower:
                density = d
                break

    # Hollow objects: reduce effective volume
    # If any dimension > 200mm, assume 20% fill factor
    max_dim = max(dims_mm)
    fill_factor = 0.2 if max_dim > 200 else 0.8

    return round(vol_m3 * density * fill_factor, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_layer1(source_file, contract=None, port=9876):
    """Run Layer 1: Mechanical Extraction.

    Args:
        source_file: path to OBJ/blend file
        contract: existing BehaviorContract to populate (or creates new)
        port: Blender MCP port

    Returns:
        BehaviorContract with Layer 1 data populated
    """
    print("\n" + "=" * 60)
    print("  LAYER 1: Mechanical Extraction")
    print("  'What CAN this object do?'")
    print("=" * 60)

    # Create contract if not provided
    if contract is None:
        obj_name = os.path.splitext(os.path.basename(source_file))[0]
        contract = BehaviorContract(
            object_name=obj_name,
            object_type="unknown",
            source_file=source_file,
        )

    # Load file in Blender
    ext = os.path.splitext(source_file)[1].lower()
    if ext == ".obj":
        print(f"  Loading OBJ: {source_file}")
        load_obj_in_blender(source_file, port)
    elif ext in (".blend",):
        print(f"  Loading blend: {source_file}")
        script = f'import bpy; bpy.ops.wm.open_mainfile(filepath="{source_file}")'
        send_to_blender(script, port)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Extract scene data
    print("  Extracting scene data...")
    scene = extract_scene_data(port)
    if not scene:
        raise RuntimeError("Failed to extract scene data from Blender")

    objects = scene.get("objects", [])
    print(f"  Found {len(objects)} mesh objects")

    # Overall dims
    contract.overall_dims_mm = tuple(scene.get("overall_dims_mm", (0, 0, 0)))

    # Find the root body (largest by vertex count)
    if objects:
        root_obj = max(objects, key=lambda o: o["vertices"])
        contract.root_part = root_obj["name"]

    # Create PartContract for each object
    for obj in objects:
        mass = estimate_mass(obj["dims_mm"], obj["materials"])

        part = PartContract(
            name=obj["name"],
            part_type="unknown",  # Layer 2 will identify this
            is_static=(obj["name"] == contract.root_part),
            vertices=obj["vertices"],
            faces=obj["faces"],
            bbox_min=tuple(obj["bbox_min"]),
            bbox_max=tuple(obj["bbox_max"]),
            dims_mm=tuple(obj["dims_mm"]),
            origin=tuple(obj["origin"]),
            materials=obj["materials"],
            mass_kg=mass,
            parent_part=contract.root_part if obj["name"] != contract.root_part else None,
        )

        # Note front-blocking faces for Layer 3
        if obj.get("front_blocking_faces", 0) > 0:
            part.blender_actions.append(
                f"INVESTIGATE: {obj['front_blocking_faces']} front-facing faces may block cavity openings"
            )

        # Note triangle faces
        if obj.get("tris", 0) > 0:
            part.blender_actions.append(
                f"REMOVE: {obj['tris']} triangle faces (cause phantom collision in PhysX)"
            )

        contract.parts.append(part)

        print(f"    {obj['name']}: {obj['vertices']}v, {obj['dims_mm']}mm, "
              f"mass≈{mass}kg, mats={obj['materials']}")

    contract.layer1_complete = True
    print(f"\n  Layer 1 complete: {len(contract.parts)} parts extracted")
    return contract


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        _ASSETS_DIR, "built_in_double_oven_final (1).obj"
    )
    contract = run_layer1(source)
    print("\n" + contract.to_json()[:2000])
