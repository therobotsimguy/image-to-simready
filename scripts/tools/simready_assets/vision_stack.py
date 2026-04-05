#!/usr/bin/env python3
"""Vision Stack — Path B of the multi-agent asset generator.

Runs 4 vision models in parallel, then reconciles with deterministic math:
  1. Grounding DINO: open-vocabulary detection → labeled boxes + counts
  2. SAM3: auto segmentation → pixel masks
  3. DepthPro: metric monocular depth → depth map in meters + focal length
  4. DepthAnything3: relative depth → cross-validation

Math reconciliation:
  - DINO boxes + SAM3 masks → overlap matching → confirmed components
  - Confirmed components × depth maps → real-world dimensions (meters)
"""

import os
import sys
import time
import threading
import numpy as np
from PIL import Image

_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOLS_DIR = os.path.dirname(_DIR)
_V3_MODELS_DIR = os.path.join(_TOOLS_DIR, "v3", "models")
_MODELS_DIR = os.path.join(_TOOLS_DIR, "models")

# Grounding DINO paths
DINO_CONFIG = os.path.join(_MODELS_DIR, "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py")
DINO_WEIGHTS = os.path.join(_MODELS_DIR, "GroundingDINO/weights/groundingdino_swint_ogc.pth")

# DepthPro paths
DEPTH_PRO_DIR = os.path.join(_V3_MODELS_DIR, "ml-depth-pro")
DEPTH_PRO_CKPT = os.path.join(DEPTH_PRO_DIR, "checkpoints", "depth_pro.pt")

# SAM3 paths
SAM3_DIR = os.path.join(_V3_MODELS_DIR, "sam3")
SAM3_BPE = os.path.join(SAM3_DIR, "sam3", "assets", "bpe_simple_vocab_16e6.txt.gz")


# ═══════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL MODEL RUNNERS (each runs in its own thread)
# ═══════════════════════════════════════════════════════════════════════════════

def run_dino(image_path, results, box_threshold=0.30, text_threshold=0.25):
    """Grounding DINO: open-vocabulary detection."""
    try:
        import torch
        from groundingdino.util.inference import load_model, load_image, predict

        model = load_model(DINO_CONFIG, DINO_WEIGHTS)
        _, image = load_image(image_path)

        prompt = "drawer . cabinet door . metal bar handle . round metal knob"

        with torch.no_grad():
            boxes, logits, phrases = predict(
                model=model, image=image, caption=prompt,
                box_threshold=box_threshold, text_threshold=text_threshold,
            )

        detections = []
        for box, logit, phrase in zip(boxes, logits, phrases):
            area = float(box[2] * box[3])
            if area < 0.5:  # filter full-image false positives
                detections.append({
                    "label": phrase,
                    "confidence": float(logit),
                    "box_cxcywh": box.tolist(),  # center-x, center-y, width, height (normalized)
                })

        # Clean up GPU memory
        del model
        torch.cuda.empty_cache()

        results["dino"] = {"status": "success", "detections": detections}
    except Exception as e:
        results["dino"] = {"status": "error", "error": str(e)}


def run_sam3(image_path, results):
    """SAM3: auto segmentation (no prompts, visual-only)."""
    try:
        import torch

        if SAM3_DIR not in sys.path:
            sys.path.insert(0, SAM3_DIR)

        from sam3 import build_sam3_image_model
        from sam3.model.sam3_image_processor import Sam3Processor

        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

        with torch.autocast("cuda", dtype=torch.bfloat16):
            model = build_sam3_image_model(bpe_path=SAM3_BPE)
            processor = Sam3Processor(model, confidence_threshold=0.3)

            image = Image.open(image_path).convert("RGB")
            width, height = image.size
            state = processor.set_image(image)

            # Use text prompts for furniture components
            component_prompts = [
                "drawer", "cabinet door", "handle", "knob",
                "cabinet body", "leg",
            ]

            masks_out = []
            for prompt_text in component_prompts:
                processor.reset_all_prompts(state)
                state = processor.set_text_prompt(state=state, prompt=prompt_text)

                scores = state.get("scores", torch.tensor([]))
                boxes = state.get("boxes", torch.tensor([]))
                masks = state.get("masks", torch.tensor([]))

                if len(scores) > 0:
                    for i in range(len(scores)):
                        score = float(scores[i])
                        if score < 0.3:
                            continue
                        box = boxes[i].cpu().tolist() if len(boxes) > i else None
                        mask = masks[i].cpu().numpy() if len(masks) > i else None
                        masks_out.append({
                            "label": prompt_text,
                            "score": score,
                            "bbox": box,  # [x1, y1, x2, y2] in pixel coords
                            "mask_shape": mask.shape if mask is not None else None,
                            "mask_area": int(mask.sum()) if mask is not None else 0,
                            "mask": mask,
                        })

        # Clean up GPU memory
        del model, processor
        torch.cuda.empty_cache()

        results["sam3"] = {
            "status": "success",
            "masks": masks_out,
            "image_size": (width, height),
        }
    except Exception as e:
        results["sam3"] = {"status": "error", "error": str(e)}


def run_depth_pro(image_path, results):
    """DepthPro: metric monocular depth estimation."""
    try:
        import torch

        if DEPTH_PRO_DIR not in sys.path:
            sys.path.insert(0, DEPTH_PRO_DIR)

        import depth_pro
        from depth_pro.depth_pro import DEFAULT_MONODEPTH_CONFIG_DICT
        from dataclasses import replace

        config = replace(DEFAULT_MONODEPTH_CONFIG_DICT, checkpoint_uri=DEPTH_PRO_CKPT)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model, transform = depth_pro.create_model_and_transforms(config=config, device=device)
        model.eval()

        image = Image.open(image_path).convert("RGB")
        img_w, img_h = image.size
        input_tensor = transform(image).to(device)

        with torch.no_grad():
            prediction = model.infer(input_tensor)

        depth_map = prediction["depth"].cpu().numpy()  # (H, W) in meters
        focal_px = prediction.get("focallength_px", None)
        if focal_px is not None:
            focal_px = float(focal_px)

        # Clean up GPU memory
        del model
        torch.cuda.empty_cache()

        results["depth_pro"] = {
            "status": "success",
            "depth_map": depth_map,
            "focal_px": focal_px,
            "depth_shape": depth_map.shape,
            "image_size": (img_w, img_h),
            "depth_range": (float(depth_map.min()), float(depth_map.max())),
        }
    except Exception as e:
        results["depth_pro"] = {"status": "error", "error": str(e)}


def run_depth_anything(image_path, results):
    """DepthAnything3: relative depth estimation for cross-validation."""
    try:
        import torch

        da3_dir = os.path.join(_V3_MODELS_DIR, "depth-anything-3")
        if da3_dir not in sys.path:
            sys.path.insert(0, da3_dir)

        from depth_anything_3.api import DepthAnything3

        model = DepthAnything3.from_pretrained("depth-anything/DA3-LARGE")
        model = model.eval()
        if torch.cuda.is_available():
            model = model.cuda()

        image = Image.open(image_path)
        prediction = model.inference([image])

        da_depth = None
        if hasattr(prediction, "depth") and prediction.depth is not None:
            da_depth = prediction.depth[0]
            if hasattr(da_depth, "cpu"):
                da_depth = da_depth.cpu().numpy()
            else:
                da_depth = np.array(da_depth)
        elif hasattr(prediction, "disp") and prediction.disp is not None:
            da_depth = prediction.disp[0]
            if hasattr(da_depth, "cpu"):
                da_depth = da_depth.cpu().numpy()
            else:
                da_depth = np.array(da_depth)

        # Clean up GPU memory
        del model
        torch.cuda.empty_cache()

        if da_depth is not None:
            results["depth_anything"] = {
                "status": "success",
                "depth_map": da_depth,
                "depth_shape": da_depth.shape,
                "depth_range": (float(da_depth.min()), float(da_depth.max())),
            }
        else:
            results["depth_anything"] = {"status": "error", "error": "No depth output"}
    except Exception as e:
        results["depth_anything"] = {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# MATH RECONCILIATION — combines all 4 model outputs
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_label(label):
    """Normalize detection labels to canonical names."""
    label = label.lower()
    if "knob" in label:
        return "knob"
    elif "handle" in label or "pull" in label:
        return "handle"
    elif "door" in label:
        return "door"
    elif "drawer" in label:
        return "drawer"
    elif "leg" in label:
        return "leg"
    elif "body" in label or "carcass" in label:
        return "body"
    return label


def _iou_box_mask(box_cxcywh, mask, img_w, img_h, mask_h, mask_w):
    """Compute IoU between a DINO box (normalized cxcywh) and a SAM3 mask."""
    # Convert DINO box to pixel coords
    cx, cy, w, h = box_cxcywh
    x1 = int((cx - w / 2) * img_w)
    y1 = int((cy - h / 2) * img_h)
    x2 = int((cx + w / 2) * img_w)
    y2 = int((cy + h / 2) * img_h)

    # Scale to mask resolution
    sx = mask_w / img_w
    sy = mask_h / img_h
    mx1, my1 = int(x1 * sx), int(y1 * sy)
    mx2, my2 = int(x2 * sx), int(y2 * sy)
    mx1, my1 = max(0, mx1), max(0, my1)
    mx2, my2 = min(mask_w, mx2), min(mask_h, my2)

    # Create box mask
    box_mask = np.zeros((mask_h, mask_w), dtype=bool)
    box_mask[my1:my2, mx1:mx2] = True

    # Handle multi-dim SAM masks (take first channel if needed)
    m = mask
    while m.ndim > 2:
        m = m[0]

    m_bool = m > 0.5

    intersection = np.logical_and(box_mask, m_bool).sum()
    union = np.logical_or(box_mask, m_bool).sum()

    if union == 0:
        return 0.0
    return float(intersection / union)


def _dino_box_to_pixel_bbox(box_cxcywh, img_w, img_h):
    """Convert DINO normalized cxcywh to pixel [x1, y1, x2, y2]."""
    cx, cy, w, h = box_cxcywh
    x1 = int((cx - w / 2) * img_w)
    y1 = int((cy - h / 2) * img_h)
    x2 = int((cx + w / 2) * img_w)
    y2 = int((cy + h / 2) * img_h)
    return [x1, y1, x2, y2]


def reconcile(results, image_path):
    """Reconcile outputs from all 4 vision models using math."""
    image = Image.open(image_path).convert("RGB")
    img_w, img_h = image.size

    dino = results.get("dino", {})
    sam3 = results.get("sam3", {})
    dp = results.get("depth_pro", {})
    da = results.get("depth_anything", {})

    components = []
    model_status = {
        "dino": dino.get("status", "missing"),
        "sam3": sam3.get("status", "missing"),
        "depth_pro": dp.get("status", "missing"),
        "depth_anything": da.get("status", "missing"),
    }

    # ── Step 1: DINO boxes + SAM3 masks → overlap matching ──────────────
    dino_dets = dino.get("detections", [])
    sam3_masks = sam3.get("masks", [])

    for det in dino_dets:
        label = _normalize_label(det["label"])
        box = det["box_cxcywh"]
        conf = det["confidence"]
        pixel_bbox = _dino_box_to_pixel_bbox(box, img_w, img_h)

        comp = {
            "label": label,
            "dino_confidence": conf,
            "pixel_bbox": pixel_bbox,
            "pixel_width": pixel_bbox[2] - pixel_bbox[0],
            "pixel_height": pixel_bbox[3] - pixel_bbox[1],
            "sam3_match": None,
            "sam3_iou": 0.0,
        }

        # Find best matching SAM3 mask by IoU
        best_iou = 0.0
        best_mask_idx = -1
        for i, sm in enumerate(sam3_masks):
            if sm.get("mask") is None:
                continue
            mask = sm["mask"]
            while mask.ndim > 2:
                mask = mask[0]
            mask_h, mask_w = mask.shape
            iou = _iou_box_mask(box, sm["mask"], img_w, img_h, mask_h, mask_w)
            if iou > best_iou:
                best_iou = iou
                best_mask_idx = i

        if best_iou > 0.15:  # minimum overlap threshold
            comp["sam3_match"] = sam3_masks[best_mask_idx]["label"]
            comp["sam3_iou"] = round(best_iou, 3)
            comp["sam3_score"] = sam3_masks[best_mask_idx]["score"]
            comp["confirmed"] = True
        else:
            comp["confirmed"] = conf > 0.4  # DINO-only if confident enough

        components.append(comp)

    # ── Step 2: Measure dimensions using depth maps ─────────────────────
    dp_depth = dp.get("depth_map")
    dp_focal = dp.get("focal_px")
    da_depth = da.get("depth_map")

    for comp in components:
        bbox = comp["pixel_bbox"]
        px_w = comp["pixel_width"]
        px_h = comp["pixel_height"]

        # DepthPro: metric depth → real-world size
        if dp_depth is not None and dp_focal and dp_focal > 0:
            dp_h, dp_w = dp_depth.shape
            # Scale bbox to depth map resolution
            sx, sy = dp_w / img_w, dp_h / img_h
            dx1 = max(0, int(bbox[0] * sx))
            dy1 = max(0, int(bbox[1] * sy))
            dx2 = min(dp_w, int(bbox[2] * sx))
            dy2 = min(dp_h, int(bbox[3] * sy))

            roi = dp_depth[dy1:dy2, dx1:dx2]
            if roi.size > 0:
                avg_depth = float(np.median(roi))  # median is more robust than mean
                comp["depth_m"] = round(avg_depth, 4)
                comp["measured_width_m"] = round(px_w * avg_depth / dp_focal, 4)
                comp["measured_height_m"] = round(px_h * avg_depth / dp_focal, 4)

        # DepthAnything: cross-validate depth ordering
        if da_depth is not None:
            da_h, da_w = da_depth.shape
            cx = int((bbox[0] + bbox[2]) / 2 * da_w / img_w)
            cy = int((bbox[1] + bbox[3]) / 2 * da_h / img_h)
            cx, cy = min(da_w - 1, max(0, cx)), min(da_h - 1, max(0, cy))
            comp["da_relative_depth"] = float(da_depth[cy, cx])

    # ── Step 3: Sample pixel colors from image using bounding boxes ──────
    img_array = np.array(image)  # (H, W, 3) RGB uint8

    for comp in components:
        bbox = comp["pixel_bbox"]
        x1, y1, x2, y2 = bbox
        # Clamp to image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(img_w, x2), min(img_h, y2)

        if x2 > x1 and y2 > y1:
            roi_pixels = img_array[y1:y2, x1:x2]  # (h, w, 3)

            # Check if we have a SAM3 mask for more precise sampling
            best_mask = None
            if comp.get("sam3_iou", 0) > 0.15:
                for sm in sam3_masks:
                    if sm.get("mask") is not None and sm.get("label") == comp.get("sam3_match"):
                        m = sm["mask"]
                        while m.ndim > 2:
                            m = m[0]
                        best_mask = m
                        break

            if best_mask is not None:
                # Sample only within the mask
                mask_h, mask_w = best_mask.shape
                # Resize mask region to match bbox
                from PIL import Image as PILImage
                mask_roi = best_mask[
                    max(0, int(y1 * mask_h / img_h)):min(mask_h, int(y2 * mask_h / img_h)),
                    max(0, int(x1 * mask_w / img_w)):min(mask_w, int(x2 * mask_w / img_w)),
                ]
                if mask_roi.size > 0 and roi_pixels.shape[0] > 0 and roi_pixels.shape[1] > 0:
                    # Resize mask to roi size
                    mask_pil = PILImage.fromarray((mask_roi > 0.5).astype(np.uint8) * 255)
                    mask_pil = mask_pil.resize((roi_pixels.shape[1], roi_pixels.shape[0]), PILImage.NEAREST)
                    mask_np = np.array(mask_pil) > 127
                    masked_pixels = roi_pixels[mask_np]
                    if len(masked_pixels) > 10:
                        roi_pixels = masked_pixels

            # Compute average color (normalized 0-1)
            if roi_pixels.ndim == 3:
                avg_rgb = roi_pixels.mean(axis=(0, 1)) / 255.0
            else:  # masked pixels are (N, 3)
                avg_rgb = roi_pixels.mean(axis=0) / 255.0

            comp["sampled_rgb"] = [round(float(avg_rgb[0]), 3), round(float(avg_rgb[1]), 3), round(float(avg_rgb[2]), 3)]

            # Also compute color variance (high variance = textured/wood, low = solid/metal)
            if roi_pixels.ndim == 3:
                std_rgb = roi_pixels.std(axis=(0, 1)) / 255.0
            else:
                std_rgb = roi_pixels.std(axis=0) / 255.0
            comp["color_variance"] = round(float(std_rgb.mean()), 4)

    # ── Step 4: Aggregate counts, dimensions, colors, spatial layout ────
    confirmed = [c for c in components if c.get("confirmed", False)]

    counts = {}
    for c in confirmed:
        label = c["label"]
        counts[label] = counts.get(label, 0) + 1

    # Compute overall dimensions from all confirmed components
    overall_dims = {}
    if confirmed and any("measured_width_m" in c for c in confirmed):
        all_x1 = [c["pixel_bbox"][0] for c in confirmed]
        all_y1 = [c["pixel_bbox"][1] for c in confirmed]
        all_x2 = [c["pixel_bbox"][2] for c in confirmed]
        all_y2 = [c["pixel_bbox"][3] for c in confirmed]

        # Use the component with largest bbox to estimate scale
        largest = max(confirmed, key=lambda c: c.get("measured_width_m", 0) * c.get("measured_height_m", 0))
        if "depth_m" in largest and dp_focal:
            depth = largest["depth_m"]
            total_px_w = max(all_x2) - min(all_x1)
            total_px_h = max(all_y2) - min(all_y1)
            overall_dims["measured_total_width_m"] = round(total_px_w * depth / dp_focal, 4)
            overall_dims["measured_total_height_m"] = round(total_px_h * depth / dp_focal, 4)

    # Row height ratios from component positions
    row_ratios = {}
    doors = [c for c in confirmed if c["label"] == "door"]
    drawers = [c for c in confirmed if c["label"] == "drawer"]
    if doors and drawers:
        avg_door_h = np.mean([c["pixel_height"] for c in doors])
        avg_drawer_h = np.mean([c["pixel_height"] for c in drawers])
        total_h = avg_door_h + avg_drawer_h
        if total_h > 0:
            row_ratios["door_ratio"] = round(float(avg_door_h / total_h), 3)
            row_ratios["drawer_ratio"] = round(float(avg_drawer_h / total_h), 3)

    # Aggregate colors per component type
    sampled_colors = {}
    for label in ["door", "drawer", "handle", "knob"]:
        typed = [c for c in confirmed if c["label"] == label and "sampled_rgb" in c]
        if typed:
            avg = np.mean([c["sampled_rgb"] for c in typed], axis=0)
            var = np.mean([c.get("color_variance", 0) for c in typed])
            sampled_colors[label] = {
                "avg_rgb": [round(float(avg[0]), 3), round(float(avg[1]), 3), round(float(avg[2]), 3)],
                "color_variance": round(float(var), 4),
                "is_metallic": var < 0.03,  # low variance = solid color = likely metal
                "sample_count": len(typed),
            }

    # Spatial layout: which components are in top vs bottom row (by Y position)
    spatial_layout = {}
    if doors and drawers:
        avg_door_y = np.mean([(c["pixel_bbox"][1] + c["pixel_bbox"][3]) / 2 for c in doors])
        avg_drawer_y = np.mean([(c["pixel_bbox"][1] + c["pixel_bbox"][3]) / 2 for c in drawers])
        # In image coords: lower Y = higher in image = higher on furniture
        if avg_drawer_y < avg_door_y:
            spatial_layout["top_row"] = "drawers"
            spatial_layout["bottom_row"] = "doors"
        else:
            spatial_layout["top_row"] = "doors"
            spatial_layout["bottom_row"] = "drawers"
        spatial_layout["avg_door_y_px"] = round(float(avg_door_y))
        spatial_layout["avg_drawer_y_px"] = round(float(avg_drawer_y))

    # Per-component measured dimensions (averaged by type)
    measured_by_type = {}
    for label in ["door", "drawer", "handle", "knob"]:
        typed = [c for c in confirmed if c["label"] == label and "measured_width_m" in c]
        if typed:
            measured_by_type[label] = {
                "avg_width_mm": round(float(np.mean([c["measured_width_m"] for c in typed]) * 1000), 1),
                "avg_height_mm": round(float(np.mean([c["measured_height_m"] for c in typed]) * 1000), 1),
                "count": len(typed),
            }

    # Cross-validate DepthPro vs DepthAnything ordering
    depth_consistency = None
    if da_depth is not None and dp_depth is not None:
        comps_with_both = [c for c in confirmed if "depth_m" in c and "da_relative_depth" in c]
        if len(comps_with_both) >= 2:
            agreements = 0
            total = 0
            for i in range(len(comps_with_both)):
                for j in range(i + 1, len(comps_with_both)):
                    dp_closer = comps_with_both[i]["depth_m"] < comps_with_both[j]["depth_m"]
                    da_closer = comps_with_both[i]["da_relative_depth"] < comps_with_both[j]["da_relative_depth"]
                    if dp_closer == da_closer:
                        agreements += 1
                    total += 1
            depth_consistency = round(agreements / total, 3) if total > 0 else None

    # Strip mask arrays from output (not serializable, large)
    components_clean = []
    for c in components:
        cc = {k: v for k, v in c.items() if k != "mask"}
        components_clean.append(cc)

    return {
        "counts": counts,
        "components": components_clean,
        "overall_dims": overall_dims,
        "row_ratios": row_ratios,
        "sampled_colors": sampled_colors,
        "spatial_layout": spatial_layout,
        "measured_by_type": measured_by_type,
        "depth_consistency": depth_consistency,
        "model_status": model_status,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def run_vision_stack(image_path):
    """Run all 4 vision models in parallel, then reconcile.

    Returns:
        dict with keys: counts, components, overall_dims, row_ratios,
        depth_consistency, model_status, elapsed_s
    """
    print("  Starting 4 vision models in parallel...")

    results = {}
    t0 = time.time()

    threads = [
        threading.Thread(target=run_dino, args=(image_path, results)),
        threading.Thread(target=run_sam3, args=(image_path, results)),
        threading.Thread(target=run_depth_pro, args=(image_path, results)),
        threading.Thread(target=run_depth_anything, args=(image_path, results)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)

    parallel_time = time.time() - t0

    # Print status
    for name in ["dino", "sam3", "depth_pro", "depth_anything"]:
        r = results.get(name, {})
        status = r.get("status", "missing")
        if status == "success":
            if name == "dino":
                print(f"    DINO: {len(r.get('detections', []))} detections")
            elif name == "sam3":
                print(f"    SAM3: {len(r.get('masks', []))} masks")
            elif name == "depth_pro":
                print(f"    DepthPro: depth range {r.get('depth_range', '?')}")
            elif name == "depth_anything":
                print(f"    DA3: depth range {r.get('depth_range', '?')}")
        else:
            print(f"    {name}: {status} — {r.get('error', '?')[:80]}")

    print(f"  Parallel inference: {parallel_time:.1f}s")

    # Reconcile
    t1 = time.time()
    output = reconcile(results, image_path)
    recon_time = time.time() - t1

    output["elapsed_s"] = round(parallel_time + recon_time, 1)
    print(f"  Reconciliation: {recon_time:.3f}s")
    print(f"  Confirmed counts: {output['counts']}")
    if output["overall_dims"]:
        dims = output["overall_dims"]
        w = dims.get("measured_total_width_m", 0) * 1000
        h = dims.get("measured_total_height_m", 0) * 1000
        print(f"  Measured dims: {w:.0f} × {h:.0f} mm")
    if output["row_ratios"]:
        print(f"  Row ratios: {output['row_ratios']}")
    if output["depth_consistency"] is not None:
        print(f"  Depth consistency (DP vs DA): {output['depth_consistency']}")
    if output.get("sampled_colors"):
        print(f"  Sampled colors:")
        for label, cdata in output["sampled_colors"].items():
            metal = "metallic" if cdata["is_metallic"] else "textured"
            print(f"    {label}: RGB={cdata['avg_rgb']} ({metal}, var={cdata['color_variance']})")
    if output.get("spatial_layout"):
        sl = output["spatial_layout"]
        print(f"  Spatial layout: top={sl.get('top_row')}, bottom={sl.get('bottom_row')}")
    if output.get("measured_by_type"):
        print(f"  Per-type dimensions:")
        for label, mdata in output["measured_by_type"].items():
            print(f"    {label}: {mdata['avg_width_mm']:.0f}×{mdata['avg_height_mm']:.0f}mm (n={mdata['count']})")

    return output


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    image = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_DIR, "cabinet_2.png")
    if not os.path.isabs(image):
        image = os.path.join(_DIR, image)

    print(f"Vision Stack — {image}")
    print("=" * 70)

    result = run_vision_stack(image)

    # Print JSON-safe output
    safe = {k: v for k, v in result.items() if k != "components"}
    print(f"\n{json.dumps(safe, indent=2)}")
    print(f"\nComponents ({len(result['components'])}):")
    for c in result["components"]:
        dims = ""
        if "measured_width_m" in c:
            dims = f" → {c['measured_width_m']*1000:.0f}×{c['measured_height_m']*1000:.0f}mm"
        sam = f" SAM3:{c['sam3_iou']}" if c.get("sam3_iou", 0) > 0 else ""
        print(f"  {c['label']:8s} conf={c['dino_confidence']:.2f}{sam}{dims}  {'✓' if c.get('confirmed') else '✗'}")
