#!/usr/bin/env python3
"""V5 Orchestrator — Semantic Behavior Pipeline.

Input: Image OR OBJ/Blend file
Output: SimReady USD with Behavior Contract

Pipeline:
  Layer 1: Mechanical Extraction (from Blender scene)
  Layer 2: Plausible Behaviors (16 behaviors × matrix lookup + AI)
  Layer 3: Semantic Filtering → Behavior Contract (15 domains)
  Blender Prep: Fix geometry per contract
  PhysX: Add joints/collision/mass per contract
  Judge D: Validate per contract at each stage

Usage:
    python orchestrator_v5.py --input oven.obj
    python orchestrator_v5.py --input cabinet.blend --output output.usd
"""

import argparse
import json
import os
import sys
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.dirname(_DIR)
sys.path.insert(0, _ASSETS_DIR)

from v5.behavior_contract import BehaviorContract
from v5.layer1_mechanical import run_layer1, send_to_blender
from v5.layer2_plausible import run_layer2
from v5.layer3_semantic import run_layer3


# ═══════════════════════════════════════════════════════════════════════════════
# BLENDER PREP — reads contract, fixes geometry
# ═══════════════════════════════════════════════════════════════════════════════

def run_blender_prep(contract: BehaviorContract, port=9876):
    """Fix Blender GEOMETRY ONLY per Behavior Contract.

    Blender prep owns: geometry (faces, materials, normals)
    Blender prep does NOT own: positioning (origins, locations)

    PhysX stage is the ONLY authority on articulated body positions.
    All parts stay at origin (0,0,0) in Blender. PhysX uses localPos0.
    """
    print("\n" + "=" * 60)
    print("  BLENDER PREP: Fix geometry only (no positioning)")
    print("=" * 60)

    # DO NOT set origins or locations — PhysX handles positioning via localPos0
    # All parts stay at Blender origin (0,0,0)

    # Remove cavity-blocking front faces (from contract blender_actions)
    for part in contract.parts:
        if part.is_static:
            for action in part.blender_actions:
                if "front" in action.lower() and ("blocking" in action.lower() or "cavity" in action.lower()):
                    print(f"    Checking {part.name} for cavity-blocking faces...")
                    script = (
                        f'import bpy, bmesh\n'
                        f'from mathutils import Vector\n'
                        f'obj = bpy.data.objects["{part.name}"]\n'
                        f'bm = bmesh.new()\n'
                        f'bm.from_mesh(obj.data)\n'
                        f'bm.faces.ensure_lookup_table()\n'
                        f'rm = []\n'
                        f'for f in bm.faces:\n'
                        f'    if f.normal.y > -0.5: continue\n'
                        f'    vs = [obj.matrix_world @ v.co for v in f.verts]\n'
                        f'    if max(v.y for v in vs) < 0.01 and (max(v.z for v in vs)-min(v.z for v in vs)) > 0.3 and (max(v.x for v in vs)-min(v.x for v in vs)) > 0.3:\n'
                        f'        rm.append(f)\n'
                        f'for f in rm: bm.faces.remove(f)\n'
                        f'bm.to_mesh(obj.data)\n'
                        f'bm.free()\n'
                        f'obj.data.update()\n'
                        f'print(f"Removed {{len(rm)}} cavity-blocking faces from {part.name}")\n'
                    )
                    result = send_to_blender(script, port)
                    out = result.get("result", {}).get("result", "")
                    if out:
                        print(f"    {out.strip()}")

    # 3. Fix materials
    print("    Fixing materials...")
    script = '''
import bpy
for mat in bpy.data.materials:
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    name = mat.name.lower()
    if "chrome" in name:
        bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.82, 1)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.1
    elif "stainless" in name:
        bsdf.inputs["Base Color"].default_value = (0.7, 0.7, 0.72, 1)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.25
    elif "enamel" in name:
        bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1)
        bsdf.inputs["Roughness"].default_value = 0.4
    elif "white" in name or "logo" in name:
        bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
        bsdf.inputs["Roughness"].default_value = 0.3
    else:
        bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
        bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["Alpha"].default_value = 1.0
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
print("Materials fixed")
'''
    send_to_blender(script, port)

    contract.blender_complete = True
    print("  Blender prep complete")
    return contract


# ═══════════════════════════════════════════════════════════════════════════════
# USD EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

def export_usd(output_usd, output_blend=None, port=9876):
    """Export from Blender to USD."""
    script = f'import bpy\nbpy.ops.wm.usd_export(filepath="{output_usd}", export_materials=True)\nprint("Exported USD")'
    send_to_blender(script, port)
    if output_blend:
        script = f'import bpy\nbpy.ops.wm.save_as_mainfile(filepath="{output_blend}")\nprint("Saved blend")'
        send_to_blender(script, port)
    print(f"  Exported: {output_usd}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHYSX STAGE — reads contract, adds physics
# ═══════════════════════════════════════════════════════════════════════════════

def run_physx(contract: BehaviorContract, usd_path: str):
    """Add PhysX properties to USD, reading from Behavior Contract.

    PhysX is the SOLE AUTHORITY on articulated body positioning.
    - localPos0 = pivot world position (from contract)
    - xformOp:translate = zeroed (PhysX overrides it anyway)
    - body0/body1 = parent-child hierarchy (from contract)
    """
    print("\n" + "=" * 60)
    print("  PHYSX: Add physics per Behavior Contract (sole positioning authority)")
    print("=" * 60)

    from pxr import Usd, UsdPhysics, Sdf, Gf

    stage = Usd.Stage.Open(usd_path)
    root = stage.GetPrimAtPath("/root")
    UsdPhysics.ArticulationRootAPI.Apply(root)

    for part in contract.parts:
        behavior = part.primary_behavior
        if not behavior:
            continue

        xform_path = f"/root/{part.name}"
        mesh_path = f"/root/{part.name}/{part.name}"
        xform = stage.GetPrimAtPath(xform_path)
        mesh = stage.GetPrimAtPath(mesh_path)

        if not xform.IsValid():
            print(f"    SKIP {part.name}: not found in USD")
            continue

        # Rigid body + mass
        UsdPhysics.RigidBodyAPI.Apply(xform)
        UsdPhysics.MassAPI.Apply(xform).CreateMassAttr(part.mass_kg)

        # Collision
        if mesh.IsValid() and behavior.collision_type != "none":
            UsdPhysics.CollisionAPI.Apply(mesh)
            UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr(behavior.collision_type)

        # Joint
        if behavior.joint_type == "fixed":
            j = UsdPhysics.FixedJoint.Define(stage, f"{xform_path}/fixed_joint")
            j.CreateBody1Rel().SetTargets([xform_path])
            print(f"    {part.name}: fixed, mass={part.mass_kg}kg, collision={behavior.collision_type}")

        elif behavior.joint_type == "revolute":
            j = UsdPhysics.RevoluteJoint.Define(stage, f"{xform_path}/revolute_joint")
            j.CreateBody0Rel().SetTargets([f"/root/{contract.root_part}"])
            j.CreateBody1Rel().SetTargets([xform_path])
            j.CreateAxisAttr(behavior.joint_axis)

            if behavior.joint_limits_deg:
                j.CreateLowerLimitAttr(behavior.joint_limits_deg[0])
                j.CreateUpperLimitAttr(behavior.joint_limits_deg[1])

            # Local positions from contract
            if part.joint_local_pos0:
                j.CreateLocalPos0Attr(Gf.Vec3f(*part.joint_local_pos0))
            j.CreateLocalPos1Attr(Gf.Vec3f(*part.joint_local_pos1))

            # Disable collision between connected bodies
            j.CreateCollisionEnabledAttr(not behavior.collision_enabled_between_bodies)

            # Drive
            drive = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
            drive.CreateDampingAttr(behavior.damping)
            drive.CreateStiffnessAttr(behavior.stiffness)

            limits = behavior.joint_limits_deg
            lp0 = part.joint_local_pos0 or (0, 0, 0)
            print(f"    {part.name}: revolute {behavior.joint_axis} [{limits[0]}-{limits[1]}°] "
                  f"localPos0=({lp0[0]*1000:.0f},{lp0[1]*1000:.0f},{lp0[2]*1000:.0f})mm "
                  f"damping={behavior.damping}")

        elif behavior.joint_type == "prismatic":
            j = UsdPhysics.PrismaticJoint.Define(stage, f"{xform_path}/prismatic_joint")
            j.CreateBody0Rel().SetTargets([f"/root/{contract.root_part}"])
            j.CreateBody1Rel().SetTargets([xform_path])
            j.CreateAxisAttr(behavior.joint_axis)

            if behavior.joint_limits_m:
                j.CreateLowerLimitAttr(behavior.joint_limits_m[0] * 100)  # m to cm
                j.CreateUpperLimitAttr(behavior.joint_limits_m[1] * 100)

            if part.joint_local_pos0:
                j.CreateLocalPos0Attr(Gf.Vec3f(*part.joint_local_pos0))
            j.CreateLocalPos1Attr(Gf.Vec3f(*part.joint_local_pos1))

            j.CreateCollisionEnabledAttr(False)

            drive = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "linear")
            drive.CreateDampingAttr(behavior.damping)

            limits = behavior.joint_limits_m
            print(f"    {part.name}: prismatic {behavior.joint_axis} [{limits[0]*1000:.0f}-{limits[1]*1000:.0f}mm]")

    # Zero out xform translates on articulated children
    # PhysX articulation uses localPos0 for positioning, NOT xform translate
    # Having both causes double-offset
    from pxr import UsdGeom
    for part in contract.parts:
        if part.is_static:
            continue
        xform_path = f"/root/{part.name}"
        prim = stage.GetPrimAtPath(xform_path)
        attr = prim.GetAttribute("xformOp:translate")
        if attr and attr.Get():
            attr.Set(Gf.Vec3d(0, 0, 0))

    # Physics scene
    UsdPhysics.Scene.Define(stage, "/physicsScene").CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))

    stage.GetRootLayer().Save()
    contract.physx_complete = True
    print(f"  PhysX complete: {usd_path}")
    return contract


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="V5 Semantic Behavior Pipeline")
    parser.add_argument("--input", required=True, help="OBJ or blend file")
    parser.add_argument("--output", default=None, help="Output USD path")
    parser.add_argument("--port", type=int, default=9876, help="Blender MCP port")
    parser.add_argument("--contract-only", action="store_true", help="Generate contract only, skip Blender/PhysX")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    obj_name = os.path.splitext(os.path.basename(input_path))[0].replace(" ", "_")
    output_dir = os.path.join(_ASSETS_DIR, obj_name)
    os.makedirs(output_dir, exist_ok=True)
    output_usd = args.output or os.path.join(output_dir, f"{obj_name}_simready.usd")
    output_blend = os.path.join(output_dir, f"{obj_name}.blend")

    print()
    print("=" * 60)
    print("  V5 SEMANTIC BEHAVIOR PIPELINE")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_usd}")
    print("=" * 60)

    t0 = time.time()

    # Layer 1: Mechanical Extraction
    contract = run_layer1(input_path, port=args.port)

    # Layer 2: Plausible Behaviors
    contract = run_layer2(contract)

    # Layer 3: Semantic Filtering → Behavior Contract
    contract = run_layer3(contract)

    # Save contract
    contract_path = os.path.join(output_dir, "behavior_contract.json")
    with open(contract_path, "w") as f:
        f.write(contract.to_json())
    print(f"\n  Contract saved: {contract_path}")

    if args.contract_only:
        print(f"\n  Total: {time.time() - t0:.1f}s (contract only)")
        return

    # Blender Prep
    contract = run_blender_prep(contract, port=args.port)

    # Export USD
    export_usd(output_usd, output_blend, port=args.port)

    # PhysX
    contract = run_physx(contract, output_usd)

    # Save final contract
    with open(contract_path, "w") as f:
        f.write(contract.to_json())

    print(f"\n  {'=' * 60}")
    print(f"  V5 COMPLETE")
    print(f"  SimReady USD: {output_usd}")
    print(f"  Contract:     {contract_path}")
    print(f"  Parts:        {len(contract.parts)}")
    print(f"  Moving:       {sum(1 for p in contract.parts if not p.is_static)}")
    print(f"  Total:        {time.time() - t0:.1f}s")
    print(f"  {'=' * 60}")


if __name__ == "__main__":
    main()
