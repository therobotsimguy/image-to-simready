#!/usr/bin/env python3
"""Multi-Agent Asset Generator — general purpose.

Architecture:
  Phase 1 — Path A (6 AI agents) ‖ Path B (4 vision models) — all parallel
    Path A: Gemini×3 + Claude×3 → semantic understanding
    Path B: DINO + SAM3 + DepthPro + DepthAnything3 → measurements

  Phase 2 — Path C: AI reconciliation + Blender script generation
    Gemini + Claude reconcile A+B, then Claude writes the Blender script.

  Phase 3 — Execute in Blender via MCP

Works for ANY object: bolts, cabinets, glasses, ovens, etc.
No hardcoded templates — C generates the script based on what the object is.

Usage:
    python generate_asset.py --image cabinet.png
    python generate_asset.py --image bolt.png --no-execute
"""

import argparse
import base64
import json
import os
import socket
import sys
import time
import threading

_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOLS_DIR = os.path.dirname(_DIR)

# Always top models
BEST_GEMINI = "gemini-3.1-pro-preview"
BEST_CLAUDE = "claude-opus-4-6"

# Path B: Vision Stack
from vision_stack import run_vision_stack


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT PROMPTS — general purpose, works for any object
# ═══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "gemini_type": """Look at this image. Identify the object and its structure.
Answer in EXACTLY this JSON format, nothing else:
{
  "object_type": "what is this (e.g., hex bolt, sideboard cabinet, wine glass, microwave oven)",
  "category": "fastener | furniture | kitchenware | appliance | tool | other",
  "manufacturing": "how was it made (e.g., machined, panel construction, blown glass, injection molded)",
  "geometry_approach": "revolution (rotational symmetry) | panel_construction (boxes joined) | shell (thin walls) | solid (single block) | composite (mixed)",
  "components": [
    {"name": "part name", "shape": "cylinder | box | sphere | cone | hex_prism | custom_profile", "is_separate_object": false}
  ]
}
Count distinct parts carefully. Describe each visible component.
Return ONLY the JSON.""",

    "gemini_dims": """Look at this image. Estimate real-world dimensions of this object.
Answer in EXACTLY this JSON format:
{
  "overall_width_mm": <number>,
  "overall_depth_mm": <number>,
  "overall_height_mm": <number>,
  "components": [
    {"name": "part name", "width_mm": <num>, "depth_mm": <num>, "height_mm": <num>}
  ]
}
For rotational objects: width=depth=diameter, height=length along axis.
Return ONLY the JSON.""",

    "gemini_materials": """Look at this image. Identify ALL materials and their appearance.
Answer in EXACTLY this JSON format:
{
  "materials": [
    {
      "name": "descriptive name (e.g., galvanized steel, walnut wood, clear glass)",
      "type": "metal | wood | glass | plastic | ceramic | rubber | fabric",
      "color_rgb": [<r 0-1>, <g 0-1>, <b 0-1>],
      "metallic": <0 or 1>,
      "roughness": <0-1>,
      "applied_to": ["list of component names that use this material"]
    }
  ]
}
Return ONLY the JSON.""",

    "claude_behavior": """Look at this image. Analyze the physical behavior of this object.
Answer in EXACTLY this JSON format:
{
  "object_type": "what is this object",
  "behaviors": [
    {"part": "part name", "motion": "none | linear | rotational | free", "axis": "X | Y | Z | none", "description": "brief description"}
  ],
  "structural_notes": "how parts connect, what's hidden, what constraints exist",
  "simulation_notes": "what matters for physics simulation (mass, friction, joints)"
}
If the object has no moving parts (e.g., a bolt), behaviors should have motion=none.
Return ONLY the JSON.""",

    "claude_bodies": """Look at this image. Define the body list for 3D modeling.
Each body = one Blender object. Parts that are fixed together = joined into one body.
Parts that move independently or have different materials = separate bodies.
Answer in EXACTLY this JSON format:
{
  "bodies": [
    {"name": "Body_Name", "material": "material name", "geometry": "description of shape and how to build it in Blender", "separate": true_or_false, "reason": "why separate or joined"}
  ],
  "total_objects": <int>,
  "origin_hint": "where the object origin should be (e.g., bottom center, geometric center)"
}
Return ONLY the JSON.""",

    "claude_geometry": """Look at this image. Describe the EXACT geometry needed to build this in Blender 4.3.
Think about manufacturing: how was this object made? That determines the modeling approach.
Answer in EXACTLY this JSON format:
{
  "approach": "revolution | extrude | primitive_assembly | boolean | sculpt",
  "blender_operations": [
    {"step": 1, "operation": "what to do", "details": "specific Blender API calls or approach"}
  ],
  "critical_details": ["list of details that must be correct for realism"],
  "common_mistakes": ["what to avoid when modeling this object"]
}
For revolution objects (bolts, glasses): describe the 2D profile to revolve.
For panel objects (furniture): describe each panel's position.
For complex objects: describe step by step.
Return ONLY the JSON.""",
}

# Path C: Blender script generation prompt
SCRIPT_GEN_PROMPT = """You are an expert Blender 4.3 Python scripter. You must write a complete Blender script to create the 3D object described below.

## Object Analysis (from 6 AI agents + 4 vision models):
{spec_data}

## Rules:
1. Clear the scene first (remove all objects, meshes, materials).
2. Use Blender 4.3 API ONLY — no deprecated functions.
3. All dimensions in METERS (convert from mm).
4. Create proper materials using Principled BSDF nodes.
5. Each body listed as separate = a separate Blender object.
6. Apply transforms (scale, rotation) after creating each object.
7. Use smooth shading on all objects.
8. Set object origins correctly for physics articulation:
   - DOORS: origin MUST be at the HINGE EDGE (left or right edge), NOT center.
   - DRAWERS: origin at center is fine (prismatic joint slides along axis).
   - To move the origin WITHOUT moving the visible geometry, use this pattern:
     ```
     def set_origin_keep_visual(obj, new_origin_x, new_origin_y, new_origin_z):
         from mathutils import Vector
         new_origin = Vector((new_origin_x, new_origin_y, new_origin_z))
         offset = new_origin - obj.location
         obj.location = new_origin
         for v in obj.data.vertices:
             v.co -= offset
     ```
     Call this AFTER creating each door, passing the hinge edge position as the new origin.
     The door stays visually in the same place but its origin moves to the hinge edge.
9. Export to USD and save .blend file at the end.

## Blender 4.3 API reminders:
- NO `use_auto_smooth` (removed in 4.x)
- NO `Specular` input on Principled BSDF (removed)
- Use `bpy.ops.mesh.primitive_*_add()` for primitives
- For revolution/lathe objects: use `from_pydata()` with computed vertices
- For threaded bolts: modulate vertex radius along helix
- Apply scale: `bpy.ops.object.transform_apply(scale=True)`
- Materials: create node tree with ShaderNodeOutputMaterial + ShaderNodeBsdfPrincipled
- USD export: `bpy.ops.wm.usd_export(filepath='...', export_materials=True)`
- Save: `bpy.ops.wm.save_as_mainfile(filepath='...')`

## Output paths:
- USD: {output_usd}
- Blend: {output_blend}

## IMPORTANT:
- Write the COMPLETE script. No placeholders, no "TODO", no imports that aren't available in Blender.
- The script runs via exec() inside Blender — no `if __name__` guards.
- Print object count, vertex count, and dimensions at the end for verification.

Write ONLY the Python script, no markdown fences, no explanations."""


# ═══════════════════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def load_api_keys():
    with open(os.path.join(_TOOLS_DIR, "api_keys.json")) as f:
        return json.load(f)

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode()

def call_gemini(api_key, model, prompt, image_path=None):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    contents = []
    if image_path:
        with open(image_path, "rb") as f:
            data = f.read()
        import mimetypes
        mime = mimetypes.guess_type(image_path)[0] or "image/png"
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))
    contents.append(prompt)
    resp = client.models.generate_content(
        model=model, contents=contents,
        config=types.GenerateContentConfig(max_output_tokens=8192, temperature=0.1),
    )
    return resp.text

def call_claude(api_key, model, prompt, image_path=None):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    content = []
    if image_path:
        b64 = image_to_base64(image_path)
        import mimetypes
        mime = mimetypes.guess_type(image_path)[0] or "image/png"
        content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}})
    content.append({"type": "text", "text": prompt})
    resp = client.messages.create(model=model, max_tokens=16384,
                                   messages=[{"role": "user", "content": content}])
    return resp.content[0].text

def parse_json_response(text):
    """Extract JSON from AI response, handling markdown fences."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return json.loads(text)

def extract_script(text):
    """Extract Python script from AI response, stripping markdown fences."""
    text = text.strip()
    if "```python" in text:
        text = text.split("```python")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# BLENDER MCP
# ═══════════════════════════════════════════════════════════════════════════════

def send_to_blender(script, port=9876):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(180)
    sock.connect(("localhost", port))
    sock.sendall(json.dumps({"type": "execute_code", "params": {"code": script}}).encode())
    response = b""
    while True:
        try:
            chunk = sock.recv(8192)
            if not chunk: break
            response += chunk
            try: json.loads(response.decode()); break
            except: continue
        except socket.timeout: break
    sock.close()
    if not response: raise RuntimeError("No response from Blender")
    return json.loads(response.decode())

def blender_screenshot(filepath, port=9876):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect(("localhost", port))
        sock.sendall(json.dumps({"type": "get_viewport_screenshot", "params": {"filepath": filepath}}).encode())
        resp = b""
        while True:
            try:
                c = sock.recv(65536)
                if not c: break
                resp += c
                try: json.loads(resp.decode()); break
                except: continue
            except socket.timeout: break
        sock.close()
        return json.loads(resp.decode()).get("status") == "success"
    except:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIOR → GEOMETRIC CONSTRAINTS
# ═══════════════════════════════════════════════════════════════════════════════

def derive_constraints(behavior_data, bodies_data):
    """Convert behavior analysis into DO/DON'T rules for script generation.

    These rules prevent the script from creating geometry that would
    block moving parts or violate physical behavior requirements.
    """
    rules = []
    behaviors = behavior_data.get("behaviors", [])
    bodies = bodies_data.get("bodies", [])

    for b in behaviors:
        part = b.get("part", "").lower()
        motion = b.get("motion", "none").lower()
        axis = b.get("axis", "").upper()

        if motion == "linear":
            # Sliding parts (drawers, sliding doors)
            rules.append(
                f"CONSTRAINT ({part}, linear on {axis}): "
                f"DO NOT place any structural geometry (rails, dividers, trim) in front of "
                f"the {part} face that would visually block or intersect its slide path. "
                f"The {part} front face must be flush with or slightly recessed from the carcass front. "
                f"Any horizontal rail between rows must be BEHIND the {part} front face, not in front of it."
            )
            rules.append(
                f"CONSTRAINT ({part}, clearance): "
                f"Leave at least 3-5mm gap around all sides of the {part} so it can slide freely. "
                f"The {part} must NOT touch the carcass sides, top, or bottom panels."
            )
            if "drawer" in part:
                rules.append(
                    f"CONSTRAINT ({part}, geometry): "
                    f"Each drawer MUST be a 5-sided open-top box, NOT just a front panel. "
                    f"It needs: front panel (visible face), bottom panel, left side wall, right side wall, "
                    f"and back wall. The top is OPEN. The box extends back into the carcass ~80% of the "
                    f"carcass depth. Wall thickness ~12mm. Join all 5 panels into ONE drawer object. "
                    f"The front panel is the decorative face; the other 4 panels form the box behind it."
                )

        elif motion == "rotational":
            # Swinging parts (doors, lids)
            rules.append(
                f"CONSTRAINT ({part}, rotational on {axis}): "
                f"DO NOT place any geometry in the {part}'s swing arc. "
                f"The {part} must be able to swing open 90+ degrees without collision. "
                f"Adjacent {part}s should not collide when opened simultaneously."
            )
            rules.append(
                f"CONSTRAINT ({part}, hinge): "
                f"The {part}'s origin/pivot MUST be at the hinge edge using set_origin_keep_visual(). "
                f"Knobs/handles go on the OPPOSITE side of the hinge."
            )
            count = b.get("count", 0)
            if "door" in part and count > 1:
                rules.append(
                    f"CONSTRAINT ({part}, dividers): "
                    f"There are {count} {part}s side by side. The carcass frame MUST include "
                    f"{count - 1} vertical divider stiles between them. Each stile is a vertical panel "
                    f"(panel_thickness wide, full depth, full row height) that the {part}s close against. "
                    f"Without these stiles, there would be visible gaps between adjacent {part}s."
                )

    # Global structural rules from bodies
    separate_parts = [b["name"] for b in bodies if b.get("separate", True)]
    joined_parts = [b["name"] for b in bodies if not b.get("separate", True)]

    if separate_parts:
        rules.append(
            f"CONSTRAINT (separation): These MUST be separate Blender objects: {separate_parts}. "
            f"Do NOT join them into the carcass/frame."
        )

    if joined_parts:
        rules.append(
            f"CONSTRAINT (joining): These should be joined into ONE frame object: {joined_parts}. "
            f"Use bpy.ops.object.join() after creating all frame panels."
        )

    # Visual rules
    rules.append(
        "CONSTRAINT (visual): Drawer fronts and door fronts must be the OUTERMOST geometry "
        "on the front face. No rail, divider, or frame element should protrude past them. "
        "Rails between rows should be recessed or flush with the inner edge of the front panels."
    )

    rules.append(
        "CONSTRAINT (proportions): Moving parts (doors, drawers) should fill their grid cell "
        "with only a small gap (3-5mm) around edges. They should NOT be significantly smaller "
        "than their cell opening."
    )

    return rules


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_agent(func, key, model, prompt, image_path, result_dict, agent_name):
    """Thread target for a single agent."""
    try:
        raw = func(key, model, prompt, image_path=image_path)
        result_dict[agent_name] = {"raw": raw, "parsed": parse_json_response(raw), "error": None}
    except Exception as e:
        result_dict[agent_name] = {"raw": "", "parsed": None, "error": str(e)}


def build_spec_summary(results, vdata):
    """Build a complete text summary of all agent + vision results for Path C."""
    lines = ["# COMPLETE OBJECT ANALYSIS", ""]

    # Path A results
    for name in ["gemini_type", "gemini_dims", "gemini_materials",
                 "claude_behavior", "claude_bodies", "claude_geometry"]:
        r = results.get(name, {})
        parsed = r.get("parsed", {})
        if parsed:
            lines.append(f"## {name}:")
            lines.append(json.dumps(parsed, indent=2))
            lines.append("")

    # Derive behavioral constraints
    behavior = results.get("claude_behavior", {}).get("parsed", {})
    bodies = results.get("claude_bodies", {}).get("parsed", {})
    if behavior or bodies:
        constraints = derive_constraints(behavior or {}, bodies or {})
        if constraints:
            lines.append("## GEOMETRIC CONSTRAINTS (derived from behavior analysis):")
            lines.append("These are MANDATORY rules. Violating them will break physics simulation.")
            lines.append("")
            for i, rule in enumerate(constraints, 1):
                lines.append(f"  {i}. {rule}")
            lines.append("")

    # Path B results
    if vdata:
        lines.append("## Vision Stack (measured data):")
        lines.append(f"  Confirmed counts: {vdata.get('counts', {})}")
        lines.append(f"  Overall measured dims: {vdata.get('overall_dims', {})}")
        lines.append(f"  Row ratios: {vdata.get('row_ratios', {})}")
        lines.append(f"  Depth consistency: {vdata.get('depth_consistency', 'N/A')}")

        spatial = vdata.get("spatial_layout", {})
        if spatial:
            lines.append(f"  Spatial layout: {spatial}")

        measured = vdata.get("measured_by_type", {})
        if measured:
            lines.append(f"  Per-component measured dimensions:")
            for label, mdata in measured.items():
                lines.append(f"    {label}: {mdata['avg_width_mm']:.0f}×{mdata['avg_height_mm']:.0f}mm (n={mdata['count']})")

        sampled = vdata.get("sampled_colors", {})
        if sampled:
            lines.append(f"  Pixel-sampled colors (from image):")
            for label, cdata in sampled.items():
                metal = "metallic" if cdata.get("is_metallic") else "textured"
                lines.append(f"    {label}: RGB={cdata['avg_rgb']} ({metal})")

        lines.append("")

    return "\n".join(lines)


def run_pipeline(image_path, api_keys, output_usd, output_blend):
    gkey = api_keys["gemini"]["api_key"]
    ckey = api_keys["anthropic"]["api_key"]

    # ══ PHASE 1: Path A (6 AI agents) ‖ Path B (4 vision models) ═══════
    print("\n" + "=" * 70)
    print("  PHASE 1: Path A (6 AI agents) ‖ Path B (4 vision models)")
    print("           All 10 workers running in parallel")
    print("=" * 70)

    t0 = time.time()

    # ── Path B: Vision Stack (background thread) ────────────────────────
    vision_result = {}

    def _run_vision():
        vision_result["data"] = run_vision_stack(image_path)

    vision_thread = threading.Thread(target=_run_vision)
    vision_thread.start()

    # ── Path A: 6 AI agents ─────────────────────────────────────────────
    results = {}
    agents = [
        ("gemini_type",     call_gemini, gkey, BEST_GEMINI, PROMPTS["gemini_type"]),
        ("gemini_dims",     call_gemini, gkey, BEST_GEMINI, PROMPTS["gemini_dims"]),
        ("gemini_materials", call_gemini, gkey, BEST_GEMINI, PROMPTS["gemini_materials"]),
        ("claude_behavior", call_claude, ckey, BEST_CLAUDE, PROMPTS["claude_behavior"]),
        ("claude_bodies",   call_claude, ckey, BEST_CLAUDE, PROMPTS["claude_bodies"]),
        ("claude_geometry", call_claude, ckey, BEST_CLAUDE, PROMPTS["claude_geometry"]),
    ]

    ai_threads = []
    for name, func, key, model, prompt in agents:
        t = threading.Thread(target=run_agent, args=(func, key, model, prompt, image_path, results, name))
        t.start()
        ai_threads.append((name, t))

    # Wait for all
    for name, t in ai_threads:
        t.join(timeout=120)
    vision_thread.join(timeout=180)

    phase1_time = time.time() - t0

    # ── Path A status ───────────────────────────────────────────────────
    print(f"\n  ── Path A: AI Agents ──")
    all_ok = True
    for name, _ in ai_threads:
        r = results.get(name, {})
        if r.get("error"):
            print(f"    {name}: ERROR — {r['error']}")
            all_ok = False
        elif r.get("parsed"):
            print(f"    {name}: OK ({len(r['raw'])} chars)")
        else:
            print(f"    {name}: PARSE FAILED")
            print(f"      Raw: {r.get('raw', '')[:200]}")
            all_ok = False

    # ── Path B status ───────────────────────────────────────────────────
    vdata = vision_result.get("data", {})
    print(f"\n  ── Path B: Vision Stack ──")
    for m, s in vdata.get("model_status", {}).items():
        print(f"    {m}: {s}")
    print(f"    Counts: {vdata.get('counts', {})}")

    print(f"\n  Phase 1: {phase1_time:.1f}s (all parallel)")

    if not all_ok:
        print("  Path A agents failed. Aborting.")
        return None, results

    # ══ PHASE 2: Path C — AI generates Blender script ══════════════════
    print("\n" + "=" * 70)
    print("  PHASE 2: Path C — reconcile + generate Blender script")
    print("=" * 70)

    t1 = time.time()

    # Build complete spec summary from A + B
    spec_summary = build_spec_summary(results, vdata)

    # Print what object we're building
    obj_type = results.get("gemini_type", {}).get("parsed", {}).get("object_type", "unknown")
    approach = results.get("gemini_type", {}).get("parsed", {}).get("geometry_approach", "unknown")
    print(f"  Object: {obj_type}")
    print(f"  Geometry approach: {approach}")

    # Claude writes the Blender script (sees image + all analysis)
    script_prompt = SCRIPT_GEN_PROMPT.format(
        spec_data=spec_summary,
        output_usd=output_usd,
        output_blend=output_blend,
    )

    print(f"  Generating Blender script with {BEST_CLAUDE}...")

    try:
        raw_script = call_claude(ckey, BEST_CLAUDE, script_prompt, image_path=image_path)
        script = extract_script(raw_script)
        print(f"  Script: {len(script.splitlines())} lines, {len(script)} chars")
    except Exception as e:
        print(f"  Claude script generation FAILED: {e}")
        print(f"  Falling back to Gemini...")
        try:
            raw_script = call_gemini(gkey, BEST_GEMINI, script_prompt, image_path=image_path)
            script = extract_script(raw_script)
            print(f"  Gemini script: {len(script.splitlines())} lines")
        except Exception as e2:
            print(f"  Gemini also failed: {e2}")
            return None, results

    phase2_time = time.time() - t1
    print(f"  Phase 2: {phase2_time:.1f}s")
    print(f"  Total: {phase1_time + phase2_time:.1f}s")

    return script, {
        "object_type": obj_type,
        "approach": approach,
        "vision": {k: v for k, v in vdata.items() if k != "components"},
        "agents": {k: {"raw": v["raw"]} for k, v in results.items()},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Asset Generator")
    parser.add_argument("--image", required=True, help="Path to reference image")
    parser.add_argument("--output", default=None, help="Output USD path")
    parser.add_argument("--blender-port", type=int, default=9876, help="Blender MCP port")
    parser.add_argument("--no-execute", action="store_true", help="Generate script only")
    args = parser.parse_args()

    image_path = args.image
    if not os.path.isabs(image_path):
        image_path = os.path.join(_DIR, image_path)
    if not os.path.exists(image_path):
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)

    obj_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = os.path.join(_DIR, obj_name)
    os.makedirs(output_dir, exist_ok=True)
    output_usd = args.output or os.path.join(output_dir, f"{obj_name}_asset.usd")
    output_blend = os.path.join(output_dir, f"{obj_name}.blend")

    print()
    print("=" * 70)
    print("  MULTI-AGENT ASSET GENERATOR")
    print(f"  Image:    {image_path}")
    print(f"  Output:   {output_usd}")
    print(f"  Path A:   {BEST_GEMINI} (×3) + {BEST_CLAUDE} (×3)")
    print(f"  Path B:   DINO + SAM3 + DepthPro + DepthAnything3")
    print(f"  Path C:   {BEST_CLAUDE} (Blender script generation)")
    print(f"  Workers:  10 parallel (6 AI + 4 vision) + 1 script gen")
    print("=" * 70)

    api_keys = load_api_keys()
    t0 = time.time()

    script, log = run_pipeline(image_path, api_keys, output_usd, output_blend)
    if not script:
        print("\n  Pipeline failed.")
        return

    # Save
    def _json_default(o):
        """Handle numpy types for JSON serialization."""
        import numpy as np
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.ndarray,)):
            return o.tolist()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    with open(os.path.join(output_dir, "spec.json"), "w") as f:
        json.dump({k: v for k, v in log.items() if k != "agents"}, f, indent=2, default=_json_default)
    script_path = os.path.join(output_dir, "final_blender_script.py")
    with open(script_path, "w") as f:
        f.write(script)

    if args.no_execute:
        print(f"\n  Script saved: {script_path}")
        return

    # Execute
    print("\n" + "=" * 70)
    print("  EXECUTING IN BLENDER")
    print("=" * 70)

    try:
        t1 = time.time()
        result = send_to_blender(script, port=args.blender_port)

        if result.get("status") == "error":
            print(f"\n  BLENDER ERROR: {result.get('message', '?')}")
            print(f"  Script: {script_path}")
        else:
            print(f"\n  Success ({time.time()-t1:.1f}s)")
            out = result.get("result", {})
            print(f"  {out.get('result', '')[:500] if isinstance(out, dict) else str(out)[:500]}")

            # Screenshot
            time.sleep(1)
            setup = ('import bpy, math\n'
                     'for a in bpy.context.screen.areas:\n'
                     '    if a.type == "VIEW_3D":\n'
                     '        for s in a.spaces:\n'
                     '            if s.type == "VIEW_3D": s.shading.type = "MATERIAL"\n'
                     '        for r in a.regions:\n'
                     '            if r.type == "WINDOW":\n'
                     '                with bpy.context.temp_override(area=a, region=r):\n'
                     '                    bpy.ops.view3d.view_axis(type="BACK")\n'
                     '                    bpy.ops.view3d.view_all()\n'
                     '                    bpy.ops.view3d.view_orbit(angle=math.radians(15), type="ORBITDOWN")\n'
                     '                    bpy.ops.view3d.view_orbit(angle=math.radians(-20), type="ORBITRIGHT")\n'
                     '                break\n'
                     'bpy.ops.object.select_all(action="DESELECT")\n')
            send_to_blender(setup, port=args.blender_port)
            time.sleep(1)

            ss = f"/tmp/{obj_name}_vp.png"
            if blender_screenshot(ss, port=args.blender_port):
                import shutil
                shutil.copy(ss, os.path.join(output_dir, "viewport.png"))
                print(f"  Screenshot saved")

    except ConnectionRefusedError:
        print(f"\n  ERROR: Blender MCP not running")
    except Exception as e:
        print(f"\n  ERROR: {e}")

    print(f"\n  Total: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
