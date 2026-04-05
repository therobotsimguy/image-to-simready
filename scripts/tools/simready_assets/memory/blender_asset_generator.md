---
name: Blender Asset Generator
description: General-purpose multi-agent 3D asset generator — architecture, constraints system, vision stack, lessons learned
type: project
---

## Pipeline: scripts/tools/simready_assets/generate_asset.py

General-purpose multi-agent asset generator. Works for ANY object (bolts, cabinets, glasses, ovens, etc.)

## Architecture (as of April 5, 2026)

```
Phase 1 (parallel, ~45s): Path A ‖ Path B
  Path A: 6 AI agents (3 Gemini + 3 Claude)
    - gemini_type: object type, category, geometry approach, components
    - gemini_dims: dimensions in mm per component
    - gemini_materials: materials with RGB, metallic, roughness
    - claude_behavior: behaviors (linear/rotational), structural notes
    - claude_bodies: body list (separate vs joined), origin hints
    - claude_geometry: exact geometry approach, Blender operations
  Path B: 4 vision models (vision_stack.py)
    - Grounding DINO: component detection + counts
    - SAM3: segmentation masks → pixel color sampling
    - DepthPro: metric depth → real-world dimensions
    - DepthAnything3: relative depth cross-validation
    
Phase 2 (~90s): Path C
  - derive_constraints(): behavior → geometric DO/DON'T rules
  - Claude writes complete Blender script using all A+B data + constraints
  - No hardcoded templates — script generated for each object type

Phase 3: Execute in Blender via MCP (localhost:9876)
```

## Behavioral Constraints System (derive_constraints)

Converts behavior analysis into mandatory geometric rules:
- **Linear motion (drawers)**: no geometry blocking slide path, 5-sided open-top box geometry, clearance gaps
- **Rotational motion (doors)**: no geometry in swing arc, pivot at hinge edge, stile dividers between adjacent doors
- **Separation rules**: moving parts = separate objects, fixed parts = joined frame
- **Visual rules**: drawer/door fronts must be outermost geometry

## Key Files
- `generate_asset.py` — main pipeline
- `vision_stack.py` — Path B (4 vision models parallel + reconciliation)
- `spec_math.py` — math validation for all paths
- `geometry_math.py` — CabinetGrid, RevolutionProfile (available but not hardcoded)

## Lessons Learned
- AI-generated Blender scripts need explicit constraints or they produce bad geometry
- Token limit must be 16384+ for Claude script generation (complex objects = 600+ line scripts)
- Door origins must use set_origin_keep_visual() pattern — just telling AI "set origin" causes geometry explosion
- Behavioral constraints are the key to quality — they bridge the gap between "what moves" and "how to build it"
- Vision stack color sampling gives more accurate colors than AI guessing
- DepthPro sometimes deadlocks with timm.layers — intermittent, not blocking
