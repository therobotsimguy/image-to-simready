# Behavior Definitions — 16 Behaviors x 15 Semantic Constraint Domains

> This document covers behavior definitions and constraint rules only. For Isaac Sim/PhysX parameters see ISAAC_SIM_PHYSICS_REFERENCE.md. For Blender geometry requirements see BLENDER_ASSET_REQUIREMENTS.md.

---

## Executive Summary

You have identified the **critical missing link** in 3D asset generation:

**Semantic Constraints** (the 15 domains) define the **rules** for what behaviors are valid.
**Behaviors** (the 8 fundamental types) define the **actions** that can be performed.

Together, they create a **Behavior-Constraint Matrix** that determines:
- Which behaviors are **valid** for a given object
- Which behaviors are **invalid** (violate semantic constraints)
- What **parameters** each behavior must have
- What **outcomes** each behavior should produce

This document maps all combinations.

---

## Part 1: The Behavior-Semantic Constraint Matrix

### Understanding the Matrix

For each object, we can create a matrix showing:
- **Rows**: The 8 fundamental behavior categories
- **Columns**: The 15 semantic constraint domains
- **Cells**: Whether that behavior is valid/invalid, and if valid, what constraints apply

### Example: Cabinet Door

```
                    1.Dir  2.Range  3.Pivot  4.Clear  5.Seq  6.Force  7.Contact  8.Sym  9.Mat  10.Vol  11.Kin  12.Energy  13.Feed  14.Safety  15.Aes
1. Rotational       ✓      ✓        ✓        ✓        ✗      ✓        ✓          ✓      ✓      ✓       ✓       ✓          ✓        ✓          ✓
2. Linear           ✗      ✗        ✗        ✗        ✗      ✗        ✗          ✗      ✗      ✗       ✗       ✗          ✗        ✗          ✗
3. Grasping         ✓      ✗        ✗        ✗        ✗      ✓        ✓          ✗      ✗      ✗       ✗       ✗          ✗        ✗          ✗
4. Insertion        ✗      ✗        ✗        ✗        ✗      ✗        ✗          ✗      ✗      ✗       ✗       ✗          ✗        ✗          ✗
5. Deformation      ✗      ✗        ✗        ✗        ✗      ✗        ✗          ✗      ✗      ✗       ✗       ✗          ✗        ✗          ✗
6. Contact          ✗      ✗        ✗        ✗        ✗      ✗        ✗          ✗      ✗      ✗       ✗       ✗          ✗        ✗          ✗
7. Sequential       ✓      ✓        ✓        ✓        ✓      ✓        ✓          ✓      ✓      ✓       ✓       ✓          ✓        ✓          ✓
8. Dynamic          ✗      ✗        ✗        ✗        ✗      ✗        ✗          ✗      ✗      ✗       ✗       ✗          ✗        ✗          ✗

Legend:
✓ = Valid (behavior is allowed)
✗ = Invalid (behavior violates constraint)
```

---

## Part 2: Detailed Behavior-Constraint Specifications

### BEHAVIOR 1: ROTATIONAL (Twist Right/Left)

#### Valid For:
- Door knobs, jar lids, valves, hinges, locks, fasteners

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | Must match hinge/pivot direction | Cabinet door: CW = outward |
| **2. Range Limits** | Must respect rotation limits | Cabinet: 0° - 110° max |
| **3. Pivot Placement** | Must rotate around correct pivot | Hinge on edge, not center |
| **4. Clearance** | Must not self-collide | Door edge clears frame |
| **5. Sequential** | May require prior actions | Unlock BEFORE twist |
| **6. Force/Torque** | Must apply realistic torque | Door knob: 1-10 Nm |
| **7. Contact/Friction** | Must maintain bearing contact | Hinge bearing stays engaged |
| **8. Symmetry** | May be symmetric or asymmetric | Hinge on one side only |
| **9. Material** | Material affects friction | Metal hinge vs. plastic |
| **10. Internal Volume** | May prevent certain directions | Shelves inside prevent inward |
| **11. Kinematic Chain** | Single revolute joint | One axis of rotation |
| **12. Energy** | May be gravity-driven or powered | Gravity-driven hinge |
| **13. Feedback** | May need limit switches | Limit switch at 110° |
| **14. Safety** | Hard stops prevent over-rotation | Cannot exceed 110° |
| **15. Aesthetic** | May affect appearance | Hinge visible or hidden |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Twist Right (Outward)",
  "object": "Cabinet Door",
  "constraints": {
    "direction": "clockwise_outward",
    "rotation_axis": [0, 0, 1],
    "rotation_limits": [0.0, 1.92],
    "pivot_location": [0.4, 2.0, 0.0],
    "torque_required": 5.0,
    "friction_coefficient": 0.15,
    "damping": 2.0,
    "collision_check": true,
    "limit_switch": true
  },
  "invalid_alternatives": [
    "Twist Left (Inward) - violates Domain 1 (Directional) and Domain 10 (Internal Volume)"
  ]
}
```

#### Invalid Behavior Specifications:

```json
{
  "behavior": "Twist Left (Inward)",
  "object": "Cabinet Door",
  "reason": "INVALID",
  "violations": [
    "Domain 1 (Directional Semantics): Cabinet has internal shelves, must open outward",
    "Domain 10 (Internal Volume): Door would intersect with shelves",
    "Domain 14 (Safety): Inward opening would crush contents"
  ]
}
```

---

### BEHAVIOR 2: LINEAR TRANSLATIONAL (Push/Pull)

#### Valid For:
- Drawers, sliding doors, buttons, levers, sliding gates

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | Must match sliding direction | Drawer: forward only |
| **2. Range Limits** | Must respect travel distance | Drawer: 0 - depth x 0.9 |
| **3. Pivot Placement** | Not applicable (linear motion) | N/A |
| **4. Clearance** | Must not self-collide | Drawer clears frame |
| **5. Sequential** | May require prior actions | Release latch BEFORE pull |
| **6. Force/Torque** | Must apply realistic force | Drawer: 10-50 N |
| **7. Contact/Friction** | Must maintain rail contact | Smooth gliding on rails |
| **8. Symmetry** | Usually asymmetric | Handles on front only |
| **9. Material** | Material affects friction | Metal rails vs. plastic |
| **10. Internal Volume** | May prevent certain directions | Drawer cannot push through back |
| **11. Kinematic Chain** | Single prismatic joint | One axis of translation |
| **12. Energy** | Usually gravity-driven | Gravity helps close drawer |
| **13. Feedback** | May need position sensors | Encoder tracks drawer position |
| **14. Safety** | Hard stops prevent over-extension | Cannot pull out beyond depth |
| **15. Aesthetic** | May affect appearance | Drawer flush with frame |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Pull Forward",
  "object": "Drawer",
  "constraints": {
    "direction": "forward_only",
    "translation_axis": [1, 0, 0],
    "translation_limits": [0.0, 0.45],
    "force_required": 25.0,
    "friction_coefficient": 0.1,
    "damping": 1.0,
    "collision_check": true,
    "position_feedback": true
  },
  "invalid_alternatives": [
    "Push Backward - violates Domain 1 (Directional) and Domain 10 (Internal Volume)",
    "Push Left/Right - violates Domain 1 (Directional) and Domain 11 (Kinematic Chain)"
  ]
}
```

---

### BEHAVIOR 3: GRASPING/GRIPPING

#### Valid For:
- Any object that needs to be held

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | Not applicable | N/A |
| **2. Range Limits** | Grip force limits | 0.1 - 500 N |
| **3. Pivot Placement** | Not applicable | N/A |
| **4. Clearance** | Gripper must fit around object | Gripper opening >= object size |
| **5. Sequential** | Usually first action | Grasp BEFORE any other action |
| **6. Force/Torque** | Must apply appropriate grip force | Egg: 0.5-5 N, Heavy object: 100-500 N |
| **7. Contact/Friction** | Must maintain contact | Friction prevents slipping |
| **8. Symmetry** | May be symmetric or asymmetric | Two-finger vs. multi-finger |
| **9. Material** | Material affects friction | Rubber vs. metal gripper |
| **10. Internal Volume** | Not applicable | N/A |
| **11. Kinematic Chain** | Multiple contact points | 2-10+ contact points |
| **12. Energy** | Gripper actuated | Motor-driven or pneumatic |
| **13. Feedback** | Force/slip sensing | Slip detection threshold |
| **14. Safety** | Force limits prevent crushing | Max grip force = object breaking point |
| **15. Aesthetic** | Not applicable | N/A |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Gentle Grip",
  "object": "Egg",
  "constraints": {
    "grip_force": 2.0,
    "grip_force_min": 0.5,
    "grip_force_max": 5.0,
    "contact_points": 3,
    "contact_area_per_point": 50,
    "friction_coefficient": 0.3,
    "slip_threshold": 0.5,
    "force_feedback": true,
    "slip_detection": true
  },
  "invalid_alternatives": [
    "Firm Grip - violates Domain 14 (Safety), would crush egg"
  ]
}
```

---

### BEHAVIOR 4: INSERTION/ASSEMBLY

#### Valid For:
- Pegs, plugs, keys, screws, connectors

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | Must match insertion axis | Vertical or horizontal |
| **2. Range Limits** | Must respect insertion depth | Peg-in-hole: 0 - hole depth |
| **3. Pivot Placement** | Not applicable | N/A |
| **4. Clearance** | Must not jam | Tolerance: 0.1-1 mm |
| **5. Sequential** | May require alignment first | Align BEFORE insert |
| **6. Force/Torque** | Must apply insertion force | Peg: 10-50 N |
| **7. Contact/Friction** | Must maintain contact during insertion | Friction guides insertion |
| **8. Symmetry** | Usually asymmetric | Key profile specific |
| **9. Material** | Material affects friction | Metal vs. plastic |
| **10. Internal Volume** | Not applicable | N/A |
| **11. Kinematic Chain** | Single axis insertion | Linear or helical motion |
| **12. Energy** | Usually manual or motor-driven | Motor-driven assembly |
| **13. Feedback** | Force/position feedback | Detect insertion completion |
| **14. Safety** | Hard stops prevent over-insertion | Cannot insert beyond depth |
| **15. Aesthetic** | Not applicable | N/A |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Insert Peg in Hole",
  "object": "Wooden Peg in Wooden Board",
  "constraints": {
    "direction": "vertical_downward",
    "insertion_axis": [0, -1, 0],
    "insertion_limits": [0.0, 0.05],
    "force_required": 30.0,
    "alignment_precision": 0.5,
    "tolerance": 0.2,
    "friction_coefficient": 0.5,
    "damping": 5.0,
    "collision_check": true,
    "force_feedback": true
  }
}
```

---

### BEHAVIOR 5: DEFORMATION

#### Valid For:
- Flexible objects: wire, cloth, rubber, foam, dough

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | May have preferred deformation direction | Wire bends along length |
| **2. Range Limits** | Must respect material limits | Max bend angle before breaking |
| **3. Pivot Placement** | Deformation center | Where object bends |
| **4. Clearance** | Must not self-collide | Bent wire doesn't intersect |
| **5. Sequential** | May require prior actions | Warm material BEFORE bending |
| **6. Force/Torque** | Must apply deformation force | Wire: 10-100 N |
| **7. Contact/Friction** | May need support contact | Support prevents kinking |
| **8. Symmetry** | May be symmetric or asymmetric | Symmetric bend vs. asymmetric |
| **9. Material** | Material properties critical | Elasticity, plasticity |
| **10. Internal Volume** | Not applicable | N/A |
| **11. Kinematic Chain** | Distributed deformation | Entire object deforms |
| **12. Energy** | Usually manual | Manual bending |
| **13. Feedback** | Force/angle feedback | Monitor bend angle |
| **14. Safety** | Prevent breaking | Max force = breaking point |
| **15. Aesthetic** | May affect appearance | Final shape |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Bend Wire 90 Degrees",
  "object": "Steel Wire",
  "constraints": {
    "deformation_force": 50.0,
    "deformation_distance": 0.02,
    "target_bend_angle": 90,
    "bend_radius": 0.01,
    "youngs_modulus": 206,
    "yield_strength": 500,
    "elasticity": 0.95,
    "plasticity": 0.05,
    "damping": 2.0,
    "force_feedback": true,
    "angle_monitoring": true
  },
  "invalid_alternatives": [
    "Bend 180 Degrees - violates Domain 14 (Safety), would break wire"
  ]
}
```

---

### BEHAVIOR 6: CONTACT-BASED (Tap/Stroke/Press)

#### Valid For:
- Buttons, switches, surfaces, keyboards

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | Usually downward for buttons | Vertical contact |
| **2. Range Limits** | Contact depth limit | Button: 0 - 5mm |
| **3. Pivot Placement** | Not applicable | N/A |
| **4. Clearance** | Not applicable | N/A |
| **5. Sequential** | Usually single action | Tap button once |
| **6. Force/Torque** | Must apply contact force | Button: 0.5-5 N |
| **7. Contact/Friction** | Surface contact | Friction between gripper and surface |
| **8. Symmetry** | Usually symmetric | Contact from any direction |
| **9. Material** | Material affects friction | Rubber vs. metal |
| **10. Internal Volume** | Not applicable | N/A |
| **11. Kinematic Chain** | Point contact | Single contact point |
| **12. Energy** | Usually manual | Manual pressing |
| **13. Feedback** | Contact detection | Detect when button pressed |
| **14. Safety** | Prevent over-pressing | Max force = button breaking point |
| **15. Aesthetic** | Not applicable | N/A |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Tap Button",
  "object": "Electronic Button",
  "constraints": {
    "contact_force": 3.0,
    "contact_duration": 0.1,
    "contact_area": 50,
    "contact_pressure": 60000,
    "activation_force": 1.0,
    "return_force": 0.5,
    "stiffness": 500,
    "friction_coefficient": 0.8,
    "force_feedback": true,
    "activation_detection": true
  }
}
```

---

### BEHAVIOR 7: SEQUENTIAL/COMPOUND

#### Valid For:
- Complex objects requiring multi-step interactions

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | Each step has direction | Step 1: outward, Step 2: forward |
| **2. Range Limits** | Each step has limits | Step 1: 0-90 deg, Step 2: 0-0.5m |
| **3. Pivot Placement** | Each step has pivot | Step 1: hinge, Step 2: N/A |
| **4. Clearance** | Each step must clear | All steps collision-free |
| **5. Sequential** | Critical constraint | Steps must occur in order |
| **6. Force/Torque** | Each step has force | Step 1: 5 Nm, Step 2: 50 N |
| **7. Contact/Friction** | Each step has contact | Step 1: bearing, Step 2: rail |
| **8. Symmetry** | Each step symmetry | Step 1: asymmetric, Step 2: asymmetric |
| **9. Material** | Each step material | Step 1: metal, Step 2: wood |
| **10. Internal Volume** | Each step considers volume | All steps respect internal structure |
| **11. Kinematic Chain** | Multiple joints | Multiple joints in sequence |
| **12. Energy** | Each step energy | Step 1: manual, Step 2: gravity |
| **13. Feedback** | Each step feedback | Detect completion of each step |
| **14. Safety** | Each step safety | Hard stops for each step |
| **15. Aesthetic** | Each step aesthetic | Final appearance |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Unlock and Open Door",
  "object": "Locked Door",
  "constraints": {
    "steps": [
      {
        "step_id": 1,
        "name": "Insert Key",
        "behavior_type": "Insertion",
        "direction": "vertical",
        "force": 10.0,
        "limits": [0.0, 0.05]
      },
      {
        "step_id": 2,
        "name": "Twist Key",
        "behavior_type": "Rotational",
        "direction": "clockwise",
        "torque": 5.0,
        "limits": [0.0, 1.57]
      },
      {
        "step_id": 3,
        "name": "Extract Key",
        "behavior_type": "Linear",
        "direction": "upward",
        "force": 8.0,
        "limits": [0.0, 0.05]
      },
      {
        "step_id": 4,
        "name": "Pull Door",
        "behavior_type": "Linear",
        "direction": "forward",
        "force": 60.0,
        "limits": [0.0, 0.8]
      }
    ],
    "sequence_dependency": true,
    "cumulative_error_tolerance": 5.0,
    "error_recovery": true
  }
}
```

---

### BEHAVIOR 8: DYNAMIC/BALLISTIC

#### Valid For:
- Throwing, catching, swinging, bouncing

#### Semantic Constraints That Apply:

| Constraint Domain | Specification | Example |
|-------------------|---------------|---------|
| **1. Directional** | Launch direction | Throw forward and upward |
| **2. Range Limits** | Trajectory range | Max distance before hitting wall |
| **3. Pivot Placement** | Release point | Hand position at release |
| **4. Clearance** | Trajectory clearance | Path must not intersect obstacles |
| **5. Sequential** | Usually single action | Throw once |
| **6. Force/Torque** | Launch force | Throw force 50-500 N |
| **7. Contact/Friction** | Initial contact | Gripper to object contact |
| **8. Symmetry** | Usually asymmetric | Throw direction specific |
| **9. Material** | Material affects trajectory | Weight, aerodynamics |
| **10. Internal Volume** | Not applicable | N/A |
| **11. Kinematic Chain** | Arm trajectory | Multi-joint arm motion |
| **12. Energy** | Kinetic energy | Launch velocity |
| **13. Feedback** | Trajectory feedback | Monitor object flight |
| **14. Safety** | Prevent hazards | Ensure safe landing zone |
| **15. Aesthetic** | Not applicable | N/A |

#### Valid Behavior Specifications:

```json
{
  "behavior": "Throw Ball",
  "object": "Tennis Ball",
  "constraints": {
    "initial_velocity": 8.0,
    "launch_angle": 30,
    "launch_direction": [1, 0, 0.5],
    "target_distance": 5.0,
    "object_mass": 0.057,
    "aerodynamic_drag": 0.5,
    "coefficient_of_restitution": 0.8,
    "impact_force": 150,
    "trajectory_feedback": true,
    "impact_detection": true
  }
}
```

---

## Part 3: Object-Behavior Validity Matrix

### Complete Matrix for Common Objects

#### Cabinet Door
```
Rotational:        ✓ (Twist outward only, 0-110°)
Linear:            ✗ (Violates directional semantics)
Grasping:          ✓ (Grasp handle to open)
Insertion:         ✗ (Not applicable)
Deformation:       ✗ (Not applicable)
Contact:           ✗ (Not applicable)
Sequential:        ✓ (Unlock + open)
Dynamic:           ✗ (Not applicable)
```

#### Drawer
```
Rotational:        ✗ (Violates kinematic chain)
Linear:            ✓ (Pull forward only, 0-depth)
Grasping:          ✓ (Grasp handle to pull)
Insertion:         ✗ (Not applicable)
Deformation:       ✗ (Not applicable)
Contact:           ✗ (Not applicable)
Sequential:        ✓ (Release latch + pull)
Dynamic:           ✗ (Not applicable)
```

#### Door Knob
```
Rotational:        ✓ (Twist CW/CCW, 0-90°)
Linear:            ✗ (Violates kinematic chain)
Grasping:          ✓ (Grasp knob to twist)
Insertion:         ✗ (Not applicable)
Deformation:       ✗ (Not applicable)
Contact:           ✗ (Not applicable)
Sequential:        ✓ (Twist + push)
Dynamic:           ✗ (Not applicable)
```

#### Button
```
Rotational:        ✗ (Violates kinematic chain)
Linear:            ✓ (Press down, 0-5mm)
Grasping:          ✗ (Not applicable)
Insertion:         ✗ (Not applicable)
Deformation:       ✗ (Not applicable)
Contact:           ✓ (Tap/press contact)
Sequential:        ✗ (Single action)
Dynamic:           ✗ (Not applicable)
```

#### Screw/Bolt
```
Rotational:        ✓ (Twist CW/CCW, multi-turn)
Linear:            ✓ (Push while twisting)
Grasping:          ✓ (Grasp with wrench/gripper)
Insertion:         ✓ (Insert into hole)
Deformation:       ✗ (Not applicable)
Contact:           ✗ (Not applicable)
Sequential:        ✓ (Insert + twist + stop)
Dynamic:           ✗ (Not applicable)
```

---

## Part 4: Behavior Validation Rules

### Rule 1: Directional Consistency
```
IF object has Domain 1 (Directional Semantics) constraint
THEN behavior direction must match constraint
ELSE behavior is INVALID
```

### Rule 2: Range Limit Enforcement
```
IF behavior specifies motion
AND object has Domain 2 (Range Limits) constraint
THEN motion must not exceed limits
ELSE behavior is INVALID
```

### Rule 3: Pivot Placement Correctness
```
IF behavior requires rotation
AND object has Domain 3 (Pivot Placement) constraint
THEN rotation must occur around correct pivot
ELSE behavior is INVALID
```

### Rule 4: Clearance Validation
```
IF behavior causes motion
AND object has Domain 4 (Clearance) constraint
THEN motion must not cause self-collision
ELSE behavior is INVALID
```

### Rule 5: Sequential Dependency
```
IF object has Domain 5 (Sequential Dependency) constraint
THEN behaviors must occur in specified order
ELSE behavior is INVALID
```

### Rule 6: Force/Torque Realism
```
IF behavior specifies force/torque
AND object has Domain 6 (Force/Torque) constraint
THEN force/torque must be within realistic range
ELSE behavior is INVALID
```

### Rule 7: Contact Maintenance
```
IF behavior requires contact
AND object has Domain 7 (Contact/Friction) constraint
THEN contact must be maintained throughout behavior
ELSE behavior is INVALID
```

### Rule 8: Internal Volume Protection
```
IF object has Domain 10 (Internal Volume) constraint
THEN no behavior can cause motion that intersects internal volume
ELSE behavior is INVALID
```

### Rule 9: Safety Limits
```
IF behavior specifies force/torque/motion
AND object has Domain 14 (Safety) constraint
THEN behavior must not exceed safety limits
ELSE behavior is INVALID
```

---

## Conclusion

The complete framework is:

**Semantic Constraints** (15 domains) + **Behaviors** (8 types) = **Valid Behavior Specifications**

For each object:
1. Identify applicable semantic constraints (from 15 domains)
2. For each behavior, check if it violates any constraint
3. If no violations, specify behavior parameters
4. If violations exist, mark behavior as INVALID

This ensures that generated 3D assets have **correct kinematics, realistic physics, and valid behaviors** from the start.

---

**Document Version**: 1.0
**Last Updated**: 2026-04-01
**Status**: Complete Behavior-Semantic Constraint Mapping


---

# Extended Behaviors (9-16)

---

# BEHAVIOR: SLIDING/FRICTION-BASED MOTION

## SECTION 1: Behavior Definition

This behavior describes the robotic manipulation task of **pushing a free-floating object across a surface using a robot's end-effector**, where the object is not grasped but rather propelled by contact forces. The defining characteristic of this behavior is that the object's motion is primarily governed by the interplay of surface friction, contact forces, and the inertia of the object, rather than being constrained by mechanical joints or direct grasping. This differentiates it from pick-and-place operations, where objects are firmly held, or articulated object manipulation, where internal joints dictate movement. The robot applies a force to the object, initiating and sustaining its movement across a substrate, with the resulting trajectory and stability heavily dependent on the coefficient of friction between the object and the surface, as well as the applied force vector.

This behavior is physically distinct due to its reliance on dynamic contact mechanics and friction models. Unlike grasping, which establishes a rigid connection, pushing involves continuous, often sliding, contact. The success of the operation hinges on maintaining stable contact without causing the object to tumble, slip uncontrollably, or lose contact entirely. This requires precise control over the robot's force and velocity, considering the object's center of mass and the point of contact. Real-world applications for this behavior are diverse, including clearing debris from a workspace, arranging items on a table without lifting them, pushing components into alignment during assembly, or even artistic applications like sweeping paint or arranging small objects in a display. It is particularly relevant in scenarios where grasping is impractical due to object geometry, fragility, or the need for rapid, continuous movement across a surface.

For the Franka Emika Panda robot, this behavior involves using its end-effector (e.g., the gripper fingers in a closed or partially open state, or a custom pushing tool) to exert force on objects such as boxes, books, or plates. The robot's compliance and force control capabilities are crucial for executing this task smoothly, preventing excessive forces that could damage the object or cause unstable motion. The interaction is fundamentally about controlling the object's planar motion on a surface through controlled contact, making it a foundational skill for many unstructured manipulation tasks in robotics.

## SECTION 2: Semantic Constraint Matrix

This matrix outlines the applicability and specific rules for each of the 15 semantic constraint domains within the context of the SLIDING/FRICTION-BASED MOTION behavior. Each constraint is accompanied by a justification and an example relevant to the Franka Panda robot.

| Constraint Domain | Applies (Y/N) | Specific Constraint Value/Rule | Example for Franka Panda Context |
|---|---|---|---|
| Directional Semantics | Y | The direction of the pushing force relative to the object's geometry and desired motion path. Force should be applied in the direction of intended motion, or slightly offset to induce rotation if desired. | Franka end-effector pushes a box from its rear face to move it forward on a table. The force vector is parallel to the table surface and aligned with the box's longitudinal axis. |
| Range Limits | Y | Maximum and minimum distances for object movement, robot joint limits, and end-effector workspace limits. Object must remain within the table boundaries. | The box must be pushed no further than 0.5 meters from its starting position, and the Franka's joints must not exceed their operational limits. |
| Pivot Placement | N | Not applicable as the object is free-floating and not constrained by a pivot. Motion is translational and rotational based on contact. | N/A |
| Clearance/Tolerance | Y | Minimum required gap between the robot's end-effector and surrounding obstacles, and between the pushed object and obstacles. Prevents collisions. | The Franka's end-effector maintains a minimum 5mm clearance from the box's edges not being pushed, and the box maintains a 1cm clearance from the table's edge. |
| Sequential Dependency | N | This behavior is a single, continuous action. No explicit sequential sub-behaviors are defined within the pushing motion itself. | N/A |
| Force/Torque Realism | Y | Realistic application of forces and torques by the robot, considering its payload capacity, wrist torque, and main joint torque limits. Prevents unrealistic accelerations or deformations. | The Franka applies a pushing force between 5N and 20N to the box, well within its 70N continuous force limit and 3kg payload. Wrist torque remains below +/-12 Nm. |
| Contact/Friction | Y | Accurate modeling of contact points, normal forces, and friction coefficients between the object and the surface, and between the end-effector and the object. Crucial for realistic sliding motion. | The static friction coefficient between the plastic box and the wooden table is 0.3, and the dynamic friction coefficient is 0.2. The end-effector maintains continuous contact with the box. |
| Symmetry | N | Object's motion is not inherently symmetric; it depends on the applied force and friction. While the object itself might be symmetric, its behavior under pushing is not necessarily so. | N/A |
| Material Properties | Y | Accurate physical properties of the object (mass, inertia, density) and the surface (friction coefficients, stiffness, damping). Influences dynamic response. | The box is made of ABS plastic (density 1040 kg/m3) with a mass of 0.2 kg. The table surface is wood. |
| Internal Volume | N | The behavior does not involve interacting with the internal volume of the object. The object is treated as a solid body. | N/A |
| Kinematic Chain | Y | The robot's kinematic chain must be correctly defined and constrained, allowing for accurate end-effector positioning and force application. | The Franka's 7-DOF kinematic chain is fully defined, allowing for precise control of the end-effector's pose to apply force to the object. |
| Energy | Y | Energy conservation and dissipation through friction should be accurately modeled. This affects the object's deceleration and final resting position. | The simulation accurately models energy loss due to dynamic friction as the box slides across the surface, causing it to eventually come to rest. |
| Feedback | Y | Real-time force/torque feedback from the robot's sensors is essential for adaptive control and maintaining stable contact. | The Franka utilizes its internal force/torque sensors to detect contact with the box and adjust its pushing force to maintain a desired contact force of 10N. |
| Safety | Y | Constraints to prevent collisions, excessive forces, and unstable robot configurations. Ensures safe operation in both simulation and real-world. | The robot's joint velocities are limited to prevent sudden movements, and a virtual safety boundary is established around the workspace to prevent the robot from colliding with the environment. |
| Aesthetic | N | The aesthetic appearance of the object or robot is not a functional constraint for the physical behavior itself. | N/A |

---

# WIPING/SWEEPING BEHAVIOR SPECIFICATION

## SECTION 1: Behavior Definition

The **Wiping/Sweeping Behavior** is characterized by a robot's end-effector executing a repetitive motion across a designated surface while actively maintaining continuous and sustained physical contact. This behavior is fundamentally distinct from simple trajectory following or pick-and-place operations due to its critical requirement for dynamic force control. Unlike tasks where contact is incidental or brief, wiping/sweeping necessitates a consistent interaction force between the end-effector and the surface throughout the entire motion. This sustained contact, coupled with repetitive movement, is essential for effectively performing surface-altering actions such as cleaning or material displacement.

Physically, the distinction lies in the active regulation of interaction forces. A robot performing a wiping task must not only follow a path but also exert a controlled normal force against the surface to ensure effective friction and material removal, while simultaneously minimizing excessive force that could damage the surface or the robot. This often involves the use of impedance or admittance control strategies, which allow the robot to compliantly interact with its environment. Without such control, the end-effector would either lose contact, rendering the task ineffective, or apply excessive force, leading to potential damage or instability. Therefore, the core physical characteristic is the precise management of contact dynamics rather than purely kinematic execution.

Real-world applications for this behavior are diverse and critical across various industries. Examples include the automated cleaning of industrial surfaces, such as conveyor belts or machinery components, to maintain hygiene and operational efficiency. In domestic or commercial settings, it encompasses tasks like wiping tables, sweeping floors to remove debris, or cleaning windows. The ability to robustly execute this behavior is crucial for enhancing automation in maintenance, sanitation, and manufacturing processes, where surface interaction and cleanliness are paramount.

## SECTION 2: Semantic Constraint Matrix

The following matrix defines the semantic constraints applicable to the Wiping/Sweeping behavior. Each domain is evaluated for its relevance, and specific rules and examples are provided for the Franka Emika Panda robot.

| Constraint Domain | Applies | Specific Constraint Value/Rule | Example for Franka Panda Context |
| :--- | :---: | :--- | :--- |
| 1. Directional Semantics | Y | Motion must be constrained to a plane parallel to the target surface. The primary movement axis (e.g., X or Y) dictates the wiping stroke, while the normal axis (Z) is strictly controlled for force application. | Wiping a horizontal table requires the end-effector to move primarily in the world X-Y plane, with the Z-axis aligned downwards to apply force. |
| 2. Range Limits | Y | The wiping stroke length must not exceed the kinematic reachability of the robot arm while maintaining the required contact force. The workspace limits must be strictly observed to prevent singularities. | The wiping stroke on a table should be limited to a 0.5m x 0.5m area within the Panda's optimal manipulability ellipsoid to ensure consistent force application. |
| 3. Pivot Placement | N | Not strictly applicable as wiping is typically a translational motion across a surface rather than a rotational motion around a fixed pivot point. | N/A |
| 4. Clearance/Tolerance | Y | The end-effector must maintain a zero or slightly negative clearance (penetration depth in simulation) relative to the surface to ensure continuous contact and force application. | The simulated end-effector (e.g., a sponge) must be commanded to a Z-height slightly below the table surface (e.g., -2mm) to generate the desired 10N contact force via impedance control. |
| 5. Sequential Dependency | Y | The behavior must follow a strict sequence: 1. Approach surface, 2. Establish contact (force threshold met), 3. Execute wiping motion, 4. Retract from surface. | The Panda must first lower the sponge until the wrist force-torque sensor registers >5N in the Z-axis before initiating the lateral wiping motion. |
| 6. Force/Torque Realism | Y | The applied normal force must be sufficient for the task (e.g., cleaning) but must not exceed the robot's continuous force limits or damage the surface. | The Panda should apply a continuous normal force of 10-20N during wiping, well within its 70N continuous force limit, to avoid motor overheating or surface damage. |
| 7. Contact/Friction | Y | The interaction requires specific friction models (e.g., Coulomb friction) to simulate the resistance encountered during wiping. The friction coefficient must reflect the materials involved. | Wiping a glass window with a rubber squeegee requires a high static and kinetic friction coefficient in the simulation to accurately model the resistance and prevent slip. |
| 8. Symmetry | N | Wiping motions are often asymmetric (e.g., back-and-forth strokes) and do not inherently require symmetrical constraints on the object or the motion path. | N/A |
| 9. Material Properties | Y | The compliance and friction of both the end-effector tool and the target surface must be accurately modeled to achieve realistic force interaction and wiping effectiveness. | The sponge attached to the Panda must be modeled with a soft, compliant material (low stiffness) to allow for deformation and consistent contact over minor surface irregularities. |
| 10. Internal Volume | N | Wiping is a surface-level interaction; the internal volume of the target object is generally irrelevant to the behavior. | N/A |
| 11. Kinematic Chain | Y | The robot's kinematic chain must be optimized to maintain manipulability and avoid singularities throughout the extended wiping motion. | The Panda's elbow joint should be positioned to allow for maximum lateral reach without approaching a singular configuration during a long sweeping stroke. |
| 12. Energy | Y | The energy exerted (work done) during the wiping motion must be monitored to ensure it aligns with the expected physical effort and does not exceed system limits. | The total energy consumed by the Panda's joint motors during a 10-minute wiping task must be calculated to ensure it remains within safe operating parameters. |
| 13. Feedback | Y | Continuous feedback from force-torque sensors or joint torques is mandatory to maintain the desired contact force and adapt to surface variations. | The Panda's control loop must use real-time feedback from its internal joint torque sensors to adjust the Z-axis position and maintain a constant 15N normal force. |
| 14. Safety | Y | Safety limits on maximum velocity, acceleration, and applied force must be strictly enforced to prevent damage to the robot, the tool, or the environment. | The wiping velocity must be capped at 0.2 m/s, and the maximum allowable normal force must be limited to 30N to ensure safe operation around humans or delicate surfaces. |
| 15. Aesthetic | N | The visual appearance of the wiping motion is secondary to its functional execution and physical realism. | N/A |

---

# TWISTING/TORQUE-BASED ROTATION Specification

## SECTION 1: Behavior Definition

The **TWISTING/TORQUE-BASED ROTATION** behavior is defined as the continuous or discrete rotation of an object around its own internal axis while it is actively grasped by a robotic end-effector. Unlike simple pushing or sliding, this behavior requires the robot to maintain a stable grasp (applying normal force) while simultaneously applying a torque (rotational force) to overcome the object's internal friction or resistance. The axis of rotation is intrinsic to the object itself, rather than an external pivot point in the environment.

What makes this behavior physically distinct is the dual requirement of force and torque application. The gripper must apply sufficient normal force to prevent slipping (dependent on the friction coefficient between the gripper pads and the object), while the wrist and main joints must generate enough torque to rotate the object. If the applied torque exceeds the friction limit of the grasp, the gripper will slip around the object instead of rotating it. Conversely, if the object's internal resistance is higher than the robot's maximum torque capacity, the rotation will fail.

Real-world applications of this behavior are ubiquitous in industrial and domestic settings. Examples include twisting open a jar lid, tightening or loosening a bolt with a wrench, turning a doorknob, or operating a rotary dial. In all these cases, the robot must understand the object's internal kinematic constraints (e.g., the thread pitch of a bolt or the rotational limits of a dial) and apply forces accordingly.

## SECTION 2: Semantic Constraint Matrix

| Domain | Applies | Constraint Value/Rule | Example for Franka Panda | Justification |
| :--- | :---: | :--- | :--- | :--- |
| 1. Directional Semantics | Y | Rotation around a specific local axis (e.g., Z-axis). | Rotate jar lid around its local Z-axis. | The robot must know which axis to apply torque around; applying torque off-axis will cause binding or slipping. |
| 2. Range Limits | Y | `lowerLimit` and `upperLimit` in degrees/radians. | Dial limited to [-90 deg, 90 deg]. | Prevents the robot from attempting to rotate beyond physical stops, which could damage the object or the robot. |
| 3. Pivot Placement | Y | Pivot must be exactly at the center of rotation. | Pivot at the center of the bolt head. | Incorrect pivot placement causes eccentric rotation, leading to unintended lateral forces and grasp failure. |
| 4. Clearance/Tolerance | Y | Gripper opening must accommodate object diameter + tolerance. | Gripper opens to 65mm for a 60mm lid. | Ensures the gripper can successfully approach and enclose the object before grasping. |
| 5. Sequential Dependency | Y | Grasp MUST precede Rotation. | Close fingers -> Apply Torque. | Attempting to rotate before a secure grasp is established will result in the gripper spinning freely. |
| 6. Force/Torque Realism | Y | Applied torque < max wrist torque (12 Nm). | Apply 2 Nm torque to loosen lid. | Exceeding the robot's torque limits will cause a safety stop or tracking error. |
| 7. Contact/Friction | Y | Grasp friction > (Torque / Radius). | High friction pads for smooth metal dial. | If friction is too low, the gripper will slip instead of transferring torque to the object. |
| 8. Symmetry | Y | Object geometry should ideally be rotationally symmetric. | Cylindrical jar lid. | Asymmetric objects require complex, dynamic grasp adjustments during rotation. |
| 9. Material Properties | Y | Object must withstand applied grasp force. | Max grasp force 30N for plastic lid. | Applying maximum grasp force (70N) to a fragile object will crush it. |
| 10. Internal Volume | N | N/A | N/A | Internal volume does not directly affect the twisting mechanics. |
| 11. Kinematic Chain | Y | Object must be modeled as an articulation (Revolute Joint). | Lid is a child of the jar via RevoluteJoint. | Without a kinematic joint, the simulator treats the object as a free rigid body, making constrained rotation impossible. |
| 12. Energy | Y | Work done = Torque x Angular Displacement. | Monitor energy to detect jamming. | Sudden spikes in energy indicate cross-threading or jamming. |
| 13. Feedback | Y | Monitor joint efforts and position errors. | Check wrist torque feedback. | Essential for detecting when a limit is reached or if the grasp is slipping. |
| 14. Safety | Y | Torque limits must be strictly enforced. | Max torque capped at 5 Nm. | Protects the robot's joints and the object from damage during unexpected resistance. |
| 15. Aesthetic | N | N/A | N/A | Visual appearance does not impact the physics of the twisting behavior. |

---

# STACKING/PLACEMENT BEHAVIOR Specification for Franka Emika Panda

## SECTION 1: Behavior Definition

The **STACKING/PLACEMENT BEHAVIOR** involves the precise manipulation and release of an object onto a designated surface or another object, ensuring its stable resting position. This behavior is fundamentally characterized by a controlled approach, accurate 6-Degrees of Freedom (DOF) positioning, and a gentle release, allowing gravity to settle the object into its final state. Unlike a simple 'drop' behavior, which lacks positional precision and stability considerations, or a 'grasp-and-hold' behavior, which maintains continuous contact, stacking/placement necessitates a momentary detachment where the object's stability is paramount post-release. The success of this behavior hinges on the accurate prediction of the object's gravitational settling and the absence of significant post-release disturbances.

This behavior is distinct from other manipulation tasks due to its emphasis on static stability after the robot's intervention ceases. For instance, while a 'pushing' behavior involves continuous contact and force application to change an object's position, stacking/placement concludes with the object being entirely supported by the target surface. Similarly, 'insertion' behaviors require fitting an object into a constrained opening, often involving force feedback and alignment, whereas stacking/placement focuses on surface contact and gravitational stability. The critical differentiator is the transition from active robotic control to passive environmental stability, demanding meticulous pre-release alignment and orientation.

Real-world applications for the STACKING/PLACEMENT BEHAVIOR are widespread in manufacturing, logistics, and domestic robotics. Examples include industrial robots stacking components on an assembly line, robotic arms placing items onto shelves in a warehouse, or even household robots setting down a cup on a table. The Franka Emika Panda, with its high precision and compliant control capabilities, is well-suited for such tasks, enabling delicate handling and accurate positioning required for successful stacking and placement operations. The behavior is applicable to a variety of objects, from rigid blocks and containers to more irregularly shaped items, provided their center of mass and contact points allow for stable resting configurations.

## SECTION 2: Semantic Constraint Matrix

The Semantic Constraint Matrix details the various constraints that govern the STACKING/PLACEMENT BEHAVIOR, ensuring its realistic and successful execution within a simulation environment. Each domain is evaluated for its applicability to the behavior, with specific rules and examples tailored for the Franka Emika Panda robot.

| Constraint Domain | Applies (Y/N) | Specific Constraint Value/Rule |
| :--- | :---: | :--- |
| **Directional Semantics** | Y | The final placement approach must be anti-parallel to the surface normal of the target location. |
| **Range Limits** | Y | Gripper opening must be within 0mm to 80mm. Joint positions must adhere to the Franka's specified kinematic limits. |
| **Pivot Placement** | Y | The object's pivot point must be at its center of mass for stable placement. |
| **Clearance/Tolerance** | Y | A minimum clearance of 1cm must be maintained from obstacles during approach. Final placement precision must be within +/-2mm. |
| **Sequential Dependency** | Y | The sequence is: Approach -> Grasp -> Lift -> Move -> Position -> Release -> Retreat. |
| **Force/Torque Realism** | Y | Gripper force must not exceed 70N. Joint torques must not exceed 87Nm (main) and 12Nm (wrist). |
| **Contact/Friction** | Y | Static and dynamic friction coefficients must be defined for all interacting surfaces to ensure stable placement. |
| **Symmetry** | N | Not directly applicable, as the behavior is defined by the interaction of forces and geometry, not symmetry. |
| **Material Properties** | Y | Object mass must be within the Franka's 3kg payload limit. Restitution should be low to prevent bouncing. |
| **Internal Volume** | N | Not applicable for solid objects. For hollow objects, it is implicitly handled by the collision geometry. |
| **Kinematic Chain** | Y | The robot's kinematic chain must be correctly defined in the URDF/USD file. |
| **Energy** | N | While energy consumption is a factor in real-world robotics, it is not a primary constraint for the simulation of this behavior. |
| **Feedback** | Y | Joint positions and velocities are required for closed-loop control. Contact sensors can be used to detect successful placement. |
| **Safety** | Y | Joint limits and collision avoidance are critical to prevent self-damage and damage to the environment. |
| **Aesthetic** | N | Not a primary constraint for the physical behavior, although smooth motion is a desirable outcome of good control. |

---

# COMPLIANT/FORCE-CONTROLLED MOTION Specification

## SECTION 1: Behavior Definition

Compliant or force-controlled motion is a robotic behavior where the manipulator actively regulates the contact force exerted on an environment or object, rather than strictly following a predefined positional trajectory. This behavior is physically distinct from pure position control because it allows the robot to yield to external forces or maintain a constant pressure against a surface, even if the exact geometry of that surface is unknown or varying. In impedance or admittance control schemes, the robot acts as a mass-spring-damper system, dynamically adjusting its position to achieve the target contact force while absorbing shocks and preventing damage to both the tool and the workpiece.

This behavior is essential for tasks that require physical interaction with the environment where rigid position control would result in excessive forces, jamming, or breakage. Real-world applications include polishing a curved surface, sanding wood, scrubbing a table, or assembling tight-fitting parts like peg-in-hole insertions. In these scenarios, the Franka Emika Panda must leverage its joint torque sensors to estimate external forces and adjust its end-effector pose accordingly, ensuring that the applied force remains within the desired limits, such as maintaining a 10 N normal force while moving tangentially across a surface.

## SECTION 2: Semantic Constraint Matrix

| Domain | Applies | Constraint Value/Rule | Example for Franka Panda |
| :--- | :---: | :--- | :--- |
| 1. Directional Semantics | Y | Force must be regulated along specific axes (e.g., surface normal) while position is controlled along others (e.g., surface tangent). | Regulating 15 N force along the Z-axis (downward) while moving along the X-Y plane for scrubbing. |
| 2. Range Limits | Y | Contact force must not exceed the maximum continuous force of the end-effector or the payload capacity. | Force target must be <= 30 N (well within the 3 kg payload and 70 N gripper limit) to avoid protective stops. |
| 3. Pivot Placement | N | Not strictly applicable as this behavior focuses on end-effector interaction rather than articulating a jointed object. | N/A |
| 4. Clearance/Tolerance | Y | Position tracking error tolerance must be relaxed along the force-controlled axes to allow compliance. | Allowing up to 5 cm of positional deviation along the Z-axis to maintain the target contact force. |
| 5. Sequential Dependency | Y | The robot must establish contact (guarded move) before initiating the force-tracking phase. | Approach the surface at 0.05 m/s until a 2 N contact force is detected, then switch to 15 N force control. |
| 6. Force/Torque Realism | Y | Commanded torques must respect the physical limits of the robot's actuators to prevent instability. | Wrist torques must not exceed +/-12 Nm, and main joint torques must not exceed +/-87 Nm during impedance control. |
| 7. Contact/Friction | Y | Friction coefficients between the tool and the surface must be modeled to account for lateral forces during sliding. | Setting the dynamic friction coefficient of the polishing tool and the table to 0.3 to simulate realistic drag. |
| 8. Symmetry | N | Not generally applicable unless the task involves dual-arm coordination or symmetric workpieces. | N/A |
| 9. Material Properties | Y | The stiffness and damping of the environment dictate the required impedance parameters of the controller. | High stiffness (e.g., 5000 N/m) is required for interacting with a rigid metal surface compared to a soft sponge. |
| 10. Internal Volume | N | Not applicable as the interaction is primarily on the surface of the object. | N/A |
| 11. Kinematic Chain | Y | The robot must avoid singular configurations where it loses the ability to exert or measure forces in certain directions. | Keeping the elbow joint slightly bent to maintain a high manipulability measure during the polishing task. |
| 12. Energy | Y | The controller must dissipate energy (via damping) to ensure stable contact and prevent bouncing or oscillations. | Setting the damping ratio of the impedance controller to 1.0 (critically damped) to prevent the end-effector from chattering on the surface. |
| 13. Feedback | Y | Continuous high-frequency feedback from joint torque sensors or a force-torque sensor is required to close the control loop. | Reading the Franka Panda's estimated external wrench at 1000 Hz to update the impedance control law. |
| 14. Safety | Y | Force and torque limits must be strictly enforced to prevent injury to humans or damage to the robot. | Implementing a safety monitor that triggers a Category 0 stop if the measured external force exceeds 50 N. |
| 15. Aesthetic | N | Not applicable to the physical execution of the behavior. | N/A |

---

# IMPACT/STRIKING BEHAVIOR: Franka Emika Panda Specification

## SECTION 1: Behavior Definition

**Impact/Striking Behavior** describes a robot's controlled, high-speed motion designed to transfer a significant amount of kinetic energy to a target object through a direct collision. This behavior is fundamentally distinct from other manipulation tasks, such as pushing or grasping, due to its primary objective: the intentional application of a concentrated, transient force to elicit a specific physical response from the target. Unlike pushing, which involves continuous contact and force application over a duration, striking is characterized by a rapid acceleration phase followed by an abrupt deceleration upon impact, maximizing the instantaneous force delivered. Similarly, it differs from grasping, which focuses on secure object manipulation and often minimizes impact forces to prevent damage.

This behavior is crucial for tasks where a sudden, forceful interaction is required. Real-world applications include hammering a nail, where the impact drives the nail into a surface; striking a bell or percussion instrument to produce sound; or even controlled demolition tasks where precise, high-energy impacts are necessary to break or deform materials. The effectiveness of this behavior is directly proportional to the kinetic energy transferred, making factors like end-effector velocity, mass, and material properties of both the end-effector and the target critical considerations. The collision itself is not an accidental byproduct but the core mechanism through which the robot achieves its objective.

## SECTION 2: Semantic Constraint Matrix

The semantic constraint matrix outlines the critical parameters and rules governing the Impact/Striking Behavior, ensuring its proper execution and physical realism within the simulation environment. Each domain is assessed for its applicability to this specific behavior, with detailed values or rules and concrete examples tailored to the Franka Emika Panda robot.

| Constraint Domain | Applies (Y/N) | Specific Constraint Value/Rule | Example for the Franka Panda context |
| :--- | :---: | :--- | :--- |
| Directional Semantics | Y | The impact direction must be specified as a vector relative to the end-effector's frame. | The end-effector must strike the nail along its primary axis to drive it in. |
| Range Limits | Y | The robot's joint limits and workspace must be respected during the high-speed motion. | The Franka Panda's wrist must not exceed its torque limits of +/-12 Nm during the swing. |
| Pivot Placement | Y | The pivot point of the end-effector and target object must be at their center of mass for realistic dynamics. | The pivot of the hammer tool attached to the Franka should be at its center of mass. |
| Clearance/Tolerance | Y | A minimum clearance must be maintained from other objects during the backswing and approach. | A 5 cm clearance must be maintained from the work surface during the hammering motion. |
| Sequential Dependency | Y | The striking action must be preceded by a backswing and followed by a retraction. | The robot must first perform a backswing of at least 20 cm before initiating the strike. |
| Force/Torque Realism | Y | The impact force must be sufficient to achieve the task, and the robot's joints must withstand the resulting torques. | The impact must generate at least 500 N of force to hammer the nail. |
| Contact/Friction | Y | The material properties (friction, restitution) of the end-effector and target must be accurately modeled. | The restitution between the hammer and nail should be low (e.g., 0.1) to minimize bouncing. |
| Symmetry | N | Not directly applicable, as impact is typically a directional, asymmetric action. | N/A |
| Material Properties | Y | The density and stiffness of the end-effector and target object are critical for accurate impact simulation. | The hammer head should be modeled as steel (density ~7850 kg/m3) for realistic mass. |
| Internal Volume | N | Not relevant for solid objects typically involved in striking tasks. | N/A |
| Kinematic Chain | Y | The entire kinematic chain of the robot must be considered to ensure stability and accurate force propagation. | The solver iteration counts for the Franka's articulation must be high enough to handle the impact forces without instability. |
| Energy | Y | The kinetic energy of the end-effector must be sufficient to perform the task, and energy dissipation upon impact must be realistic. | The end-effector should reach a velocity of at least 2 m/s before impact. |
| Feedback | Y | The system must provide feedback on contact forces and object states to validate the impact. | Contact reports must be enabled to detect the precise moment and force of impact. |
| Safety | Y | The robot's motion must be constrained to avoid self-collision and damage to the environment. | A safety controller should monitor joint torques and halt the robot if they exceed a predefined threshold. |
| Aesthetic | N | Aesthetics are not a primary concern for this behavior, which prioritizes function over form. | N/A |

---

# PULLING/TENSION-BASED MOTION Specification

## SECTION 1: Behavior Definition

The **PULLING/TENSION-BASED MOTION** behavior involves a robot applying a sustained tensile force to an object to overcome resistance, such as friction or mechanical constraints, thereby extracting or moving it. This behavior is distinct from simple grasping or lifting in that it specifically focuses on the continuous application of force along a vector to dislodge or translate an object against an opposing force. Unlike pushing, which involves compressive forces, pulling relies on tensile strength and the ability to maintain a secure grasp while exerting force away from the robot's base. This motion is critical for tasks requiring the extraction of components, such as pulling a stuck drawer open, removing a tight-fitting peg from a hole, or disconnecting an electrical plug from a socket. The success of this behavior is highly dependent on the robot's ability to generate sufficient force, maintain stability, and accurately control the direction of pull.

For the Franka Emika Panda, executing a pulling motion requires careful consideration of its physical capabilities. The Franka Hand gripper, with a maximum continuous force of 70 N and an 80 mm maximum opening, must securely grasp the target object. The robot's payload capacity of 3 kg dictates the maximum weight it can effectively pull without compromising stability or control. Furthermore, the wrist torque of +/-12 Nm and main joint torque of +/-87 Nm are crucial for generating and sustaining the necessary pulling force while maintaining the desired trajectory and resisting reactive forces from the object. Insufficient gripper force would lead to slippage, while inadequate joint torque could result in the robot being unable to overcome the object's resistance or deviating from the intended path. Therefore, precise control over these parameters is essential for successful tension-based manipulation.

## SECTION 2: Semantic Constraint Matrix

| Domain | Applies | Constraint Value/Rule | Example for Franka Panda |
| :--- | :---: | :--- | :--- |
| 1. Directional Semantics | Y | The primary force vector must be aligned with the object's axis of extraction (e.g., outward from a socket or along a drawer's rails). | Pulling a plug straight out of a wall socket along the Z-axis of the socket frame. |
| 2. Range Limits | Y | The pulling motion must not exceed the kinematic reach of the robot or the physical limits of the object's extraction path. | Pulling a drawer open only up to its maximum extension limit (e.g., 30 cm) to prevent damage. |
| 3. Pivot Placement | N | Pulling is typically a translational motion, not a rotational one around a pivot. | N/A |
| 4. Clearance/Tolerance | Y | The gripper must have sufficient clearance to grasp the object without colliding with surrounding structures. | Ensuring the Franka Hand (80 mm max opening) can fit around a plug without hitting the socket faceplate. |
| 5. Sequential Dependency | Y | The object must be securely grasped *before* the pulling force is applied. | The gripper must close and achieve a stable grasp on a peg before the arm moves to extract it. |
| 6. Force/Torque Realism | Y | The applied pulling force must exceed the object's resistance (friction, mechanical retention) but remain within the robot's capabilities. | Applying a 40 N pulling force to overcome the static friction of a stuck drawer, well within the Franka's limits. |
| 7. Contact/Friction | Y | The friction between the gripper fingers and the object must be sufficient to prevent slippage during the pull. | Using high-friction gripper pads to maintain a secure hold on a smooth plastic plug while pulling. |
| 8. Symmetry | N | Pulling does not inherently require symmetrical motion or object properties. | N/A |
| 9. Material Properties | Y | The object must be rigid enough to withstand the pulling force without deforming or breaking. | Pulling a solid metal peg rather than a fragile glass tube that might shatter under tension. |
| 10. Internal Volume | N | Internal volume is generally irrelevant to the external pulling motion. | N/A |
| 11. Kinematic Chain | Y | The robot's kinematic chain must be configured to allow for a smooth, continuous pulling motion along the desired vector. | Positioning the Franka arm such that the pulling motion primarily utilizes the more powerful base joints rather than relying solely on the wrist. |
| 12. Energy | Y | The energy expended during the pull must be managed to avoid sudden jerks or instability when the object releases. | Controlling the velocity and acceleration of the arm to ensure a smooth extraction of a plug, preventing it from flying out uncontrollably. |
| 13. Feedback | Y | Force/torque feedback is essential to detect when the object has been successfully extracted or if the resistance is too high. | Monitoring the wrist torque sensor to detect the sudden drop in resistance when a peg pops out of its hole. |
| 14. Safety | Y | The pulling motion must not endanger the robot, the object, or the surrounding environment, especially upon sudden release. | Ensuring the robot's trajectory after pulling a plug does not cause it to collide with other equipment or personnel. |
| 15. Aesthetic | N | Aesthetic considerations are not a primary constraint for the physical execution of this behavior. | N/A |

---

# ROLLING BEHAVIOR Specification

## SECTION 1: Behavior Definition

The ROLLING BEHAVIOR describes the action of a robotic manipulator causing a round object (such as a ball, cylinder, or bottle) to translate and rotate simultaneously across a surface. This behavior is distinct from simple pushing or sliding in that it specifically enforces a kinematic constraint where the linear velocity of the object's contact point with the surface is equal to the product of its angular velocity and its radius (v = omega * r). This constraint ensures that the object is truly rolling without slipping. The robot initiates and guides this motion without grasping the object, relying instead on controlled contact forces to impart the necessary linear and angular momentum.

Physically, this behavior is characterized by the continuous change in the contact point between the object and the surface, as opposed to a sliding motion where the contact point remains relatively fixed or exhibits significant friction-induced slippage. The primary challenge lies in precisely controlling the applied force to maintain the rolling constraint, especially given variations in object geometry, mass distribution, and surface friction. This behavior is crucial for tasks such as manipulating objects across a workspace, reorienting items without lifting them, or clearing a path. It finds real-world applications in industrial settings for sorting or positioning cylindrical components, in logistics for moving packages, or even in domestic robotics for tidying up spherical or cylindrical household items.

## SECTION 2: Semantic Constraint Matrix

The semantic constraint matrix outlines the various domains that influence the successful execution and simulation of the ROLLING BEHAVIOR. Each domain specifies whether it applies to this behavior, the specific rule or value, and a relevant example within the context of the Franka Emika Panda robot.

| Constraint Domain | Applies (YES/NO) | Constraint Value/Rule |
| :--- | :---: | :--- |
| Directional Semantics | YES | The force must be applied tangentially to the object's surface to induce rotation. The force vector should be perpendicular to the radius at the point of contact. A downward force would pin the object, while a force through the center of mass would cause it to slide. For the Franka, this means the gripper must approach the object from the side. |
| Range Limits | YES | The robot's payload (3 kg), gripper force (70 N continuous), and joint torques must not be exceeded. The object's size and mass must be within these limits. A heavy object will overload the robot, while a very small object may be difficult to control. For the Franka, rolling a 1 kg cylinder with a 5 cm radius is well within its capabilities. |
| Pivot Placement | YES | The object's pivot (origin) must be at its center of mass. If the pivot is offset, the object will have an unbalanced rotation, causing it to wobble and fail to roll straight. In Blender, this means setting the object's origin to its geometric center, assuming uniform density. |
| Clearance/Tolerance | YES | The robot's gripper must have enough clearance to apply force without colliding with the rolling surface. The tolerance for maintaining the rolling contact point is small. A slight deviation in force application can cause slipping. The Franka Hand's fingers need to be positioned to avoid hitting the table. |
| Sequential Dependency | YES | The behavior must be initiated with a specific sequence: 1. Establish stable contact. 2. Apply tangential force and angular velocity simultaneously. 3. Maintain force and velocity to sustain rolling. Skipping or reordering these steps will result in failure. |
| Force/Torque Realism | YES | The applied force must be sufficient to overcome inertia and friction while maintaining the rolling constraint. The Franka's wrist and joint torques must be within their limits (+/-12 Nm and +/-87 Nm, respectively). An incorrect force will cause slipping or failure to initiate rolling. |
| Contact/Friction | YES | High static and dynamic friction are essential for rolling. If static friction is too low, the object will slip instead of roll. If dynamic friction is too high, it will be difficult to initiate and maintain smooth rolling. The choice of friction coefficients depends on the object and surface materials (e.g., a rubber ball on a wooden table). |
| Symmetry | YES | The object should be rotationally symmetric around its rolling axis. Asymmetric objects (e.g., a rock) will have a shifting center of mass as they rotate, making controlled rolling nearly impossible. The Franka would need a highly adaptive controller to handle such an object, which is beyond the scope of this basic behavior. |
| Material Properties | YES | The object's material properties, particularly its friction coefficients and restitution (bounciness), are critical. A soft, deformable object will behave differently from a rigid one. The material properties must be accurately modeled in the simulation to achieve realistic behavior. |
| Internal Volume | NO | The internal volume of the object is not directly relevant to the rolling behavior, as long as the object is treated as a rigid body with a defined mass and center of mass. |
| Kinematic Chain | YES | The robot's kinematic chain must be correctly defined in its USD file to allow for accurate inverse kinematics and trajectory planning. An incorrect kinematic chain will lead to unreachable targets and failed manipulation. The Franka's 7-DOF arm and gripper must be accurately represented. |
| Energy | YES | The rolling motion must be energetically plausible. The energy input by the robot must be sufficient to overcome frictional losses and increase the kinetic energy (both linear and rotational) of the object. An energy-conserving simulation is crucial for realistic behavior. |
| Feedback | YES | The robot needs continuous feedback (e.g., from joint encoders and force/torque sensors) to adjust its applied force and maintain the rolling constraint. Without feedback, any small perturbation would cause the behavior to fail. The Franka's built-in sensors are essential for this. |
| Safety | YES | The robot's movements must be smooth and predictable to ensure safety. Sudden changes in force or velocity could cause the object to become a projectile. The Franka's collision detection and emergency stop features are crucial safety constraints. The behavior should include limits on acceleration and velocity. |
| Aesthetic | NO | The aesthetic appearance of the rolling motion is not a primary constraint for this behavior, although a smooth, controlled roll is inherently more aesthetically pleasing than a jerky, slipping one. |
