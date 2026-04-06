#!/usr/bin/env python3
"""V4 Asset Viewer — Load asset in Isaac Sim with telemetry.

Writes object positions, joint states, and physics data to a JSON file
that Claude can read to understand the simulation state.

Usage:
    ./isaaclab.sh -p scripts/tools/v3/view_asset.py scripts/tools/simready_assets/double_oven_simready.usd
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="V4 Asset Viewer with telemetry")
parser.add_argument("asset", help="Path to *_simready.usd")
parser.add_argument("--pos", type=float, nargs=3, default=[0.0, 0.0, 0.0], help="Asset position")
parser.add_argument("--telemetry", default="/tmp/isaaclab_telemetry.json", help="Telemetry output file")
parser.add_argument("--telemetry-interval", type=int, default=100, help="Write telemetry every N steps")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(vars(args))
simulation_app = app_launcher.app

import json
import os
import time
import isaaclab.sim as sim_utils
from isaaclab.sim import SimulationContext

# Isaac Sim imports (after app launch)
from pxr import Usd, UsdGeom, UsdPhysics, Gf
import omni.usd

# Create simulation context — CPU for mouse interaction (shift+drag)
sim_cfg = sim_utils.SimulationCfg(dt=0.01, device="cpu")
sim = SimulationContext(sim_cfg)

# Set camera
sim.set_camera_view(eye=[2.0, 2.0, 1.5], target=[0.0, 0.0, 0.4])

# Ground plane
cfg_ground = sim_utils.GroundPlaneCfg()
cfg_ground.func("/World/GroundPlane", cfg_ground)

# Light
cfg_light = sim_utils.DomeLightCfg(intensity=2000.0)
cfg_light.func("/World/Light", cfg_light)

# Spawn the asset
asset_path = os.path.abspath(args.asset)
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg

asset_cfg = UsdFileCfg(usd_path=asset_path)
asset_cfg.func("/World/Asset", asset_cfg, translation=tuple(args.pos))

print(f"\n{'='*60}")
print(f"  V4 ASSET VIEWER + TELEMETRY")
print(f"  Asset: {os.path.basename(asset_path)}")
print(f"  Position: {args.pos}")
print(f"  Telemetry: {args.telemetry}")
print(f"  Interval: every {args.telemetry_interval} steps")
print(f"{'='*60}\n")

# Play
sim.reset()

# Get stage for telemetry
stage = omni.usd.get_context().get_stage()


def collect_telemetry(step_count):
    """Collect positions, rotations, joint states, and relative positions from simulation."""
    telemetry = {
        "timestamp": time.time(),
        "step": step_count,
        "sim_time": step_count * 0.01,
        "objects": {},
        "joints": {},
        "relative_positions": {},
    }

    asset_prim = stage.GetPrimAtPath("/World/Asset")
    if not asset_prim.IsValid():
        return telemetry

    # Collect all world transforms
    world_positions = {}

    for prim in Usd.PrimRange(asset_prim):
        path = str(prim.GetPath())
        name = prim.GetName()

        xformable = UsdGeom.Xformable(prim)
        if xformable and prim.GetTypeName() in ("Xform", "Mesh"):
            try:
                world_transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
                translation = world_transform.ExtractTranslation()
                rotation = world_transform.ExtractRotation()

                # Get bounding box
                bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default"])
                bbox = bbox_cache.ComputeWorldBound(prim)
                bbox_range = bbox.ComputeAlignedRange()
                bbox_min = bbox_range.GetMin()
                bbox_max = bbox_range.GetMax()

                pos = [round(translation[0], 4), round(translation[1], 4), round(translation[2], 4)]
                world_positions[name] = pos

                telemetry["objects"][name] = {
                    "path": path,
                    "type": prim.GetTypeName(),
                    "position": pos,
                    "rotation_deg": round(rotation.GetAngle(), 2) if rotation.GetAngle() > 0.01 else 0,
                    "rotation_axis": [round(rotation.GetAxis()[i], 3) for i in range(3)] if rotation.GetAngle() > 0.01 else [0, 0, 0],
                    "bbox_min": [round(bbox_min[0], 4), round(bbox_min[1], 4), round(bbox_min[2], 4)],
                    "bbox_max": [round(bbox_max[0], 4), round(bbox_max[1], 4), round(bbox_max[2], 4)],
                    "dims_mm": [
                        round((bbox_max[0] - bbox_min[0]) * 1000, 1),
                        round((bbox_max[1] - bbox_min[1]) * 1000, 1),
                        round((bbox_max[2] - bbox_min[2]) * 1000, 1),
                    ],
                }
            except:
                pass

        # Joint data
        if "Joint" in prim.GetTypeName():
            joint_data = {
                "path": path,
                "type": prim.GetTypeName(),
                "body0": str(prim.GetRelationship("physics:body0").GetTargets()[0]) if prim.GetRelationship("physics:body0").GetTargets() else None,
                "body1": str(prim.GetRelationship("physics:body1").GetTargets()[0]) if prim.GetRelationship("physics:body1").GetTargets() else None,
            }

            if prim.GetTypeName() == "PhysicsRevoluteJoint":
                joint = UsdPhysics.RevoluteJoint(prim)
                joint_data["axis"] = str(joint.GetAxisAttr().Get()) if joint.GetAxisAttr() else "?"
                joint_data["lower_limit"] = joint.GetLowerLimitAttr().Get() if joint.GetLowerLimitAttr() else None
                joint_data["upper_limit"] = joint.GetUpperLimitAttr().Get() if joint.GetUpperLimitAttr() else None

            elif prim.GetTypeName() == "PhysicsPrismaticJoint":
                joint = UsdPhysics.PrismaticJoint(prim)
                joint_data["axis"] = str(joint.GetAxisAttr().Get()) if joint.GetAxisAttr() else "?"
                joint_data["lower_limit"] = joint.GetLowerLimitAttr().Get() if joint.GetLowerLimitAttr() else None
                joint_data["upper_limit"] = joint.GetUpperLimitAttr().Get() if joint.GetUpperLimitAttr() else None

            # Unique key using parent name + joint name
            parent_name = prim.GetParent().GetName() if prim.GetParent() else ""
            joint_key = f"{parent_name}/{name}"
            telemetry["joints"][joint_key] = joint_data

    # Compute relative positions (every object relative to chassis)
    chassis_pos = world_positions.get("oven_chassis", world_positions.get("oven_chassis", None))
    if not chassis_pos:
        # Use the first large object as reference
        for n, p in world_positions.items():
            if "chassis" in n.lower() or "frame" in n.lower() or "body" in n.lower():
                chassis_pos = p
                break
    if not chassis_pos and world_positions:
        chassis_pos = list(world_positions.values())[0]

    if chassis_pos:
        for name, pos in world_positions.items():
            rel = [
                round((pos[0] - chassis_pos[0]) * 1000, 1),
                round((pos[1] - chassis_pos[1]) * 1000, 1),
                round((pos[2] - chassis_pos[2]) * 1000, 1),
            ]
            telemetry["relative_positions"][name] = {
                "relative_to": "oven_chassis",
                "offset_mm": rel,
            }

    return telemetry


# Initial telemetry
step_count = 0
telemetry = collect_telemetry(step_count)
telemetry["status"] = "running"
telemetry["asset"] = os.path.basename(asset_path)

with open(args.telemetry, "w") as f:
    json.dump(telemetry, f, indent=2)
print(f"Initial telemetry written to {args.telemetry}")

# Print initial object positions
print("\nSpawned objects:")
for name, data in sorted(telemetry["objects"].items()):
    if data["type"] == "Xform":
        pos = data["position"]
        print(f"  {name}: ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")

print(f"\nJoints: {len(telemetry['joints'])}")
for name, data in sorted(telemetry["joints"].items()):
    print(f"  {name}: {data['type']} axis={data.get('axis','?')} limits=[{data.get('lower_limit','?')}, {data.get('upper_limit','?')}]")

print(f"\nSimulation running... (telemetry updates every {args.telemetry_interval} steps)")

# Main loop
while simulation_app.is_running():
    sim.step()
    step_count += 1

    if step_count % args.telemetry_interval == 0:
        telemetry = collect_telemetry(step_count)
        telemetry["status"] = "running"
        telemetry["asset"] = os.path.basename(asset_path)
        with open(args.telemetry, "w") as f:
            json.dump(telemetry, f, indent=2)

# Final telemetry
telemetry = collect_telemetry(step_count)
telemetry["status"] = "stopped"
with open(args.telemetry, "w") as f:
    json.dump(telemetry, f, indent=2)

simulation_app.close()
