---
name: Never use V1 code in V3
description: V3 must be built from scratch — never import/call V1 pipeline code (component_layout.py, geometry_compiler.py, etc.)
type: feedback
---

NEVER use V1 code inside V3. Build V3 stages from scratch.

**Why:** User designed V3 as a completely new pipeline. I imported V1's `component_layout.py` and `kinematic_builders.py` into V3 Stage 5 instead of building native V3 geometry generation. This caused every collision problem, door ordering issue, and required dozens of hacks to fix V1 behavior. Hours wasted patching V1 code when the right answer was to not use it at all.

**How to apply:** When building any V3 stage, write new code that uses V3's data (SAM masks, Depth Pro measurements, behavioral contract). Never `from component_layout import` or `from geometry_compiler import`. If V1 has useful LOGIC (not code), understand the logic and reimplement it in V3's context.
