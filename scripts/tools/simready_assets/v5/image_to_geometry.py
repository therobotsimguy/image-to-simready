#!/usr/bin/env python3
"""V5 Image-to-Geometry: Generate 3D geometry in Blender from an image.

Uses Claude + Gemini to analyze the image, then Claude writes a Blender script.
After this stage, Layer 1 picks up from the Blender scene (same as OBJ path).

This is the V4 approach integrated into V5.
"""

import json
import os
import sys
import threading
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.dirname(_DIR)
_DOCS_DIR = os.path.join(_ASSETS_DIR, "docs")
sys.path.insert(0, _ASSETS_DIR)

from v5.ai_agents import load_api_keys, call_claude, call_gemini, parse_json, run_parallel_agents
from v5.layer1_mechanical import send_to_blender


ANALYZE_PROMPT = """Look at this image. Identify the object and ALL its parts for 3D modeling.
Answer in EXACTLY this JSON format:
{{
  "object_type": "what is this (e.g., double wall oven, sideboard cabinet)",
  "category": "appliance | furniture | kitchenware | tool | other",
  "parts": [
    {{
      "name": "part_name (use snake_case, e.g., door_lower, knob_left)",
      "shape": "box | cylinder | sphere | panel | custom",
      "is_moving": true_or_false,
      "motion": "rotational | linear | none",
      "dims_mm_estimate": [width, depth, height],
      "position_description": "where is it relative to the body"
    }}
  ],
  "overall_dims_mm": [width, depth, height],
  "materials": ["list of materials visible"]
}}
Return ONLY the JSON."""


SCRIPT_PROMPT = """You are an expert Blender 4.3 Python scripter. Write a complete Blender script to create a 3D model.

## Object Analysis:
{analysis}

## Rules:
1. Clear scene first.
2. All dimensions in METERS.
3. Each part that moves = SEPARATE Blender object with a descriptive name (snake_case).
4. Static parts (body/frame/chassis) = joined into one object.
5. Use Principled BSDF materials.
6. Apply transforms after creation.
7. Smooth shading on all objects.
8. DO NOT set origins — leave all at (0,0,0). PhysX handles positioning later.
9. NO `use_auto_smooth` (removed in 4.x).
10. NO `if __name__` guards.
11. Print object names and vertex counts at the end.

{blender_rules}

Write ONLY the Python script, no markdown fences."""

BLENDER_RULES = """## Blender 4.3 API:
- Use `bpy.ops.mesh.primitive_*_add()` for primitives
- Materials: ShaderNodeOutputMaterial + ShaderNodeBsdfPrincipled
- Apply scale: `bpy.ops.object.transform_apply(scale=True)`
- Join: select objects, set active, `bpy.ops.object.join()`"""


def run_image_to_geometry(image_path, port=9876):
    """Generate 3D geometry in Blender from an image.

    Returns True if geometry was created in Blender scene.
    """
    print("\n" + "=" * 60)
    print("  IMAGE → GEOMETRY: Generate 3D model from image")
    print(f"  Image: {image_path}")
    print("=" * 60)

    keys = load_api_keys()
    ckey = keys["anthropic"]["api_key"]
    gkey = keys["gemini"]["api_key"]
    t0 = time.time()

    # Step 1: Analyze image (Claude + Gemini parallel)
    print("  Analyzing image (Claude ‖ Gemini)...")

    import base64
    import mimetypes

    with open(image_path, "rb") as f:
        img_b64 = base64.standard_b64encode(f.read()).decode()
    mime = mimetypes.guess_type(image_path)[0] or "image/png"

    def _analyze_claude():
        import anthropic
        client = anthropic.Anthropic(api_key=ckey)
        resp = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": img_b64}},
                {"type": "text", "text": ANALYZE_PROMPT},
            ]}],
        )
        return parse_json(resp.content[0].text)

    def _analyze_gemini():
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gkey)
        contents = [
            types.Part.from_bytes(data=base64.standard_b64decode(img_b64), mime_type=mime),
            ANALYZE_PROMPT,
        ]
        resp = client.models.generate_content(
            model="gemini-3.1-pro-preview", contents=contents,
            config=types.GenerateContentConfig(max_output_tokens=4096, temperature=0.1),
        )
        return parse_json(resp.text)

    results, errors = run_parallel_agents([
        ("claude", _analyze_claude),
        ("gemini", _analyze_gemini),
    ])

    analysis = results.get("claude") or results.get("gemini")
    source = "Claude" if "claude" in results else "Gemini"

    if not analysis:
        print(f"  Analysis failed: {errors}")
        return False

    obj_type = analysis.get("object_type", "unknown")
    n_parts = len(analysis.get("parts", []))
    print(f"  Object: {obj_type} ({n_parts} parts) [{source}]")
    for p in analysis.get("parts", []):
        motion = p.get("motion", "none")
        print(f"    {p['name']}: {p['shape']}, {motion}")

    # Step 2: Generate Blender script (Claude — needs image context)
    print(f"  Generating Blender script...")

    script_prompt = SCRIPT_PROMPT.format(
        analysis=json.dumps(analysis, indent=2),
        blender_rules=BLENDER_RULES,
    )

    # Send to Claude API with image
    import anthropic
    client = anthropic.Anthropic(api_key=ckey)
    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16384,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": img_b64}},
            {"type": "text", "text": script_prompt},
        ]}],
    )
    raw_script = resp.content[0].text

    # Extract script
    script = raw_script.strip()
    if "```python" in script:
        script = script.split("```python")[1].split("```")[0].strip()
    elif "```" in script:
        script = script.split("```")[1].split("```")[0].strip()

    print(f"  Script: {len(script.splitlines())} lines")

    # Step 3: Execute in Blender
    print(f"  Executing in Blender...")

    # Clear scene first
    send_to_blender('import bpy\nbpy.ops.object.select_all(action="SELECT")\nbpy.ops.object.delete(use_global=False)\nfor m in list(bpy.data.meshes): bpy.data.meshes.remove(m)\nfor m in list(bpy.data.materials): bpy.data.materials.remove(m)', port)

    result = send_to_blender(script, port)
    status = result.get("status", "?")
    output = result.get("result", {}).get("result", "")

    if status == "error":
        print(f"  BLENDER ERROR: {result.get('message', '?')[:200]}")
        return False

    print(f"  Blender: OK")
    if output:
        print(f"  {output[:300]}")

    elapsed = time.time() - t0
    print(f"  Image → Geometry: {elapsed:.1f}s")
    return True
