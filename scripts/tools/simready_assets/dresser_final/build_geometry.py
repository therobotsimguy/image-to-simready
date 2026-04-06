import sys, importlib
sys.path.insert(0, "/home/msi/IsaacLab/scripts/tools")
import kinematic_builders as kb
importlib.reload(kb)

kb.clear_scene()

# V3 Stage 5: Geometry from MEASURED data (SAM + Depth Pro)
# Body: 1.351 x 0.300 x 0.603m

body = kb.build_body("asset_body", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.0100, "sx": 1.3509, "sy": 0.3000, "sz": 0.0200},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.5925, "sx": 1.3509, "sy": 0.3000, "sz": 0.0200},
    {"cx": 0.0000, "cy": -0.1400, "cz": 0.3013, "sx": 1.3509, "sy": 0.0200, "sz": 0.6025},
    {"cx": -0.6654, "cy": 0.0000, "cz": 0.3013, "sx": 0.0200, "sy": 0.3000, "sz": 0.6025},
    {"cx": 0.6654, "cy": 0.0000, "cz": 0.3013, "sx": 0.0200, "sy": 0.3000, "sz": 0.6025}
])
kb.apply_preset(body, "brushed_stainless_steel")

# === DRAWERS: 2 columns × 3 rows ===

kb.add_fixed_child(body, "divider_0", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.2042,
     "sx": 1.3109, "sy": 0.2600, "sz": 0.0200}
])

kb.add_fixed_child(body, "divider_1", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.3983,
     "sx": 1.3109, "sy": 0.2600, "sz": 0.0200}
])

kb.add_fixed_child(body, "divider_2", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.3013,
     "sx": 0.0200, "sy": 0.2600, "sz": 0.5625}
])

# Drawer: drawer_row1_col1 (row 0, col 0)
drawer_row1_col1 = kb.add_prismatic_child(
    body, "drawer_row1_col1",
    panels=[
        {"cx": -0.3327, "cy": 0.0200, "cz": 0.0320, "sx": 0.6414, "sy": 0.2400, "sz": 0.0200},
        {"cx": -0.6434, "cy": 0.0200, "cz": 0.1071, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": -0.0220, "cy": 0.0200, "cz": 0.1071, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": -0.3327, "cy": -0.0900, "cz": 0.1071, "sx": 0.6414, "sy": 0.0200, "sz": 0.1702}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_row1_col1, "dark_walnut")

_front_drawer_row1_col1 = kb.add_fixed_child(drawer_row1_col1, "front_drawer_row1_col1", panels=[
    {"cx": -0.3327, "cy": 0.1400, "cz": 0.1071,
     "sx": 0.6454, "sy": 0.0300, "sz": 0.1742}
])
kb.apply_preset(_front_drawer_row1_col1, "dark_walnut")

_h_drawer_row1_col1 = kb.add_fixed_child(drawer_row1_col1, "handle_drawer_row1_col1", panels=[
    {"cx": -0.3327, "cy": 0.1600, "cz": 0.1071,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_row1_col1, "brass")

# Drawer: drawer_row1_col2 (row 0, col 1)
drawer_row1_col2 = kb.add_prismatic_child(
    body, "drawer_row1_col2",
    panels=[
        {"cx": 0.3327, "cy": 0.0200, "cz": 0.0320, "sx": 0.6414, "sy": 0.2400, "sz": 0.0200},
        {"cx": 0.0220, "cy": 0.0200, "cz": 0.1071, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": 0.6434, "cy": 0.0200, "cz": 0.1071, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": 0.3327, "cy": -0.0900, "cz": 0.1071, "sx": 0.6414, "sy": 0.0200, "sz": 0.1702}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_row1_col2, "dark_walnut")

_front_drawer_row1_col2 = kb.add_fixed_child(drawer_row1_col2, "front_drawer_row1_col2", panels=[
    {"cx": 0.3327, "cy": 0.1400, "cz": 0.1071,
     "sx": 0.6454, "sy": 0.0300, "sz": 0.1742}
])
kb.apply_preset(_front_drawer_row1_col2, "dark_walnut")

_h_drawer_row1_col2 = kb.add_fixed_child(drawer_row1_col2, "handle_drawer_row1_col2", panels=[
    {"cx": 0.3327, "cy": 0.1600, "cz": 0.1071,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_row1_col2, "brass")

# Drawer: drawer_row2_col1 (row 1, col 0)
drawer_row2_col1 = kb.add_prismatic_child(
    body, "drawer_row2_col1",
    panels=[
        {"cx": -0.3327, "cy": 0.0200, "cz": 0.2262, "sx": 0.6414, "sy": 0.2400, "sz": 0.0200},
        {"cx": -0.6434, "cy": 0.0200, "cz": 0.3012, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": -0.0220, "cy": 0.0200, "cz": 0.3012, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": -0.3327, "cy": -0.0900, "cz": 0.3012, "sx": 0.6414, "sy": 0.0200, "sz": 0.1702}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_row2_col1, "dark_walnut")

_front_drawer_row2_col1 = kb.add_fixed_child(drawer_row2_col1, "front_drawer_row2_col1", panels=[
    {"cx": -0.3327, "cy": 0.1400, "cz": 0.3012,
     "sx": 0.6454, "sy": 0.0300, "sz": 0.1742}
])
kb.apply_preset(_front_drawer_row2_col1, "dark_walnut")

_h_drawer_row2_col1 = kb.add_fixed_child(drawer_row2_col1, "handle_drawer_row2_col1", panels=[
    {"cx": -0.3327, "cy": 0.1600, "cz": 0.3012,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_row2_col1, "brass")

# Drawer: drawer_row2_col2 (row 1, col 1)
drawer_row2_col2 = kb.add_prismatic_child(
    body, "drawer_row2_col2",
    panels=[
        {"cx": 0.3327, "cy": 0.0200, "cz": 0.2262, "sx": 0.6414, "sy": 0.2400, "sz": 0.0200},
        {"cx": 0.0220, "cy": 0.0200, "cz": 0.3012, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": 0.6434, "cy": 0.0200, "cz": 0.3012, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": 0.3327, "cy": -0.0900, "cz": 0.3012, "sx": 0.6414, "sy": 0.0200, "sz": 0.1702}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_row2_col2, "dark_walnut")

_front_drawer_row2_col2 = kb.add_fixed_child(drawer_row2_col2, "front_drawer_row2_col2", panels=[
    {"cx": 0.3327, "cy": 0.1400, "cz": 0.3012,
     "sx": 0.6454, "sy": 0.0300, "sz": 0.1742}
])
kb.apply_preset(_front_drawer_row2_col2, "dark_walnut")

_h_drawer_row2_col2 = kb.add_fixed_child(drawer_row2_col2, "handle_drawer_row2_col2", panels=[
    {"cx": 0.3327, "cy": 0.1600, "cz": 0.3012,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_row2_col2, "brass")

# Drawer: drawer_row3_col1 (row 2, col 0)
drawer_row3_col1 = kb.add_prismatic_child(
    body, "drawer_row3_col1",
    panels=[
        {"cx": -0.3327, "cy": 0.0200, "cz": 0.4203, "sx": 0.6414, "sy": 0.2400, "sz": 0.0200},
        {"cx": -0.6434, "cy": 0.0200, "cz": 0.4954, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": -0.0220, "cy": 0.0200, "cz": 0.4954, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": -0.3327, "cy": -0.0900, "cz": 0.4954, "sx": 0.6414, "sy": 0.0200, "sz": 0.1702}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_row3_col1, "dark_walnut")

_front_drawer_row3_col1 = kb.add_fixed_child(drawer_row3_col1, "front_drawer_row3_col1", panels=[
    {"cx": -0.3327, "cy": 0.1400, "cz": 0.4954,
     "sx": 0.6454, "sy": 0.0300, "sz": 0.1742}
])
kb.apply_preset(_front_drawer_row3_col1, "dark_walnut")

_h_drawer_row3_col1 = kb.add_fixed_child(drawer_row3_col1, "handle_drawer_row3_col1", panels=[
    {"cx": -0.3327, "cy": 0.1600, "cz": 0.4954,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_row3_col1, "brass")

# Drawer: drawer_row3_col2 (row 2, col 1)
drawer_row3_col2 = kb.add_prismatic_child(
    body, "drawer_row3_col2",
    panels=[
        {"cx": 0.3327, "cy": 0.0200, "cz": 0.4203, "sx": 0.6414, "sy": 0.2400, "sz": 0.0200},
        {"cx": 0.0220, "cy": 0.0200, "cz": 0.4954, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": 0.6434, "cy": 0.0200, "cz": 0.4954, "sx": 0.0200, "sy": 0.2400, "sz": 0.1702},
        {"cx": 0.3327, "cy": -0.0900, "cz": 0.4954, "sx": 0.6414, "sy": 0.0200, "sz": 0.1702}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_row3_col2, "dark_walnut")

_front_drawer_row3_col2 = kb.add_fixed_child(drawer_row3_col2, "front_drawer_row3_col2", panels=[
    {"cx": 0.3327, "cy": 0.1400, "cz": 0.4954,
     "sx": 0.6454, "sy": 0.0300, "sz": 0.1742}
])
kb.apply_preset(_front_drawer_row3_col2, "dark_walnut")

_h_drawer_row3_col2 = kb.add_fixed_child(drawer_row3_col2, "handle_drawer_row3_col2", panels=[
    {"cx": 0.3327, "cy": 0.1600, "cz": 0.4954,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_row3_col2, "brass")

# Flatten for PhysX: unparent all REV_/PRIS_ objects to root level
import bpy
for obj in list(bpy.data.objects):
    if obj.parent and (obj.name.startswith('REV_') or obj.name.startswith('PRIS_')):
        # Store world transform before unparenting
        world_matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world_matrix

kb.export_blueprint("/home/msi/IsaacLab/scripts/tools/simready_assets/dresser_final/raw_blueprint.usd")