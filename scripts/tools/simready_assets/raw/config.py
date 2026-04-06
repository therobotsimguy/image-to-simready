"""Auto-generated Isaac Lab config for euro_double_wall_oven_with_digital_display (articulated).

Physics notes (from SimReady Pipeline v2):
  - Actuator stiffness=0 so USD joint drive values are used (Lesson 3).
  - Spawn 5cm above ground to prevent impact-opening doors (Lesson 6).
  - USD has real mass. For teleop where you don't want the object to slide,
    override body mass at runtime: asset.root_physx_view.set_masses(...)
  - All link self-collision is disabled in USD via FilteredPairsAPI (Lesson 15).
"""

import os

from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg

_ASSET_DIR = os.path.dirname(os.path.abspath(__file__))

EuroDoubleWallOvenWithDigitalDisplayCfg = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Euro_double_wall_oven_with_digital_display",
    spawn=UsdFileCfg(
        usd_path=os.path.join(_ASSET_DIR, "euro_double_wall_oven_with_digital_display_simready.usd"),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.5, 0.0, 0.05),  # +5cm above ground (Lesson 6)
        joint_pos={
                "upper_oven_door": 0.0,
    "lower_oven_door": 0.0,
    "knob_1": 0.0,
    "knob_2": 0.0,
    "knob_3": 0.0,
    "knob_4": 0.0,
        },
    ),
    actuators={
            "all_joints": ImplicitActuatorCfg(
    joint_names_expr=[".*"],
    stiffness=0.0,
    damping=0.0,
),
    },
)
