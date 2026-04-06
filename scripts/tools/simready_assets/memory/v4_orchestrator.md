---
name: V4 Orchestrator
description: General-purpose multi-agent 3D asset generator — full architecture, data flow, retry logic
type: project
---

## V4 Orchestrator: scripts/tools/simready_assets/generate_asset.py

General-purpose pipeline. Works for ANY object (bolts, cabinets, glasses, ovens, etc.)

## Full Architecture

```
Image (any object)
  ↓
Phase 1 (parallel, ~50s): Path A ‖ Path B
  Path A: 6 AI agents
    - gemini_type: object type, category, geometry approach, components
    - gemini_dims: dimensions per component in mm
    - gemini_materials: materials with RGB, metallic, roughness
    - claude_behavior: behaviors (linear/rotational/none), structural notes
    - claude_bodies: body list (separate vs joined), origin hints
    - claude_geometry: exact Blender modeling approach
  Path B: 4 vision models (vision_stack.py)
    - Grounding DINO: component detection + counts
    - SAM3: segmentation masks → pixel color sampling per component
    - DepthPro: metric depth → real-world dimensions
    - DepthAnything3: relative depth cross-validation
  ↓
Math Engine: geometry_math.py
  - Computes EXACT xyz positions for every panel, door, drawer, knob, handle
  - Uses CabinetGrid for furniture, RevolutionProfile for bolts
  - Deterministic — same inputs always produce same coordinates
  ↓
derive_constraints(): behavior → geometric DO/DON'T rules
  - Linear motion (drawers): no blocking geometry, 5-sided box, clearance
  - Rotational motion (doors): no swing arc blocking, hinge pivot, divider stiles
  - Auto-generated per object — no hardcoding
  ↓
Phase 2 (race, ~100s): Path C → Blender → Path D (loop)
  C: Claude + Gemini both write full Blender scripts (parallel race)
     - Receives pre-computed coordinates (MUST use, not guess)
     - Receives behavioral constraints
     - Receives vision data (colors, ratios, spatial layout)
     - Claude preferred (better quality), Gemini as fallback
  ↓
  Blender execution via MCP (localhost:9876)
  ↓
  D: Structural judge (math-only, instant, no AI)
     - Queries Blender scene graph: objects, vertices, bounding boxes, origins
     - Validates against pre-computed coordinates
     - Checks: object existence, size consistency, position accuracy,
       door pivots, drawer depth, material assignment, Z ordering
     - If FAIL → specific feedback ("Door_Left X off by 340mm")
  ↓
  PASS → done
  FAIL → feedback feeds back to C as additional constraints
         C retries with: same A+B data + same coordinates + D's feedback
         Max 3 attempts: Claude → Gemini → Claude retry with fixes
```

## What C Receives (always)

**Attempt 1:**
- spec_summary (all A+B agent outputs as JSON)
- pre-computed coordinates (exact xyz from math engine)
- behavioral constraints (DO/DON'T rules from behavior analysis)
- Blender API rules (4.3 compatibility)

**Attempt N (after D fails):**
- Everything from attempt 1 (unchanged)
- ALL D feedback from ALL previous attempts (stacked)
- D feedback is specific: "Door_Left width=571mm, expected=380mm"

Pre-computed coordinates and constraints never change. D's feedback stacks.

## Key Files
- `generate_asset.py` — main pipeline (A+B → Math → C → D loop)
- `vision_stack.py` — Path B (4 vision models parallel + reconciliation)
- `judge.py` — Path D (structural audit, Blender scene inspection)
- `spec_math.py` — math validation helpers
- `geometry_math.py` — CabinetGrid, RevolutionProfile, thread geometry

## Key Design Decisions
- C MUST use pre-computed coordinates — prevents inconsistent geometry
- D is pure math, no AI — instant, deterministic, no API costs
- Behavioral constraints are generic — auto-generated for any object type
- Race approach: both AIs write scripts, test in order, first to pass D wins
- Vision stack provides ground truth: pixel colors, component counts, ratios
