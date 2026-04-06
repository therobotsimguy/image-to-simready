---
name: Blender Asset Generator
description: General-purpose multi-agent 3D asset generator — architecture, constraints, vision stack, data flywheel
type: project
---

## Pipeline: scripts/tools/simready_assets/generate_asset.py

General-purpose multi-agent asset generator. Works for ANY object.

## Architecture (as of April 5, 2026)

```
Phase 1 (parallel, ~50s): Path A ‖ Path B
  Path A: 6 AI agents (3 Gemini + 3 Claude) → semantics
  Path B: 4 vision models (DINO+SAM3+DepthPro+DA3) → measurements

Math Engine: geometry_math.py computes exact coordinates from A+B

Phase 2 (race, ~90-180s): Path C → Blender → Path D (loop)
  C: Claude+Gemini both write full Blender scripts (parallel race)
     - Receives pre-computed coordinates (MUST use, not guess)
     - Receives behavioral constraints (DO/DON'T rules)
  D: Structural judge (math-only, instant)
     - Validates scene against pre-computed coordinates
     - Checks: object existence, sizes, positions, consistency, bounds
     - If FAIL → feedback goes back to C as additional constraints
     - Max 3 attempts: Claude → Gemini → Claude retry with fixes
```

## Key Design Decisions
- C must use pre-computed coordinates, NOT invent positions (consistency)
- D is pure math, no AI — instant validation, no API costs
- Behavioral constraints auto-generated from behavior analysis (generic for any object)
- Gemini produces garbage Blender scripts — always prefer Claude
- D's feedback to C is specific and measurable ("Door_Left X off by 340mm")

## Behavioral Constraints (derive_constraints)
- Linear motion (drawers): no blocking geometry, 5-sided box, clearance
- Rotational motion (doors): no swing arc blocking, hinge pivot, divider stiles
- Drawer geometry: front+bottom+left+right+back walls, open top
- Door dividers: N doors need N-1 vertical stiles between them

## Known Issues (next session)
- D bounds check too strict — uses largest object as frame reference, fails when legs extend beyond
- D drawer depth check shows 20mm expected when row_types detection fails (Gemini returns varying structures)
- DepthAnything sometimes fails with "meta tensor" error (intermittent)
- Gemini writes ~30-line scripts that are syntactically broken

## Key Files
- `generate_asset.py` — main pipeline (A+B+C+D)
- `vision_stack.py` — Path B (4 vision models)
- `judge.py` — Path D (structural audit)
- `spec_math.py` — math validation helpers
- `geometry_math.py` — CabinetGrid, RevolutionProfile
