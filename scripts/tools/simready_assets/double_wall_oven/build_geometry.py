import sys, importlib
sys.path.insert(0, "/home/msi/IsaacLab/scripts/tools")
import kinematic_builders as kb
importlib.reload(kb)

kb.clear_scene()

# V3 Stage 5: Geometry from MEASURED data (SAM + Depth Pro)
# Body: 0.600 x 0.500 x 0.800m
# lower_oven_door: 0.635 x 0.489m (measured)
# upper_oven_door: 0.630 x 0.314m (measured)

body = kb.build_body("asset_body", panels=[
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.0063, "sx": 0.6000, "sy": 0.5000, "sz": 0.0127},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.7937, "sx": 0.6000, "sy": 0.5000, "sz": 0.0127},
    {"cx": 0.0000, "cy": -0.2437, "cz": 0.4000, "sx": 0.6000, "sy": 0.0127, "sz": 0.8000},
    {"cx": -0.2936, "cy": 0.0000, "cz": 0.4000, "sx": 0.0127, "sy": 0.5000, "sz": 0.8000},
    {"cx": 0.2936, "cy": 0.0000, "cz": 0.4000, "sx": 0.0127, "sy": 0.5000, "sz": 0.8000},
    {"cx": 0.0000, "cy": 0.0000, "cz": 0.4500, "sx": 0.5746, "sy": 0.4746, "sz": 0.0127},
    {"cx": 0.0000, "cy": 0.2437, "cz": 0.7473, "sx": 0.6000, "sy": 0.0127, "sz": 0.0800},
    {"cx": 0.0000, "cy": 0.2437, "cz": 0.0327, "sx": 0.6000, "sy": 0.0127, "sz": 0.0400}
])

# lower_oven_door: measured 0.635 x 0.489m
lower_oven_door = kb.add_revolute_child(
    body, "lower_oven_door",
    panels=[
        {"cx": 0.0000, "cy": 0.2437, "cz": 0.4236, "sx": 0.5706, "sy": 0.0127, "sz": 0.0400},
        {"cx": 0.0000, "cy": 0.2437, "cz": 0.0727, "sx": 0.5706, "sy": 0.0127, "sz": 0.0400},
        {"cx": -0.2653, "cy": 0.2437, "cz": 0.2482, "sx": 0.0400, "sy": 0.0127, "sz": 0.3909},
        {"cx": 0.2653, "cy": 0.2437, "cz": 0.2482, "sx": 0.0400, "sy": 0.0127, "sz": 0.3909}
    ],
    hinge_pos=(0.0000, 0.2437, 0.0527),
    hinge_axis="X"
)

_glass_lower_oven_door = kb.add_fixed_child(lower_oven_door, "glass_lower_oven_door", panels=[
    {"cx": 0.0000, "cy": 0.2437, "cz": 0.2482, "sx": 0.4906, "sy": 0.0038, "sz": 0.3109}
])
kb.apply_preset(_glass_lower_oven_door, "oven_glass")

kb.add_fixed_child(lower_oven_door, "handle_lower_oven_door", panels=[
    {"cx": 0, "cy": 0.2686, "cz": 0.3654,
     "sx": 0.3424, "sy": 0.0250, "sz": 0.0200},
    {"cx": -0.1612, "cy": 0.2561, "cz": 0.3654,
     "sx": 0.025, "sy": 0.0300, "sz": 0.025},
    {"cx": 0.1612, "cy": 0.2561, "cz": 0.3654,
     "sx": 0.025, "sy": 0.0300, "sz": 0.025}
])

# upper_oven_door: measured 0.630 x 0.314m
upper_oven_door = kb.add_revolute_child(
    body, "upper_oven_door",
    panels=[
        {"cx": 0.0000, "cy": 0.2437, "cz": 0.6873, "sx": 0.5706, "sy": 0.0127, "sz": 0.0400},
        {"cx": 0.0000, "cy": 0.2437, "cz": 0.4763, "sx": 0.5706, "sy": 0.0127, "sz": 0.0400},
        {"cx": -0.2653, "cy": 0.2437, "cz": 0.5818, "sx": 0.0400, "sy": 0.0127, "sz": 0.2510},
        {"cx": 0.2653, "cy": 0.2437, "cz": 0.5818, "sx": 0.0400, "sy": 0.0127, "sz": 0.2510}
    ],
    hinge_pos=(0.0000, 0.2437, 0.4563),
    hinge_axis="X"
)

_glass_upper_oven_door = kb.add_fixed_child(upper_oven_door, "glass_upper_oven_door", panels=[
    {"cx": 0.0000, "cy": 0.2437, "cz": 0.5818, "sx": 0.4906, "sy": 0.0038, "sz": 0.1710}
])
kb.apply_preset(_glass_upper_oven_door, "oven_glass")

kb.add_fixed_child(upper_oven_door, "handle_upper_oven_door", panels=[
    {"cx": 0, "cy": 0.2686, "cz": 0.6571,
     "sx": 0.3424, "sy": 0.0250, "sz": 0.0200},
    {"cx": -0.1612, "cy": 0.2561, "cz": 0.6571,
     "sx": 0.025, "sy": 0.0300, "sz": 0.025},
    {"cx": 0.1612, "cy": 0.2561, "cz": 0.6571,
     "sx": 0.025, "sy": 0.0300, "sz": 0.025}
])

left_outer_knob = kb.add_revolute_child(
    body, "left_outer_knob",
    panels=[
        {"cx": -0.1875, "cy": 0.2561, "cz": 0.7473,
         "sx": 0.0419, "sy": 0.0250, "sz": 0.0419}
    ],
    hinge_pos=(-0.1875, 0.2437, 0.7473),
    hinge_axis="Y"
)

left_inner_knob = kb.add_revolute_child(
    body, "left_inner_knob",
    panels=[
        {"cx": -0.0625, "cy": 0.2561, "cz": 0.7473,
         "sx": 0.0418, "sy": 0.0250, "sz": 0.0418}
    ],
    hinge_pos=(-0.0625, 0.2437, 0.7473),
    hinge_axis="Y"
)

right_inner_knob = kb.add_revolute_child(
    body, "right_inner_knob",
    panels=[
        {"cx": 0.0625, "cy": 0.2561, "cz": 0.7473,
         "sx": 0.0436, "sy": 0.0250, "sz": 0.0436}
    ],
    hinge_pos=(0.0625, 0.2437, 0.7473),
    hinge_axis="Y"
)

right_outer_knob = kb.add_revolute_child(
    body, "right_outer_knob",
    panels=[
        {"cx": 0.1875, "cy": 0.2561, "cz": 0.7473,
         "sx": 0.0436, "sy": 0.0250, "sz": 0.0436}
    ],
    hinge_pos=(0.1875, 0.2437, 0.7473),
    hinge_axis="Y"
)

# Flatten for PhysX: unparent all REV_/PRIS_ objects to root level
import bpy
for obj in list(bpy.data.objects):
    if obj.parent and (obj.name.startswith('REV_') or obj.name.startswith('PRIS_')):
        # Store world transform before unparenting
        world_matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world_matrix

kb.export_blueprint("/home/msi/IsaacLab/scripts/tools/simready_assets/double_wall_oven/raw_blueprint.usd")