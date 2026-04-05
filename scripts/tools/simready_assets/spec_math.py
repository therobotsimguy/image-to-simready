#!/usr/bin/env python3
"""Spec Math — Deterministic validation and computation for asset specs.

Used by all three paths:
  Path A: validate AI agent outputs
  Path B: validate vision measurements
  Path C: validate final reconciled spec

Every function is pure math — no AI, no randomness, no estimation.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# PATH A: AI output validation
# ═══════════════════════════════════════════════════════════════════════════════

def validate_ai_spec(parsed):
    """Validate Path A's 6 agent outputs against geometric constraints.

    Returns: (is_valid, fixes_applied, warnings)
    """
    fixes = []
    warnings = []

    gt = parsed.get("gemini_type", {})
    gd = parsed.get("gemini_dims", {})
    cb = parsed.get("claude_behavior", {})
    cbo = parsed.get("claude_bodies", {})
    ch = parsed.get("claude_hardware", {})

    n_cols = gt.get("grid", {}).get("columns", 0)
    n_rows = gt.get("grid", {}).get("rows", 0)
    row_contents = gt.get("grid", {}).get("row_contents", [])

    # ── Count consistency ──
    # Number of drawers should match drawer rows × columns
    n_drawer_rows = sum(1 for rc in row_contents if "drawer" in rc.lower())
    n_door_rows = sum(1 for rc in row_contents if "door" in rc.lower())
    expected_drawers = n_drawer_rows * n_cols
    expected_doors = n_door_rows * n_cols

    behaviors = cb.get("behaviors", [])
    for b in behaviors:
        if b.get("part") == "drawer" and b.get("count", 0) != expected_drawers:
            fixes.append(f"claude_behavior drawer count {b['count']} → {expected_drawers} (grid says {n_drawer_rows} rows × {n_cols} cols)")
            b["count"] = expected_drawers
        if b.get("part") == "door" and b.get("count", 0) != expected_doors:
            fixes.append(f"claude_behavior door count {b['count']} → {expected_doors} (grid says {n_door_rows} rows × {n_cols} cols)")
            b["count"] = expected_doors

    # ── Dimension sanity ──
    W = gd.get("overall_width_mm", 0)
    D = gd.get("overall_depth_mm", 0)
    H = gd.get("overall_height_mm", 0)
    T = gd.get("panel_thickness_mm", 0)
    leg_h = gd.get("leg_height_mm", 0)

    if W <= 0 or D <= 0 or H <= 0:
        warnings.append(f"Invalid dimensions: {W}×{D}×{H}mm")

    if T <= 0:
        gd["panel_thickness_mm"] = 20
        fixes.append(f"panel_thickness was {T}mm → 20mm (default)")
        T = 20

    # Panel thickness should be < 10% of smallest dimension
    min_dim = min(W, D, H)
    if min_dim > 0 and T > min_dim * 0.1:
        old_t = T
        T = round(min_dim * 0.05)
        gd["panel_thickness_mm"] = T
        fixes.append(f"panel_thickness {old_t}mm too thick → {T}mm (5% of min dim)")

    # ── Row heights must sum correctly ──
    row_heights = gd.get("row_heights_mm", [])
    if row_heights and len(row_heights) == n_rows:
        inner_h = H - leg_h - (n_rows + 1) * T
        actual_sum = sum(row_heights)
        if abs(actual_sum - inner_h) > 5:  # >5mm discrepancy
            # Rescale to fit
            scale = inner_h / actual_sum if actual_sum > 0 else 1
            new_heights = [round(rh * scale, 1) for rh in row_heights]
            fixes.append(f"row_heights sum {actual_sum:.0f}mm ≠ inner height {inner_h:.0f}mm → rescaled to {new_heights}")
            gd["row_heights_mm"] = new_heights

    # ── Hardware count must match grid ──
    bodies = cbo.get("bodies", [])
    n_handles = sum(1 for b in bodies if "handle" in b.get("name", "").lower())
    n_knobs = sum(1 for b in bodies if "knob" in b.get("name", "").lower())

    if n_handles != expected_drawers:
        warnings.append(f"Handle count ({n_handles}) ≠ drawer count ({expected_drawers})")
    if n_knobs != expected_doors:
        warnings.append(f"Knob count ({n_knobs}) ≠ door count ({expected_doors})")

    # ── Hinge sides must match door count ──
    hinge_sides = ch.get("door_hinge_sides", [])
    if len(hinge_sides) != n_cols:
        old = hinge_sides
        # Default: alternate left/right
        hinge_sides = ["left" if i % 2 == 0 else "right" for i in range(n_cols)]
        ch["door_hinge_sides"] = hinge_sides
        fixes.append(f"hinge_sides length {len(old)} ≠ {n_cols} cols → {hinge_sides}")

    is_valid = len(warnings) == 0
    return is_valid, fixes, warnings


# ═══════════════════════════════════════════════════════════════════════════════
# PATH B: Vision measurement validation
# ═══════════════════════════════════════════════════════════════════════════════

def validate_vision_spec(vision_data):
    """Validate Path B's vision measurements against geometric constraints.

    Returns: (is_valid, fixes_applied, warnings)
    """
    fixes = []
    warnings = []

    counts = vision_data.get("counts", {})
    components = vision_data.get("components", [])
    row_ratios = vision_data.get("row_ratios", {})

    # ── Hardware must pair with moving parts ──
    n_handles = counts.get("handle", 0)
    n_knobs = counts.get("knob", 0)
    n_drawers = counts.get("drawer", 0)
    n_doors = counts.get("door", 0)

    if n_handles > 0 and n_drawers > 0 and n_handles != n_drawers:
        warnings.append(f"Handle count ({n_handles}) ≠ drawer count ({n_drawers})")
    if n_knobs > 0 and n_doors > 0 and n_knobs != n_doors:
        warnings.append(f"Knob count ({n_knobs}) ≠ door count ({n_doors})")

    # ── Row ratios must sum to ~1.0 ──
    if row_ratios:
        total = sum(row_ratios.values())
        if abs(total - 1.0) > 0.05:
            # Renormalize
            for k in row_ratios:
                row_ratios[k] = round(row_ratios[k] / total, 3)
            fixes.append(f"Row ratios summed to {total:.3f} → renormalized to 1.0")

    # ── Component dimensions should be consistent within type ──
    doors = [c for c in components if c.get("label") == "door" and c.get("confirmed")]
    drawers = [c for c in components if c.get("label") == "drawer" and c.get("confirmed")]

    if len(doors) >= 2:
        heights = [c.get("pixel_height", 0) for c in doors]
        mean_h = sum(heights) / len(heights)
        for i, h in enumerate(heights):
            if mean_h > 0 and abs(h - mean_h) / mean_h > 0.3:  # >30% deviation
                warnings.append(f"Door {i} height ({h}px) deviates >30% from mean ({mean_h:.0f}px)")

    if len(drawers) >= 2:
        heights = [c.get("pixel_height", 0) for c in drawers]
        mean_h = sum(heights) / len(heights)
        for i, h in enumerate(heights):
            if mean_h > 0 and abs(h - mean_h) / mean_h > 0.3:
                warnings.append(f"Drawer {i} height ({h}px) deviates >30% from mean ({mean_h:.0f}px)")

    # ── Depth consistency ──
    depth_consistency = vision_data.get("depth_consistency")
    if depth_consistency is not None and depth_consistency < 0.7:
        warnings.append(f"Low depth consistency ({depth_consistency}) — DepthPro and DA3 disagree")

    is_valid = len(warnings) == 0
    return is_valid, fixes, warnings


# ═══════════════════════════════════════════════════════════════════════════════
# PATH C: Final spec validation (after AI reconciliation)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_final_spec(spec):
    """Validate the final merged spec before template generation.

    This is the last math gate — catches anything the AI reconciliation got wrong.
    Returns: (is_valid, fixes_applied, warnings)
    """
    fixes = []
    warnings = []

    W = spec["dims"]["width"]
    D = spec["dims"]["depth"]
    H = spec["dims"]["height"]
    T = spec["dims"]["panel_t"]
    leg_h = spec["dims"]["leg_h"]
    n_cols = spec["grid"]["columns"]
    n_rows = spec["grid"]["rows"]
    row_heights = spec["dims"]["row_heights"]

    # ── Row heights must fit inside carcass ──
    inner_h = H - leg_h - (n_rows + 1) * T
    actual_sum = sum(row_heights)

    if abs(actual_sum - inner_h) > 0.005:  # >5mm error
        scale = inner_h / actual_sum if actual_sum > 0 else 1
        new_heights = [rh * scale for rh in row_heights]
        fixes.append(f"row_heights sum {actual_sum*1000:.0f}mm → {inner_h*1000:.0f}mm (rescaled)")
        spec["dims"]["row_heights"] = new_heights

    # ── All dimensions must be positive ──
    for key in ["width", "depth", "height", "panel_t"]:
        if spec["dims"][key] <= 0:
            warnings.append(f"dims.{key} = {spec['dims'][key]} (must be positive)")

    # ── Row heights must all be positive ──
    for i, rh in enumerate(spec["dims"]["row_heights"]):
        if rh <= 0:
            warnings.append(f"row_height[{i}] = {rh*1000:.0f}mm (must be positive)")

    # ── Column width must be positive ──
    col_w = (W - 2 * T - (n_cols - 1) * T) / n_cols if n_cols > 0 else 0
    if col_w <= 0:
        warnings.append(f"Column width {col_w*1000:.0f}mm (must be positive — too many columns or panel too thick)")

    # ── Hardware counts vs grid ──
    n_drawer_rows = sum(1 for rt in spec["grid"]["row_types"] if rt == "drawers")
    n_door_rows = sum(1 for rt in spec["grid"]["row_types"] if rt == "doors")
    expected_drawers = n_drawer_rows * n_cols
    expected_doors = n_door_rows * n_cols

    hinge_sides = spec["hardware"].get("hinge_sides", [])
    if len(hinge_sides) != n_cols:
        hinge_sides = ["left" if i % 2 == 0 else "right" for i in range(n_cols)]
        spec["hardware"]["hinge_sides"] = hinge_sides
        fixes.append(f"hinge_sides adjusted to {n_cols} columns: {hinge_sides}")

    # ── Aspect ratio sanity (furniture shouldn't be paper-thin or absurdly deep) ──
    if D > 0 and W / D > 10:
        warnings.append(f"Aspect ratio W/D = {W/D:.1f} (unusually wide and shallow)")
    if H > 0 and W / H > 5:
        warnings.append(f"Aspect ratio W/H = {W/H:.1f} (unusually wide and short)")

    is_valid = len(warnings) == 0
    return is_valid, fixes, warnings


# ═══════════════════════════════════════════════════════════════════════════════
# RECONCILIATION MATH — used by Path C's AI agent
# ═══════════════════════════════════════════════════════════════════════════════

def compute_confidence_scores(ai_spec, vision_data):
    """Compute per-field confidence scores based on A vs B agreement.

    Returns dict of field → {a_value, b_value, confidence, recommended}.
    """
    scores = {}

    # ── Counts ──
    ai_grid = ai_spec.get("grid", {})
    n_cols = ai_grid.get("columns", 0)
    row_types = ai_grid.get("row_types", [])

    ai_drawers = sum(1 for rt in row_types if rt == "drawers") * n_cols
    ai_doors = sum(1 for rt in row_types if rt == "doors") * n_cols

    v_counts = vision_data.get("counts", {})
    v_drawers = v_counts.get("drawer", 0)
    v_doors = v_counts.get("door", 0)
    v_handles = v_counts.get("handle", 0)
    v_knobs = v_counts.get("knob", 0)

    # Drawer count: if vision handles match vision drawers, vision is more trustworthy
    drawer_conf = 1.0 if ai_drawers == v_drawers else 0.5
    if v_handles == v_drawers and v_drawers > 0:
        drawer_conf = min(drawer_conf + 0.3, 1.0)  # handle=drawer cross-validation

    scores["drawer_count"] = {
        "a": ai_drawers, "b": v_drawers,
        "confidence": drawer_conf,
        "recommended": ai_drawers if drawer_conf >= 0.8 else v_drawers,
        "reason": "A=B" if ai_drawers == v_drawers else f"A≠B, handles={v_handles}",
    }

    door_conf = 1.0 if ai_doors == v_doors else 0.5
    if v_knobs == v_doors and v_doors > 0:
        door_conf = min(door_conf + 0.3, 1.0)

    scores["door_count"] = {
        "a": ai_doors, "b": v_doors,
        "confidence": door_conf,
        "recommended": ai_doors if door_conf >= 0.8 else v_doors,
        "reason": "A=B" if ai_doors == v_doors else f"A≠B, knobs={v_knobs}",
    }

    # ── Row ratios ──
    ai_heights = ai_spec.get("dims", {}).get("row_heights", [])
    v_ratios = vision_data.get("row_ratios", {})

    if ai_heights and v_ratios:
        ai_total = sum(ai_heights)
        if ai_total > 0:
            ai_ratios = {
                rt: h / ai_total
                for rt, h in zip(row_types, ai_heights)
            }
        else:
            ai_ratios = {}

        # Compare ratios
        for rt in set(list(ai_ratios.keys()) + [k.replace("_ratio", "") for k in v_ratios]):
            a_ratio = ai_ratios.get(rt, 0)
            b_key = f"{rt}_ratio"
            b_ratio = v_ratios.get(b_key, 0)

            if a_ratio > 0 and b_ratio > 0:
                diff = abs(a_ratio - b_ratio)
                conf = max(0, 1.0 - diff * 3)  # penalize large differences
                scores[f"{rt}_ratio"] = {
                    "a": round(a_ratio, 3), "b": round(b_ratio, 3),
                    "confidence": round(conf, 3),
                    "recommended": round((a_ratio + b_ratio) / 2, 3),  # average as default
                    "reason": f"diff={diff:.3f}",
                }

    return scores


def build_reconciliation_context(ai_spec, vision_data, confidence_scores):
    """Build a structured text summary for the AI reconciliation agent.

    This gives Gemini/Claude all the data + math analysis to make final decisions.
    """
    lines = [
        "# RECONCILIATION DATA",
        "",
        "## Path A (AI Agents) Results:",
        f"  Object type: {ai_spec.get('object_type', '?')}",
        f"  Grid: {ai_spec.get('grid', {}).get('columns', '?')}×{ai_spec.get('grid', {}).get('rows', '?')}",
        f"  Row types: {ai_spec.get('grid', {}).get('row_types', '?')}",
        f"  Dimensions: {ai_spec.get('dims', {}).get('width', 0)*1000:.0f}×{ai_spec.get('dims', {}).get('depth', 0)*1000:.0f}×{ai_spec.get('dims', {}).get('height', 0)*1000:.0f}mm",
        f"  Row heights: {[round(h*1000) for h in ai_spec.get('dims', {}).get('row_heights', [])]}mm",
        f"  Materials: primary RGB={ai_spec.get('materials', {}).get('primary_color_rgb', '?')}, "
        f"hardware RGB={ai_spec.get('materials', {}).get('hardware_color_rgb', '?')}",
        f"  Primary roughness: {ai_spec.get('materials', {}).get('primary_roughness', '?')}",
        f"  Hardware roughness: {ai_spec.get('materials', {}).get('hardware_roughness', '?')}",
        "",
        "## Path B (Vision Stack) Results:",
        f"  Confirmed counts: {vision_data.get('counts', {})}",
        f"  Measured dims: {vision_data.get('overall_dims', {})}",
        f"  Row ratios: {vision_data.get('row_ratios', {})}",
        f"  Depth consistency: {vision_data.get('depth_consistency', 'N/A')}",
        f"  Model status: {vision_data.get('model_status', {})}",
    ]

    # Sampled colors from actual pixels
    sampled = vision_data.get("sampled_colors", {})
    if sampled:
        lines.append("")
        lines.append("  ### Pixel-Sampled Colors (from SAM3 masks × original image):")
        for label, cdata in sampled.items():
            metal = "METALLIC (low variance)" if cdata.get("is_metallic") else "TEXTURED (high variance, likely wood/fabric)"
            lines.append(f"    {label}: avg RGB={cdata['avg_rgb']}, "
                         f"variance={cdata.get('color_variance', '?')}, {metal}, "
                         f"sampled from {cdata.get('sample_count', '?')} instances")

    # Spatial layout
    spatial = vision_data.get("spatial_layout", {})
    if spatial:
        lines.append("")
        lines.append(f"  ### Spatial Layout (from pixel Y positions):")
        lines.append(f"    Top row: {spatial.get('top_row', '?')} (avg Y={spatial.get('avg_drawer_y_px', spatial.get('avg_door_y_px', '?'))}px)")
        lines.append(f"    Bottom row: {spatial.get('bottom_row', '?')} (avg Y={spatial.get('avg_door_y_px', spatial.get('avg_drawer_y_px', '?'))}px)")

    # Per-type measured dimensions
    measured = vision_data.get("measured_by_type", {})
    if measured:
        lines.append("")
        lines.append("  ### Per-Component Measured Dimensions (from depth + pixel size):")
        for label, mdata in measured.items():
            lines.append(f"    {label}: {mdata['avg_width_mm']:.0f}×{mdata['avg_height_mm']:.0f}mm "
                         f"(averaged from {mdata['count']} instances)")

    lines.append("")
    lines.append("## Math Analysis (confidence scores):")

    for field, data in confidence_scores.items():
        lines.append(f"  {field}: A={data['a']}, B={data['b']}, "
                     f"confidence={data['confidence']}, "
                     f"recommended={data['recommended']} ({data['reason']})")

    return "\n".join(lines)
