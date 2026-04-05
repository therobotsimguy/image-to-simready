#!/usr/bin/env python3
"""Template-Based Multi-Agent Asset Generator.

Architecture:
  Phase 1 — 6 parallel AI agents (all top models, ~25s):
    Gemini 1: Object type + grid layout
    Gemini 2: Dimensions in mm
    Gemini 3: Materials + finishes
    Claude 1: Behavior analysis (what moves, hidden structure)
    Claude 2: Body list (what's separate vs joined)
    Claude 3: Hardware details (handle types, knob positions, hinge sides)

  Phase 2 — Deterministic (instant, no API):
    Merge → JSON spec → geometry_math.py → Blender template → execute

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


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT PROMPTS — each agent has ONE focused job, returns structured data
# ═══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "gemini_type": """Look at this image. Answer in EXACTLY this JSON format, nothing else:
{
  "object_type": "what is this object (e.g., sideboard cabinet, hex bolt, wine glass)",
  "manufacturing": "how was it made (e.g., panel construction, machined, blown glass)",
  "grid": {
    "columns": <int>,
    "rows": <int>,
    "row_contents": ["what's in row 0 (bottom)", "what's in row 1", ...]
  }
}
Count HARDWARE to determine grid: 3 bar pulls on top = 3 columns of drawers.
3 round knobs on bottom = 3 columns of doors. Hardware count is truth.
Return ONLY the JSON.""",

    "gemini_dims": """Look at this image. Estimate dimensions. Answer in EXACTLY this JSON format:
{
  "overall_width_mm": <number>,
  "overall_depth_mm": <number>,
  "overall_height_mm": <number>,
  "panel_thickness_mm": <number>,
  "leg_height_mm": <number or 0>,
  "row_heights_mm": [<height of row 0 (bottom)>, <height of row 1>, ...],
  "handle_length_mm": <number or 0>,
  "knob_diameter_mm": <number or 0>
}
Return ONLY the JSON.""",

    "gemini_materials": """Look at this image. Identify materials. Answer in EXACTLY this JSON format:
{
  "primary_material": "wood type or metal type",
  "primary_color_rgb": [<r 0-1>, <g 0-1>, <b 0-1>],
  "primary_color_dark_rgb": [<r>, <g>, <b>],
  "primary_roughness": <0-1>,
  "hardware_material": "steel, brass, etc",
  "hardware_color_rgb": [<r>, <g>, <b>],
  "hardware_metallic": <0 or 1>,
  "hardware_roughness": <0-1>
}
Return ONLY the JSON.""",

    "claude_behavior": """Look at this image. Analyze behavior and hidden structure.
Answer in EXACTLY this JSON format:
{
  "behaviors": [
    {"part": "drawer", "count": <int>, "motion": "linear", "axis": "Y", "row": <int>},
    {"part": "door", "count": <int>, "motion": "rotational", "axis": "Z", "row": <int>}
  ],
  "hidden_structure": {
    "has_back_panel": true,
    "has_bottom_panel": true,
    "has_internal_dividers": true,
    "body_is_enclosed": true,
    "drawers_have_depth": true,
    "drawer_sides": 5,
    "notes": "any additional structural requirements"
  },
  "hinge_sides": ["left", "right", "left"]
}
The key rule: if drawers exist, body MUST be enclosed (solid bottom, back, sides).
Each drawer = 5-sided box (open top). Knob is on opposite side of hinge.
Return ONLY the JSON.""",

    "claude_bodies": """Look at this image. Define the body list for 3D simulation.
Answer in EXACTLY this JSON format:
{
  "bodies": [
    {"name": "Carcass", "type": "joined", "material": "wood", "includes": "top, bottom, sides, back, dividers, legs"},
    {"name": "Drawer_0", "type": "separate", "material": "wood", "reason": "slides independently"},
    {"name": "Handle_0", "type": "separate", "material": "metal", "reason": "different material, on drawer"},
    {"name": "Door_0", "type": "separate", "material": "wood", "reason": "swings independently"},
    {"name": "Knob_0", "type": "separate", "material": "metal", "reason": "different material, on door"}
  ],
  "total_objects": <int>
}
Rules: moving parts = separate. Fixed parts = joined into carcass. Every drawer gets a handle. Every door gets a knob.
Return ONLY the JSON.""",

    "claude_hardware": """Look at this image. Describe hardware placement in detail.
Answer in EXACTLY this JSON format:
{
  "drawer_hardware": {
    "type": "bar_pull or knob or recessed",
    "position_on_face": "center or offset_top or offset_bottom",
    "z_ratio": 0.5
  },
  "door_hardware": {
    "type": "round_knob or bar_pull or ring",
    "knob_x_ratio": 0.35,
    "knob_z_ratio": 0.55
  },
  "door_hinge_sides": ["left", "right", "left"],
  "legs": {
    "count": 4,
    "shape": "square or round or tapered",
    "inset_from_corner_mm": 50
  }
}
knob_x_ratio: 0.0=left edge, 0.5=center, 1.0=right edge of the door.
knob_z_ratio: 0.0=bottom, 0.5=center, 1.0=top.
hinge side is OPPOSITE of where the knob is.
Return ONLY the JSON.""",
}


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
        config=types.GenerateContentConfig(max_output_tokens=2048, temperature=0.1),
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
    resp = client.messages.create(model=model, max_tokens=2048,
                                   messages=[{"role": "user", "content": content}])
    return resp.content[0].text

def parse_json_response(text):
    """Extract JSON from AI response, handling markdown fences."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return json.loads(text)


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
# BLENDER TEMPLATE — pre-tested, no AI code generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_cabinet_script(spec, output_usd, output_blend):
    """Generate Blender script from a merged spec using geometry_math.py positions."""
    from geometry_math import CabinetGrid

    # Extract from spec
    W = spec["dims"]["width"]
    D = spec["dims"]["depth"]
    H = spec["dims"]["height"]
    T = spec["dims"]["panel_t"]
    leg_h = spec["dims"]["leg_h"]
    row_heights = spec["dims"]["row_heights"]
    n_cols = spec["grid"]["columns"]
    n_rows = spec["grid"]["rows"]

    # Materials
    wood_rgb = spec["materials"]["primary_color_rgb"]
    wood_dark = spec["materials"]["primary_color_dark_rgb"]
    wood_rough = spec["materials"]["primary_roughness"]
    hw_rgb = spec["materials"]["hardware_color_rgb"]
    hw_rough = spec["materials"]["hardware_roughness"]

    # Hardware
    handle_len = spec["hardware"]["handle_length"]
    knob_d = spec["hardware"]["knob_diameter"]
    knob_x_ratio = spec["hardware"]["knob_x_ratio"]
    knob_z_ratio = spec["hardware"]["knob_z_ratio"]
    hinge_sides = spec["hardware"].get("hinge_sides", ["left"] * n_cols)

    # Row types
    row_types = spec["grid"]["row_types"]

    # Compute grid
    grid = CabinetGrid(
        width=W, depth=D, height=H - leg_h,
        columns=n_cols, rows=n_rows, panel_t=T,
        row_heights=row_heights, leg_height=leg_h,
    )

    # Build the Blender script from template
    lines = []
    lines.append("import bpy")
    lines.append("import math")
    lines.append("")
    lines.append("# Clear scene")
    lines.append("for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)")
    lines.append("for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)")
    lines.append("for m in list(bpy.data.materials): bpy.data.materials.remove(m)")
    lines.append("")

    # Materials
    lines.append("# Wood material")
    lines.append("wood = bpy.data.materials.new('Wood')")
    lines.append("wood.use_nodes = True")
    lines.append("_n = wood.node_tree.nodes; _l = wood.node_tree.links; _n.clear()")
    lines.append("_out = _n.new('ShaderNodeOutputMaterial')")
    lines.append("_bsdf = _n.new('ShaderNodeBsdfPrincipled')")
    lines.append(f"_bsdf.inputs['Roughness'].default_value = {wood_rough}")
    lines.append("_tc = _n.new('ShaderNodeTexCoord')")
    lines.append("_mp = _n.new('ShaderNodeMapping')")
    lines.append("_mp.inputs['Scale'].default_value = (3, 3, 25)")
    lines.append("_ns = _n.new('ShaderNodeTexNoise')")
    lines.append("_ns.inputs['Scale'].default_value = 5")
    lines.append("_ns.inputs['Detail'].default_value = 14")
    lines.append("_ns.inputs['Roughness'].default_value = 0.8")
    lines.append("_ramp = _n.new('ShaderNodeValToRGB')")
    lines.append("_ramp.color_ramp.elements[0].position = 0.3")
    lines.append(f"_ramp.color_ramp.elements[0].color = ({wood_dark[0]}, {wood_dark[1]}, {wood_dark[2]}, 1)")
    lines.append("_ramp.color_ramp.elements[1].position = 0.7")
    lines.append(f"_ramp.color_ramp.elements[1].color = ({wood_rgb[0]}, {wood_rgb[1]}, {wood_rgb[2]}, 1)")
    lines.append("_l.new(_tc.outputs['Object'], _mp.inputs['Vector'])")
    lines.append("_l.new(_mp.outputs['Vector'], _ns.inputs['Vector'])")
    lines.append("_l.new(_ns.outputs['Fac'], _ramp.inputs['Fac'])")
    lines.append("_l.new(_ramp.outputs['Color'], _bsdf.inputs['Base Color'])")
    lines.append("_l.new(_bsdf.outputs['BSDF'], _out.inputs['Surface'])")
    lines.append("")
    lines.append("# Metal material")
    lines.append("metal = bpy.data.materials.new('Metal')")
    lines.append("metal.use_nodes = True")
    lines.append("_n = metal.node_tree.nodes; _l = metal.node_tree.links; _n.clear()")
    lines.append("_out = _n.new('ShaderNodeOutputMaterial')")
    lines.append("_bsdf = _n.new('ShaderNodeBsdfPrincipled')")
    lines.append(f"_bsdf.inputs['Base Color'].default_value = ({hw_rgb[0]}, {hw_rgb[1]}, {hw_rgb[2]}, 1)")
    lines.append("_bsdf.inputs['Metallic'].default_value = 1.0")
    lines.append(f"_bsdf.inputs['Roughness'].default_value = {hw_rough}")
    lines.append("_l.new(_bsdf.outputs['BSDF'], _out.inputs['Surface'])")
    lines.append("")

    # Helper
    lines.append("def box(x, y, z, w, d, h):")
    lines.append("    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z), scale=(w, d, h))")
    lines.append("    o = bpy.context.active_object")
    lines.append("    bpy.ops.object.transform_apply(scale=True)")
    lines.append("    return o")
    lines.append("")

    # Carcass panels
    lines.append("# Carcass panels")
    lines.append("parts = []")
    for p in grid.carcass_panels():
        lines.append(f"parts.append(box({p['cx']:.6f}, {p['cy']:.6f}, {p['cz']:.6f}, {p['w']:.6f}, {p['d']:.6f}, {p['h']:.6f}))")

    # Legs
    lines.append("# Legs")
    for i, (lx, ly, lz) in enumerate(grid.leg_positions()):
        lines.append(f"parts.append(box({lx:.6f}, {ly:.6f}, {lz:.6f}, {grid.leg_width}, {grid.leg_width}, {grid.leg_height}))")

    # Join carcass
    lines.append("")
    lines.append("bpy.ops.object.select_all(action='DESELECT')")
    lines.append("for p in parts: p.select_set(True)")
    lines.append("bpy.context.view_layer.objects.active = parts[0]")
    lines.append("bpy.ops.object.join()")
    lines.append("carcass = bpy.context.active_object")
    lines.append("carcass.name = 'Carcass'")
    lines.append("carcass.data.materials.append(wood)")
    lines.append("bpy.ops.object.shade_smooth()")
    lines.append("")

    # Generate objects for each row
    for row in range(n_rows):
        rt = row_types[row] if row < len(row_types) else "unknown"

        if rt == "drawers":
            lines.append(f"# Row {row}: Drawers")
            DW_T = 0.012  # drawer wall thickness
            drawer_depth = (D - T) * 0.85

            for col in range(n_cols):
                cx = grid.col_center(col)
                cz = grid.row_center(row)
                rh = grid.row_height(row)
                rb = grid.row_bottom(row)
                cw = grid.col_w
                fw = cw - grid.gap * 2
                fh = rh - grid.gap * 2
                fy = grid.front_panel_y()

                lines.append(f"# Drawer {col}")
                lines.append(f"_dp = []")
                # Front
                lines.append(f"_dp.append(box({cx:.6f}, {fy:.6f}, {cz:.6f}, {fw:.6f}, {T:.6f}, {fh:.6f}))")
                # Bottom
                by = fy - T/2 - (drawer_depth - T)/2
                lines.append(f"_dp.append(box({cx:.6f}, {by:.6f}, {rb + grid.gap + DW_T/2:.6f}, {fw - 2*DW_T:.6f}, {drawer_depth - T:.6f}, {DW_T:.6f}))")
                # Left side
                lines.append(f"_dp.append(box({cx - fw/2 + DW_T/2:.6f}, {by:.6f}, {cz:.6f}, {DW_T:.6f}, {drawer_depth - T:.6f}, {fh - DW_T:.6f}))")
                # Right side
                lines.append(f"_dp.append(box({cx + fw/2 - DW_T/2:.6f}, {by:.6f}, {cz:.6f}, {DW_T:.6f}, {drawer_depth - T:.6f}, {fh - DW_T:.6f}))")
                # Back
                lines.append(f"_dp.append(box({cx:.6f}, {fy - drawer_depth + DW_T/2:.6f}, {cz:.6f}, {fw - 2*DW_T:.6f}, {DW_T:.6f}, {fh - DW_T:.6f}))")
                # Join
                lines.append("bpy.ops.object.select_all(action='DESELECT')")
                lines.append("for p in _dp: p.select_set(True)")
                lines.append("bpy.context.view_layer.objects.active = _dp[0]")
                lines.append("bpy.ops.object.join()")
                lines.append(f"bpy.context.active_object.name = 'Drawer_{col}'")
                lines.append("bpy.context.active_object.data.materials.append(wood)")
                lines.append("bpy.ops.object.shade_smooth()")
                lines.append("")

                # Handle
                px, py, pz = grid.pull_position(col, row)
                lines.append(f"box({px:.6f}, {py:.6f}, {pz:.6f}, {handle_len:.6f}, 0.012, 0.015)")
                lines.append(f"bpy.context.active_object.name = 'Handle_{col}'")
                lines.append("bpy.context.active_object.data.materials.append(metal)")
                lines.append("bpy.ops.object.shade_smooth()")
                lines.append("")

        elif rt == "doors":
            lines.append(f"# Row {row}: Doors")
            for col in range(n_cols):
                cx = grid.col_center(col)
                cz = grid.row_center(row)
                dw, dt, dh = grid.door_dims(col, row)
                fy = grid.front_panel_y()

                lines.append(f"box({cx:.6f}, {fy:.6f}, {cz:.6f}, {dw:.6f}, {dt:.6f}, {dh:.6f})")
                lines.append(f"bpy.context.active_object.name = 'Door_{col}'")
                lines.append("bpy.context.active_object.data.materials.append(wood)")
                lines.append("bpy.ops.object.shade_smooth()")
                lines.append("")

                # Knob
                hs = hinge_sides[col] if col < len(hinge_sides) else "left"
                # Knob on opposite side of hinge
                if hs == "left":
                    kx_ratio = knob_x_ratio  # toward right
                else:
                    kx_ratio = 1.0 - knob_x_ratio  # toward left

                kx, ky, kz = grid.knob_position(col, row,
                                                  x_offset_ratio=kx_ratio,
                                                  z_offset_ratio=knob_z_ratio)
                lines.append(f"bpy.ops.mesh.primitive_uv_sphere_add(radius={knob_d/2:.6f}, segments=16, ring_count=8, location=({kx:.6f}, {ky:.6f}, {kz:.6f}))")
                lines.append(f"bpy.context.active_object.name = 'Knob_{col}'")
                lines.append("bpy.context.active_object.data.materials.append(metal)")
                lines.append("bpy.ops.object.shade_smooth()")
                lines.append("")

    # Stats + export
    lines.append("# Stats")
    lines.append("all_objs = [o for o in bpy.data.objects]")
    lines.append("tv = sum(len(o.data.vertices) for o in all_objs if hasattr(o.data, 'vertices'))")
    lines.append("from mathutils import Vector")
    lines.append("bmin = Vector((1e9,1e9,1e9)); bmax = Vector((-1e9,-1e9,-1e9))")
    lines.append("for o in all_objs:")
    lines.append("    if not hasattr(o.data, 'vertices'): continue")
    lines.append("    for v in o.data.vertices:")
    lines.append("        w = o.matrix_world @ v.co")
    lines.append("        bmin = Vector((min(bmin.x,w.x), min(bmin.y,w.y), min(bmin.z,w.z)))")
    lines.append("        bmax = Vector((max(bmax.x,w.x), max(bmax.y,w.y), max(bmax.z,w.z)))")
    lines.append("d = bmax - bmin")
    lines.append("print(f'Objects: {len(all_objs)}')")
    lines.append("print(f'Vertices: {tv}')")
    lines.append("print(f'Dims: {d.x:.3f} x {d.y:.3f} x {d.z:.3f} m')")
    lines.append("for o in all_objs: print(f'  {o.name}: {[m.name for m in o.data.materials]}')")
    lines.append(f"bpy.ops.wm.usd_export(filepath='{output_usd}', export_materials=True)")
    lines.append(f"bpy.ops.wm.save_as_mainfile(filepath='{output_blend}')")
    lines.append("print('Saved')")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SPEC MERGER — combines 6 agent outputs into one spec
# ═══════════════════════════════════════════════════════════════════════════════

def merge_spec(results):
    """Merge 6 agent JSON outputs into a unified spec."""
    gt = results["gemini_type"]
    gd = results["gemini_dims"]
    gm = results["gemini_materials"]
    cb = results["claude_behavior"]
    cbo = results["claude_bodies"]
    ch = results["claude_hardware"]

    n_cols = gt["grid"]["columns"]
    n_rows = gt["grid"]["rows"]

    # Parse row types from row_contents
    row_types = []
    for rc in gt["grid"].get("row_contents", []):
        rc_lower = rc.lower()
        if "drawer" in rc_lower:
            row_types.append("drawers")
        elif "door" in rc_lower:
            row_types.append("doors")
        else:
            row_types.append("unknown")

    # Dimensions in meters
    W = gd["overall_width_mm"] / 1000
    D = gd["overall_depth_mm"] / 1000
    H = gd["overall_height_mm"] / 1000
    T = gd["panel_thickness_mm"] / 1000
    leg_h = gd.get("leg_height_mm", 0) / 1000

    # Row heights in meters
    row_heights_mm = gd.get("row_heights_mm", [])
    if not row_heights_mm or len(row_heights_mm) != n_rows:
        # Fallback: distribute evenly
        inner_h = H - leg_h - (n_rows + 1) * T
        row_heights_mm = [inner_h / n_rows * 1000] * n_rows
    row_heights = [rh / 1000 for rh in row_heights_mm]

    # Hardware
    handle_len = gd.get("handle_length_mm", 120) / 1000
    knob_d = gd.get("knob_diameter_mm", 25) / 1000

    hinge_sides = ch.get("door_hinge_sides", ["left", "right", "left"][:n_cols])
    knob_x_ratio = ch.get("door_hardware", {}).get("knob_x_ratio", 0.35)
    knob_z_ratio = ch.get("door_hardware", {}).get("knob_z_ratio", 0.55)

    return {
        "object_type": gt["object_type"],
        "manufacturing": gt["manufacturing"],
        "grid": {
            "columns": n_cols,
            "rows": n_rows,
            "row_types": row_types,
        },
        "dims": {
            "width": W,
            "depth": D,
            "height": H,
            "panel_t": T,
            "leg_h": leg_h,
            "row_heights": row_heights,
        },
        "materials": {
            "primary_color_rgb": gm.get("primary_color_rgb", [0.55, 0.35, 0.18]),
            "primary_color_dark_rgb": gm.get("primary_color_dark_rgb", [0.30, 0.18, 0.08]),
            "primary_roughness": gm.get("primary_roughness", 0.4),
            "hardware_color_rgb": gm.get("hardware_color_rgb", [0.7, 0.7, 0.72]),
            "hardware_roughness": gm.get("hardware_roughness", 0.25),
        },
        "hardware": {
            "handle_length": handle_len,
            "knob_diameter": knob_d,
            "knob_x_ratio": knob_x_ratio,
            "knob_z_ratio": knob_z_ratio,
            "hinge_sides": hinge_sides,
        },
        "behavior": cb,
        "bodies": cbo,
    }


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


def run_pipeline(image_path, api_keys, output_usd, output_blend):
    gkey = api_keys["gemini"]["api_key"]
    ckey = api_keys["anthropic"]["api_key"]

    # ══ PHASE 1: 6 parallel agents ══════════════════════════════════════
    print("\n" + "=" * 70)
    print("  PHASE 1: 6 parallel agents (3 Gemini + 3 Claude)")
    print("=" * 70)

    results = {}
    agents = [
        ("gemini_type",     call_gemini, gkey, BEST_GEMINI, PROMPTS["gemini_type"]),
        ("gemini_dims",     call_gemini, gkey, BEST_GEMINI, PROMPTS["gemini_dims"]),
        ("gemini_materials", call_gemini, gkey, BEST_GEMINI, PROMPTS["gemini_materials"]),
        ("claude_behavior", call_claude, ckey, BEST_CLAUDE, PROMPTS["claude_behavior"]),
        ("claude_bodies",   call_claude, ckey, BEST_CLAUDE, PROMPTS["claude_bodies"]),
        ("claude_hardware", call_claude, ckey, BEST_CLAUDE, PROMPTS["claude_hardware"]),
    ]

    t0 = time.time()
    threads = []
    for name, func, key, model, prompt in agents:
        t = threading.Thread(target=run_agent, args=(func, key, model, prompt, image_path, results, name))
        t.start()
        threads.append((name, t))

    for name, t in threads:
        t.join(timeout=120)

    phase1_time = time.time() - t0

    # Check results
    all_ok = True
    for name, _ in threads:
        r = results.get(name, {})
        if r.get("error"):
            print(f"  {name}: ERROR — {r['error']}")
            all_ok = False
        elif r.get("parsed"):
            print(f"  {name}: OK ({len(r['raw'])} chars)")
        else:
            print(f"  {name}: PARSE FAILED")
            print(f"    Raw: {r.get('raw', '')[:200]}")
            all_ok = False

    print(f"\n  Phase 1: {phase1_time:.1f}s (parallel)")

    if not all_ok:
        print("  Some agents failed. Aborting.")
        return None, results

    # ══ PHASE 2: Merge + Template (no API call) ═════════════════════════
    print("\n" + "=" * 70)
    print("  PHASE 2: Merge spec + generate script (deterministic)")
    print("=" * 70)

    t1 = time.time()

    parsed = {name: results[name]["parsed"] for name in results}
    spec = merge_spec(parsed)

    # Print spec summary
    print(f"  Type: {spec['object_type']}")
    print(f"  Grid: {spec['grid']['columns']}×{spec['grid']['rows']} ({spec['grid']['row_types']})")
    print(f"  Dims: {spec['dims']['width']*1000:.0f}×{spec['dims']['depth']*1000:.0f}×{spec['dims']['height']*1000:.0f}mm")
    print(f"  Materials: wood={spec['materials']['primary_color_rgb']}, metal={spec['materials']['hardware_color_rgb']}")

    # Generate script from template
    script = generate_cabinet_script(spec, output_usd, output_blend)

    phase2_time = time.time() - t1
    print(f"\n  Phase 2: {phase2_time:.3f}s (no API call)")
    print(f"  Script: {len(script.splitlines())} lines")
    print(f"  Total: {phase1_time + phase2_time:.1f}s")

    return script, {"spec": spec, "agents": {k: {"raw": v["raw"]} for k, v in results.items()}}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Template-Based Multi-Agent Asset Generator")
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
    print("  TEMPLATE-BASED MULTI-AGENT ASSET GENERATOR")
    print(f"  Image:   {image_path}")
    print(f"  Output:  {output_usd}")
    print(f"  Gemini:  {BEST_GEMINI} (×3 parallel)")
    print(f"  Claude:  {BEST_CLAUDE} (×3 parallel)")
    print("=" * 70)

    api_keys = load_api_keys()
    t0 = time.time()

    script, log = run_pipeline(image_path, api_keys, output_usd, output_blend)
    if not script:
        print("\n  Pipeline failed.")
        return

    # Save
    with open(os.path.join(output_dir, "spec.json"), "w") as f:
        json.dump(log.get("spec", {}), f, indent=2)
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
