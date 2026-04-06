# Isaac Sim Physics Reference — PhysX Parameters, USD Schemas, Valid/Invalid Specifications

This document covers Isaac Sim / PhysX implementation only. For behavior definitions see BEHAVIOR_DEFINITIONS.md. For Blender requirements see BLENDER_ASSET_REQUIREMENTS.md.

---

# Part 3: Isaac Sim Implementations (Original 8 Behaviors)

# Behavior x Semantic Constraint Mapping for Isaac Sim

## Executive Summary

This document translates the **Behavior x Semantic Constraint Mapping Framework** into actionable Isaac Sim PhysX/OpenUSD parameter configurations. For every valid behavior and semantic constraint, it provides the exact API to use, the recommended parameter values for the Franka Emika Panda robot (70 N gripper force, 3 kg payload), and **detailed justifications for why these specific parameters are required**.

---

## 1. ROTATIONAL BEHAVIOR (Twist Right/Left)

**Valid For:** Doors, knobs, valves, hinges, locks.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **1. Directional** | `UsdPhysics.RevoluteJoint` > `physics:lowerLimit` & `upperLimit` | e.g., `0.0` to `1.92` rad | **Why:** The physics solver strictly enforces joint limits at every timestep. Setting the lower limit to 0.0 physically prevents the door from rotating inward, perfectly enforcing the directional constraint without requiring complex collision meshes for the door frame. |
| **3. Pivot Placement** | USD Hierarchy (`Xform` location of the Joint prim) | Hinge edge | **Why:** A revolute joint rotates around its own local origin. If the joint prim is placed at the center of the door instead of the edge, the door will spin like a revolving door instead of swinging like a cabinet door, violating the kinematic chain. |
| **4. Clearance** | `UsdPhysics.DriveAPI` > `drive:damping` (Soft Limits) | `0.5` - `2.0` | **Why:** While hard limits stop motion instantly, adding damping creates a "soft limit" that slows the door down before it hits the frame. This prevents the physics solver from experiencing infinite force spikes (which cause explosions in simulation) when the door slams shut. |
| **6. Force/Torque** | `PhysxJointAxisAPI` > `maxJointVelocity` | `260` deg/s | **Why:** Real motors have speed limits. The Franka Inspire Hand maxes out at 260 deg/s. If you don't cap this in simulation, the RL policy might learn to "flick" the door at 10,000 deg/s--a behavior that will instantly fail when deployed to the real robot. |
| **7. Contact/Friction** | `PhysxJointAxisAPI` > `staticFrictionEffort` | `< 5.0` Nm | **Why:** This parameter defines how much torque is needed to start moving the joint. The Franka gripper (70 N) at a 0.3m handle distance can apply max 21 Nm of torque. If `staticFrictionEffort` is > 21 Nm, the Franka physically cannot open the door. |

---

## 2. LINEAR TRANSLATIONAL BEHAVIOR (Push/Pull)

**Valid For:** Drawers, sliding doors, buttons, levers.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **1. Directional** | `UsdPhysics.PrismaticJoint` | 1-Axis Translation | **Why:** A prismatic joint constrains motion to exactly one axis. This is vastly superior to using a free-floating rigid body enclosed in a collision box (like a real drawer), because free-floating bodies in tight collision spaces often suffer from numerical jitter and get permanently stuck. |
| **2. Range Limits** | `UsdPhysics.PrismaticJoint` > `lowerLimit` & `upperLimit` | `0.0` to `0.45` m | **Why:** Enforces the physical depth of the drawer. If the Franka pulls beyond 0.45m, the drawer stops, accurately simulating the physical hard stop of the rail mechanism. |
| **6. Force/Torque** | `UsdPhysics.DriveAPI` > `drive:stiffness` | `0.0` N/m | **Why:** For a standard drawer, stiffness must be zero because a drawer doesn't spring back when you let go. If you set stiffness > 0, the drawer will fight the Franka and automatically close itself when released. |
| **7. Contact/Friction** | `PhysxJointAxisAPI` > `dynamicFrictionEffort` | `10.0` - `30.0` N | **Why:** This simulates the friction of the sliding rails. It must be low enough for the Franka's 70 N gripper to overcome, but high enough that the drawer doesn't slide open on its own due to gravity or minor robot bumps. |

---

## 3. GRASPING BEHAVIOR

**Valid For:** Any manipulatable object.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **4. Clearance** | Visual vs. Collision Geometry | `convexHull` | **Why:** The Franka gripper has an 80mm maximum opening. If you use `approximation: none` (triangle mesh) for the object's collision, the gripper fingers will often numerically penetrate the mesh and get permanently stuck. Always use a simplified `convexHull` that is strictly < 80mm wide. |
| **6. Force/Torque** | `UsdPhysics.DriveAPI` (on Gripper) > `maxForce` | `70.0` N | **Why:** This is the physical limit of the Franka Hand's continuous grasping force. Setting this correctly ensures that heavy objects (> 2kg) will realistically slip out of the gripper, forcing the RL policy to learn proper grasp poses rather than relying on infinite simulation strength. |
| **7. Contact/Friction** | `UsdPhysics.MaterialAPI` > `staticFriction` | `0.4` - `0.8` | **Why:** Friction is what actually holds the object against gravity. With a 70 N grip force and a 1.5 kg object (14.7 N gravity), the required friction coefficient is $\mu = F_g / F_{grip} = 14.7 / 70 = 0.21$. Setting it to 0.4-0.8 provides a realistic safety margin. |
| **9. Material** | `PhysxMaterialAPI` > `frictionCombineMode` | `average` or `min` | **Why:** When the gripper (Material A) touches the object (Material B), PhysX needs to know how to combine their friction values. Using `average` is the most realistic for standard materials, preventing an artificially "sticky" object from overriding a slippery gripper. |
| **13. Feedback** | `Isaac Sensor API` > `ContactSensor` | Enabled on fingers | **Why:** To detect slip, you must measure the net contact force on the fingers. If the force drops while the gripper is closed, the object is slipping. This is essential for training policies that adjust grip strength dynamically. |

---

## 4. INSERTION BEHAVIOR

**Valid For:** Pegs, plugs, keys, assembly parts.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **4. Clearance** | Collision Mesh Tolerance | `0.5` - `2.0` mm | **Why:** In simulation, perfect zero-tolerance fits (e.g., a 10mm peg in a 10mm hole) will result in infinite collision forces and explosions. You MUST model a realistic clearance gap to allow the PhysX solver to resolve the contacts smoothly. |
| **7. Contact/Friction** | `UsdPhysics.MaterialAPI` > `staticFriction` | `0.1` - `0.2` | **Why:** During insertion, the peg rubs against the walls of the hole. If friction is high, the peg will jam instantly upon slight misalignment. Low friction allows the peg to slide into alignment, mimicking chamfered edges in real assembly parts. |
| **13. Feedback** | `Isaac Sensor API` > `ContactSensor` | Enabled on hole bottom | **Why:** The only way the robot knows the insertion is complete is when the peg hits the bottom of the hole. The contact sensor detects this force spike, serving as the "success" signal for the behavior. |

---

## 5. DEFORMATION BEHAVIOR

**Valid For:** Cloth, rubber, foam, wire.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **9. Material** | `PhysxDeformableBodyAPI` > `youngsModulus` | `1e5` - `1e7` Pa | **Why:** Young's Modulus defines stiffness. If you use rigid bodies for a foam block, the Franka gripper will bounce off it. By using FEM (Finite Element Method) soft bodies with a realistic Young's modulus, the gripper can actually compress the foam, creating a stable, high-friction grasp. |
| **11. Kinematic** | `PhysxDeformableBodyAPI` > `poissonsRatio` | `0.3` - `0.45` | **Why:** Poisson's ratio defines how much the object bulges sideways when compressed. Rubber bulges a lot (~0.45), cork barely bulges (~0.1). This determines whether the object will squish out of the gripper's fingers during a tight grasp. |
| **12. Energy** | `PhysxDeformableBodyAPI` > `damping` | `0.5` - `2.0` | **Why:** Without damping, an FEM soft body behaves like a perfect spring and will vibrate infinitely when touched. Damping dissipates this energy, allowing the cloth or rubber to settle into a stable shape in the gripper. |

---

## 6. CONTACT-BASED BEHAVIOR (Tap/Press)

**Valid For:** Buttons, switches, touchscreens.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **2. Range Limits** | `UsdPhysics.PrismaticJoint` > `upperLimit` | `0.005` m (5mm) | **Why:** A button only travels a few millimeters. Setting this hard limit prevents the robot from pushing the button completely through the control panel. |
| **6. Force/Torque** | `UsdPhysics.DriveAPI` > `stiffness` | `500.0` N/m | **Why:** This is the spring that returns the button. To press a 5mm button with 500 N/m stiffness requires $F = kx = 500 \times 0.005 = 2.5$ N of force. This is well within the Franka's capabilities and provides realistic resistance. |
| **13. Feedback** | `Isaac Sensor API` > `ContactSensor` | Threshold > `1.0` N | **Why:** A button isn't activated just by touching it; it requires a specific force threshold. The contact sensor allows you to trigger the semantic "button pressed" event only when the robot applies enough force to overcome the stiffness. |

---

## 7. SEQUENTIAL BEHAVIOR

**Valid For:** Unlocking doors, complex assemblies.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **5. Sequential** | Python State Machine Controller | N/A | **Why:** The PhysX engine only simulates the current timestep; it has no concept of "sequences." To enforce that a door must be unlocked before opening, you must write a Python controller that dynamically changes the door's `upperLimit` from `0.0` (locked) to `1.92` (unlocked) only AFTER the key insertion sequence is successfully detected via contact sensors. |

---

## 8. DYNAMIC/BALLISTIC BEHAVIOR

**Valid For:** Throwing, dropping, bouncing.

### Isaac Sim Implementation

| Constraint Domain | Isaac Sim API & Parameter | Franka Target Value | Justification |
|-------------------|---------------------------|---------------------|---------------|
| **9. Material** | `UsdPhysics.MaterialAPI` > `restitution` | `0.5` - `0.8` | **Why:** Restitution controls bounciness. A value of 1.0 means perfect energy conservation (bounces forever). A value of 0.0 means it stops dead. For throwing a tennis ball, 0.7 provides a realistic bounce trajectory. |
| **11. Kinematic** | Motion Generator API (Lula) | Task-Space Trajectory | **Why:** You cannot reliably throw an object using simple joint position commands. You must use Isaac Sim's Lula trajectory generator to plan a smooth, time-optimal task-space path that accelerates the end-effector to the required release velocity. |

---

## Conclusion: The "Sim-to-Real" Guarantee

By explicitly mapping semantic constraints to precise PhysX parameters, we guarantee that the simulation behaves like reality. If an RL policy learns to open a cabinet door in Isaac Sim using these parameters, it will work on the real Franka Panda because:
1. The torque required (`staticFrictionEffort`) matches the real hinge.
2. The maximum speed (`maxJointVelocity`) respects the real motor limits.
3. The collision geometry (`convexHull`) prevents impossible geometric phasing.
4. The grip force (`maxForce` = 70N) ensures the robot is actually holding the handle, not just magically attached to it.


---

# Extended Behaviors — Isaac Sim Implementation

---

# BEHAVIOR: SLIDING/FRICTION-BASED MOTION — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

This section details the mapping of the identified semantic constraints to specific Isaac Sim API calls and USD schema properties. Accurate configuration of these parameters is crucial for realistic simulation and successful transfer to real-world robotic systems.

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value Range for Franka | Justification (WHY this parameter, WHAT breaks if wrong) |
|---|---|---|---|---|
| Directional Semantics | `omni.isaac.core.articulations.ArticulationView.apply_action()` / `omni.isaac.core.prims.RigidPrim.apply_force_at_pos()` | `applied_force` (vector), `position` (vector) | `applied_force`: [5.0, 0.0, 0.0] N (example for x-direction push); `position`: [0.0, 0.0, 0.01] m (relative to object COM, slightly above base) | **Why:** These APIs directly control the force applied by the robot to the object. `apply_action` is for controlling robot joints to achieve a desired end-effector force, while `apply_force_at_pos` can be used for direct force application on a rigid body. The `position` parameter defines the point of force application, which is critical for controlling rotational dynamics. **What breaks:** Incorrect force vectors or application points will lead to unintended object rotation, tumbling, or failure to move in the desired direction. If the force is too high, the object might accelerate unrealistically or even penetrate the surface. If too low, it won't move. |
| Range Limits | `omni.isaac.core.articulations.ArticulationView.set_joint_position_targets()` / `omni.isaac.core.articulations.ArticulationView.set_joint_velocity_targets()` / `omni.isaac.core.prims.RigidPrim.set_world_pose()` | `joint_position_targets`, `joint_velocity_targets`, `position` (for object) | `joint_position_targets`: within Franka joint limits (e.g., -2.74 to 2.74 rad for joint 1); `joint_velocity_targets`: max 2.175 rad/s; `position`: object x,y,z coordinates within table bounds. | **Why:** Robot joint limits prevent self-collision and maintain kinematic feasibility. Object position limits ensure the task is performed within the designated workspace. **What breaks:** Exceeding joint limits can cause simulation errors, unrealistic robot configurations, or even damage in real-world deployment. Allowing the object to move outside the defined workspace makes the task ill-defined or impossible to complete. |
| Clearance/Tolerance | `omni.isaac.core.physics.scene.Scene.add_ground_plane()` / `omni.isaac.core.prims.RigidPrim.set_collision_enabled()` / USD `PhysicsCollisionAPI` | `collision_enabled` (boolean), `collision_group` (string), `contact_offset` (float), `rest_offset` (float) | `collision_enabled`: True for all relevant objects; `contact_offset`: 0.001 m; `rest_offset`: 0.0001 m. | **Why:** Proper collision detection and response are fundamental for realistic physical interaction. `contact_offset` and `rest_offset` influence how collisions are detected and resolved, impacting stability. **What breaks:** Disabled collisions or incorrect offsets lead to object interpenetration, unrealistic bouncing, or objects passing through each other. Insufficient clearance can cause unintended collisions between the robot and the environment or the object. |
| Force/Torque Realism | `omni.isaac.core.articulations.ArticulationView.set_max_efforts()` / `omni.isaac.core.articulations.ArticulationView.set_max_velocities()` / USD `PhysicsRigidBodyAPI` | `max_efforts` (array of floats), `max_velocities` (array of floats), `mass` (float), `solver_position_iteration_count` (int), `solver_velocity_iteration_count` (int) | `max_efforts`: Franka joint torque limits (e.g., 87.0 Nm for main joints); `max_velocities`: Franka joint velocity limits (e.g., 2.175 rad/s); `mass`: 0.2 kg for the box; `solver_position_iteration_count`: 8; `solver_velocity_iteration_count`: 1. | **Why:** Setting realistic effort and velocity limits for the robot joints ensures that the simulated robot behaves like its real-world counterpart. Accurate mass properties for the object are crucial for correct dynamic response. Solver iterations affect the accuracy and stability of the physics simulation. **What breaks:** Unrealistic force/torque limits can lead to the robot performing actions impossible in the real world (e.g., accelerating too quickly). Incorrect mass will result in inaccurate inertia and dynamic behavior. Low solver iteration counts can cause instability, jitter, or inaccurate collision resolution. |
| Contact/Friction | USD `PhysicsMaterialAPI` / `omni.isaac.core.prims.RigidPrim.set_friction_coefficients()` | `static_friction` (float), `dynamic_friction` (float), `restitution` (float) | `static_friction`: 0.3; `dynamic_friction`: 0.2; `restitution`: 0.01 (for low bounce). | **Why:** Friction coefficients directly govern the sliding behavior of the object. `static_friction` determines the force required to initiate motion, while `dynamic_friction` affects the object's deceleration once moving. Restitution influences how much energy is conserved during collisions, impacting bouncing. **What breaks:** Incorrect friction values will lead to unrealistic sliding behavior (e.g., object slides too easily or not at all, or bounces excessively). This is the core of a friction-based motion task. |
| Material Properties | USD `PhysicsRigidBodyAPI` / `omni.isaac.core.prims.RigidPrim.set_mass()` / `omni.isaac.core.prims.RigidPrim.set_density()` | `mass` (float), `density` (float), `linear_damping` (float), `angular_damping` (float) | `mass`: 0.2 kg; `density`: 1040 kg/m3 (for ABS plastic); `linear_damping`: 0.01; `angular_damping`: 0.01. | **Why:** Accurate mass and density are fundamental for correct inertial properties and dynamic response. Damping parameters help stabilize the simulation and represent energy loss due to air resistance or internal material friction. **What breaks:** Incorrect mass or density will result in unrealistic acceleration, deceleration, and overall dynamic behavior. Improper damping can lead to oscillations or an overly stable simulation. |
| Kinematic Chain | USD `ArticulationRoot` / `omni.isaac.core.articulations.ArticulationView` | `joint_prim_paths` (array of strings), `fixed_joint_prim_paths` (array of strings) | `joint_prim_paths`: Paths to all Franka joints; `fixed_joint_prim_paths`: Paths to fixed joints (e.g., base to world). | **Why:** A correctly defined kinematic chain ensures that the robot's joints and links are properly connected and constrained, allowing for accurate forward and inverse kinematics. This is essential for precise end-effector control. **What breaks:** An incorrectly defined kinematic chain will lead to an improperly articulated robot, making accurate control impossible. The robot might behave erratically, or its end-effector might not reach desired poses. |
| Energy | USD `PhysicsScene` / `omni.isaac.core.physics.scene.Scene` | `gravity` (vector), `bounce_threshold_velocity` (float), `enable_ccd` (boolean) | `gravity`: [0.0, 0.0, -9.81] m/s2; `bounce_threshold_velocity`: 0.05 m/s; `enable_ccd`: False (unless high-speed collisions are critical). | **Why:** Gravity is a fundamental force in any physical simulation. `bounce_threshold_velocity` affects when restitution is applied, influencing energy conservation during low-velocity impacts. Continuous Collision Detection (CCD) improves accuracy for fast-moving objects but comes with a performance cost. **What breaks:** Incorrect gravity will lead to objects floating or falling too fast/slow. An inappropriate bounce threshold can cause objects to appear to stick or bounce unrealistically at low speeds. Enabling CCD unnecessarily can significantly slow down the simulation. |
| Feedback | `omni.isaac.core.articulations.ArticulationView.get_applied_joint_efforts()` / `omni.isaac.core.articulations.ArticulationView.get_joint_forces()` / `omni.isaac.core.prims.RigidPrim.get_applied_force()` | `applied_joint_efforts` (array of floats), `joint_forces` (array of floats), `applied_force` (vector) | N/A (these are read-only feedback values) | **Why:** Accessing force/torque feedback from the robot's sensors is crucial for implementing closed-loop control strategies. This allows the robot to react to contact and adjust its actions dynamically. **What breaks:** Without accurate feedback, the robot cannot adapt to unexpected contact conditions, leading to unstable pushing, loss of contact, or excessive force application. This is vital for robust interaction. |
| Safety | USD `PhysicsCollisionAPI` / `omni.isaac.core.prims.RigidPrim.set_collision_enabled()` / `omni.isaac.core.articulations.ArticulationView.set_joint_velocity_targets()` | `collision_enabled` (boolean), `max_velocities` (array of floats), `max_angular_velocities` (array of floats) | `collision_enabled`: True for all environmental obstacles; `max_velocities`: Franka joint velocity limits; `max_angular_velocities`: Franka link angular velocity limits. | **Why:** Enabling collisions for environmental objects prevents the robot from passing through them. Limiting joint and link velocities prevents sudden, dangerous movements. These are fundamental for safe operation in both simulation and real-world. **What breaks:** Disabled collisions lead to robot-environment interpenetration. Unrestricted velocities can cause jerky, unstable, and potentially damaging movements. |

## SECTION 4: Valid Behavior Specification (JSON)

This JSON block provides a complete and valid specification for an instance of the SLIDING/FRICTION-BASED MOTION behavior, demonstrating the configuration of key parameters for a Franka Panda robot pushing a specific object on a surface. Each parameter is set to a value within the recommended ranges, ensuring a physically plausible and executable simulation.

```json
{
  "behavior_name": "SLIDING/FRICTION-BASED_MOTION",
  "robot": {
    "type": "FrankaEmikaPanda",
    "end_effector_configuration": {
      "gripper_state": "partially_closed",
      "contact_point_offset": [0.0, 0.0, 0.01] 
    },
    "control_mode": "force_control",
    "max_push_force_N": 20.0,
    "max_push_velocity_m_s": 0.1
  },
  "object_to_push": {
    "usd_path": "/World/Props/Box",
    "mass_kg": 0.2,
    "dimensions_m": [0.1, 0.1, 0.05],
    "material": {
      "name": "ABS_Plastic",
      "static_friction": 0.3,
      "dynamic_friction": 0.2,
      "restitution": 0.01
    }
  },
  "surface": {
    "usd_path": "/World/Table",
    "material": {
      "name": "Wood",
      "static_friction": 0.3,
      "dynamic_friction": 0.2,
      "restitution": 0.01
    }
  },
  "task_parameters": {
    "initial_robot_pose": {
      "position": [0.5, 0.0, 0.5], 
      "orientation": [0.0, 0.0, 0.0, 1.0] 
    },
    "initial_object_pose": {
      "position": [0.6, 0.0, 0.275], 
      "orientation": [0.0, 0.0, 0.0, 1.0] 
    },
    "target_object_displacement_m": [0.3, 0.0, 0.0],
    "push_duration_s": 5.0,
    "collision_detection_enabled": true,
    "solver_position_iterations": 8,
    "solver_velocity_iterations": 1
  },
  "safety_constraints": {
    "joint_velocity_limits_rad_s": 2.175,
    "workspace_limits_m": {
      "x_min": -1.0, "x_max": 1.0,
      "y_min": -1.0, "y_max": 1.0,
      "z_min": 0.0, "z_max": 1.5
    }
  }
}
```

**Justification:**

*   **`behavior_name`**: Clearly identifies the specific manipulation task, which is crucial for task management and logging within Isaac Sim. Without this, it would be difficult to categorize and analyze simulation results.
*   **`robot`**: Specifies the robot type and its end-effector configuration. The `gripper_state` and `contact_point_offset` are vital for defining how the robot interacts with the object. `force_control` is chosen as it's appropriate for pushing tasks, allowing the robot to maintain a desired contact force. `max_push_force_N` and `max_push_velocity_m_s` are set within the Franka's capabilities to ensure realistic and safe operation. Incorrect values here would lead to either insufficient force to move the object or excessive force causing instability or damage.
*   **`object_to_push`**: Defines the physical properties and USD path of the object. `mass_kg`, `dimensions_m`, and `material` properties (especially `static_friction`, `dynamic_friction`, `restitution`) are paramount for accurate physics simulation. If these are incorrect, the object will not respond realistically to the pushing force, leading to an invalid simulation of friction-based motion.
*   **`surface`**: Similar to the object, the surface properties, particularly its `material` friction coefficients, are critical. The interaction between the object and surface materials dictates the sliding behavior. Mismatched friction values would invalidate the core premise of friction-based motion.
*   **`task_parameters`**: Sets up the initial conditions and goals for the simulation. `initial_robot_pose` and `initial_object_pose` define the starting configuration. `target_object_displacement_m` specifies the desired outcome. `push_duration_s` controls the time allocated for the push. `collision_detection_enabled` ensures physical interactions are computed. `solver_position_iterations` and `solver_velocity_iterations` are physics engine parameters that balance simulation accuracy and performance. Too few iterations can lead to unstable or inaccurate physics, especially with contacts.
*   **`safety_constraints`**: Defines limits to ensure the robot operates safely within its physical capabilities and designated workspace. `joint_velocity_limits_rad_s` prevents overly aggressive movements, and `workspace_limits_m` ensures the robot and object remain within a defined operational area. Violating these could lead to collisions, robot damage, or simulation instability.

## SECTION 5: Invalid Behavior Specification (JSON)

This JSON block presents an invalid configuration for the SLIDING/FRICTION-BASED MOTION behavior, highlighting common pitfalls and demonstrating how certain parameter choices can violate semantic constraints, leading to unrealistic or unexecutable simulations. The justifications explain which constraints are violated and why.

```json
{
  "behavior_name": "SLIDING/FRICTION-BASED_MOTION",
  "robot": {
    "type": "FrankaEmikaPanda",
    "end_effector_configuration": {
      "gripper_state": "fully_open", 
      "contact_point_offset": [0.0, 0.0, 0.0] 
    },
    "control_mode": "velocity_control", 
    "max_push_force_N": 100.0, 
    "max_push_velocity_m_s": 5.0 
  },
  "object_to_push": {
    "usd_path": "/World/Props/HeavyBlock",
    "mass_kg": 50.0, 
    "dimensions_m": [0.5, 0.5, 0.5],
    "material": {
      "name": "Polished_Ice",
      "static_friction": 0.01,
      "dynamic_friction": 0.005,
      "restitution": 0.9 
    }
  },
  "surface": {
    "usd_path": "/World/IceRink",
    "material": {
      "name": "Ice",
      "static_friction": 0.01,
      "dynamic_friction": 0.005,
      "restitution": 0.9 
    }
  },
  "task_parameters": {
    "initial_robot_pose": {
      "position": [0.5, 0.0, 0.5], 
      "orientation": [0.0, 0.0, 0.0, 1.0] 
    },
    "initial_object_pose": {
      "position": [0.6, 0.0, 0.275], 
      "orientation": [0.0, 0.0, 0.0, 1.0] 
    },
    "target_object_displacement_m": [0.3, 0.0, 0.0],
    "push_duration_s": 5.0,
    "collision_detection_enabled": true,
    "solver_position_iterations": 2, 
    "solver_velocity_iterations": 1
  },
  "safety_constraints": {
    "joint_velocity_limits_rad_s": 2.175,
    "workspace_limits_m": {
      "x_min": -1.0, "x_max": 1.0,
      "y_min": -1.0, "y_max": 1.0,
      "z_min": 0.0, "z_max": 1.5
    }
  }
}
```

**Violated Semantic Constraint Domains and Justifications:**

*   **Force/Torque Realism**: The `max_push_force_N` is set to `100.0` N, which exceeds the Franka Panda's continuous force limit of 70 N. Additionally, the `object_to_push` has a `mass_kg` of `50.0` kg, far exceeding the Franka's 3 kg payload capacity. Attempting to push such a heavy object with excessive force would be physically impossible for the robot and would lead to immediate failure or damage in a real-world scenario. In simulation, this would result in unrealistic acceleration or an inability to move the object at all, depending on the physics engine's error handling.
*   **Contact/Friction**: The `static_friction` and `dynamic_friction` coefficients for both the object and surface are set to extremely low values (0.01 and 0.005, respectively), simulating a highly slippery surface like polished ice. While technically possible, this drastically alters the nature of the "friction-based motion" behavior. With near-zero friction, the object would slide uncontrollably with the slightest touch, making precise control impossible. This violates the core challenge of the behavior, which is to manage and overcome friction.
*   **Energy**: The `restitution` value of `0.9` for both the object and the surface is extremely high, implying that collisions are almost perfectly elastic. This would cause the object to bounce unrealistically upon contact with the end-effector or any other surface, making stable pushing impossible. In a real-world pushing task, energy is dissipated through friction and inelastic collisions, and this specification fails to model that, thus violating the energy realism constraint.
*   **Directional Semantics**: The `gripper_state` is set to `fully_open`. While not strictly an error, pushing with a fully open gripper is not a stable or effective way to apply directional force. The contact area would be small and poorly defined, likely leading to the object slipping or rotating unexpectedly. A partially closed or fully closed gripper provides a more stable and predictable contact surface for pushing, making the intended directional control achievable. This choice of gripper state, therefore, undermines the directional semantics of the task.
*   **Safety**: The `max_push_velocity_m_s` is set to `5.0` m/s, which is an extremely high and unsafe velocity for a contact-rich manipulation task in a typical workspace. Such high speeds would likely lead to instability, loss of contact, or violent collisions, posing a significant safety risk in a real-world deployment. This violates the safety constraint, which requires movements to be controlled and within safe operational limits.
*   **Solver Iterations**: The `solver_position_iterations` is set to `2`. While not a direct violation of a physical constraint, such a low value for position iterations can lead to significant instability and inaccuracies in the physics simulation, especially when dealing with contacts and friction. This would manifest as jittering, interpenetration, or incorrect collision responses, making the simulation unreliable and not representative of real-world physics.

---

# WIPING/SWEEPING BEHAVIOR SPECIFICATION — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

This section provides a detailed mapping of the identified semantic constraints to specific Isaac Sim APIs and OpenUSD PhysX schemas. Each mapping includes the exact API/schema, relevant parameter names, recommended value ranges for the Franka Emika Panda, and a justification for its inclusion and the consequences of incorrect parameterization.

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value Range (Franka Panda) | Justification (WHY this parameter, WHAT breaks if wrong) |
| :--- | :--- | :--- | :--- | :--- |
| 1. Directional Semantics | `isaacsim.robot_motion.core.set_end_effector_pose()` / `omni.isaac.core.articulations.ArticulationView` | `target_position`, `target_orientation` | `target_position`: X, Y plane movement within a defined range; `target_orientation`: fixed normal to surface (e.g., `[0, 0, 0, 1]` for identity quaternion, or specific rotation to align tool). | **Why:** These parameters directly control the desired pose of the end-effector. For wiping, the translational movement must be primarily in the plane of the surface, while the orientation maintains the tool's contact angle. **What breaks:** If `target_position` is not constrained to the surface plane, the robot will lift off or dig into the surface. If `target_orientation` is incorrect, the tool will not make proper contact, leading to ineffective wiping or damage to the tool/surface. |
| 2. Range Limits | `UsdPhysics.Joint` / `omni.isaac.core.articulations.ArticulationView` | `physics:low`, `physics:high` (for joint limits) / `get_joint_limits()` | Franka Panda joint limits (e.g., `physics:low = -2.79`, `physics:high = 2.79` for J1) | **Why:** These define the physical range of motion for each joint. Adhering to these limits is crucial for realistic robot behavior and preventing self-collisions or reaching singular configurations. **What breaks:** Exceeding these limits in simulation leads to unrealistic joint angles, potential self-intersections, or solver instability. In a real robot, this would cause hardware damage or joint errors. |
| 4. Clearance/Tolerance | `PhysxSchemaPhysxCollisionAPI` / `UsdPhysics.CollisionAPI` | `physics:contactOffset`, `physics:restOffset` | `contactOffset`: 0.001-0.005 m; `restOffset`: 0.0001-0.0005 m | **Why:** `contactOffset` determines the distance at which collision detection begins, and `restOffset` defines the minimum separation distance maintained between colliding bodies. For continuous contact, these values must be carefully tuned to ensure stable and consistent interaction without excessive penetration or floating. **What breaks:** An overly large `contactOffset` can lead to premature collision responses, making the robot appear to interact with the surface before actual contact. An `restOffset` that is too large will cause the end-effector to float above the surface, breaking contact. Conversely, if `restOffset` is too small, the end-effector might interpenetrate the surface, leading to unrealistic physics and potentially high, unstable forces. |
| 5. Sequential Dependency | Custom Python Script (e.g., using `omni.isaac.core.simulation_context.SimulationContext.step()`) | N/A (Logic-based state machine) | N/A | **Why:** The wiping behavior is a multi-stage process requiring precise sequencing of actions (approach, contact, wipe, retract). This is typically managed through a state machine implemented in Python. **What breaks:** Incorrect sequencing, such as initiating wiping motion before stable contact is established, will result in the robot failing to perform the task effectively. For instance, if the robot attempts to wipe without sufficient normal force, it will merely slide over the surface without cleaning. |
| 6. Force/Torque Realism | `UsdPhysics.MassAPI` / `PhysxSchemaPhysxRigidBodyAPI` | `physics:mass`, `physics:density` | `mass`: ~1.0 kg (end-effector + tool); `density`: appropriate for material (e.g., 1000 kg/m^3 for water-like material) | **Why:** Accurate mass and density properties for the end-effector and any attached tools are fundamental for realistic force and torque calculations within the PhysX engine. These properties directly influence the gravitational forces and inertial responses, which are critical for maintaining a consistent contact force during wiping. **What breaks:** Inaccurate mass or density will lead to incorrect force feedback and control. If the simulated mass is too low, the robot might not apply enough pressure to wipe effectively, or it might bounce off the surface. If too high, it could exert excessive force, potentially damaging the simulated surface or causing the robot to struggle to maintain its trajectory. |
| 7. Contact/Friction | `PhysxSchemaPhysxMaterialAPI` | `physics:staticFriction`, `physics:dynamicFriction`, `physics:restitution` | `staticFriction`: 0.5-0.8; `dynamicFriction`: 0.3-0.6; `restitution`: 0.0-0.1 | **Why:** These parameters govern the interaction between the end-effector tool and the surface. For wiping, sufficient friction is necessary to move debris or clean effectively, while low restitution ensures stable contact without bouncing. **What breaks:** If `staticFriction` and `dynamicFriction` are too low, the end-effector will slip excessively, failing to perform the wiping action. If they are too high, the robot might experience excessive resistance, leading to high joint torques, control instability, or even getting stuck. High `restitution` would cause the end-effector to bounce off the surface, disrupting continuous contact. |
| 9. Material Properties | `PhysxSchemaPhysxMaterialAPI` / `UsdPhysics.RigidBodyAPI` | `physics:compliance`, `physics:damping` (for tool) | `compliance`: 0.0-0.01; `damping`: 0.1-0.5 | **Why:** The compliance (inverse of stiffness) and damping of the wiping tool are crucial for compliant interaction with the surface. A compliant tool can deform to maintain contact over minor surface irregularities, while damping helps to dissipate energy and prevent oscillations during contact. **What breaks:** A tool that is too rigid will not conform to the surface, leading to intermittent contact and ineffective wiping. A tool that is too compliant might deform excessively, losing its structural integrity and wiping effectiveness. Insufficient damping can lead to unstable contact, causing the end-effector to oscillate or chatter against the surface. |
| 11. Kinematic Chain | `omni.isaac.core.articulations.ArticulationView.compute_inverse_kinematics()` / `omni.isaac.core.articulations.ArticulationView.get_manipulability_index()` | `target_end_effector_pose`, `max_iterations`, `tolerance` | `max_iterations`: 100-500; `tolerance`: 1e-4 - 1e-6 | **Why:** Inverse Kinematics (IK) is used to determine the joint configurations required to achieve a desired end-effector pose. For wiping, maintaining a smooth and stable end-effector trajectory is critical. Manipulability index helps in avoiding singular configurations. **What breaks:** Inaccurate or unstable IK solutions can lead to jerky movements, inability to reach target poses, or sudden changes in joint velocities, which can disrupt the wiping process and potentially cause collisions. Operating near singularities can lead to unpredictable robot behavior and control issues. |
| 12. Energy | `omni.isaac.core.simulation_context.SimulationContext.get_current_time()` / `omni.isaac.core.articulations.ArticulationView.get_applied_joint_efforts()` | N/A (Calculated from simulation data) | N/A | **Why:** While not a direct input parameter, monitoring the energy (work done by joints) is vital for assessing the efficiency and long-term feasibility of the wiping behavior. It provides insights into the robot's power consumption and potential for overheating. **What breaks:** Failure to monitor energy could lead to designing behaviors that are energetically inefficient, causing excessive wear on robot components or exceeding the power capabilities of the real robot. In simulation, this might manifest as unrealistic joint efforts or temperatures. |
| 13. Feedback | `omni.isaac.sensor.ForceSensor` / `omni.isaac.core.articulations.ArticulationView.get_joint_forces()` | `force`, `torque` (from force sensor) / `joint_forces` (from articulation) | N/A (Read-only sensor/state data) | **Why:** Continuous and accurate feedback from force-torque sensors (at the wrist or end-effector) and joint force/torque sensors is absolutely critical for implementing closed-loop force control. This feedback allows the robot to adapt to the environment and maintain a desired contact force. **What breaks:** Without reliable force feedback, the robot cannot implement impedance or admittance control, leading to unstable contact, loss of contact, or application of excessive force. This would render the wiping task ineffective or potentially damaging. |
| 14. Safety | `omni.isaac.core.articulations.ArticulationView.set_joint_velocity_targets()` / `omni.isaac.core.articulations.ArticulationView.set_joint_effort_targets()` / `UsdPhysics.DriveAPI` | `max_velocity`, `max_acceleration`, `max_effort` (for joints) / `max_linear_velocity`, `max_angular_velocity` (for end-effector) | `max_velocity`: 0.2 m/s (end-effector); `max_acceleration`: 0.5 m/s^2 (end-effector); `max_effort`: 87 Nm (joint torque) | **Why:** Implementing strict safety limits on velocity, acceleration, and applied forces/torques is paramount to prevent damage to the robot, the environment, and ensure the safety of any nearby personnel. These limits define the operational envelope of the robot. **What breaks:** Exceeding these safety limits can lead to catastrophic failures, including robot damage due to excessive stress, collisions with the environment, or injury to humans. Uncontrolled high velocities or accelerations can also make the robot unstable and difficult to control, especially during contact-rich tasks like wiping. |


## SECTION 4: Valid Behavior Specification (JSON)

This JSON block provides a complete and valid specification for an instance of the Wiping/Sweeping behavior, specifically for wiping a rectangular table surface using the Franka Emika Panda robot with a compliant end-effector.

```json
{
  "behavior_name": "Wiping/Sweeping Table Surface",
  "robot_model": "Franka Emika Panda",
  "end_effector_tool": {
    "name": "Compliant Sponge",
    "mass_kg": 0.1,
    "density_kg_m3": 500,
    "material_properties": {
      "staticFriction": 0.7,
      "dynamicFriction": 0.5,
      "restitution": 0.05,
      "compliance": 0.005,
      "damping": 0.3
    }
  },
  "target_surface": {
    "name": "Rectangular Table",
    "dimensions_m": [1.0, 0.6, 0.02],
    "material_properties": {
      "staticFriction": 0.6,
      "dynamicFriction": 0.4,
      "restitution": 0.01
    }
  },
  "behavior_parameters": {
    "wiping_path": {
      "type": "linear_raster",
      "start_point_m": [0.4, -0.2, 0.01],
      "end_point_m": [-0.4, 0.2, 0.01],
      "stroke_length_m": 0.8,
      "stroke_width_m": 0.4,
      "overlap_ratio": 0.2,
      "direction": "x_axis_dominant"
    },
    "contact_force_n": 15.0,
    "wiping_speed_m_s": 0.15,
    "approach_height_m": 0.1,
    "retract_height_m": 0.1,
    "safety_limits": {
      "max_end_effector_velocity_m_s": 0.2,
      "max_end_effector_acceleration_m_s2": 0.5,
      "max_joint_effort_nm": 80.0
    },
    "kinematics_solver": {
      "max_iterations": 200,
      "tolerance": 1e-5
    },
    "collision_parameters": {
      "contactOffset_m": 0.002,
      "restOffset_m": 0.0002
    }
  },
  "control_strategy": {
    "type": "impedance_control",
    "impedance_gains": {
      "stiffness_n_m": [1000, 1000, 5000, 500, 500, 500],
      "damping_n_m_s": [100, 100, 200, 50, 50, 50]
    },
    "force_feedback_sensor": "wrist_ft_sensor"
  }
}
```

## SECTION 5: Invalid Behavior Specification (JSON)

This JSON block illustrates an invalid specification for the Wiping/Sweeping behavior, highlighting violations of several semantic constraint domains. Each violation is explained with its corresponding constraint domain.

```json
{
  "behavior_name": "Invalid Wiping Attempt",
  "robot_model": "Franka Emika Panda",
  "end_effector_tool": {
    "name": "Rigid Metal Scraper",
    "mass_kg": 0.5,
    "density_kg_m3": 7800,
    "material_properties": {
      "staticFriction": 0.1,
      "dynamicFriction": 0.05,
      "restitution": 0.8,
      "compliance": 0.0,
      "damping": 0.0
    }
  },
  "target_surface": {
    "name": "Delicate Wooden Table",
    "dimensions_m": [1.0, 0.6, 0.02],
    "material_properties": {
      "staticFriction": 0.4,
      "dynamicFriction": 0.3,
      "restitution": 0.05
    }
  },
  "behavior_parameters": {
    "wiping_path": {
      "type": "circular_motion",
      "center_point_m": [0.0, 0.0, 0.05],
      "radius_m": 0.2,
      "speed_rad_s": 1.0
    },
    "contact_force_n": 5.0,
    "wiping_speed_m_s": 0.5,
    "approach_height_m": 0.0,
    "retract_height_m": 0.0,
    "safety_limits": {
      "max_end_effector_velocity_m_s": 1.0,
      "max_end_effector_acceleration_m_s2": 2.0,
      "max_joint_effort_nm": 100.0
    },
    "kinematics_solver": {
      "max_iterations": 10,
      "tolerance": 1e-2
    },
    "collision_parameters": {
      "contactOffset_m": 0.05,
      "restOffset_m": 0.01
    }
  },
  "control_strategy": {
    "type": "position_control",
    "force_feedback_sensor": "none"
  }
}
```

**Violated Semantic Constraint Domains:**

*   **1. Directional Semantics:** The `wiping_path` is defined as `circular_motion` with a `center_point_m` at `[0.0, 0.0, 0.05]`, placing the end-effector 5 cm *above* the surface. This violates the requirement for motion to be constrained to a plane parallel to the target surface and maintaining sustained contact. The robot would be attempting to wipe in the air.
*   **4. Clearance/Tolerance:** The `collision_parameters` specify a `contactOffset_m` of `0.05` m and `restOffset_m` of `0.01` m. These values are excessively large for a contact-rich task like wiping. The large `restOffset` would cause the end-effector to float significantly above the surface, preventing continuous contact. The large `contactOffset` would lead to premature and inaccurate collision responses.
*   **6. Force/Torque Realism:** The `end_effector_tool` is a `Rigid Metal Scraper` with high density and mass, but the `contact_force_n` is set to a low `5.0` N. This combination is unrealistic for effective wiping, especially on a `Delicate Wooden Table`. The low friction properties (`staticFriction`: 0.1, `dynamicFriction`: 0.05) further exacerbate this, indicating the tool would merely slide without applying effective force.
*   **7. Contact/Friction:** The `material_properties` for the `Rigid Metal Scraper` have very low `staticFriction` (0.1) and `dynamicFriction` (0.05), and a high `restitution` (0.8). These values are inappropriate for a wiping behavior, as they would cause the end-effector to slip and bounce rather than maintain stable, friction-based contact necessary for cleaning or sweeping. The tool would not effectively engage with the surface.
*   **9. Material Properties:** The `end_effector_tool` is described as a `Rigid Metal Scraper` with `compliance`: 0.0 and `damping`: 0.0. This indicates a perfectly rigid tool with no ability to conform to surface irregularities or absorb impact. This violates the need for a compliant tool to maintain consistent contact over uneven surfaces, leading to intermittent contact and ineffective wiping.
*   **13. Feedback:** The `control_strategy` is `position_control` and `force_feedback_sensor` is set to `none`. This directly violates the critical requirement for continuous feedback from force-torque sensors to maintain desired contact force and adapt to surface variations. Without force feedback, the robot cannot perform compliant interaction, making sustained contact impossible.
*   **14. Safety:** The `safety_limits` include `max_joint_effort_nm`: 100.0, which exceeds the Franka Panda's maximum main joint torque of +/-87 Nm. Additionally, `max_end_effector_velocity_m_s`: 1.0 and `max_end_effector_acceleration_m_s2`: 2.0 are significantly higher than typical safe operating speeds for contact-rich tasks, increasing the risk of damage or instability. The combination of a rigid tool, high speeds, and excessive joint effort limits poses a significant safety risk.

---

# TWISTING/TORQUE-BASED ROTATION — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value for Franka | Justification |
| :--- | :--- | :--- | :--- | :--- |
| Kinematic Chain | `UsdPhysics.RevoluteJoint` | `physics:axis` | `"Z"` (or appropriate local axis) | Defines the single degree of freedom for rotation. If wrong, the object will rotate in the wrong direction or bind. |
| Range Limits | `UsdPhysics.RevoluteJoint` | `physics:lowerLimit`, `physics:upperLimit` | e.g., `-90.0`, `90.0` (degrees) | Defines the physical stops of the rotation. If wrong, the robot will push through the visual geometry, causing physics instability. |
| Force/Torque Realism | `UsdPhysics.DriveAPI` | `drive:angular:physics:maxForce` | `< 12.0` (Nm) | Limits the torque the joint can resist or apply. Must be less than Franka's wrist limit (12 Nm) so the robot can actually turn it. |
| Force/Torque Realism | `UsdPhysics.DriveAPI` | `drive:angular:physics:damping` | `0.1` to `5.0` | Simulates the internal friction/resistance of the twisting mechanism. If 0, the object spins freely; if too high, the robot cannot turn it. |
| Contact/Friction | `PhysxSchema.PhysxMaterialAPI` | `physxMaterial:frictionCombineMode` | `"multiply"` or `"max"` | Determines how gripper and object friction interact. "max" ensures a strong grip if the gripper pads have high friction. |
| Contact/Friction | `PhysxSchema.PhysxMaterialAPI` | `physxMaterial:staticFriction`, `dynamicFriction` | `0.8` to `1.5` | High friction is required to transfer torque without slipping. If too low, the gripper will just slide over the object's surface. |
| Pivot Placement | `UsdPhysics.RevoluteJoint` | `physics:localPos0`, `physics:localPos1` | `(0, 0, 0)` relative to rotation center | Defines the exact center of rotation. If offset, the rotation will be eccentric, causing the robot to lose its grasp as the object moves laterally. |

## SECTION 4: Valid Behavior Specification (JSON)

```json
{
  "behavior_name": "TWISTING/TORQUE-BASED ROTATION",
  "target_object": "jar_lid",
  "robot": "franka_panda",
  "usd_physics_configuration": {
    "joint_type": "UsdPhysics.RevoluteJoint",
    "axis": "Z",
    "localPos0": [0.0, 0.0, 0.0],
    "localPos1": [0.0, 0.0, 0.0],
    "lowerLimit": -360.0,
    "upperLimit": 360.0,
    "driveAPI": {
      "type": "angular",
      "damping": 0.5,
      "stiffness": 0.0,
      "maxForce": 5.0
    },
    "materialAPI": {
      "staticFriction": 1.2,
      "dynamicFriction": 1.0,
      "frictionCombineMode": "max"
    }
  },
  "execution_sequence": [
    {
      "action": "move_to_pre_grasp",
      "target_pose": "aligned_with_lid_z_axis"
    },
    {
      "action": "close_gripper",
      "force": 40.0
    },
    {
      "action": "apply_wrist_torque",
      "axis": "Z",
      "magnitude": 3.0,
      "duration": 2.0
    }
  ]
}
```

## SECTION 5: Invalid Behavior Specification (JSON)

```json
{
  "behavior_name": "TWISTING/TORQUE-BASED ROTATION",
  "target_object": "jar_lid",
  "robot": "franka_panda",
  "usd_physics_configuration": {
    "joint_type": "UsdPhysics.RevoluteJoint",
    "axis": "X", 
    "localPos0": [0.05, 0.0, 0.0], 
    "lowerLimit": 0.0,
    "upperLimit": 0.0, 
    "driveAPI": {
      "type": "angular",
      "damping": 50.0, 
      "maxForce": 100.0 
    },
    "materialAPI": {
      "staticFriction": 0.1 
    }
  }
}
```

**Violated Semantic Constraint Domains:**
- **Directional Semantics:** Axis is set to "X" instead of "Z", meaning the robot will try to flip the lid like a coin rather than twist it.
- **Pivot Placement:** `localPos0` has an offset of 0.05m. The rotation will be eccentric, causing the lid to swing in an arc and break the grasp.
- **Range Limits:** Both limits are 0.0, meaning the joint is completely locked and cannot rotate.
- **Force/Torque Realism:** Damping is 50.0 and maxForce is 100.0 Nm. This exceeds the Franka's wrist torque limit (12 Nm), so the robot will fail to turn it and likely trigger a safety fault.
- **Contact/Friction:** Static friction is 0.1. The gripper will slip immediately upon applying torque.

---

# STACKING/PLACEMENT BEHAVIOR — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

This section maps the applicable semantic constraints for the stacking and placement behavior to the specific Isaac Sim APIs and USD schemas. The correct application of these parameters is critical for achieving a stable and realistic simulation of the Franka Emika Panda robot performing this task.

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value Range (for Franka) | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Range Limits** | `UsdPhysics.Joint` | `lowerLimit`, `upperLimit` | For gripper: `0.0` to `0.08` (meters). For arm joints: Use robot URDF values. | Defines the operational range of the gripper and arm joints. Incorrect limits will cause unrealistic motion or prevent the robot from successfully grasping or releasing the object. |
| **Pivot Placement** | `UsdGeom.Xformable` | `xformOp:translate`, `xformOp:orient` | Object-specific, defined in Blender/USD. | The pivot point (`xformOp`) of the object being manipulated is critical. If it's not at the object's center of mass or a logical grasp point, the robot's IK solver will fail to compute a stable grasp and placement pose, leading to immediate instability upon release. |
| **Clearance/Tolerance** | `omni.isaac.core.controllers.RMPFlowController` | `end_effector_frame_name`, `target_prim_frame_name` | N/A (runtime calculation) | The controller uses the transforms of the end-effector and target prims to calculate the required motion. The final placement precision depends on the controller's ability to minimize the distance between these frames. A loose tolerance in the controller or noisy sensor data will result in misplaced objects that topple. |
| **Force/Torque Realism** | `UsdPhysics.DriveAPI` | `maxForce` (for prismatic/gripper joint) | `70.0` (Newtons) | This directly corresponds to the Franka Hand's maximum continuous force. Exceeding this value results in an unrealistic simulation where the gripper can hold objects heavier than its real-world counterpart. Setting it too low may cause the robot to drop the object. |
| **Force/Torque Realism** | `UsdPhysics.DriveAPI` | `maxForce` (for revolute joints) | `87.0` for main joints, `12.0` for wrist (Newton-meters) | These values represent the maximum torque for the Panda's joints. Incorrect values will lead to unrealistic acceleration or the inability to lift the specified 3kg payload, breaking the simulation's physical accuracy. |
| **Contact/Friction** | `PhysxSchema.PhysxMaterialAPI` | `staticFriction`, `dynamicFriction` | `0.5` to `0.8` (unitless) | These parameters define the frictional forces between the object and the surface it's placed on. If friction is too low, the object will slide off upon placement, especially if the surface is not perfectly level. If it's too high, the object might stick unrealistically. |
| **Material Properties** | `UsdPhysics.MassAPI` | `mass` | `0.1` to `3.0` (kg) | This defines the object's mass. It must be within the Franka's 3kg payload limit. An incorrect mass will invalidate the simulation, as the robot's dynamics (e.g., joint torques) are directly affected by the payload. |
| **Material Properties** | `PhysxSchema.PhysxMaterialAPI` | `restitution` | `0.0` to `0.2` (unitless) | This controls the "bounciness" of the object. For stable stacking, restitution should be low. A high value will cause the object to bounce upon release, making stable placement impossible. |
| **Kinematic Chain** | `UsdPhysics.ArticulationRootAPI` | N/A | Applied to the root prim of the robot model. | This API is essential for treating the robot as a single articulated system. Without it, the joints and links would behave as independent rigid bodies, and the robot would simply fall apart. |
| **Feedback** | `omni.isaac.core.articulation_view.ArticulationView` | `get_joint_positions()`, `get_joint_velocities()` | N/A (runtime data) | These functions provide the necessary feedback for the control loop to determine the current state of the robot and calculate the next action. Without this feedback, closed-loop control is impossible. |
| **Safety** | `UsdPhysics.Joint` | `lowerLimit`, `upperLimit` | Use robot URDF values. | These act as hard stops for the robot's joints, preventing self-collision and unrealistic configurations. Incorrect limits can lead to simulation errors or damage to the virtual robot model. |

## SECTION 4: Valid Behavior Specification (JSON)

This JSON block provides a valid instance of the stacking/placement behavior for a Franka Emika Panda robot, demonstrating the configuration of key parameters for a successful operation. In this example, the robot is tasked with picking up a small cube and placing it on top of a larger cube.

```json
{
  "behavior_name": "STACKING_PLACEMENT_CUBE_ON_CUBE",
  "robot": {
    "name": "Franka_Emika_Panda",
    "gripper": {
      "type": "Franka Hand",
      "max_force": 70.0, 
      "max_opening": 0.08 
    },
    "payload_capacity": 3.0 
  },
  "objects": [
    {
      "id": "small_cube",
      "usd_path": "/World/small_cube",
      "mass": 0.1, 
      "dimensions": [0.05, 0.05, 0.05], 
      "material_properties": {
        "static_friction": 0.7,
        "dynamic_friction": 0.6,
        "restitution": 0.05 
      }
    },
    {
      "id": "large_cube",
      "usd_path": "/World/large_cube",
      "mass": 1.0, 
      "dimensions": [0.1, 0.1, 0.1], 
      "material_properties": {
        "static_friction": 0.7,
        "dynamic_friction": 0.6,
        "restitution": 0.05 
      }
    }
  ],
  "task": {
    "type": "stacking",
    "pickup_object_id": "small_cube",
    "place_on_object_id": "large_cube",
    "target_relative_position": [0.0, 0.0, 0.05], 
    "pre_release_clearance": 0.01, 
    "release_height": 0.005, 
    "approach_vector": [0.0, 0.0, 1.0], 
    "grasp_pose": {
      "position": [0.0, 0.0, 0.025], 
      "orientation": [0.707, 0.0, 0.707, 0.0] 
    }
  },
  "simulation_parameters": {
    "physics_scene": {
      "gravity": [0.0, 0.0, -9.81],
      "simulation_steps_per_second": 120 
    },
    "collision_detection": {
      "enable_ccd": true 
    }
  }
}
```

## SECTION 5: Invalid Behavior Specification (JSON)

This JSON block presents an invalid configuration for the stacking/placement behavior, highlighting common errors that violate semantic constraints. Each violation is explicitly noted with its corresponding constraint domain.

```json
{
  "behavior_name": "STACKING_PLACEMENT_INVALID_HEAVY_OBJECT",
  "robot": {
    "name": "Franka_Emika_Panda",
    "gripper": {
      "type": "Franka Hand",
      "max_force": 70.0,
      "max_opening": 0.08
    },
    "payload_capacity": 3.0
  },
  "objects": [
    {
      "id": "heavy_block",
      "usd_path": "/World/heavy_block",
      "mass": 5.0, 
      "dimensions": [0.1, 0.1, 0.1],
      "material_properties": {
        "static_friction": 0.7,
        "dynamic_friction": 0.6,
        "restitution": 0.05
      }
    },
    {
      "id": "slippery_surface",
      "usd_path": "/World/slippery_surface",
      "mass": 1.0,
      "dimensions": [0.2, 0.2, 0.01],
      "material_properties": {
        "static_friction": 0.1, 
        "dynamic_friction": 0.05, 
        "restitution": 0.1
      }
    }
  ],
  "task": {
    "type": "stacking",
    "pickup_object_id": "heavy_block",
    "place_on_object_id": "slippery_surface",
    "target_relative_position": [0.0, 0.0, 0.05],
    "pre_release_clearance": 0.01,
    "release_height": 0.005,
    "approach_vector": [0.0, 0.0, 1.0],
    "grasp_pose": {
      "position": [0.0, 0.0, 0.025],
      "orientation": [0.707, 0.0, 0.707, 0.0]
    }
  },
  "simulation_parameters": {
    "physics_scene": {
      "gravity": [0.0, 0.0, -9.81],
      "simulation_steps_per_second": 120
    },
    "collision_detection": {
      "enable_ccd": true
    }
  }
}
```

**Violated Semantic Constraints:**

*   **Material Properties (Mass):** The `heavy_block` has a `mass` of 5.0 kg, which exceeds the Franka Emika Panda's maximum payload capacity of 3.0 kg. This violates the payload constraint, and the robot would fail to lift the object in a real-world scenario.
*   **Contact/Friction:** The `slippery_surface` has very low `static_friction` (0.1) and `dynamic_friction` (0.05). This would make stable placement impossible, as the `heavy_block` would slide off immediately upon release, violating the stability requirement of the stacking behavior.

---

# COMPLIANT/FORCE-CONTROLLED MOTION — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value Range for Franka | Justification |
| :--- | :--- | :--- | :--- | :--- |
| 1. Directional Semantics | `omni.isaac.core.controllers.ArticulationController` | `selection_matrix` (in custom impedance controller) | `[0, 0, 1, 0, 0, 0]` (Z-axis force control) | **Why:** Determines which Cartesian axes are force-controlled vs. position-controlled. **What breaks:** If incorrect, the robot might push uncontrollably along the wrong axis, causing instability or missing the surface entirely. |
| 2. Range Limits | `PhysxSchema.PhysxArticulationAPI` | `physxArticulation:maxJointVelocity` | `1.0` to `2.175` rad/s | **Why:** Limits the maximum speed the joints can move when yielding to forces. **What breaks:** If set too high, the robot may snap back violently when contact is lost; if too low, it cannot comply fast enough to impact. |
| 4. Clearance/Tolerance | `UsdPhysics.DriveAPI` | `physics:stiffness` | `0.0` (for force-controlled axes) | **Why:** Disables position tracking stiffness along the compliant axis, allowing the applied force to dictate motion. **What breaks:** If stiffness is non-zero on a force axis, the position controller will fight the force controller, leading to massive torque spikes and simulation explosions. |
| 5. Sequential Dependency | `omni.isaac.sensor.ContactSensor` | `threshold` | `1.0` to `5.0` N | **Why:** Defines the minimum force required to register a contact event and transition from approach to force control. **What breaks:** If too low, sensor noise triggers premature switching; if too high, the robot crashes into the surface before switching modes. |
| 6. Force/Torque Realism | `UsdPhysics.DriveAPI` | `physics:maxForce` | `12.0` (wrist) to `87.0` (base) Nm | **Why:** Clamps the maximum torque the simulated actuators can output, matching the Franka Panda's hardware limits. **What breaks:** If infinite or too high, the simulated robot can exert unrealistic forces, breaking objects or violating the 3 kg payload constraint. |
| 7. Contact/Friction | `UsdPhysics.MaterialAPI` | `physics:dynamicFriction` | `0.1` to `0.5` | **Why:** Defines the lateral resistance when the force-controlled tool slides across the surface. **What breaks:** If zero, the tool slips uncontrollably; if too high, the robot may get stuck or experience stick-slip oscillations during scrubbing. |
| 9. Material Properties | `UsdPhysics.DriveAPI` | `physics:damping` | `10.0` to `50.0` Ns/m | **Why:** Provides the necessary damping to dissipate energy during contact and prevent oscillations. **What breaks:** If under-damped, the robot will bounce repeatedly on the surface (chattering); if over-damped, it will respond too sluggishly to surface variations. |
| 11. Kinematic Chain | `omni.isaac.motion_generation.LulaKinematicsSolver` | `position_tolerance` | `0.01` m | **Why:** Ensures the IK solver finds configurations that are close to the desired pose while avoiding singularities. **What breaks:** If the robot enters a singularity, the Jacobian becomes ill-conditioned, causing infinite joint velocity commands and simulation crashes. |
| 12. Energy | `PhysxSchema.PhysxSceneAPI` | `physxScene:bounceThresholdVelocity` | `0.2` m/s | **Why:** Determines the relative velocity below which colliding objects will not bounce, aiding in stable contact establishment. **What breaks:** If set too low, micro-collisions during force control will cause continuous jittering and energy injection into the system. |
| 13. Feedback | `omni.isaac.core.articulations.ArticulationView` | `get_measured_joint_efforts()` | N/A (Read-only) | **Why:** Retrieves the simulated joint torques to estimate the external wrench for the impedance control loop. **What breaks:** If not called at every physics step (e.g., 120 Hz or higher), the control loop lags, causing unstable force tracking and divergent behavior. |
| 14. Safety | `PhysxSchema.PhysxArticulationAPI` | `physxArticulation:sleepThreshold` | `0.0` | **Why:** Prevents the physics engine from putting the articulation to sleep when it is moving very slowly during force control. **What breaks:** If the articulation sleeps, it stops applying the commanded torques, causing the robot to drop the tool or lose contact force abruptly. |

## SECTION 4: Valid Behavior Specification (JSON)

```json
{
  "behavior_id": "compliant_motion_scrubbing",
  "robot": "franka_panda",
  "target_object": "wooden_table",
  "control_mode": "cartesian_impedance",
  "parameters": {
    "selection_matrix": {
      "x": "position",
      "y": "position",
      "z": "force",
      "rx": "position",
      "ry": "position",
      "rz": "position"
    },
    "target_wrench": {
      "force": [0.0, 0.0, -15.0],
      "torque": [0.0, 0.0, 0.0]
    },
    "impedance_gains": {
      "stiffness": {
        "translational": [1000.0, 1000.0, 0.0],
        "rotational": [50.0, 50.0, 50.0]
      },
      "damping": {
        "translational": [31.6, 31.6, 60.0],
        "rotational": [10.0, 10.0, 10.0]
      }
    },
    "safety_limits": {
      "max_contact_force": 40.0,
      "max_joint_torques": [87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0],
      "max_velocity": 0.2
    },
    "physics_material": {
      "dynamic_friction": 0.3,
      "static_friction": 0.4,
      "restitution": 0.0
    }
  }
}
```

## SECTION 5: Invalid Behavior Specification (JSON)

```json
{
  "behavior_id": "compliant_motion_scrubbing_invalid",
  "robot": "franka_panda",
  "target_object": "wooden_table",
  "control_mode": "cartesian_impedance",
  "parameters": {
    "selection_matrix": {
      "x": "position",
      "y": "position",
      "z": "force",
      "rx": "position",
      "ry": "position",
      "rz": "position"
    },
    "target_wrench": {
      "force": [0.0, 0.0, -150.0],
      "torque": [0.0, 0.0, 0.0]
    },
    "impedance_gains": {
      "stiffness": {
        "translational": [1000.0, 1000.0, 5000.0],
        "rotational": [50.0, 50.0, 50.0]
      },
      "damping": {
        "translational": [31.6, 31.6, 0.0],
        "rotational": [10.0, 10.0, 10.0]
      }
    },
    "safety_limits": {
      "max_contact_force": 200.0,
      "max_joint_torques": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
      "max_velocity": 5.0
    }
  }
}
```

The invalid specification violates several semantic constraint domains. It violates Domain 2 (Range Limits) because the target wrench force of -150 N exceeds the Franka Panda's continuous force limit of 70 N and its payload capacity, which will cause hardware faults in reality and unrealistic behavior in simulation. It violates Domain 4 (Clearance/Tolerance) because the Z-axis stiffness is set to 5000.0 despite being a force-controlled axis; this causes the position controller to fight the force controller, leading to massive instability. It violates Domain 6 (Force/Torque Realism) by setting the maximum joint torques to 1000.0 Nm, which far exceeds the physical limits of the Franka Panda's 87 Nm base joints and 12 Nm wrist joints. It violates Domain 12 (Energy) because the Z-axis translational damping is set to 0.0; without damping, the robot will bounce uncontrollably upon contact, injecting energy into the system and causing the simulation to explode. Finally, it violates Domain 14 (Safety) because the maximum contact force limit of 200.0 N is unsafe for collaborative robots and would cause severe damage to the environment or the robot itself.

---

# IMPACT/STRIKING BEHAVIOR — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

This section details the mapping of each applicable semantic constraint domain to specific Isaac Sim APIs and USD schemas. It also provides recommended value ranges for the Franka Emika Panda robot and justifications for each parameter, highlighting the consequences of incorrect settings.

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value Range (Franka) | Justification (WHY this parameter, WHAT breaks if wrong) |
| :---------------- | :------------------------- | :------------- | :------------------------------- | :------------------------------------------------------- |
| Force/Torque Realism | `PhysxSchema.PhysxRigidBodyAPI` | `physxRigidBody:maxContactImpulse` | `1000 - 5000 Ns` | This parameter directly controls the maximum impulse that can be applied during a collision. For impact behaviors, a sufficiently high impulse is crucial to accurately simulate the energy transfer. If set too low, the impact will appear soft or dampened, failing to transfer the expected kinetic energy, and the object being struck might not react realistically (e.g., a nail won't be hammered, a bell won't ring with appropriate force). |
| Force/Torque Realism | `PhysxSchema.PhysxRigidBodyAPI` | `physxRigidBody:maxDepenetrationVelocity` | `10 m/s` | This parameter defines the maximum velocity at which objects can separate after penetration. For high-speed impacts, a high depenetration velocity is necessary to prevent objects from getting stuck or exhibiting unnatural bouncing. If too low, objects might interpenetrate or resolve collisions too slowly, leading to visual artifacts and inaccurate physics. |
| Contact/Friction | `PhysxSchema.PhysxMaterialAPI` | `physxMaterial:staticFriction` | `0.5 - 0.9` | Static friction influences the force required to initiate sliding between two surfaces in contact. For impact behaviors, this is critical for the brief contact phase where the end-effector might grip or slide against the target object. An incorrect value can lead to the end-effector slipping prematurely or sticking unnaturally, affecting the direction and magnitude of the impact force. |
| Contact/Friction | `PhysxSchema.PhysxMaterialAPI` | `physxMaterial:dynamicFriction` | `0.3 - 0.7` | Dynamic friction governs the resistance to motion between two surfaces that are already sliding. While the primary action is impact, dynamic friction plays a role in how the end-effector interacts with the object immediately after the initial strike or if there's a glancing blow. Too low, and the end-effector might slide off too easily; too high, and it might drag the object unnaturally. |
| Contact/Friction | `PhysxSchema.PhysxMaterialAPI` | `physxMaterial:restitution` | `0.1 - 0.5` | Restitution determines the "bounciness" of a collision. For impact behaviors, a low to moderate restitution is generally desired to simulate energy absorption rather than a perfectly elastic bounce. If restitution is too high, the end-effector might bounce back excessively, reducing the effective energy transfer and making the impact appear less forceful. If too low, the impact might seem overly damped. |
| Energy | `PhysxSchema.PhysxRigidBodyAPI` | `physxRigidBody:linearDamping` | `0.01 - 0.1` | Linear damping reduces the linear velocity of a rigid body over time. While the impact itself is a sudden energy transfer, some damping is necessary to prevent perpetual motion or unrealistic oscillations after the primary event. Excessive damping will absorb too much kinetic energy, making the impact less effective, while too little can lead to unstable simulations. |
| Energy | `PhysxSchema.PhysxRigidBodyAPI` | `physxRigidBody:angularDamping` | `0.01 - 0.1` | Similar to linear damping, angular damping reduces the angular velocity. This is important for controlling any rotational motion induced by the impact. Too much angular damping can make the robot's end-effector or the impacted object appear sluggish, while too little can lead to unrealistic spinning or instability. |
| Kinematic Chain | `PhysxSchema.PhysxArticulationAPI` | `physxArticulation:solverPositionIterationCount` | `8 - 16` | This parameter controls the number of iterations the physics solver performs to resolve joint constraints. For high-speed impacts, accurate joint constraint resolution is crucial to prevent the robot's arm from collapsing or behaving unnaturally. Too few iterations can lead to "joint popping" or inaccurate force transmission through the kinematic chain, especially during sudden impacts. |
| Kinematic Chain | `PhysxSchema.PhysxArticulationAPI` | `physxArticulation:solverVelocityIterationCount` | `2 - 4` | This parameter controls the number of iterations for velocity constraints. It is essential for ensuring that the robot's joints maintain their velocity limits and respond correctly to sudden forces. Insufficient iterations can result in inaccurate velocity propagation through the arm, leading to unstable or unrealistic impact responses. |
| Safety | `PhysxSchema.PhysxRigidBodyAPI` | `physxRigidBody:maxAngularVelocity` | `100 rad/s` | This parameter sets a limit on the maximum angular velocity of a rigid body. For safety and stability, especially during high-speed impacts, limiting the rotational speed of the end-effector and other robot links is important. Exceeding this can lead to numerical instability or unrealistic rotational behavior. |
| Safety | `PhysxSchema.PhysxRigidBodyAPI` | `physxRigidBody:sleepThreshold` | `0.005` | The sleep threshold determines when a rigid body can "sleep" (i.e., stop being simulated to save performance). For impact behaviors, it's important that objects involved in the impact don't go to sleep prematurely, as this would prevent accurate force propagation. A value too high might cause objects to become unresponsive too quickly after a minor impact. |
| Safety | `PhysxSchema.PhysxRigidBodyAPI` | `physxRigidBody:stabilizationThreshold` | `0.001` | This threshold helps in stabilizing resting bodies. While less critical during the active impact, it contributes to the overall stability of the scene before and after the impact. An unstable scene can lead to unpredictable impact results. |
| Feedback | `PhysxSchema.PhysxContactReportAPI` | `physxContactReport:enabled` | `True` | Enabling contact reports is crucial for receiving feedback on collisions. For impact behaviors, this allows the simulation to detect when and where contact occurs, providing data for validation and control. If disabled, the system will not register collisions, making it impossible to detect successful impacts or trigger subsequent actions. |
| Feedback | `PhysxSchema.PhysxContactReportAPI` | `physxContactReport:threshold` | `0.1 N` | This threshold defines the minimum force required for a contact to be reported. For impact behaviors, setting an appropriate threshold ensures that only significant impacts are registered, filtering out minor grazing contacts. If too high, actual impacts might be missed; if too low, the system might be flooded with irrelevant contact events. |
| Material Properties | `PhysxSchema.PhysxMaterialAPI` | `physxMaterial:density` | `7850 kg/m^3` (steel) | The density of the material directly affects the mass of the object, which is a fundamental component in kinetic energy calculations (`KE = 0.5 * m * v^2`). For accurate impact simulation, the mass of both the end-effector and the target object must be realistic. Incorrect density will lead to inaccurate mass, resulting in unrealistic energy transfer and impact forces. |

## SECTION 4: Valid Behavior Specification (JSON)

This JSON block represents a valid instance of the IMPACT/STRIKING BEHAVIOR, configured for the Franka Emika Panda robot to strike a small, rigid object. The parameters are chosen to reflect a forceful, intentional collision where kinetic energy transfer is paramount.

```json
{
  "behavior_name": "IMPACT/STRIKING BEHAVIOR",
  "robot_model": "Franka Emika Panda",
  "end_effector": {
    "type": "Franka Hand",
    "max_force": "70 N",
    "max_opening": "80 mm"
  },
  "target_object": {
    "name": "Nail",
    "material": {
      "type": "steel",
      "density": 7850,
      "static_friction": 0.6,
      "dynamic_friction": 0.4,
      "restitution": 0.2
    },
    "dimensions": {
      "length": "50 mm",
      "diameter": "3 mm"
    },
    "initial_pose": {
      "position": [0.5, 0.0, 0.1],
      "orientation": [0.0, 0.0, 0.0, 1.0] 
    }
  },
  "impact_parameters": {
    "approach_speed": {
      "linear": "2.0 m/s",
      "angular": "0.0 rad/s"
    },
    "impact_force_threshold": "50 N",
    "impact_duration": "0.01 s",
    "end_effector_pose_at_impact": {
      "position": [0.4, 0.0, 0.05],
      "orientation": [0.0, 0.707, 0.0, 0.707] 
    },
    "post_impact_retraction_distance": "0.05 m"
  },
  "physics_settings": {
    "max_contact_impulse": 2500,
    "max_depenetration_velocity": 10,
    "linear_damping": 0.05,
    "angular_damping": 0.05,
    "solver_position_iteration_count": 12,
    "solver_velocity_iteration_count": 3,
    "max_angular_velocity": 100,
    "sleep_threshold": 0.005,
    "stabilization_threshold": 0.001
  },
  "feedback_settings": {
    "contact_report_enabled": true,
    "contact_report_threshold": 0.5
  }
}
```

## SECTION 5: Invalid Behavior Specification (JSON)

This JSON block illustrates an invalid configuration for the IMPACT/STRIKING BEHAVIOR, specifically designed to violate several semantic constraint domains. Understanding these violations is crucial for debugging and ensuring robust behavior implementation.

```json
{
  "behavior_name": "IMPACT/STRIKING BEHAVIOR",
  "robot_model": "Franka Emika Panda",
  "end_effector": {
    "type": "Franka Hand",
    "max_force": "70 N",
    "max_opening": "80 mm"
  },
  "target_object": {
    "name": "Bell",
    "material": {
      "type": "rubber",
      "density": 1100,
      "static_friction": 0.9,
      "dynamic_friction": 0.8,
      "restitution": 0.9
    },
    "dimensions": {
      "radius": "50 mm",
      "height": "70 mm"
    },
    "initial_pose": {
      "position": [0.5, 0.0, 0.1],
      "orientation": [0.0, 0.0, 0.0, 1.0]
    }
  },
  "impact_parameters": {
    "approach_speed": {
      "linear": "0.1 m/s",
      "angular": "0.0 rad/s"
    },
    "impact_force_threshold": "5 N",
    "impact_duration": "0.5 s",
    "end_effector_pose_at_impact": {
      "position": [0.4, 0.0, 0.05],
      "orientation": [0.0, 0.707, 0.0, 0.707]
    },
    "post_impact_retraction_distance": "0.01 m"
  },
  "physics_settings": {
    "max_contact_impulse": 100,
    "max_depenetration_velocity": 1,
    "linear_damping": 0.5,
    "angular_damping": 0.5,
    "solver_position_iteration_count": 2,
    "solver_velocity_iteration_count": 1,
    "max_angular_velocity": 10,
    "sleep_threshold": 0.1,
    "stabilization_threshold": 0.05
  },
  "feedback_settings": {
    "contact_report_enabled": false,
    "contact_report_threshold": 10.0
  }
}
```

**Violated Semantic Constraint Domains:**

1.  **Force/Torque Realism:** The `approach_speed` is set to a very low `0.1 m/s`, and `max_contact_impulse` is `100 Ns`. This is insufficient for a high-speed impact behavior where significant kinetic energy transfer is the primary goal. The impact would be perceived as a gentle push rather than a strike, failing to achieve the intended effect (e.g., ringing a bell with force). The `max_depenetration_velocity` of `1 m/s` is also too low for high-speed impacts, potentially leading to interpenetration or unrealistic collision resolution.

2.  **Energy:** The `linear_damping` and `angular_damping` are set to `0.5`, which are excessively high. This would cause the end-effector and the target object to lose kinetic and angular energy too rapidly, making the impact appear overly damped and ineffective. The energy transfer would be significantly reduced, undermining the core characteristic of an impact behavior.

3.  **Contact/Friction:** The `target_object` material is specified as `rubber` with a `restitution` of `0.9`. While rubber can be bouncy, a high restitution for an impact behavior meant to *transfer* energy (like hammering) is counterproductive. This would cause the end-effector to bounce off the target object excessively, reducing the effective force transmission and making the interaction less like a strike and more like a bounce. The high static and dynamic friction values might also cause the end-effector to stick unnaturally.

4.  **Kinematic Chain:** The `solver_position_iteration_count` is `2` and `solver_velocity_iteration_count` is `1`. These values are far too low for accurately resolving joint constraints during a high-speed impact. This would lead to significant inaccuracies in force propagation through the robot's kinematic chain, potentially causing joint instability, unrealistic joint movements, or even simulation crashes, especially under the sudden forces of an impact.

5.  **Feedback:** The `contact_report_enabled` is set to `false`, and `contact_report_threshold` is `10.0 N`. Disabling contact reports means the simulation will not provide any information about collisions, making it impossible to detect if an impact occurred or to gather data for validation. A threshold of `10.0 N` is also too high, meaning only very strong contacts would be reported even if enabled, potentially missing lighter but still significant impacts. This directly violates the need for feedback to monitor and control the behavior.

6.  **Safety:** The `max_angular_velocity` is set to `10 rad/s`, which might be too restrictive for a high-speed impact where some rotational motion is expected. While safety is important, an overly restrictive limit can hinder the natural dynamics of the impact. The `sleep_threshold` of `0.1` and `stabilization_threshold` of `0.05` are too high, potentially causing objects to go to sleep prematurely or leading to an unstable simulation environment, especially for objects that are expected to move or react significantly after an impact.

---

# PULLING/TENSION-BASED MOTION — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

This section details the mapping of the identified semantic constraints to specific Isaac Sim API calls and Universal Scene Description (USD) schemas. The justifications clarify the necessity of each parameter and the consequences of incorrect configuration.

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value Range for Franka | Justification (WHY this parameter, WHAT breaks if wrong) |
| :--- | :--- | :--- | :--- | :--- |
| 1. Directional Semantics | `UsdPhysics.DriveAPI` (for joint control) or `omni.isaac.core.articulations.Articulation.set_joint_velocity_targets` / `set_joint_position_targets` | `physics:targetVelocity` or `physics:targetPosition` | Varies based on object and desired pull speed; typically 0.01-0.1 m/s for linear pull, or 0.1-0.5 rad/s for rotational joint. | **Why:** Defines the direction and magnitude of the pulling motion. For a successful pull, the force must be applied precisely along the intended extraction axis. **What breaks:** Incorrect direction leads to binding, jamming, or failure to extract. Incorrect magnitude can cause excessive force, damaging the object or robot, or insufficient force, failing the task. |
| 2. Range Limits | `UsdPhysics.LimitAPI` (for joint limits) or `omni.isaac.core.articulations.Articulation.set_joint_limits` | `physics:low`, `physics:high` | Varies per joint and task; e.g., for a linear slide, 0.0 to 0.3 meters. | **Why:** Prevents over-extension or collision during the pulling motion. Essential for safe operation and to prevent damage to the robot, object, or environment. **What breaks:** Exceeding limits can cause collisions, joint damage, or an unrealistic simulation of the object's movement. |
| 4. Clearance/Tolerance | `UsdPhysics.CollisionAPI` (for collision geometry) or `omni.isaac.core.prims.GeometryPrim.set_collision_enabled` | `physics:collisionEnabled`, `physics:collisionGroup` | `True` for collision-active components; appropriate collision group assignments. | **Why:** Ensures the robot's gripper and arm can approach and grasp the object without unintended contact with the environment or the object itself. **What breaks:** Lack of proper clearance results in collisions, preventing successful grasping or pulling, and leading to simulation errors or unrealistic behavior. |
| 5. Sequential Dependency | `omni.isaac.core.articulations.Articulation.set_joint_position_targets` (for gripper control) | `physics:targetPosition` (for gripper joints) | 0.0 (closed) to 0.08 (open) meters for Franka Hand. | **Why:** The object must be firmly grasped before any pulling force is applied to ensure stability and prevent slippage. This is a critical pre-condition for the behavior. **What breaks:** Attempting to pull without a secure grasp will result in the object slipping from the gripper, failing the task. |
| 6. Force/Torque Realism | `UsdPhysics.DriveAPI` (for joint control) or `omni.isaac.core.articulations.Articulation.set_joint_effort_targets` | `physics:stiffness`, `physics:damping`, `physics:maxForce` (for drives); `effort` (for direct effort control) | `stiffness`: 1000-5000 N/m, `damping`: 100-500 Ns/m; `maxForce`: up to 70 N for gripper, up to 87 Nm for main joints. | **Why:** Accurately simulates the robot's ability to exert and withstand forces. The applied force must be sufficient to overcome resistance but not exceed the robot's physical limits. **What breaks:** Insufficient force leads to task failure (object not moving). Excessive force can cause unrealistic acceleration, object damage, or instability in the robot. |
| 7. Contact/Friction | `UsdPhysics.MaterialAPI` (for physics materials) or `omni.isaac.core.materials.PhysicsMaterial.set_friction_coefficients` | `physics:staticFriction`, `physics:dynamicFriction`, `physics:restitution` | `staticFriction`: 0.5-0.9; `dynamicFriction`: 0.3-0.7; `restitution`: 0.0-0.1. | **Why:** Defines the interaction between the gripper and the object, and between the object and its environment. High friction is needed for a secure grasp, while appropriate friction with the environment dictates the resistance to pulling. **What breaks:** Low friction between gripper and object causes slippage. Incorrect friction with the environment leads to unrealistic resistance, making the pull too easy or impossible. |
| 9. Material Properties | `UsdPhysics.RigidBodyAPI` (for mass properties) or `omni.isaac.core.prims.RigidPrim.set_mass` | `physics:mass`, `physics:density` | `mass`: 0.1-3.0 kg (for object); `density`: Varies based on material (e.g., 2700 kg/m^3 for aluminum). | **Why:** Determines how the object responds to applied forces. An object's rigidity and mass are crucial for realistic pulling behavior. **What breaks:** Incorrect mass or density leads to unrealistic acceleration or deceleration. Fragile materials not modeled correctly can shatter or deform unrealistically under tension. |
| 11. Kinematic Chain | `UsdPhysics.ArticulationAPI` (for robot structure) or `omni.isaac.core.articulations.Articulation` | N/A (inherent in robot USD definition) | N/A | **Why:** The robot's kinematic structure defines its reach, joint limits, and how forces propagate through its links. Proper configuration ensures the robot can execute the pull efficiently and stably. **What breaks:** An improperly defined kinematic chain can lead to incorrect joint movements, self-collisions, or an inability to reach the target object or execute the pulling trajectory. |
| 12. Energy | `UsdPhysics.RigidBodyAPI` (for damping) or `omni.isaac.core.prims.RigidPrim.set_linear_damping` / `set_angular_damping` | `physics:linearDamping`, `physics:angularDamping` | `linearDamping`: 0.01-0.1; `angularDamping`: 0.01-0.1. | **Why:** Controls the dissipation of energy, preventing excessive oscillations or unrealistic jerks upon object release. **What breaks:** Without proper damping, the object might oscillate violently or fly off uncontrollably upon release, leading to unrealistic simulation and potential secondary collisions. |
| 13. Feedback | `omni.isaac.core.articulations.Articulation.get_measured_joint_forces` / `get_measured_joint_velocities` / `get_measured_joint_positions` | N/A (read-only properties) | N/A | **Why:** Real-time feedback from force/torque sensors and joint encoders is critical for detecting task completion (e.g., object release) or unexpected resistance. This enables adaptive control strategies. **What breaks:** Lack of feedback means the robot cannot react to changes in the environment or object state, leading to inefficient or failed pulls, or even damage if resistance is too high. |
| 14. Safety | `UsdPhysics.CollisionAPI` (for collision filtering) or `omni.isaac.core.prims.GeometryPrim.set_collision_group` | `physics:collisionGroup`, `physics:filteredPairs` | Appropriate group assignments to prevent unwanted collisions between robot and environment/self. | **Why:** Ensures the robot operates within safe limits, preventing collisions with itself, the environment, or personnel. This is paramount for real-world deployment and robust simulation. **What breaks:** Unchecked collisions can lead to simulation crashes, unrealistic behavior, or damage to virtual assets. In a real robot, this would be a major safety hazard. |


## SECTION 4: Valid Behavior Specification (JSON)

This JSON block provides a valid specification for the PULLING/TENSION-BASED MOTION behavior, exemplified by pulling a drawer. The parameters are set within the recommended ranges for the Franka Emika Panda, ensuring physical realism and adherence to semantic constraints.

```json
{
  "behavior_name": "PULLING/TENSION-BASED_MOTION",
  "description": "Robot grasps a drawer handle and pulls it open along its linear axis.",
  "robot": {
    "model": "Franka Emika Panda",
    "gripper": {
      "type": "Franka Hand",
      "max_continuous_force_N": 70,
      "max_opening_mm": 80
    },
    "payload_kg": 3,
    "wrist_torque_Nm": 12,
    "main_joint_torque_Nm": 87
  },
  "task_parameters": {
    "object_id": "drawer_cabinet_01_drawer_handle",
    "target_pull_direction_vector": [0.0, 1.0, 0.0], 
    "pull_distance_m": 0.25, 
    "pull_speed_m_s": 0.05, 
    "gripper_grasp_force_N": 50, 
    "gripper_opening_before_grasp_mm": 70,
    "gripper_closing_after_grasp_mm": 10,
    "max_pull_force_N": 60, 
    "force_feedback_threshold_N": 5, 
    "collision_avoidance_enabled": true,
    "material_properties": {
      "object_mass_kg": 1.5,
      "object_static_friction": 0.6,
      "object_dynamic_friction": 0.4,
      "object_restitution": 0.05
    },
    "damping": {
      "linear_damping": 0.05,
      "angular_damping": 0.05
    }
  },
  "isaac_sim_mapping": {
    "directional_semantics": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_velocity_targets",
      "parameter": "target_velocity",
      "value_source": "task_parameters.pull_speed_m_s"
    },
    "range_limits": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_limits",
      "parameter": "upper_limit",
      "value_source": "task_parameters.pull_distance_m"
    },
    "clearance_tolerance": {
      "api": "omni.isaac.core.prims.GeometryPrim.set_collision_enabled",
      "parameter": "collision_enabled",
      "value": true
    },
    "sequential_dependency": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_position_targets",
      "parameter": "target_position",
      "value_source": "task_parameters.gripper_closing_after_grasp_mm"
    },
    "force_torque_realism": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_effort_targets",
      "parameter": "effort",
      "value_source": "task_parameters.max_pull_force_N"
    },
    "contact_friction": {
      "api": "omni.isaac.core.materials.PhysicsMaterial.set_friction_coefficients",
      "parameters": {
        "static_friction": "task_parameters.material_properties.object_static_friction",
        "dynamic_friction": "task_parameters.material_properties.object_dynamic_friction"
      }
    },
    "material_properties": {
      "api": "omni.isaac.core.prims.RigidPrim.set_mass",
      "parameter": "mass",
      "value_source": "task_parameters.material_properties.object_mass_kg"
    },
    "energy": {
      "api": "omni.isaac.core.prims.RigidPrim.set_linear_damping",
      "parameter": "linear_damping",
      "value_source": "task_parameters.damping.linear_damping"
    },
    "feedback": {
      "api": "omni.isaac.core.articulations.Articulation.get_measured_joint_forces",
      "parameter": "measured_force",
      "threshold_source": "task_parameters.force_feedback_threshold_N"
    },
    "safety": {
      "api": "omni.isaac.core.prims.GeometryPrim.set_collision_group",
      "parameter": "collision_group",
      "value": "robot_safe_group"
    }
  }
}
```

## SECTION 5: Invalid Behavior Specification (JSON)

This JSON block presents an invalid specification for the PULLING/TENSION-BASED MOTION behavior, highlighting common errors that violate semantic constraints. Each violation is explicitly noted.

```json
{
  "behavior_name": "PULLING/TENSION-BASED_MOTION_INVALID",
  "description": "Robot attempts to pull a drawer with insufficient force and an incorrect direction, leading to failure.",
  "robot": {
    "model": "Franka Emika Panda",
    "gripper": {
      "type": "Franka Hand",
      "max_continuous_force_N": 70,
      "max_opening_mm": 80
    },
    "payload_kg": 3,
    "wrist_torque_Nm": 12,
    "main_joint_torque_Nm": 87
  },
  "task_parameters": {
    "object_id": "drawer_cabinet_01_drawer_handle",
    "target_pull_direction_vector": [1.0, 0.0, 0.0], 
    "pull_distance_m": 0.25, 
    "pull_speed_m_s": 0.05, 
    "gripper_grasp_force_N": 10, 
    "gripper_opening_before_grasp_mm": 70,
    "gripper_closing_after_grasp_mm": 10,
    "max_pull_force_N": 5, 
    "force_feedback_threshold_N": 5, 
    "collision_avoidance_enabled": true,
    "material_properties": {
      "object_mass_kg": 1.5,
      "object_static_friction": 0.1,
      "object_dynamic_friction": 0.05,
      "object_restitution": 0.05
    },
    "damping": {
      "linear_damping": 0.05,
      "angular_damping": 0.05
    }
  },
  "isaac_sim_mapping": {
    "directional_semantics": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_velocity_targets",
      "parameter": "target_velocity",
      "value_source": "task_parameters.pull_speed_m_s"
    },
    "range_limits": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_limits",
      "parameter": "upper_limit",
      "value_source": "task_parameters.pull_distance_m"
    },
    "clearance_tolerance": {
      "api": "omni.isaac.core.prims.GeometryPrim.set_collision_enabled",
      "parameter": "collision_enabled",
      "value": true
    },
    "sequential_dependency": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_position_targets",
      "parameter": "target_position",
      "value_source": "task_parameters.gripper_closing_after_grasp_mm"
    },
    "force_torque_realism": {
      "api": "omni.isaac.core.articulations.Articulation.set_joint_effort_targets",
      "parameter": "effort",
      "value_source": "task_parameters.max_pull_force_N"
    },
    "contact_friction": {
      "api": "omni.isaac.core.materials.PhysicsMaterial.set_friction_coefficients",
      "parameters": {
        "static_friction": "task_parameters.material_properties.object_static_friction",
        "dynamic_friction": "task_parameters.material_properties.object_dynamic_friction"
      }
    },
    "material_properties": {
      "api": "omni.isaac.core.prims.RigidPrim.set_mass",
      "parameter": "mass",
      "value_source": "task_parameters.material_properties.object_mass_kg"
    },
    "energy": {
      "api": "omni.isaac.core.prims.RigidPrim.set_linear_damping",
      "parameter": "linear_damping",
      "value_source": "task_parameters.damping.linear_damping"
    },
    "feedback": {
      "api": "omni.isaac.core.articulations.Articulation.get_measured_joint_forces",
      "parameter": "measured_force",
      "threshold_source": "task_parameters.force_feedback_threshold_N"
    },
    "safety": {
      "api": "omni.isaac.core.prims.GeometryPrim.set_collision_group",
      "parameter": "collision_group",
      "value": "robot_safe_group"
    }
  },
  "violations": [
    {
      "constraint_domain": "1. Directional Semantics",
      "description": "The target_pull_direction_vector is [1.0, 0.0, 0.0], which is perpendicular to the drawer's linear axis (assuming Y-axis pull). This will cause the drawer to bind or not move."
    },
    {
      "constraint_domain": "6. Force/Torque Realism",
      "description": "The max_pull_force_N is set to 5 N, which is likely insufficient to overcome the static friction of a typical drawer, leading to task failure."
    },
    {
      "constraint_domain": "7. Contact/Friction",
      "description": "The object_static_friction is set to 0.1 and object_dynamic_friction to 0.05, which are very low. This, combined with a gripper_grasp_force_N of 10 N, will likely cause the gripper to slip on the object."
    }
  ]
}
```

---

# ROLLING BEHAVIOR — Isaac Sim

## SECTION 3: Isaac Sim API Mapping

The following table maps the applicable semantic constraint domains to the specific Isaac Sim APIs, USD schemas, recommended parameter values for the Franka Emika Panda, and justifications for these choices.

| Constraint Domain | Isaac Sim API / USD Schema | Parameter Name | Recommended Value Range (for Franka) | Justification |
| :--- | :--- | :--- | :--- | :--- |
| Force/Torque Realism | `UsdPhysics.RigidBodyAPI` | `velocity` and `angularVelocity` attributes | Object-dependent, but gripper force must not exceed 70N. | The applied force must be sufficient to overcome inertia and friction while maintaining the rolling constraint. Incorrect forces will cause slipping or failure to initiate rolling. |
| Contact/Friction | `PhysxSchema.PhysxMaterialAPI` | `staticFriction`, `dynamicFriction` | `staticFriction`: 0.6-0.8, `dynamicFriction`: 0.4-0.6 | Friction is essential for rolling. If `staticFriction` is too low, the object will slip instead of roll. If `dynamicFriction` is too high, it will be difficult to initiate and maintain smooth rolling. |
| Kinematic Chain | `Usd.Prim` (for the robot) | N/A (defined by the robot's USD) | N/A | The robot's kinematic chain must be correctly defined in its USD file to allow for accurate inverse kinematics and trajectory planning. An incorrect kinematic chain will lead to unreachable targets and failed manipulation. |
| Safety | `UsdPhysics.ArticulationRootAPI` | `maxJointVelocity` attribute | Joint-specific, based on Franka specifications | Setting maximum joint velocities prevents the robot from moving too quickly and causing damage to itself, the object, or the environment. Exceeding these limits can lead to unstable behavior and safety hazards. |

## SECTION 4: Valid Behavior Specification (JSON)

```json
{
  "behavior_name": "ROLLING_BEHAVIOR",
  "robot_name": "Franka_Emika_Panda",
  "object_id": "sphere_01",
  "object_type": "sphere",
  "object_radius": 0.03, 
  "object_mass": 0.5, 
  "initial_position": [0.5, 0.0, 0.03], 
  "initial_orientation": [0.0, 0.0, 0.0, 1.0], 
  "target_linear_velocity": [0.1, 0.0, 0.0], 
  "target_angular_velocity": [0.0, -3.33, 0.0], 
  "applied_force": [5.0, 0.0, 0.0], 
  "force_application_point": [0.5, 0.0, 0.06], 
  "duration": 5.0, 
  "material_properties": {
    "staticFriction": 0.7,
    "dynamicFriction": 0.5
  },
  "safety_limits": {
    "max_joint_velocity_scale": 0.8 
  }
}
```

## SECTION 5: Invalid Behavior Specification (JSON)

This JSON block demonstrates an invalid instance of the ROLLING BEHAVIOR, violating several semantic constraint domains. The justifications for these violations are provided below.

```json
{
  "behavior_name": "ROLLING_BEHAVIOR_INVALID",
  "robot_name": "Franka_Emika_Panda",
  "object_id": "sphere_01",
  "object_type": "sphere",
  "object_radius": 0.01, 
  "object_mass": 5.0, 
  "initial_position": [0.5, 0.0, 0.01], 
  "initial_orientation": [0.0, 0.0, 0.0, 1.0], 
  "target_linear_velocity": [0.5, 0.0, 0.0], 
  "target_angular_velocity": [0.0, -10.0, 0.0], 
  "applied_force": [100.0, 0.0, 0.0], 
  "force_application_point": [0.5, 0.0, 0.01], 
  "duration": 2.0, 
  "material_properties": {
    "staticFriction": 0.1,
    "dynamicFriction": 0.05
  },
  "safety_limits": {
    "max_joint_velocity_scale": 1.5 
  }
}
```

**Violated Semantic Constraint Domains:**

*   **Range Limits:** The `object_mass` (5.0 kg) exceeds the Franka Panda's maximum payload (3 kg). The `object_radius` (0.01m) is too small for stable rolling with the given force. The `applied_force` (100 N) exceeds the Franka Hand's continuous force limit (70 N). The `target_linear_velocity` (0.5 m/s) and `target_angular_velocity` (10 rad/s) are excessively high for a controlled roll, likely leading to slipping.
*   **Force/Torque Realism:** The `applied_force` of 100 N is unrealistic for the Franka Hand's capabilities, which has a continuous force limit of 70 N. This would lead to motor overload or inability to execute the command.
*   **Contact/Friction:** The `staticFriction` (0.1) and `dynamicFriction` (0.05) values are too low. This would cause the object to slide rather than roll, failing to maintain the $v = \omega \cdot r$ kinematic constraint.
*   **Safety:** The `max_joint_velocity_scale` (1.5) attempts to set joint velocities beyond safe operating limits, which could damage the robot or create hazardous conditions. The excessive `applied_force` also poses a safety risk.
