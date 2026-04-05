---
name: Pipeline & Lessons
description: All pipeline knowledge, lessons, and collision fixes are in scripts/tools/LESSONS.md — the single source of truth
type: reference
---

**Read scripts/tools/LESSONS.md before doing anything.** It has 21 lessons covering:
- Geometry: clearance, bmesh, handles as separate meshes (Lesson 21)
- Physics: door direction, joint positions, flat hierarchy
- Collision: contactOffset=0.002 baked into USD (Lesson 15), phantom surfaces (Lesson 14)
- PhysX config: solver iterations=16, contactOffset on robot at runtime
- Pipeline: geometry_compiler.py, runtime_monitor.py, test_asset.py

Pipeline files: intent_profile.py → object_spec.py → geometry_compiler.py → Blender MCP → make_asset.py → verify_asset.py → runtime_monitor.py

Proven on: chevron cabinet v4, microwave
