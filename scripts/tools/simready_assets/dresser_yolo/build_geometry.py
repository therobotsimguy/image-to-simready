import sys, importlib
sys.path.insert(0, "/home/msi/IsaacLab/scripts/tools")
import kinematic_builders as kb
importlib.reload(kb)

kb.clear_scene()

# V3 Stage 5: Geometry from MEASURED data (SAM + Depth Pro)
# Body: 1.384 x 0.300 x 0.743m

body = kb.build_body("asset_body", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.0100, "sx": 1.3839, "sy": 0.3000, "sz": 0.0200},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.7327, "sx": 1.3839, "sy": 0.3000, "sz": 0.0200},
    {"cx": 0.0000, "cy": -0.1400, "cz": 0.3714, "sx": 1.3839, "sy": 0.0200, "sz": 0.7427},
    {"cx": -0.6819, "cy": 0.0000, "cz": 0.3714, "sx": 0.0200, "sy": 0.3000, "sz": 0.7427},
    {"cx": 0.6819, "cy": 0.0000, "cz": 0.3714, "sx": 0.0200, "sy": 0.3000, "sz": 0.7427}
])
kb.apply_preset(body, "brushed_stainless_steel")

# === DRAWERS: 2 columns × 3 rows ===

kb.add_fixed_child(body, "divider_0", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.2509,
     "sx": 1.3439, "sy": 0.2600, "sz": 0.0200}
])

kb.add_fixed_child(body, "divider_1", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.4918,
     "sx": 1.3439, "sy": 0.2600, "sz": 0.0200}
])

kb.add_fixed_child(body, "divider_2", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.3714,
     "sx": 0.0200, "sy": 0.2600, "sz": 0.7027}
])

# Drawer: drawer_top_left (row 0, col 0)
drawer_top_left = kb.add_prismatic_child(
    body, "drawer_top_left",
    panels=[
        {"cx": -0.3410, "cy": 0.0200, "cz": 0.0320, "sx": 0.6579, "sy": 0.2400, "sz": 0.0200},
        {"cx": -0.6599, "cy": 0.0200, "cz": 0.1304, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": -0.0220, "cy": 0.0200, "cz": 0.1304, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": -0.3410, "cy": -0.0900, "cz": 0.1304, "sx": 0.6579, "sy": 0.0200, "sz": 0.2169}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_top_left, "dark_walnut")

_front_drawer_top_left = kb.add_fixed_child(drawer_top_left, "front_drawer_top_left", panels=[
    {"cx": -0.3410, "cy": 0.1400, "cz": 0.1304,
     "sx": 0.6619, "sy": 0.0300, "sz": 0.2209}
])
kb.apply_preset(_front_drawer_top_left, "dark_walnut")

_h_drawer_top_left = kb.add_fixed_child(drawer_top_left, "handle_drawer_top_left", panels=[
    {"cx": -0.3410, "cy": 0.1600, "cz": 0.1304,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_top_left, "brass")

# Drawer: drawer_top_right (row 0, col 1)
drawer_top_right = kb.add_prismatic_child(
    body, "drawer_top_right",
    panels=[
        {"cx": 0.3410, "cy": 0.0200, "cz": 0.0320, "sx": 0.6579, "sy": 0.2400, "sz": 0.0200},
        {"cx": 0.0220, "cy": 0.0200, "cz": 0.1304, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": 0.6599, "cy": 0.0200, "cz": 0.1304, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": 0.3410, "cy": -0.0900, "cz": 0.1304, "sx": 0.6579, "sy": 0.0200, "sz": 0.2169}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_top_right, "dark_walnut")

_front_drawer_top_right = kb.add_fixed_child(drawer_top_right, "front_drawer_top_right", panels=[
    {"cx": 0.3410, "cy": 0.1400, "cz": 0.1304,
     "sx": 0.6619, "sy": 0.0300, "sz": 0.2209}
])
kb.apply_preset(_front_drawer_top_right, "dark_walnut")

_h_drawer_top_right = kb.add_fixed_child(drawer_top_right, "handle_drawer_top_right", panels=[
    {"cx": 0.3410, "cy": 0.1600, "cz": 0.1304,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_top_right, "brass")

# Drawer: drawer_middle_left (row 1, col 0)
drawer_middle_left = kb.add_prismatic_child(
    body, "drawer_middle_left",
    panels=[
        {"cx": -0.3410, "cy": 0.0200, "cz": 0.2729, "sx": 0.6579, "sy": 0.2400, "sz": 0.0200},
        {"cx": -0.6599, "cy": 0.0200, "cz": 0.3713, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": -0.0220, "cy": 0.0200, "cz": 0.3713, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": -0.3410, "cy": -0.0900, "cz": 0.3713, "sx": 0.6579, "sy": 0.0200, "sz": 0.2169}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_middle_left, "dark_walnut")

_front_drawer_middle_left = kb.add_fixed_child(drawer_middle_left, "front_drawer_middle_left", panels=[
    {"cx": -0.3410, "cy": 0.1400, "cz": 0.3713,
     "sx": 0.6619, "sy": 0.0300, "sz": 0.2209}
])
kb.apply_preset(_front_drawer_middle_left, "dark_walnut")

_h_drawer_middle_left = kb.add_fixed_child(drawer_middle_left, "handle_drawer_middle_left", panels=[
    {"cx": -0.3410, "cy": 0.1600, "cz": 0.3713,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_middle_left, "brass")

# Drawer: drawer_middle_right (row 1, col 1)
drawer_middle_right = kb.add_prismatic_child(
    body, "drawer_middle_right",
    panels=[
        {"cx": 0.3410, "cy": 0.0200, "cz": 0.2729, "sx": 0.6579, "sy": 0.2400, "sz": 0.0200},
        {"cx": 0.0220, "cy": 0.0200, "cz": 0.3713, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": 0.6599, "cy": 0.0200, "cz": 0.3713, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": 0.3410, "cy": -0.0900, "cz": 0.3713, "sx": 0.6579, "sy": 0.0200, "sz": 0.2169}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_middle_right, "dark_walnut")

_front_drawer_middle_right = kb.add_fixed_child(drawer_middle_right, "front_drawer_middle_right", panels=[
    {"cx": 0.3410, "cy": 0.1400, "cz": 0.3713,
     "sx": 0.6619, "sy": 0.0300, "sz": 0.2209}
])
kb.apply_preset(_front_drawer_middle_right, "dark_walnut")

_h_drawer_middle_right = kb.add_fixed_child(drawer_middle_right, "handle_drawer_middle_right", panels=[
    {"cx": 0.3410, "cy": 0.1600, "cz": 0.3713,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_middle_right, "brass")

# Drawer: drawer_bottom_left (row 2, col 0)
drawer_bottom_left = kb.add_prismatic_child(
    body, "drawer_bottom_left",
    panels=[
        {"cx": -0.3410, "cy": 0.0200, "cz": 0.5138, "sx": 0.6579, "sy": 0.2400, "sz": 0.0200},
        {"cx": -0.6599, "cy": 0.0200, "cz": 0.6122, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": -0.0220, "cy": 0.0200, "cz": 0.6122, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": -0.3410, "cy": -0.0900, "cz": 0.6122, "sx": 0.6579, "sy": 0.0200, "sz": 0.2169}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_bottom_left, "dark_walnut")

_front_drawer_bottom_left = kb.add_fixed_child(drawer_bottom_left, "front_drawer_bottom_left", panels=[
    {"cx": -0.3410, "cy": 0.1400, "cz": 0.6122,
     "sx": 0.6619, "sy": 0.0300, "sz": 0.2209}
])
kb.apply_preset(_front_drawer_bottom_left, "dark_walnut")

_h_drawer_bottom_left = kb.add_fixed_child(drawer_bottom_left, "handle_drawer_bottom_left", panels=[
    {"cx": -0.3410, "cy": 0.1600, "cz": 0.6122,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_bottom_left, "brass")

# Drawer: drawer_bottom_right (row 2, col 1)
drawer_bottom_right = kb.add_prismatic_child(
    body, "drawer_bottom_right",
    panels=[
        {"cx": 0.3410, "cy": 0.0200, "cz": 0.5138, "sx": 0.6579, "sy": 0.2400, "sz": 0.0200},
        {"cx": 0.0220, "cy": 0.0200, "cz": 0.6122, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": 0.6599, "cy": 0.0200, "cz": 0.6122, "sx": 0.0200, "sy": 0.2400, "sz": 0.2169},
        {"cx": 0.3410, "cy": -0.0900, "cz": 0.6122, "sx": 0.6579, "sy": 0.0200, "sz": 0.2169}
    ],
    slide_axis="Y"
)
kb.apply_preset(drawer_bottom_right, "dark_walnut")

_front_drawer_bottom_right = kb.add_fixed_child(drawer_bottom_right, "front_drawer_bottom_right", panels=[
    {"cx": 0.3410, "cy": 0.1400, "cz": 0.6122,
     "sx": 0.6619, "sy": 0.0300, "sz": 0.2209}
])
kb.apply_preset(_front_drawer_bottom_right, "dark_walnut")

_h_drawer_bottom_right = kb.add_fixed_child(drawer_bottom_right, "handle_drawer_bottom_right", panels=[
    {"cx": 0.3410, "cy": 0.1600, "cz": 0.6122,
     "sx": 0.1200, "sy": 0.0200, "sz": 0.0200}
])
kb.apply_preset(_h_drawer_bottom_right, "brass")

# Flatten for PhysX: unparent all REV_/PRIS_ objects to root level
import bpy
for obj in list(bpy.data.objects):
    if obj.parent and (obj.name.startswith('REV_') or obj.name.startswith('PRIS_')):
        # Store world transform before unparenting
        world_matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world_matrix

kb.export_blueprint("/home/msi/IsaacLab/scripts/tools/simready_assets/dresser_yolo/raw_blueprint.usd")