#!/usr/bin/env python3
"""V5 Layer 3: Semantic Filtering — "What SHOULD each part do?"

For each plausible behavior from Layer 2:
  - Check all 15 semantic constraint domains
  - Using the 16×15 matrix from BEHAVIOR_DEFINITIONS.md
  - Generate the Behavior Contract with exact parameters

Uses Claude API with BEHAVIOR_DEFINITIONS.md as context for reasoning.
"""

import json
import math
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.dirname(_DIR)
sys.path.insert(0, _ASSETS_DIR)

from v5.behavior_contract import (
    BehaviorContract, BehaviorSpec, ConstraintCheck, CONSTRAINT_DOMAINS,
)
from v5.ai_agents import (
    load_api_keys, call_claude, call_gemini, parse_json,
    load_behavior_definitions, run_parallel_agents,
)


# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC CONSTRAINT SPECS PER PART TYPE
# These are deterministic — no AI needed for common types
# ═══════════════════════════════════════════════════════════════════════════════

SEMANTIC_SPECS = {
    "oven_door": {
        "rotational": {
            "joint_type": "revolute",
            "joint_axis": "X",  # horizontal hinge, swings down
            "limits_deg": (0, 90),
            "pivot": "bottom_edge",
            "direction": "downward_swing",
            "damping": 10.0,
            "force_nm": 5.0,
            "collision_type": "boundingCube",
            "mass_default": 10.0,
            "constraints": {
                "directional": (True, True, "Door swings downward (outward) to open"),
                "range_limits": (True, True, "0-90° — fully open is horizontal"),
                "pivot_placement": (True, True, "Hinge at bottom edge of door"),
                "clearance": (True, True, "Door must clear chassis when opening"),
                "sequential": (False, None, "No prerequisite actions"),
                "force_torque": (True, True, "5 Nm typical for oven door"),
                "contact_friction": (True, True, "Hinge bearing maintains contact"),
                "symmetry": (True, True, "Symmetric left-right"),
                "material": (True, True, "Glass + metal frame"),
                "internal_volume": (True, True, "No front face blocking cavity — door IS the front face"),
                "kinematic_chain": (True, True, "Single revolute joint"),
                "energy": (True, True, "Gravity-assisted closing"),
                "feedback": (False, None, "No sensors needed"),
                "safety": (True, True, "Hard stop at 90°"),
                "aesthetic": (True, True, "Glass window in door frame"),
            },
        },
        "grasping": {
            "joint_type": None,
            "constraints": {
                "force_torque": (True, True, "Grip force 5-10N on handle"),
                "contact_friction": (True, True, "Handle provides grip surface"),
            },
        },
    },

    "cabinet_door": {
        "rotational": {
            "joint_type": "revolute",
            "joint_axis": "Z",  # vertical hinge, swings outward
            "limits_deg": (0, 110),
            "pivot": "hinge_edge",  # left or right edge
            "direction": "outward_swing",
            "damping": 5.0,
            "force_nm": 3.0,
            "collision_type": "boundingCube",
            "mass_default": 5.0,
            "constraints": {
                "directional": (True, True, "Door swings outward only"),
                "range_limits": (True, True, "0-110° — limited by furniture behind"),
                "pivot_placement": (True, True, "Hinge at left or right edge"),
                "clearance": (True, True, "Door clears frame and adjacent doors"),
                "internal_volume": (True, True, "Cannot swing inward — shelves inside"),
                "kinematic_chain": (True, True, "Single revolute joint"),
                "safety": (True, True, "Hard stop at 110°"),
            },
        },
    },

    "drawer": {
        "linear": {
            "joint_type": "prismatic",
            "joint_axis": "Y",  # slides front-back
            "limits_m": (-0.4, 0.0),  # slides out 400mm
            "pivot": "center",
            "direction": "forward_pull",
            "damping": 5.0,
            "force_nm": 25.0,
            "collision_type": "none",
            "mass_default": 3.0,
            "constraints": {
                "directional": (True, True, "Pulls forward only"),
                "range_limits": (True, True, "0 to 90% of depth"),
                "pivot_placement": (False, None, "N/A for linear"),
                "clearance": (True, True, "Drawer clears frame sides"),
                "internal_volume": (True, True, "Cannot push through back panel"),
                "kinematic_chain": (True, True, "Single prismatic joint"),
                "safety": (True, True, "Hard stop at max extension"),
            },
        },
    },

    "knob": {
        "rotational": {
            "joint_type": "revolute",
            "joint_axis": "Y",  # rotates around depth axis
            "limits_deg": (0, 270),
            "pivot": "center",
            "direction": "clockwise",
            "damping": 0.5,
            "force_nm": 1.0,
            "collision_type": "convexHull",
            "mass_default": 0.1,
            "constraints": {
                "directional": (True, True, "Rotates CW/CCW"),
                "range_limits": (True, True, "0-270° typical for oven knobs"),
                "pivot_placement": (True, True, "Rotates around own center"),
                "kinematic_chain": (True, True, "Single revolute joint"),
                "safety": (True, True, "Detent stops at positions"),
            },
        },
    },

    "rack": {
        "linear": {
            "joint_type": "prismatic",
            "joint_axis": "Y",
            "limits_m": (-0.4, 0.0),
            "pivot": "back_center",
            "direction": "forward_slide",
            "damping": 5.0,
            "force_nm": 10.0,
            "collision_type": "none",  # too thin for convex hull
            "mass_default": 2.0,
            "constraints": {
                "directional": (True, True, "Slides forward to pull out"),
                "range_limits": (True, True, "0 to rack length"),
                "clearance": (True, True, "Rack must clear cavity walls"),
                "kinematic_chain": (True, True, "Single prismatic joint"),
                "safety": (True, True, "Hard stop at full extension"),
            },
        },
    },

    "handle": {
        # Handles don't have their own joints — they're grasping points
    },

    "chassis": {
        # Static — no behaviors
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PIVOT POSITION CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════════

def compute_pivot(part, pivot_type):
    """Compute exact pivot position from part geometry."""
    bmin = part.bbox_min
    bmax = part.bbox_max
    cx = (bmin[0] + bmax[0]) / 2
    cy = (bmin[1] + bmax[1]) / 2
    cz = (bmin[2] + bmax[2]) / 2

    if pivot_type == "bottom_edge":
        # Oven door: hinge at bottom edge, front face
        return (cx, bmin[1], bmin[2])
    elif pivot_type == "top_edge":
        return (cx, bmin[1], bmax[2])
    elif pivot_type == "hinge_edge":
        # Cabinet door: hinge at left or right edge
        # Default: left edge
        return (bmin[0], cy, cz)
    elif pivot_type == "center":
        return (cx, cy, cz)
    elif pivot_type == "back_center":
        return (cx, bmax[1], cz)
    else:
        return (cx, cy, cz)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3: AI-ASSISTED SEMANTIC FILTERING FOR UNKNOWN TYPES
# ═══════════════════════════════════════════════════════════════════════════════

SEMANTIC_PROMPT = """You are a robotics physicist analyzing parts for semantic behavior constraints.

Here is the behavior definitions reference (16 behaviors × 15 constraint domains):
{behavior_defs}

Here are parts that need semantic analysis — their types are not in our lookup table:
{unknown_parts}

For each part, determine:
1. What is the PRIMARY behavior? (one of: rotational, linear, grasping, insertion, deformation, contact, sequential, dynamic, sliding_friction, wiping_sweeping, twisting_torque, stacking_placement, compliant_force, impact_striking, pulling_tension, rolling)
2. Joint type: "revolute", "prismatic", "fixed", or null
3. Joint axis: "X", "Y", or "Z"
4. Joint limits in degrees (for revolute) or meters (for prismatic)
5. Pivot position description: "bottom_edge", "top_edge", "hinge_edge", "center", "back_center"
6. Damping value (Nm·s/rad for revolute, N·s/m for prismatic)
7. Required force/torque (Nm)
8. Collision type: "convexHull", "boundingCube", "none"
9. For each of the 15 constraint domains: does it apply? is it satisfied?

Answer in JSON:
{{
  "parts": [
    {{
      "name": "part_name",
      "primary_behavior": "behavior_type",
      "joint_type": "revolute",
      "joint_axis": "X",
      "limits_deg": [0, 90],
      "pivot": "bottom_edge",
      "damping": 10.0,
      "force_nm": 5.0,
      "collision_type": "boundingCube",
      "constraints": {{
        "directional": {{"applies": true, "satisfied": true, "reason": "..."}},
        ...all 15 domains
      }}
    }}
  ]
}}
Return ONLY the JSON."""


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_layer3(contract: BehaviorContract):
    """Run Layer 3: Semantic Filtering → Behavior Contract.

    For each part with plausible behaviors:
      - If part type is in SEMANTIC_SPECS: use deterministic lookup
      - If unknown: use Claude API with BEHAVIOR_DEFINITIONS.md context

    Returns updated contract with complete behavior specifications.
    """
    print("\n" + "=" * 60)
    print("  LAYER 3: Semantic Filtering → Behavior Contract")
    print("  'What SHOULD each part do?'")
    print("=" * 60)

    unknown_parts = []

    for part in contract.parts:
        if part.is_static:
            # Static parts: fixed joint, no behaviors
            spec = BehaviorSpec(
                behavior_type="static",
                is_valid=True,
                joint_type="fixed",
                collision_type="boundingCube",
            )
            part.primary_behavior = spec
            part.valid_behaviors = [spec]
            print(f"    {part.name}: STATIC (fixed joint)")
            continue

        if not part.plausible_behaviors:
            print(f"    {part.name}: no plausible behaviors — skipping")
            continue

        # Check if we have deterministic specs for this part type
        type_specs = SEMANTIC_SPECS.get(part.part_type, {})

        if type_specs:
            # DETERMINISTIC PATH — no AI needed
            primary_behavior_type = part.plausible_behaviors[0]
            behavior_spec_data = type_specs.get(primary_behavior_type, {})

            if behavior_spec_data and behavior_spec_data.get("joint_type"):
                # Compute pivot
                pivot_type = behavior_spec_data.get("pivot", "center")
                pivot_pos = compute_pivot(part, pivot_type)

                # Compute localPos0 (anchor on parent)
                root = contract.get_part(contract.root_part)
                if root:
                    root_origin = root.origin
                    part.joint_local_pos0 = (
                        round(pivot_pos[0] - root_origin[0], 4),
                        round(pivot_pos[1] - root_origin[1], 4),
                        round(pivot_pos[2] - root_origin[2], 4),
                    )

                # Build BehaviorSpec
                spec = BehaviorSpec(
                    behavior_type=primary_behavior_type,
                    is_valid=True,
                    joint_type=behavior_spec_data["joint_type"],
                    joint_axis=behavior_spec_data.get("joint_axis"),
                    joint_limits_deg=behavior_spec_data.get("limits_deg"),
                    joint_limits_m=behavior_spec_data.get("limits_m"),
                    damping=behavior_spec_data.get("damping", 0),
                    force_nm=behavior_spec_data.get("force_nm", 0),
                    pivot_position=pivot_pos,
                    pivot_description=pivot_type,
                    collision_type=behavior_spec_data.get("collision_type", "none"),
                    collision_enabled_between_bodies=False,
                )

                # Add constraint checks
                for domain in CONSTRAINT_DOMAINS:
                    check_data = behavior_spec_data.get("constraints", {}).get(domain)
                    if check_data:
                        applies, satisfied, reason = check_data
                        spec.constraint_checks.append(ConstraintCheck(
                            domain=domain,
                            applies=applies if applies is not None else False,
                            satisfied=satisfied if satisfied is not None else True,
                            reason=reason or "",
                        ))

                # Mass
                part.mass_kg = max(part.mass_kg, behavior_spec_data.get("mass_default", part.mass_kg))

                # Blender actions from constraints
                for cc in spec.constraint_checks:
                    if cc.domain == "internal_volume" and cc.applies:
                        part.blender_actions.append("CHECK: remove front faces blocking cavity openings")
                    if cc.domain == "pivot_placement" and cc.applies:
                        part.blender_actions.append(f"SET_ORIGIN: {pivot_type} at ({pivot_pos[0]*1000:.0f}, {pivot_pos[1]*1000:.0f}, {pivot_pos[2]*1000:.0f})mm")

                part.primary_behavior = spec
                part.valid_behaviors = [spec]

                limits = spec.joint_limits_deg or spec.joint_limits_m
                print(f"    {part.name}: {spec.joint_type} {spec.joint_axis} "
                      f"limits={limits} pivot={pivot_type} "
                      f"({pivot_pos[0]*1000:.0f},{pivot_pos[1]*1000:.0f},{pivot_pos[2]*1000:.0f})mm "
                      f"[DETERMINISTIC]")
            else:
                unknown_parts.append(part)
        else:
            unknown_parts.append(part)

    # AI PATH — for parts not in the deterministic lookup
    if unknown_parts:
        print(f"\n  {len(unknown_parts)} unknown parts — using Claude API...")
        keys = load_api_keys()
        ckey = keys["anthropic"]["api_key"]

        behavior_defs = load_behavior_definitions()
        # Truncate to fit context if too long
        if len(behavior_defs) > 50000:
            behavior_defs = behavior_defs[:50000] + "\n... (truncated)"

        parts_data = []
        for p in unknown_parts:
            parts_data.append({
                "name": p.name,
                "part_type": p.part_type,
                "plausible_behaviors": p.plausible_behaviors,
                "dims_mm": list(p.dims_mm),
                "materials": p.materials,
                "bbox_min": list(p.bbox_min),
                "bbox_max": list(p.bbox_max),
            })

        prompt = SEMANTIC_PROMPT.format(
            behavior_defs=behavior_defs[:30000],
            unknown_parts=json.dumps(parts_data, indent=2),
        )

        try:
            result = parse_json(call_claude(ckey, prompt))
            ai_parts = {p["name"]: p for p in result.get("parts", [])}

            for part in unknown_parts:
                ai = ai_parts.get(part.name, {})
                if ai:
                    pivot_pos = compute_pivot(part, ai.get("pivot", "center"))

                    spec = BehaviorSpec(
                        behavior_type=ai.get("primary_behavior", "unknown"),
                        is_valid=True,
                        joint_type=ai.get("joint_type"),
                        joint_axis=ai.get("joint_axis"),
                        damping=ai.get("damping", 0),
                        force_nm=ai.get("force_nm", 0),
                        pivot_position=pivot_pos,
                        pivot_description=ai.get("pivot", "center"),
                        collision_type=ai.get("collision_type", "none"),
                    )
                    if ai.get("limits_deg"):
                        spec.joint_limits_deg = tuple(ai["limits_deg"])
                    if ai.get("limits_m"):
                        spec.joint_limits_m = tuple(ai["limits_m"])

                    # Constraint checks from AI
                    for domain, check in ai.get("constraints", {}).items():
                        if isinstance(check, dict):
                            spec.constraint_checks.append(ConstraintCheck(
                                domain=domain,
                                applies=check.get("applies", False),
                                satisfied=check.get("satisfied", True),
                                reason=check.get("reason", ""),
                            ))

                    part.primary_behavior = spec
                    part.valid_behaviors = [spec]
                    print(f"    {part.name}: {spec.joint_type} {spec.joint_axis} [AI]")
        except Exception as e:
            print(f"  Claude API failed: {e}")

    contract.layer3_complete = True
    print(f"\n  Layer 3 complete: Behavior Contract generated")
    print(f"  {sum(1 for p in contract.parts if p.primary_behavior)} parts have behavior specs")
    return contract


if __name__ == "__main__":
    contract_path = sys.argv[1] if len(sys.argv) > 1 else None
    if contract_path:
        with open(contract_path) as f:
            contract = BehaviorContract.from_json(f.read())
        contract = run_layer3(contract)
        print("\n" + contract.to_json()[:5000])
