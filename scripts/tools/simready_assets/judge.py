#!/usr/bin/env python3
"""Judge Module — Path D of the multi-agent asset generator.

Two parallel judges:
  D1: Visual Judge — Gemini + Claude compare screenshot vs original image
  D2: Structural Auditor — inspects Blender scene graph vs behavior spec

Both use math validation. If issues found, returns fix instructions for C to retry.
"""

import json
import os
import socket
import threading
import time

_DIR = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════════════
# BLENDER SCENE INSPECTION
# ═══════════════════════════════════════════════════════════════════════════════

def query_blender_scene(port=9876):
    """Query Blender for complete scene data via MCP."""
    inspection_script = '''
import bpy
import json
from mathutils import Vector

scene_data = {
    "objects": [],
    "total_vertices": 0,
    "total_objects": 0,
}

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue

    verts = len(obj.data.vertices)
    faces = len(obj.data.polygons)

    # Bounding box in world space
    bbox_corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [c.x for c in bbox_corners]
    ys = [c.y for c in bbox_corners]
    zs = [c.z for c in bbox_corners]

    # Origin position
    origin = obj.location

    # Material info
    materials = [m.name for m in obj.data.materials if m]

    obj_data = {
        "name": obj.name,
        "vertices": verts,
        "faces": faces,
        "origin": [round(origin.x, 4), round(origin.y, 4), round(origin.z, 4)],
        "bbox_min": [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
        "bbox_max": [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)],
        "dims": [
            round(max(xs) - min(xs), 4),
            round(max(ys) - min(ys), 4),
            round(max(zs) - min(zs), 4),
        ],
        "materials": materials,
    }

    scene_data["objects"].append(obj_data)
    scene_data["total_vertices"] += verts

scene_data["total_objects"] = len(scene_data["objects"])

# Overall bounding box
if scene_data["objects"]:
    all_min = [min(o["bbox_min"][i] for o in scene_data["objects"]) for i in range(3)]
    all_max = [max(o["bbox_max"][i] for o in scene_data["objects"]) for i in range(3)]
    scene_data["overall_dims"] = [round(all_max[i] - all_min[i], 4) for i in range(3)]
else:
    scene_data["overall_dims"] = [0, 0, 0]

print(json.dumps(scene_data))
'''
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect(("localhost", port))
        sock.sendall(json.dumps({"type": "execute_code", "params": {"code": inspection_script}}).encode())
        response = b""
        while True:
            try:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                response += chunk
                try:
                    json.loads(response.decode())
                    break
                except:
                    continue
            except socket.timeout:
                break
        sock.close()

        result = json.loads(response.decode())
        # Extract the printed JSON from the result
        output = result.get("result", {}).get("result", "")
        if isinstance(output, str) and output.strip().startswith("{"):
            return json.loads(output)
        return None
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# D2: STRUCTURAL AUDITOR — math-based scene validation
# ═══════════════════════════════════════════════════════════════════════════════

def audit_structure(scene_data, behavior_data, bodies_data):
    """Validate Blender scene against expected behavior spec using math.

    Returns: (passed, issues_list)
    """
    issues = []
    if not scene_data or "error" in scene_data:
        issues.append("Could not inspect Blender scene")
        return False, issues

    objects = scene_data.get("objects", [])
    obj_names = {o["name"]: o for o in objects}

    behaviors = behavior_data.get("behaviors", [])
    bodies = bodies_data.get("bodies", [])

    # ── Check expected objects exist ──
    expected_separate = [b["name"] for b in bodies if b.get("separate", True)]
    for name in expected_separate:
        # Fuzzy match — check if any object name contains the expected name
        found = any(name.lower() in oname.lower() for oname in obj_names)
        if not found:
            issues.append(f"MISSING OBJECT: expected '{name}' but not found in scene. Objects: {list(obj_names.keys())}")

    # ── Check drawer geometry (must be box, not flat panel) ──
    for b in behaviors:
        if b.get("part", "").lower() == "drawer" and b.get("motion") == "linear":
            count = b.get("count", 0)
            drawer_objs = [o for o in objects if "drawer" in o["name"].lower()]

            if len(drawer_objs) != count:
                issues.append(f"DRAWER COUNT: expected {count} drawers, found {len(drawer_objs)}")

            for d in drawer_objs:
                # A flat panel has ~8-12 vertices. A 5-sided box has 40+
                if d["vertices"] < 20:
                    issues.append(
                        f"FLAT DRAWER: '{d['name']}' has only {d['vertices']} vertices — "
                        f"likely a flat panel, not a 5-sided box. Must have front+bottom+left+right+back walls."
                    )

                # Drawer should have depth (Y dimension > panel thickness)
                depth = d["dims"][1]
                if depth < 0.05:  # less than 50mm depth
                    issues.append(
                        f"SHALLOW DRAWER: '{d['name']}' depth is {depth*1000:.0f}mm — "
                        f"should be ~80% of carcass depth for a real drawer box."
                    )

    # ── Check door geometry ──
    for b in behaviors:
        if b.get("part", "").lower() == "door" and b.get("motion") == "rotational":
            count = b.get("count", 0)
            door_objs = [o for o in objects if "door" in o["name"].lower() and "knob" not in o["name"].lower()]

            if len(door_objs) != count:
                issues.append(f"DOOR COUNT: expected {count} doors, found {len(door_objs)}")

            for d in door_objs:
                # Check origin is at hinge edge (not center)
                origin_x = d["origin"][0]
                bbox_min_x = d["bbox_min"][0]
                bbox_max_x = d["bbox_max"][0]
                center_x = (bbox_min_x + bbox_max_x) / 2
                width = d["dims"][0]

                # Origin should be near left or right edge, not center
                dist_to_left = abs(origin_x - bbox_min_x)
                dist_to_right = abs(origin_x - bbox_max_x)
                dist_to_center = abs(origin_x - center_x)
                min_edge_dist = min(dist_to_left, dist_to_right)

                if width > 0.05 and dist_to_center < min_edge_dist:
                    issues.append(
                        f"DOOR PIVOT: '{d['name']}' origin at X={origin_x:.3f} is near center "
                        f"(bbox {bbox_min_x:.3f} to {bbox_max_x:.3f}). "
                        f"Must be at hinge edge for proper rotation."
                    )

    # ── Check dividers between doors ──
    for b in behaviors:
        if b.get("part", "").lower() == "door" and b.get("count", 0) > 1:
            count = b.get("count", 0)
            expected_dividers = count - 1

            # Look for stile/divider objects or check frame object has enough geometry
            frame_objs = [o for o in objects if any(k in o["name"].lower()
                          for k in ["frame", "carcass", "cabinet", "main"])]
            stile_objs = [o for o in objects if any(k in o["name"].lower()
                          for k in ["stile", "divider", "div"])]

            # If no separate stile objects, check frame has enough vertices for dividers
            if not stile_objs and frame_objs:
                frame_verts = sum(f["vertices"] for f in frame_objs)
                # A simple box frame = ~60-80 verts. With dividers = 100+
                if frame_verts < 80 and expected_dividers > 0:
                    issues.append(
                        f"MISSING DIVIDERS: {count} doors need {expected_dividers} vertical stiles "
                        f"between them, but frame has only {frame_verts} vertices (likely missing dividers)."
                    )

    # ── Check overall dimensions are reasonable ──
    overall = scene_data.get("overall_dims", [0, 0, 0])
    if all(d > 0 for d in overall):
        for i, label in enumerate(["width", "depth", "height"]):
            if overall[i] < 0.01:
                issues.append(f"TINY DIMENSION: overall {label} = {overall[i]*1000:.0f}mm (too small)")

    # ── Check all objects are within overall bounding box (no flying parts) ──
    if len(objects) >= 2:
        # Compute overall bounds from frame/carcass (largest object)
        frame = max(objects, key=lambda o: o["vertices"])
        frame_min = frame["bbox_min"]
        frame_max = frame["bbox_max"]
        # Allow 20% tolerance beyond frame bounds
        tolerance = max(frame["dims"]) * 0.2

        for obj in objects:
            if obj["name"] == frame["name"]:
                continue
            for axis, label in enumerate(["X", "Y", "Z"]):
                if obj["bbox_min"][axis] < frame_min[axis] - tolerance:
                    issues.append(
                        f"OUT OF BOUNDS: '{obj['name']}' {label}_min={obj['bbox_min'][axis]*1000:.0f}mm "
                        f"is {abs(obj['bbox_min'][axis] - frame_min[axis])*1000:.0f}mm below frame. "
                        f"Object is mispositioned — should be inside or flush with the frame."
                    )
                if obj["bbox_max"][axis] > frame_max[axis] + tolerance:
                    issues.append(
                        f"OUT OF BOUNDS: '{obj['name']}' {label}_max={obj['bbox_max'][axis]*1000:.0f}mm "
                        f"is {abs(obj['bbox_max'][axis] - frame_max[axis])*1000:.0f}mm above frame. "
                        f"Object is mispositioned — should be inside or flush with the frame."
                    )

    # ── Check materials are assigned ──
    for obj in objects:
        if not obj.get("materials"):
            issues.append(f"NO MATERIAL: '{obj['name']}' has no material assigned")

    passed = len(issues) == 0
    return passed, issues


# ═══════════════════════════════════════════════════════════════════════════════
# D1 + D2 COMBINED: Visual + Structural judgment
# ═══════════════════════════════════════════════════════════════════════════════

D1_VISUAL_PROMPT = """Compare these two images:
1. REFERENCE: The original photo of the object
2. GENERATED: A 2x2 grid of Blender viewport screenshots from 4 angles (front, back, side, 3/4 view)

The generated image shows the 3D model from multiple angles so you can see all sides.
Check EACH of these and report issues:
- Component count: same number of doors, drawers, handles, knobs, legs?
- Proportions: are the height/width ratios similar?
- Layout: are components in the correct positions (top row vs bottom row)?
- Colors: do the materials roughly match?
- Missing parts: anything visible in the reference that's missing in the generated?
- Extra parts: anything in the generated that shouldn't be there?

Answer in EXACTLY this JSON format:
{
  "passed": true or false,
  "score": <0-10>,
  "issues": ["list of specific problems found"],
  "suggestions": ["list of specific fixes"]
}
If everything looks correct, passed=true and issues=[].
Return ONLY the JSON."""


def run_judge(image_path, screenshot_path, behavior_data, bodies_data,
              call_gemini_fn, call_claude_fn, gkey, ckey, gemini_model, claude_model,
              blender_port=9876):
    """Run D1 (visual) + D2 (structural) in parallel.

    Returns: (passed, all_issues, fix_instructions)
    """
    results = {}
    t0 = time.time()

    print(f"\n  ── Path D: Judge (visual + structural) ──")

    # ── D2: Structural audit (query Blender + math) ─────────────────────
    def _run_d2():
        scene = query_blender_scene(port=blender_port)
        if scene and "error" not in scene:
            results["scene_data"] = scene
            passed, issues = audit_structure(scene, behavior_data, bodies_data)
            results["d2"] = {"passed": passed, "issues": issues}
            print(f"    D2 (structural): {'PASS' if passed else 'FAIL'} — {len(issues)} issues")
            for iss in issues:
                print(f"      ✗ {iss}")
        else:
            results["d2"] = {"passed": False, "issues": ["Could not query Blender scene"]}
            print(f"    D2 (structural): ERROR — could not inspect scene")

    # ── D1: Visual judge (Gemini + Claude in parallel) ──────────────────
    def _run_d1_gemini():
        try:
            # Gemini can take two images — send both
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gkey)
            contents = []

            # Reference image
            with open(image_path, "rb") as f:
                ref_data = f.read()
            import mimetypes
            mime = mimetypes.guess_type(image_path)[0] or "image/png"
            contents.append(types.Part.from_bytes(data=ref_data, mime_type=mime))

            # Screenshot
            with open(screenshot_path, "rb") as f:
                ss_data = f.read()
            ss_mime = mimetypes.guess_type(screenshot_path)[0] or "image/png"
            contents.append(types.Part.from_bytes(data=ss_data, mime_type=ss_mime))

            contents.append("Image 1 is the REFERENCE photo. Image 2 is the GENERATED 3D model screenshot.\n\n" + D1_VISUAL_PROMPT)

            resp = client.models.generate_content(
                model=gemini_model, contents=contents,
                config=types.GenerateContentConfig(max_output_tokens=2048, temperature=0.1),
            )
            text = resp.text
            # Parse JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                results["d1_gemini"] = json.loads(text[start:end])
            else:
                results["d1_gemini"] = {"passed": False, "issues": ["Could not parse response"], "score": 0}
        except Exception as e:
            results["d1_gemini"] = {"passed": False, "issues": [f"Gemini error: {str(e)[:100]}"], "score": 0}

    def _run_d1_claude():
        try:
            import anthropic
            import base64
            import mimetypes

            client = anthropic.Anthropic(api_key=ckey)

            content = []
            # Reference image
            with open(image_path, "rb") as f:
                ref_b64 = base64.standard_b64encode(f.read()).decode()
            ref_mime = mimetypes.guess_type(image_path)[0] or "image/png"
            content.append({"type": "image", "source": {"type": "base64", "media_type": ref_mime, "data": ref_b64}})

            # Screenshot
            with open(screenshot_path, "rb") as f:
                ss_b64 = base64.standard_b64encode(f.read()).decode()
            ss_mime = mimetypes.guess_type(screenshot_path)[0] or "image/png"
            content.append({"type": "image", "source": {"type": "base64", "media_type": ss_mime, "data": ss_b64}})

            content.append({"type": "text", "text": "Image 1 is the REFERENCE photo. Image 2 is the GENERATED 3D model screenshot.\n\n" + D1_VISUAL_PROMPT})

            resp = client.messages.create(model=claude_model, max_tokens=2048,
                                          messages=[{"role": "user", "content": content}])
            text = resp.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                results["d1_claude"] = json.loads(text[start:end])
            else:
                results["d1_claude"] = {"passed": False, "issues": ["Could not parse response"], "score": 0}
        except Exception as e:
            results["d1_claude"] = {"passed": False, "issues": [f"Claude error: {str(e)[:100]}"], "score": 0}

    # Run all three in parallel
    threads = [
        threading.Thread(target=_run_d2),
        threading.Thread(target=_run_d1_gemini),
        threading.Thread(target=_run_d1_claude),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    elapsed = time.time() - t0

    # ── Combine results ─────────────────────────────────────────────────
    d2 = results.get("d2", {"passed": False, "issues": ["D2 did not run"]})
    d1g = results.get("d1_gemini", {"passed": False, "issues": ["Gemini did not run"], "score": 0})
    d1c = results.get("d1_claude", {"passed": False, "issues": ["Claude did not run"], "score": 0})

    # Print D1 results
    g_score = d1g.get("score", 0)
    c_score = d1c.get("score", 0)
    avg_score = (g_score + c_score) / 2

    print(f"    D1 (visual Gemini): score={g_score}/10, {'PASS' if d1g.get('passed') else 'FAIL'}")
    for iss in d1g.get("issues", []):
        print(f"      ✗ {iss}")
    print(f"    D1 (visual Claude): score={c_score}/10, {'PASS' if d1c.get('passed') else 'FAIL'}")
    for iss in d1c.get("issues", []):
        print(f"      ✗ {iss}")

    print(f"    Average visual score: {avg_score:.1f}/10")
    print(f"    Judge time: {elapsed:.1f}s")

    # ── Decide pass/fail ────────────────────────────────────────────────
    all_issues = []

    # D2 structural issues are critical
    all_issues.extend([f"[STRUCTURAL] {i}" for i in d2.get("issues", [])])

    # D1 visual issues — merge unique issues from both
    seen = set()
    for iss in d1g.get("issues", []) + d1c.get("issues", []):
        if iss not in seen:
            all_issues.append(f"[VISUAL] {iss}")
            seen.add(iss)

    # Pass if: D2 passes AND average visual score >= 6
    passed = d2.get("passed", False) and avg_score >= 6

    # ── Build fix instructions for C retry ──────────────────────────────
    fix_instructions = ""
    if not passed and all_issues:
        fix_lines = [
            "## FIXES REQUIRED (from judge feedback):",
            "The previous script had these problems. Fix ALL of them:",
            "",
        ]
        for i, iss in enumerate(all_issues, 1):
            fix_lines.append(f"  {i}. {iss}")

        # Add suggestions from D1
        suggestions = []
        for s in d1g.get("suggestions", []) + d1c.get("suggestions", []):
            if s not in suggestions:
                suggestions.append(s)
        if suggestions:
            fix_lines.append("")
            fix_lines.append("## SUGGESTED FIXES:")
            for s in suggestions:
                fix_lines.append(f"  - {s}")

        fix_instructions = "\n".join(fix_lines)

    return passed, all_issues, fix_instructions, {
        "d1_gemini": d1g,
        "d1_claude": d1c,
        "d2": d2,
        "avg_visual_score": avg_score,
        "elapsed_s": round(elapsed, 1),
    }
