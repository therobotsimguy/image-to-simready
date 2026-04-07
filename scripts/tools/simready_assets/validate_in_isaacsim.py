#!/usr/bin/env python3
"""Validate a SimReady USD in Isaac Sim.

Loads the USD, runs physics, drives all articulated joints through their
full range, and reports pass/fail.

Usage:
    ./isaaclab.sh -p scripts/tools/simready_assets/validate_in_isaacsim.py \
        --usd scripts/tools/simready_assets/cabinet_2/cabinet_2_simready.usd
"""

import argparse
import os
import time

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="SimReady USD Validator")
parser.add_argument("--usd", required=True, help="Path to SimReady USD")
parser.add_argument("--steps", type=int, default=300, help="Sim steps per joint waypoint")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(vars(args))
simulation_app = app_launcher.app

# ── Imports after app launch ─────────────────────────────────────────────────
import json
import numpy as np
import omni.usd
import isaaclab.sim as sim_utils
from isaaclab.sim import SimulationContext
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg
from pxr import Usd, UsdGeom, UsdPhysics, Gf
from omni.isaac.core.articulations import ArticulationView

USD_PATH = os.path.abspath(args.usd)

print()
print("=" * 60)
print("  SIMREADY VALIDATOR")
print(f"  USD: {USD_PATH}")
print("=" * 60)

# ── Simulation setup (same pattern as view_asset.py) ─────────────────────────
sim_cfg = sim_utils.SimulationCfg(dt=0.01, device="cpu")
sim = SimulationContext(sim_cfg)

sim.set_camera_view(eye=[2.0, 2.0, 1.5], target=[0.0, 0.0, 0.4])

sim_utils.GroundPlaneCfg().func("/World/GroundPlane", sim_utils.GroundPlaneCfg())
sim_utils.DomeLightCfg(intensity=2000.0).func("/World/Light", sim_utils.DomeLightCfg(intensity=2000.0))

# Spawn asset
asset_cfg = UsdFileCfg(usd_path=USD_PATH)
asset_cfg.func("/World/Asset", asset_cfg, translation=(0.0, 0.0, 0.0))

sim.reset()

stage = omni.usd.get_context().get_stage()

# ── Find articulation root path ───────────────────────────────────────────────
art_root_path = None
for prim in stage.Traverse():
    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
        art_root_path = str(prim.GetPath())
        print(f"  Articulation root: {art_root_path}")
        break

if not art_root_path:
    print("  ERROR: No ArticulationRootAPI found in USD")
    simulation_app.close()
    raise SystemExit(1)

# ── Discover joints from USD stage ───────────────────────────────────────────
joints = {}   # joint_name → {"type", "axis", "lower", "upper", "path"}
for prim in stage.Traverse():
    tname = prim.GetTypeName()
    if tname not in ("PhysicsRevoluteJoint", "PhysicsPrismaticJoint"):
        continue
    j = {}
    j["path"] = str(prim.GetPath())
    j["type"] = "revolute" if tname == "PhysicsRevoluteJoint" else "prismatic"

    if tname == "PhysicsRevoluteJoint":
        joint = UsdPhysics.RevoluteJoint(prim)
        j["axis"] = str(joint.GetAxisAttr().Get()) if joint.GetAxisAttr() else "?"
        lo = joint.GetLowerLimitAttr().Get()
        hi = joint.GetUpperLimitAttr().Get()
        j["lower_deg"] = lo if lo is not None else 0.0
        j["upper_deg"] = hi if hi is not None else 0.0
        j["lower_rad"] = np.deg2rad(j["lower_deg"])
        j["upper_rad"] = np.deg2rad(j["upper_deg"])
    else:
        joint = UsdPhysics.PrismaticJoint(prim)
        j["axis"] = str(joint.GetAxisAttr().Get()) if joint.GetAxisAttr() else "?"
        lo = joint.GetLowerLimitAttr().Get()
        hi = joint.GetUpperLimitAttr().Get()
        # Isaac Sim stores prismatic limits in cm
        j["lower_m"] = (lo / 100.0) if lo is not None else 0.0
        j["upper_m"] = (hi / 100.0) if hi is not None else 0.0

    parent_name = prim.GetParent().GetName() if prim.GetParent() else "?"
    key = f"{parent_name}/{prim.GetName()}"
    joints[key] = j

print(f"\n  Joints found: {len(joints)}")
for name, j in joints.items():
    if j["type"] == "revolute":
        print(f"    {name}: revolute {j['axis']} [{j['lower_deg']:.1f}° → {j['upper_deg']:.1f}°]")
    else:
        print(f"    {name}: prismatic {j['axis']} [{j['lower_m']*1000:.1f}mm → {j['upper_m']*1000:.1f}mm]")

# ── ArticulationView for driving joints ──────────────────────────────────────
art_view = ArticulationView(prim_paths_expr=art_root_path, name="asset_art")
art_view.initialize()

n_dof = art_view.num_dof
dof_names = art_view.dof_names
print(f"\n  DOFs (ArticulationView): {n_dof}")
for i, name in enumerate(dof_names):
    print(f"    [{i}] {name}")

if n_dof == 0:
    print("  WARNING: No DOFs — asset may be fully static")

# ── Warm-up sim ───────────────────────────────────────────────────────────────
print("\n  Warm-up (50 steps)...")
for _ in range(50):
    sim.step()

# ── Gravity drop test ─────────────────────────────────────────────────────────
print("\n  Gravity drop test (200 steps)...")
pre = art_view.get_world_poses()[0][0].copy()
for _ in range(200):
    sim.step()
post = art_view.get_world_poses()[0][0]
drop_mm = float(np.linalg.norm(post - pre)) * 1000
gravity_ok = drop_mm < 10.0
print(f"    Drift: {drop_mm:.1f}mm [{'OK' if gravity_ok else 'FLOATING/FALLING'}]")

# ── Drive each DOF through its range ─────────────────────────────────────────
results = {}

if n_dof > 0:
    limits = art_view.get_dof_limits()   # (1, n_dof, 2)
    lower = limits[0, :, 0]
    upper = limits[0, :, 1]

    for dof_idx, dof_name in enumerate(dof_names):
        lo, hi = float(lower[dof_idx]), float(upper[dof_idx])

        # Guess unit from magnitude: >1.0 likely degrees, else radians
        # Isaac Sim ArticulationView uses radians for revolute, meters for prismatic
        is_rot = abs(hi - lo) < 10.0   # radians range < 10 → revolute
        unit = "°" if is_rot else "mm"
        scale = 57.3 if is_rot else 1000.0

        print(f"\n  Testing DOF [{dof_idx}] {dof_name} "
              f"[{lo*scale:.1f}{unit} → {hi*scale:.1f}{unit}]...")

        targets = np.zeros((1, n_dof))

        waypoints = [lo, hi, lo * 0.5]
        errors = []

        for target in waypoints:
            targets[0, dof_idx] = target
            art_view.set_joint_position_targets(targets)

            for _ in range(args.steps):
                sim.step()

            actual = float(art_view.get_joint_positions()[0, dof_idx])
            err = abs(actual - target) * scale
            errors.append(err)

            label = "OPEN" if target == hi else ("CLOSED" if target == lo else "MID")
            status = "OK" if err < 5.0 else "DRIFT"
            print(f"    {label}: target={target*scale:.1f}{unit}, "
                  f"actual={actual*scale:.1f}{unit}, err={err:.1f}{unit} [{status}]")

        # Reset
        targets[0, dof_idx] = 0.0
        art_view.set_joint_position_targets(targets)
        for _ in range(100):
            sim.step()

        max_err = max(errors)
        passed = max_err < 5.0
        results[dof_name] = {"passed": passed, "max_error": max_err, "unit": unit}

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  VALIDATION SUMMARY")
print("=" * 60)

all_passed = gravity_ok
grav_status = "PASS" if gravity_ok else "FAIL"
print(f"  {grav_status}  gravity_grounded  (drift {drop_mm:.1f}mm)")

for name, r in results.items():
    status = "PASS" if r["passed"] else "FAIL"
    print(f"  {status}  {name}  (max err {r['max_error']:.1f}{r['unit']})")
    if not r["passed"]:
        all_passed = False

print()
print(f"  RESULT: {'PASS — asset is SimReady' if all_passed else 'FAIL — fix issues above'}")
print("=" * 60)

# Save telemetry
telemetry_path = "/tmp/isaaclab_telemetry.json"
with open(telemetry_path, "w") as f:
    json.dump({
        "usd": USD_PATH,
        "joints_found": len(joints),
        "dofs": n_dof,
        "gravity_drift_mm": drop_mm,
        "gravity_ok": gravity_ok,
        "joint_results": results,
        "passed": all_passed,
    }, f, indent=2)
print(f"\n  Telemetry: {telemetry_path}")

simulation_app.close()
