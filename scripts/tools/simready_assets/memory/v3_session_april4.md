---
name: V3 Session April 3-4 Complete Status
description: Full state of V3 pipeline after marathon session — what works, what's broken, remaining issues
type: project
---

## V3 Pipeline Status as of April 4, 2026

### What's Working
- All 12 stages run end-to-end, 100% V3 code (zero V1 imports)
- V1 code archived at `/home/msi/IsaacLab/v1_archive.zip`
- 4-pass sequential perception: Gemini→SAM3→DepthPro→DA3
- SAM bbox Y-positions passed through to components for spatial ordering
- Stage 5 generates flat hierarchy (unparents in Blender before export)
- Stage 6 applies physics via pxr API directly (no make_asset.py)
- NVIDIA SimReady Foundation validator passes
- Telemetry recording in teleop script (press L)

### What's BROKEN (must fix next session)
1. **Upper door missing** — only lower door visible. Upper door exists in USD with correct Z position but doesn't render/show in Isaac Sim
2. **Knobs underneath oven** — knobs have correct world Z (0.728-0.767) in USD but appear below the oven in Isaac Sim
3. **Only 1 handle visible** — both handles exist in USD but only lower door handle shows

### Root Cause Analysis
The world positions in the USD are CORRECT:
- Lower door: world z=0.055-0.442 (bottom, bigger) ✓
- Upper door: world z=0.458-0.705 (top, smaller) ✓
- Knobs: world z=0.728-0.767 ✓
- Body: z=0-0.800 ✓

But Isaac Sim shows them in wrong positions. Possible causes:
- The Blender unparent step preserves `matrix_world` but the USD exporter might not bake it correctly
- The door/knob Xform translate might be interpreted differently when they're root-level vs nested
- Stage 6 rename might be breaking the transform chain

### Key Files
- Pipeline: `scripts/tools/v3/orchestrator_v3.py`
- Stages: `scripts/tools/v3/stages/stage*.py`
- Blender tool: `scripts/tools/kinematic_builders.py`
- Asset viewer: `scripts/tools/v3/view_asset.py`
- Teleop: `scripts/environments/teleoperation/teleop_se3_agent_cinematic.py`
- Models: `scripts/tools/v3/models/` (SAM3, DepthPro, DA3, SimReady Foundation)
- Config: `scripts/tools/v3/BEHAVIOR_SEMANTIC_CONSTRAINT_MAPPING.json`
- API keys: `scripts/tools/api_keys.json`

### Blender MCP
- Runs on localhost:9876
- Must be started before running pipeline
- kinematic_builders.py executes inside Blender

### HuggingFace
- Token: logged in via `huggingface-cli login`
- SAM 3: `facebook/sam3` (gated, access approved)
- DepthAnything 3: `depth-anything/DA3-LARGE`

### Critical Lessons Learned
1. **Triangle faces bug**: restructure.py adds triangle faces that cause phantom collision. Fix: `_remove_triangle_faces()` keeps only quads
2. **CollisionAPI deletion**: Must use `Sdf.TokenListOp` Deleted Items, not just `RemoveAPI`. PhysX re-adds CollisionAPI at spawn time
3. **Body collision for hollow objects**: Separate convexHull collision boxes per panel, not one merged mesh
4. **Gemini friction values**: Must include material friction table in prompt (metal=0.15, not 0.5)
5. **SAM bbox for spatial ordering**: Use sam_center_y (higher Y = lower Z in 3D) to order doors
6. **Flat hierarchy for PhysX**: Links must be siblings under root, not nested under body
7. **No V1 in V3**: NEVER import V1 code. Build from scratch using V3 data
8. **Flag errors immediately**: Don't silently continue when AI models fail

### Next Steps
1. Fix door/knob positioning issue (doors inside body, knobs underneath)
2. Investigate Blender unparent + USD export transform chain
3. Consider baking world transforms into mesh vertices before export instead of relying on Xform
4. Test on different object types (cabinet, fridge, microwave)
5. Build telemetry into the pipeline properly
