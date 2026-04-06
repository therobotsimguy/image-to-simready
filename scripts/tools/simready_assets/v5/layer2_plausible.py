#!/usr/bin/env python3
"""V5 Layer 2: Plausible Behaviors — "What COULD each part do?"

For each part from Layer 1:
  - AI identifies the part type (door, knob, rack, chassis)
  - Matrix lookup: which of 16 behaviors are plausible?
  - Compute full mechanical range (unconstrained)

Uses Claude + Gemini in parallel for part identification.
"""

import json
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.dirname(_DIR)
sys.path.insert(0, _ASSETS_DIR)

from v5.behavior_contract import BehaviorContract, BEHAVIORS
from v5.ai_agents import (
    load_api_keys, call_claude, call_gemini, parse_json,
    load_behavior_definitions, run_parallel_agents,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PART TYPE → PLAUSIBLE BEHAVIORS (from BEHAVIOR_DEFINITIONS.md matrix)
# ═══════════════════════════════════════════════════════════════════════════════

# This is the 16×N lookup table derived from the behavior matrix
# For each part type, which behaviors are mechanically plausible?
PART_BEHAVIOR_MATRIX = {
    "oven_door": ["rotational", "grasping", "sequential"],
    "cabinet_door": ["rotational", "grasping", "sequential"],
    "drawer": ["linear", "grasping", "sequential", "pulling_tension"],
    "knob": ["rotational", "twisting_torque", "grasping"],
    "dial": ["rotational", "twisting_torque", "grasping", "contact"],
    "rack": ["linear", "pulling_tension", "grasping"],
    "shelf": ["linear", "pulling_tension"],
    "button": ["linear", "contact"],
    "switch": ["rotational", "contact"],
    "lid": ["rotational", "grasping", "sequential"],
    "handle": ["grasping", "pulling_tension"],
    "lever": ["rotational", "grasping"],
    "slider": ["linear", "grasping"],
    "valve": ["rotational", "twisting_torque"],
    "bolt": ["rotational", "insertion", "twisting_torque", "sequential"],
    "peg": ["insertion", "linear", "grasping"],
    "chassis": [],  # static — no behaviors
    "frame": [],    # static
    "body": [],     # static
    "panel": [],    # static
}


IDENTIFY_PROMPT = """You are analyzing 3D object parts for robotics simulation.

Here are the parts from a 3D model, with their names, dimensions, materials, and vertex counts:

{parts_data}

For EACH part, identify:
1. "part_type": what kind of part is it? Use one of these types:
   oven_door, cabinet_door, drawer, knob, dial, rack, shelf, button, switch,
   lid, handle, lever, slider, valve, bolt, peg, chassis, frame, body, panel
2. "is_static": does this part move? (true = fixed, false = moves)
3. "object_category": what is the overall object? (appliance, furniture, tool, etc.)

Rules:
- Names containing "door" → oven_door or cabinet_door
- Names containing "knob" → knob
- Names containing "rack" → rack
- Names containing "chassis", "body", "frame", "carcass" → chassis (static)
- The LARGEST part by vertex count is usually the chassis/body (static)
- Parts with "handle", "pull" → handle
- Parts with "drawer" → drawer

Answer in JSON format:
{{
  "object_category": "appliance or furniture or tool",
  "parts": [
    {{"name": "part_name", "part_type": "type", "is_static": true/false}}
  ]
}}
Return ONLY the JSON."""


def run_layer2(contract: BehaviorContract):
    """Run Layer 2: Plausible Behavior Enumeration.

    Args:
        contract: BehaviorContract from Layer 1

    Returns:
        Updated BehaviorContract with plausible behaviors per part
    """
    print("\n" + "=" * 60)
    print("  LAYER 2: Plausible Behaviors")
    print("  'What COULD each part do?'")
    print("=" * 60)

    keys = load_api_keys()
    ckey = keys["anthropic"]["api_key"]
    gkey = keys["gemini"]["api_key"]

    # Build parts data for AI
    parts_data = []
    for p in contract.parts:
        parts_data.append({
            "name": p.name,
            "vertices": p.vertices,
            "dims_mm": list(p.dims_mm),
            "materials": p.materials,
            "mass_kg": p.mass_kg,
        })

    prompt = IDENTIFY_PROMPT.format(parts_data=json.dumps(parts_data, indent=2))

    # Run Claude + Gemini in parallel for part identification
    print("  Identifying part types (Claude ‖ Gemini)...")
    results, errors = run_parallel_agents([
        ("claude", lambda: parse_json(call_claude(ckey, prompt))),
        ("gemini", lambda: parse_json(call_gemini(gkey, prompt))),
    ])

    # Prefer Claude, fallback to Gemini
    identification = results.get("claude") or results.get("gemini")
    if not identification:
        print("  Both AI agents failed for part identification")
        print("  Falling back to name-based heuristics")
        identification = {"parts": [], "object_category": "unknown"}

    # Update contract with object category
    contract.object_type = identification.get("object_category", "unknown")

    # Map AI identification to parts
    ai_parts = {p["name"]: p for p in identification.get("parts", [])}

    for part in contract.parts:
        ai = ai_parts.get(part.name, {})

        # Part type: AI identification or name-based fallback
        if ai.get("part_type"):
            part.part_type = ai["part_type"]
        else:
            # Fallback: guess from name
            name_lower = part.name.lower()
            if "door" in name_lower:
                part.part_type = "oven_door"
            elif "knob" in name_lower:
                part.part_type = "knob"
            elif "rack" in name_lower:
                part.part_type = "rack"
            elif "drawer" in name_lower:
                part.part_type = "drawer"
            elif any(k in name_lower for k in ["chassis", "body", "frame", "carcass"]):
                part.part_type = "chassis"
            elif "handle" in name_lower:
                part.part_type = "handle"
            elif "button" in name_lower:
                part.part_type = "button"
            else:
                part.part_type = "unknown"

        # Static flag
        if ai.get("is_static") is not None:
            part.is_static = ai["is_static"]
        else:
            part.is_static = part.part_type in ("chassis", "frame", "body", "panel")

        # Look up plausible behaviors from matrix
        part.plausible_behaviors = PART_BEHAVIOR_MATRIX.get(part.part_type, [])

        status = "STATIC" if part.is_static else f"{len(part.plausible_behaviors)} behaviors"
        print(f"    {part.name}: type={part.part_type}, {status}")
        if part.plausible_behaviors:
            print(f"      plausible: {part.plausible_behaviors}")

    contract.layer2_complete = True
    print(f"\n  Layer 2 complete: {sum(1 for p in contract.parts if not p.is_static)} moving parts identified")
    return contract


if __name__ == "__main__":
    # Test with a contract from Layer 1
    contract_path = sys.argv[1] if len(sys.argv) > 1 else None
    if contract_path:
        with open(contract_path) as f:
            contract = BehaviorContract.from_json(f.read())
        contract = run_layer2(contract)
        print("\n" + contract.to_json()[:3000])
