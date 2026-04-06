#!/usr/bin/env python3
"""V5 Layer 3: Semantic Filtering — "What SHOULD each part do?"

AI reads the knowledge base (BEHAVIOR_DEFINITIONS.md + ISAAC_SIM_PHYSICS_REFERENCE.md)
as context, then generates the Behavior Contract for ANY object — seen or unseen.

No hardcoded lookup tables. The knowledge base teaches the AI how to reason.
The AI applies that reasoning to whatever parts it sees.

Uses Claude + Gemini in parallel for speed.
"""

import json
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.dirname(_DIR)
_DOCS_DIR = os.path.join(_ASSETS_DIR, "docs")
sys.path.insert(0, _ASSETS_DIR)

from v5.behavior_contract import (
    BehaviorContract, BehaviorSpec, ConstraintCheck, CONSTRAINT_DOMAINS,
)
from v5.ai_agents import (
    load_api_keys, call_claude, call_gemini, parse_json,
    run_parallel_agents,
)
from geometry_math import (
    compute_pivot_position, compute_local_offset,
    is_point_inside_bbox, validate_joint_limits,
    validate_mass, validate_part_fits_parent,
    arm_length_from_bbox, torque_from_gravity,
    damping_for_revolute, damping_for_prismatic,
    required_force_revolute, required_force_prismatic,
    inertia_box,
)


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE LOADER
# ═══════════════════════════════════════════════════════════════════════════════

def load_knowledge_base():
    """Load reference docs as context for AI reasoning."""
    docs = {}
    for name in ["BEHAVIOR_DEFINITIONS.md", "ISAAC_SIM_PHYSICS_REFERENCE.md"]:
        path = os.path.join(_DOCS_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
            # Truncate if too long for context window
            if len(content) > 40000:
                content = content[:40000] + "\n... (truncated)"
            docs[name] = content
    return docs


    # compute_pivot_position imported from geometry_math


# ═══════════════════════════════════════════════════════════════════════════════
# AI PROMPT — generates Behavior Contract from knowledge base
# ═══════════════════════════════════════════════════════════════════════════════

CONTRACT_PROMPT = """You are a robotics simulation physicist. You must generate a Behavior Contract for 3D object parts.

## KNOWLEDGE BASE (how behaviors and constraints work):

{knowledge_base}

## OBJECT PARTS TO ANALYZE:

{parts_data}

## YOUR TASK:

For EACH non-static part, generate a complete behavior specification. Use the knowledge base to reason about:
- Which of the 16 behaviors is PRIMARY for this part?
- What joint type (revolute, prismatic, fixed, null)?
- What joint axis (X, Y, Z)?
- What joint limits (degrees for revolute, meters for prismatic)?
- Where is the pivot point? Use one of: bottom_edge, top_edge, left_edge, right_edge, hinge_edge, center, back_center, front_center, bottom_center
- What damping value?
- What force/torque required (Nm)?
- What collision type (convexHull, boundingCube, none)?
- Should collision between this part and the body be enabled? (usually false for articulated parts)
- What mass (kg)?

RULES:
- Oven doors swing DOWN → hinge at bottom_edge, revolute on X axis, 0-90°
- Cabinet doors swing OUTWARD → hinge at left_edge or right_edge, revolute on Z axis, 0-110°
- Drawers slide FORWARD → prismatic on Y axis, negative limits (e.g., -0.4 to 0.0)
- Knobs ROTATE → revolute on Y axis (facing user), 0-270°
- Racks SLIDE OUT → prismatic on Y axis, negative limits
- Chassis/body/frame → fixed joint, static, is the root

Answer in EXACTLY this JSON format:
{{
  "parts": [
    {{
      "name": "part_name",
      "primary_behavior": "rotational",
      "joint_type": "revolute",
      "joint_axis": "X",
      "joint_limits_deg": [0, 90],
      "pivot_type": "bottom_edge",
      "damping": 10.0,
      "force_nm": 5.0,
      "collision_type": "boundingCube",
      "collision_between_bodies": false,
      "mass_kg": 10.0,
      "reasoning": "brief explanation"
    }}
  ]
}}

Return ONLY the JSON. Include ALL non-static parts."""


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_layer3(contract: BehaviorContract):
    """Run Layer 3: Semantic Filtering → Behavior Contract.

    AI reads knowledge base + part data → generates specs for every part.
    No hardcoded lookup tables.
    """
    print("\n" + "=" * 60)
    print("  LAYER 3: Semantic Filtering → Behavior Contract")
    print("  'What SHOULD each part do?' (AI + knowledge base)")
    print("=" * 60)

    keys = load_api_keys()
    ckey = keys["anthropic"]["api_key"]
    gkey = keys["gemini"]["api_key"]

    # Load knowledge base
    print("  Loading knowledge base...")
    kb = load_knowledge_base()
    kb_text = ""
    for name, content in kb.items():
        kb_text += f"\n### {name}:\n{content[:20000]}\n"
    print(f"  Knowledge base: {len(kb)} docs, {len(kb_text)} chars")

    # Build parts data for AI
    parts_data = []
    for p in contract.parts:
        if p.is_static:
            continue
        parts_data.append({
            "name": p.name,
            "part_type": p.part_type,
            "plausible_behaviors": p.plausible_behaviors,
            "dims_mm": list(p.dims_mm),
            "bbox_min": list(p.bbox_min),
            "bbox_max": list(p.bbox_max),
            "materials": p.materials,
            "mass_estimate_kg": p.mass_kg,
            "parent": p.parent_part,
        })

    prompt = CONTRACT_PROMPT.format(
        knowledge_base=kb_text,
        parts_data=json.dumps(parts_data, indent=2),
    )

    # Run Claude + Gemini in parallel
    print(f"  Generating contracts (Claude ‖ Gemini)...")
    results, errors = run_parallel_agents([
        ("claude", lambda: parse_json(call_claude(ckey, prompt, max_tokens=8192))),
        ("gemini", lambda: parse_json(call_gemini(gkey, prompt))),
    ])

    # Prefer Claude, fallback to Gemini
    ai_result = results.get("claude") or results.get("gemini")
    source = "Claude" if "claude" in results else ("Gemini" if "gemini" in results else "NONE")

    if not ai_result:
        print(f"  Both AI agents failed: {errors}")
        contract.layer3_complete = False
        return contract

    print(f"  Using {source} result")

    # Map AI results to contract
    ai_parts = {p["name"]: p for p in ai_result.get("parts", [])}

    for part in contract.parts:
        if part.is_static:
            # Static: fixed joint, no behavior needed
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

        ai = ai_parts.get(part.name, {})
        if not ai:
            print(f"    {part.name}: NOT IN AI RESULT — skipping")
            continue

        # Compute pivot from AI's pivot_type using geometry_math
        pivot_type = ai.get("pivot_type", "center")
        pivot_pos = compute_pivot_position(part.bbox_min, part.bbox_max, pivot_type)

        # Build BehaviorSpec
        spec = BehaviorSpec(
            behavior_type=ai.get("primary_behavior", "unknown"),
            is_valid=True,
            joint_type=ai.get("joint_type"),
            joint_axis=ai.get("joint_axis"),
            damping=ai.get("damping", 5.0),
            stiffness=ai.get("stiffness", 0.0),
            force_nm=ai.get("force_nm", 5.0),
            pivot_position=pivot_pos,
            pivot_description=pivot_type,
            collision_type=ai.get("collision_type", "boundingCube"),
            collision_enabled_between_bodies=ai.get("collision_between_bodies", False),
        )

        if ai.get("joint_limits_deg"):
            spec.joint_limits_deg = tuple(ai["joint_limits_deg"])
        if ai.get("joint_limits_m"):
            spec.joint_limits_m = tuple(ai["joint_limits_m"])

        # Mass from AI
        if ai.get("mass_kg"):
            part.mass_kg = ai["mass_kg"]

        # Compute localPos0 (pivot relative to root) using geometry_math
        root = contract.get_part(contract.root_part)
        if root:
            part.joint_local_pos0 = compute_local_offset(pivot_pos, root.origin)

        # ── PHYSICS EQUATIONS: compute exact parameters from geometry + mass ──
        # AI decides WHAT (behavior type, pivot type, axis)
        # Equations compute HOW MUCH (damping, torque, force)
        arm = arm_length_from_bbox(part.bbox_min, part.bbox_max, pivot_type, spec.joint_axis or "Z")

        if spec.joint_type == "revolute":
            spec.force_nm = torque_from_gravity(part.mass_kg, arm)
            spec.damping = damping_for_revolute(part.mass_kg, arm)
        elif spec.joint_type == "prismatic":
            spec.force_nm = required_force_prismatic(part.mass_kg)
            spec.damping = damping_for_prismatic(part.mass_kg)

        # Blender actions
        part.blender_actions.append(
            f"SHIFT_VERTICES: pivot={pivot_type} at ({pivot_pos[0]*1000:.0f},{pivot_pos[1]*1000:.0f},{pivot_pos[2]*1000:.0f})mm"
        )

        part.primary_behavior = spec
        part.valid_behaviors = [spec]

        limits = spec.joint_limits_deg or spec.joint_limits_m or "?"
        reasoning = ai.get("reasoning", "")[:60]
        print(f"    {part.name}: {spec.joint_type} {spec.joint_axis} limits={limits} "
              f"pivot={pivot_type} ({pivot_pos[0]*1000:.0f},{pivot_pos[1]*1000:.0f},{pivot_pos[2]*1000:.0f})mm "
              f"arm={arm*1000:.0f}mm damping={spec.damping} force={spec.force_nm}Nm "
              f"— {reasoning}")

    # Check for cavity-blocking faces on static parts
    for part in contract.parts:
        if part.is_static:
            has_doors = any(
                p.primary_behavior and p.primary_behavior.behavior_type == "rotational"
                for p in contract.parts if not p.is_static
            )
            if has_doors:
                part.blender_actions.append("CHECK: remove front faces blocking cavity openings")

    # ── MATH VALIDATION — catch AI mistakes ──
    print(f"\n  Math validation:")
    root_part = contract.get_part(contract.root_part)
    issues = 0

    for part in contract.parts:
        if part.is_static or not part.primary_behavior:
            continue
        b = part.primary_behavior

        # Validate joint limits
        limits = b.joint_limits_deg or b.joint_limits_m
        if limits:
            ok, msg = validate_joint_limits(b.joint_type, limits)
            if not ok:
                print(f"    ✗ {part.name}: {msg}")
                issues += 1

        # Validate mass vs parent
        if root_part:
            ok, msg = validate_mass(part.mass_kg, root_part.mass_kg)
            if not ok:
                print(f"    ✗ {part.name}: {msg}")
                issues += 1

        # Validate part fits inside parent
        if root_part:
            ok, msg = validate_part_fits_parent(part.dims_mm, root_part.dims_mm)
            if not ok:
                print(f"    ✗ {part.name}: {msg}")
                issues += 1

        # Validate pivot inside chassis bbox
        if b.pivot_position and root_part:
            inside = is_point_inside_bbox(b.pivot_position, root_part.bbox_min, root_part.bbox_max, tolerance=0.05)
            if not inside:
                print(f"    ⚠ {part.name}: pivot ({b.pivot_position[0]*1000:.0f},{b.pivot_position[1]*1000:.0f},{b.pivot_position[2]*1000:.0f})mm outside chassis bbox")
                # Don't count as hard failure — knobs can be outside chassis

    if issues == 0:
        print(f"    All checks passed")
    else:
        print(f"    {issues} issues found")

    contract.layer3_complete = True
    n_specs = sum(1 for p in contract.parts if p.primary_behavior)
    print(f"\n  Layer 3 complete: {n_specs} behavior specs generated ({source})")
    return contract


if __name__ == "__main__":
    contract_path = sys.argv[1] if len(sys.argv) > 1 else None
    if contract_path:
        with open(contract_path) as f:
            contract = BehaviorContract.from_json(f.read())
        contract = run_layer3(contract)
        print("\n" + contract.to_json()[:5000])
