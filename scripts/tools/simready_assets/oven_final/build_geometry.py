import sys, importlib
sys.path.insert(0, "/home/msi/IsaacLab/scripts/tools")
import kinematic_builders as kb
importlib.reload(kb)

kb.clear_scene()

# V3 Stage 5: Geometry from MEASURED data (SAM + Depth Pro)
# Body: 0.600 x 0.500 x 0.800m
# bottom_oven_door: 0.635 x 0.489m (measured)
# top_oven_door: 0.630 x 0.315m (measured)

body = kb.build_body("asset_body", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.0060, "sx": 0.6000, "sy": 0.5000, "sz": 0.0120},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.7940, "sx": 0.6000, "sy": 0.5000, "sz": 0.0120},
    {"cx": 0.0000, "cy": -0.2440, "cz": 0.4000, "sx": 0.6000, "sy": 0.0120, "sz": 0.8000},
    {"cx": -0.2940, "cy": 0.0000, "cz": 0.4000, "sx": 0.0120, "sy": 0.5000, "sz": 0.8000},
    {"cx": 0.2940, "cy": 0.0000, "cz": 0.4000, "sx": 0.0120, "sy": 0.5000, "sz": 0.8000},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.4500, "sx": 0.5760, "sy": 0.4760, "sz": 0.0120},
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.7480, "sx": 0.6000, "sy": 0.0120, "sz": 0.0800},
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.0320, "sx": 0.6000, "sy": 0.0120, "sz": 0.0400}
])
kb.apply_preset(body, "brushed_stainless_steel")

# bottom_oven_door: measured 0.635 x 0.489m
bottom_oven_door = kb.add_revolute_child(
    body, "bottom_oven_door",
    panels=[
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.4240, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.0720, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": -0.2660, "cy": 0.2440, "cz": 0.2480, "sx": 0.0400, "sy": 0.0500, "sz": 0.3920},
        {"cx": 0.2660, "cy": 0.2440, "cz": 0.2480, "sx": 0.0400, "sy": 0.0500, "sz": 0.3920}
    ],
    hinge_pos=(0.0000, 0.2440, 0.0520),
    hinge_axis="X",
    hinges=[
        {"z": 0.0520, "side": "left", "door_inner_y": 0.2190, "body_inner_x": -0.2880, "plate_y": 0.2320},
        {"z": 0.0520, "side": "right", "door_inner_y": 0.2190, "body_inner_x": 0.2880, "plate_y": 0.2320},
    ]
)
kb.apply_preset(bottom_oven_door, "dark_metal")

_glass_bottom_oven_door = kb.add_fixed_child(bottom_oven_door, "glass_bottom_oven_door", panels=[
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.2480, "sx": 0.4919, "sy": 0.0200, "sz": 0.3119}
])
kb.apply_preset(_glass_bottom_oven_door, "oven_glass")

_h_bottom_oven_door = kb.add_fixed_child(bottom_oven_door, "handle_bottom_oven_door", panels=[
    {"cx": 0, "cy": 0.2690, "cz": 0.3656,
     "sx": 0.3432, "sy": 0.0250, "sz": 0.0150},
    {"cx": -0.1596, "cy": 0.2565, "cz": 0.3656,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180},
    {"cx": 0.1596, "cy": 0.2565, "cz": 0.3656,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180}
])
kb.apply_preset(_h_bottom_oven_door, "chrome")

# top_oven_door: measured 0.630 x 0.315m
top_oven_door = kb.add_revolute_child(
    body, "top_oven_door",
    panels=[
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.6880, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.4760, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": -0.2660, "cy": 0.2440, "cz": 0.5820, "sx": 0.0400, "sy": 0.0500, "sz": 0.2520},
        {"cx": 0.2660, "cy": 0.2440, "cz": 0.5820, "sx": 0.0400, "sy": 0.0500, "sz": 0.2520}
    ],
    hinge_pos=(0.0000, 0.2440, 0.4560),
    hinge_axis="X",
    hinges=[
        {"z": 0.4560, "side": "left", "door_inner_y": 0.2190, "body_inner_x": -0.2880, "plate_y": 0.2320},
        {"z": 0.4560, "side": "right", "door_inner_y": 0.2190, "body_inner_x": 0.2880, "plate_y": 0.2320},
    ]
)
kb.apply_preset(top_oven_door, "dark_metal")

_glass_top_oven_door = kb.add_fixed_child(top_oven_door, "glass_top_oven_door", panels=[
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.5820, "sx": 0.4919, "sy": 0.0200, "sz": 0.1719}
])
kb.apply_preset(_glass_top_oven_door, "oven_glass")

_h_top_oven_door = kb.add_fixed_child(top_oven_door, "handle_top_oven_door", panels=[
    {"cx": 0, "cy": 0.2690, "cz": 0.6576,
     "sx": 0.3432, "sy": 0.0250, "sz": 0.0150},
    {"cx": -0.1596, "cy": 0.2565, "cz": 0.6576,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180},
    {"cx": 0.1596, "cy": 0.2565, "cz": 0.6576,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180}
])
kb.apply_preset(_h_top_oven_door, "chrome")

# Knob: top_left_knob (cylinder, r=0.021m)
top_left_knob = kb.add_revolute_child(
    body, "top_left_knob",
    panels=[
        {"cx": -0.1875, "cy": 0.2524, "cz": 0.7480,
         "sx": 0.0420, "sy": 0.0168, "sz": 0.0420}
    ],
    hinge_pos=(-0.1875, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(top_left_knob, "chrome")

# Knob: top_right_knob (cylinder, r=0.022m)
top_right_knob = kb.add_revolute_child(
    body, "top_right_knob",
    panels=[
        {"cx": -0.0625, "cy": 0.2527, "cz": 0.7480,
         "sx": 0.0436, "sy": 0.0174, "sz": 0.0436}
    ],
    hinge_pos=(-0.0625, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(top_right_knob, "chrome")

# Knob: bottom_left_knob (cylinder, r=0.021m)
bottom_left_knob = kb.add_revolute_child(
    body, "bottom_left_knob",
    panels=[
        {"cx": 0.0625, "cy": 0.2524, "cz": 0.7480,
         "sx": 0.0420, "sy": 0.0168, "sz": 0.0420}
    ],
    hinge_pos=(0.0625, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(bottom_left_knob, "chrome")

# Knob: bottom_right_knob (cylinder, r=0.021m)
bottom_right_knob = kb.add_revolute_child(
    body, "bottom_right_knob",
    panels=[
        {"cx": 0.1875, "cy": 0.2524, "cz": 0.7480,
         "sx": 0.0420, "sy": 0.0168, "sz": 0.0420}
    ],
    hinge_pos=(0.1875, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(bottom_right_knob, "chrome")

# Flatten for PhysX: unparent all REV_/PRIS_ objects to root level
import bpy
for obj in list(bpy.data.objects):
    if obj.parent and (obj.name.startswith('REV_') or obj.name.startswith('PRIS_')):
        # Store world transform before unparenting
        world_matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world_matrix

kb.export_blueprint("/home/msi/IsaacLab/scripts/tools/simready_assets/oven_final/raw_blueprint.usd")