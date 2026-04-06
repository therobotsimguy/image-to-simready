import sys, importlib
sys.path.insert(0, "/home/msi/IsaacLab/scripts/tools")
import kinematic_builders as kb
importlib.reload(kb)

kb.clear_scene()

# V3 Stage 5: Geometry from MEASURED data (SAM + Depth Pro)
# Body: 0.600 x 0.500 x 0.800m
# lower_oven_door: 0.635 x 0.489m (measured+validated)
# upper_oven_door: 0.630 x 0.314m (measured+validated)

body = kb.build_body("asset_body", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.0060, "sx": 0.6000, "sy": 0.5000, "sz": 0.0120},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.7940, "sx": 0.6000, "sy": 0.5000, "sz": 0.0120},
    {"cx": 0.0000, "cy": -0.2440, "cz": 0.4000, "sx": 0.6000, "sy": 0.0120, "sz": 0.8000},
    {"cx": -0.2940, "cy": 0.0000, "cz": 0.4000, "sx": 0.0120, "sy": 0.5000, "sz": 0.8000},
    {"cx": 0.2940, "cy": 0.0000, "cz": 0.4000, "sx": 0.0120, "sy": 0.5000, "sz": 0.8000},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.4502, "sx": 0.5760, "sy": 0.4760, "sz": 0.0120},
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.7480, "sx": 0.6000, "sy": 0.0120, "sz": 0.0800},
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.0320, "sx": 0.6000, "sy": 0.0120, "sz": 0.0400}
])
kb.apply_preset(body, "brushed_stainless_steel")

# lower_oven_door: measured 0.635 x 0.489m
lower_oven_door = kb.add_revolute_child(
    body, "lower_oven_door",
    panels=[
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.4242, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.0720, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": -0.2660, "cy": 0.2440, "cz": 0.2481, "sx": 0.0400, "sy": 0.0500, "sz": 0.3922},
        {"cx": 0.2660, "cy": 0.2440, "cz": 0.2481, "sx": 0.0400, "sy": 0.0500, "sz": 0.3922}
    ],
    hinge_pos=(0.0000, 0.2440, 0.0520),
    hinge_axis="X"
)
kb.apply_preset(lower_oven_door, "dark_metal")

_glass_lower_oven_door = kb.add_fixed_child(lower_oven_door, "glass_lower_oven_door", panels=[
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.2481, "sx": 0.4919, "sy": 0.0200, "sz": 0.3121}
])
kb.apply_preset(_glass_lower_oven_door, "oven_glass")

_h_lower_oven_door = kb.add_fixed_child(lower_oven_door, "handle_lower_oven_door", panels=[
    {"cx": 0, "cy": 0.2690, "cz": 0.3658,
     "sx": 0.3432, "sy": 0.0250, "sz": 0.0150},
    {"cx": -0.1596, "cy": 0.2565, "cz": 0.3658,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180},
    {"cx": 0.1596, "cy": 0.2565, "cz": 0.3658,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180}
])
kb.apply_preset(_h_lower_oven_door, "chrome")

# upper_oven_door: measured 0.630 x 0.314m
upper_oven_door = kb.add_revolute_child(
    body, "upper_oven_door",
    panels=[
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.6880, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": 0.0000, "cy": 0.2440, "cz": 0.4762, "sx": 0.5720, "sy": 0.0500, "sz": 0.0400},
        {"cx": -0.2660, "cy": 0.2440, "cz": 0.5821, "sx": 0.0400, "sy": 0.0500, "sz": 0.2518},
        {"cx": 0.2660, "cy": 0.2440, "cz": 0.5821, "sx": 0.0400, "sy": 0.0500, "sz": 0.2518}
    ],
    hinge_pos=(0.0000, 0.2440, 0.4562),
    hinge_axis="X"
)
kb.apply_preset(upper_oven_door, "dark_metal")

_glass_upper_oven_door = kb.add_fixed_child(upper_oven_door, "glass_upper_oven_door", panels=[
    {"cx": 0.0000, "cy": 0.2440, "cz": 0.5821, "sx": 0.4919, "sy": 0.0200, "sz": 0.1717}
])
kb.apply_preset(_glass_upper_oven_door, "oven_glass")

_h_upper_oven_door = kb.add_fixed_child(upper_oven_door, "handle_upper_oven_door", panels=[
    {"cx": 0, "cy": 0.2690, "cz": 0.6576,
     "sx": 0.3432, "sy": 0.0250, "sz": 0.0150},
    {"cx": -0.1596, "cy": 0.2565, "cz": 0.6576,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180},
    {"cx": 0.1596, "cy": 0.2565, "cz": 0.6576,
     "sx": 0.0180, "sy": 0.0370, "sz": 0.0180}
])
kb.apply_preset(_h_upper_oven_door, "chrome")

# Knob: control_knob_1 (cylinder, r=0.021m)
control_knob_1 = kb.add_revolute_child(
    body, "control_knob_1",
    panels=[
        {"cx": -0.1875, "cy": 0.2524, "cz": 0.7480,
         "sx": 0.0420, "sy": 0.0168, "sz": 0.0420}
    ],
    hinge_pos=(-0.1875, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(control_knob_1, "chrome")

# Knob: control_knob_2 (cylinder, r=0.021m)
control_knob_2 = kb.add_revolute_child(
    body, "control_knob_2",
    panels=[
        {"cx": -0.0625, "cy": 0.2524, "cz": 0.7480,
         "sx": 0.0419, "sy": 0.0168, "sz": 0.0419}
    ],
    hinge_pos=(-0.0625, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(control_knob_2, "chrome")

# Knob: control_knob_3 (cylinder, r=0.021m)
control_knob_3 = kb.add_revolute_child(
    body, "control_knob_3",
    panels=[
        {"cx": 0.0625, "cy": 0.2524, "cz": 0.7480,
         "sx": 0.0419, "sy": 0.0168, "sz": 0.0419}
    ],
    hinge_pos=(0.0625, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(control_knob_3, "chrome")

# Knob: control_knob_4 (cylinder, r=0.021m)
control_knob_4 = kb.add_revolute_child(
    body, "control_knob_4",
    panels=[
        {"cx": 0.1875, "cy": 0.2524, "cz": 0.7480,
         "sx": 0.0420, "sy": 0.0168, "sz": 0.0420}
    ],
    hinge_pos=(0.1875, 0.2440, 0.7480),
    hinge_axis="Y"
)
kb.apply_preset(control_knob_4, "chrome")

# Flatten for PhysX: unparent all REV_/PRIS_ objects to root level
import bpy
for obj in list(bpy.data.objects):
    if obj.parent and (obj.name.startswith('REV_') or obj.name.startswith('PRIS_')):
        # Store world transform before unparenting
        world_matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world_matrix

kb.export_blueprint("/home/msi/IsaacLab/scripts/tools/simready_assets/oven_test2/raw_blueprint.usd")