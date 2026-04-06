# Pipeline Architecture — 4-Layer Semantic Behavior System
*See also: BEHAVIOR_DEFINITIONS.md, ISAAC_SIM_PHYSICS_REFERENCE.md, BLENDER_ASSET_REQUIREMENTS.md*

# Semantic Behavior System: Complete Architecture & Process Guide

## Table of Contents
1. [Overview](#overview)
2. [4-Layer Architecture](#4-layer-architecture)
3. [Process Flow](#process-flow)
4. [Detailed Layer Specifications](#detailed-layer-specifications)
5. [Implementation Guide](#implementation-guide)
6. [Example: Cabinet Door](#example-cabinet-door)

---

## Overview

This document describes a **4-layer system** for modeling robot-object interactions through semantic behavior analysis. The system takes a natural language description, generates a 3D object in Blender, extracts mechanical constraints, computes valid behaviors, and filters them through robot capabilities.

### Key Concepts

- **Mechanical Constraints (Layer 1)**: What the object CAN do physically
- **Plausible Actions (Layer 2)**: What the object COULD do given its mechanics
- **Semantic Constraints (Layer 3)**: What the object SHOULD do given its context
- **Robot Interaction (Layer 4)**: What a specific robot CAN execute

---

## 4-Layer Architecture

### Layer 1: Mechanical Constraints (Object Intrinsic)

**Purpose**: Extract the fundamental mechanical properties of the object from its geometry and design.

**What it captures**:
- Joint types and configurations (revolute, prismatic, etc.)
- Degrees of freedom (DOF)
- Material properties (friction, elasticity, strength)
- Geometric properties (dimensions, mass, center of gravity)
- Attachment points (handles, grasping surfaces)

**Output**: Structured mechanical specification

**Example - Cabinet Door**:
```
Joints:
  - hinge_1: revolute joint
    - Axis: [0, 0, 1] (Z-axis)
    - Location: [0.4, 2.0, 0.0]
    - DOF: 1
    - Material: metal
    - Friction coefficient: 0.15

Geometry:
  - Type: rigid body
  - Dimensions: 0.4m × 0.6m × 0.02m
  - Mass: 5.0 kg
  - Material: wood

Attachment Points:
  - handle_1: [0.2, 0.3, 0.0]
    - Type: grasping surface
    - Diameter: 0.05m
```

---

### Layer 2: Plausible Actions (Mechanical Feasibility)

**Purpose**: Generate all physically realizable motions given the mechanical constraints.

**What it captures**:
- All possible joint motions (full range, no context)
- Force/torque requirements for each motion
- Feasibility classification (MECHANICALLY_PLAUSIBLE)

**Key insight**: This layer is UNCONSTRAINED - it represents what the object CAN physically do, regardless of context.

**Output**: Set of plausible actions

**Example - Cabinet Door**:
```
Action 1: Rotate CW
  - Type: rotation
  - Joint: hinge_1
  - Range: [0, 2π] radians (0-360°)
  - Torque range: [0, 50] Nm
  - Feasibility: MECHANICALLY_PLAUSIBLE

Action 2: Rotate CCW
  - Type: rotation
  - Joint: hinge_1
  - Range: [-2π, 0] radians (-360° to 0°)
  - Torque range: [0, 50] Nm
  - Feasibility: MECHANICALLY_PLAUSIBLE

Action 3: Grasp handle
  - Type: grasping
  - Location: [0.2, 0.3, 0.0]
  - Grip force range: [0.1, 500] N
  - Feasibility: MECHANICALLY_PLAUSIBLE
```

---

### Layer 3: Semantic Constraints (Contextual Validity)

**Purpose**: Filter plausible actions through semantic constraints based on context, environment, and purpose.

**What it captures**:
- All 15 semantic constraint domains
- Constraint violations and satisfactions
- Valid behavior ranges (e.g., 0-110° instead of 0-360°)
- Reasoning for validity/invalidity

**Key insight**: This layer is CONTEXT-DEPENDENT - it represents what the object SHOULD do given its environment and purpose.

**The 15 Semantic Constraint Domains**:

| # | Domain | Description |
|---|--------|-------------|
| 1 | Directional | Motion must match intended direction |
| 2 | Range Limits | Motion must stay within physical bounds |
| 3 | Pivot Placement | Rotation around correct pivot point |
| 4 | Clearance | Motion must not cause self-collision |
| 5 | Sequential | Actions may have prerequisites |
| 6 | Force/Torque | Applied force must be realistic |
| 7 | Contact/Friction | Surfaces must maintain proper contact |
| 8 | Symmetry | Motion may be symmetric or asymmetric |
| 9 | Material | Material properties affect behavior |
| 10 | Internal Volume | Internal geometry restricts motion |
| 11 | Kinematic Chain | Motion respects mechanical structure |
| 12 | Energy | Motion requires appropriate energy source |
| 13 | Feedback | Motion may require sensors |
| 14 | Safety | Motion includes safety limits |
| 15 | Aesthetic | Motion affects visual appearance |

**Output**: Set of semantically valid behaviors with constraint justifications

**Example - Cabinet Door**:
```
Valid Behavior 1: Rotate outward (0-110°)
  - Constraint 1 (Directional): ✓ SATISFIED
    Reason: Rotation matches intended outward direction
  - Constraint 10 (Internal Volume): ✓ SATISFIED
    Reason: Rotation clears internal shelves (limited to 110°)
  - Constraint 14 (Safety): ✓ SATISFIED
    Reason: Required torque (5 Nm) within safety limit (10 Nm)
  - Overall: ✓ SEMANTICALLY VALID

Invalid Behavior 1: Rotate inward (0-360°)
  - Constraint 10 (Internal Volume): ✗ VIOLATED
    Reason: Would collide with internal shelves
  - Constraint 14 (Safety): ✗ VIOLATED
    Reason: Would crush contents
  - Overall: ✗ SEMANTICALLY INVALID

Valid Behavior 2: Grasp handle and rotate
  - Constraint 5 (Sequential): ✓ SATISFIED
    Reason: Grasp must precede rotation
  - Constraint 6 (Force/Torque): ✓ SATISFIED
    Reason: Grip force (5 N) sufficient to hold door
  - Overall: ✓ SEMANTICALLY VALID
```

---

### Layer 4: Robot Interaction (Robot Capability Filtering)

**Purpose**: Filter semantically valid behaviors through robot-specific capabilities.

**What it captures**:
- Robot specifications (gripper type, workspace, force limits, sensors)
- Interaction feasibility checks (geometry, force, reach, sensors)
- Recommended approach parameters (grip force, velocity, etc.)

**Key insight**: This layer is ROBOT-SPECIFIC - it represents what a particular robot (Franka Emika Panda) can actually execute.

**Output**: Set of robot-executable behaviors with interaction details

**Example - Cabinet Door with Franka Panda**:
```
Robot: Franka Emika Panda
Gripper: Parallel Gripper
  - Finger width: 0.04m
  - Max grip force: 170 N
  - Min grip force (with control): 0.1 N
  - Has force feedback: Yes
  - Workspace reach: 0.85m
  - Has wrist F/T sensor: Yes

Executable Behavior 1: Grasp handle and rotate outward
  - Status: ✓ EXECUTABLE
  - Interaction Checks:
    - Gripper geometry: ✓ PASS
      Handle diameter (0.05m) fits within gripper width (0.04m)
    - Force requirement: ✓ PASS
      Required grip force (5 N) achievable (0.1-170 N range)
    - Torque requirement: ✓ PASS
      Required torque (5 Nm) easily achievable via arm
    - Workspace reachability: ✓ PASS
      Handle location within Panda workspace
    - Sensor capability: ✓ PASS
      Force feedback available for precise control
  - Recommended Approach:
    - Gripper configuration: parallel_grip
    - Grip force: 5.0 N
    - Approach velocity: 0.1 m/s
    - Rotation velocity: 0.5 rad/s

Non-Executable Behavior 1: Rotate inward
  - Status: ✗ NOT EXECUTABLE
  - Reason: Semantically invalid (Layer 3 constraint violation)
  - Cannot execute semantically invalid behaviors
```

---

## Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Natural Language Description                             │
│ Example: "Create a wooden cabinet with internal shelves,        │
│          a hinged door on the left side, and a handle"          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: BLENDER MCP - Generate 3D Asset                         │
│ - Calls Blender MCP with natural language instruction           │
│ - Generates 3D model with mechanical parts                      │
│ - Exports geometry, joint metadata, material properties         │
│ Output: 3D model file + metadata                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: LAYER 1 - Extract Mechanical Constraints               │
│ - Parse Blender model for joint definitions                     │
│ - Extract geometry and material properties                      │
│ - Identify attachment points (handles, grasping surfaces)       │
│ - Compute DOF and kinematic structure                           │
│ Output: Mechanical specification (JSON)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: LAYER 2 - Compute Plausible Actions                    │
│ - For each joint: generate all mechanically feasible motions    │
│ - For each surface: identify grasping points                    │
│ - Compute force/torque requirements                             │
│ - Mark all as MECHANICALLY_PLAUSIBLE                            │
│ Output: Set of plausible actions (JSON)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: LAYER 3 - Apply Semantic Constraints                   │
│ - Define environment context (internal obstacles, etc.)         │
│ - Define intended behavior (purpose, direction, etc.)           │
│ - Define safety limits (force, torque, etc.)                    │
│ - For each plausible action:                                    │
│   - Check all 15 semantic constraint domains                    │
│   - Mark as SEMANTICALLY_VALID or SEMANTICALLY_INVALID          │
│   - Record constraint violations/satisfactions                  │
│ Output: Semantically valid behaviors (JSON)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: LAYER 4 - Filter Through Robot Capabilities            │
│ - Define robot specs (Franka Panda gripper)                     │
│ - For each semantically valid behavior:                         │
│   - Check gripper geometry compatibility                        │
│   - Check force/torque requirements                             │
│   - Check workspace reachability                                │
│   - Check sensor requirements                                   │
│   - Mark as ROBOT_EXECUTABLE or NOT_EXECUTABLE                 │
│ - Recommend approach parameters                                 │
│ Output: Robot-executable behaviors (JSON)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: Comprehensive Specification                             │
│ - All 4 layers with full justifications                         │
│ - Ready for robot simulation/execution                          │
│ - Includes recommended approach parameters                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Layer Specifications

### Layer 1: Mechanical Constraints - Detailed Specification

```json
{
  "layer_1_mechanical_constraints": {
    "object_metadata": {
      "name": "Cabinet Door",
      "description": "Wooden cabinet door with metal hinge and handle",
      "source": "blender_mcp_generated"
    },
    "joints": [
      {
        "joint_id": "hinge_1",
        "type": "revolute",
        "axis": [0, 0, 1],
        "location": [0.4, 2.0, 0.0],
        "dof": 1,
        "rotation_limits": [0, 6.28],
        "material": "metal",
        "friction_coefficient": 0.15,
        "damping": 2.0,
        "max_torque": 50.0
      }
    ],
    "geometry": {
      "type": "rigid_body",
      "mesh_file": "cabinet_door.obj",
      "dimensions": {
        "width": 0.4,
        "height": 0.6,
        "depth": 0.02
      },
      "mass": 5.0,
      "center_of_gravity": [0.2, 0.3, 0.01],
      "material": "wood",
      "density": 600
    },
    "attachment_points": [
      {
        "point_id": "handle_1",
        "type": "grasping_surface",
        "location": [0.2, 0.3, 0.0],
        "diameter": 0.05,
        "material": "metal",
        "friction_coefficient": 0.3
      }
    ],
    "collision_geometry": {
      "type": "box",
      "dimensions": [0.4, 0.6, 0.02],
      "location": [0.2, 0.3, 0.01]
    }
  }
}
```

### Layer 2: Plausible Actions - Detailed Specification

```json
{
  "layer_2_plausible_actions": [
    {
      "action_id": "rotate_cw",
      "type": "rotation",
      "joint": "hinge_1",
      "description": "Rotate clockwise around hinge",
      "range": [0, 6.28],
      "range_degrees": [0, 360],
      "torque_range": [0, 50],
      "velocity_range": [0, 2.0],
      "feasibility": "MECHANICALLY_PLAUSIBLE",
      "feasibility_reason": "Hinge allows full rotation"
    },
    {
      "action_id": "rotate_ccw",
      "type": "rotation",
      "joint": "hinge_1",
      "description": "Rotate counter-clockwise around hinge",
      "range": [-6.28, 0],
      "range_degrees": [-360, 0],
      "torque_range": [0, 50],
      "velocity_range": [0, 2.0],
      "feasibility": "MECHANICALLY_PLAUSIBLE",
      "feasibility_reason": "Hinge allows full rotation"
    },
    {
      "action_id": "grasp_handle",
      "type": "grasping",
      "attachment_point": "handle_1",
      "description": "Grasp the door handle",
      "grip_force_range": [0.1, 500],
      "contact_points": 2,
      "feasibility": "MECHANICALLY_PLAUSIBLE",
      "feasibility_reason": "Handle is accessible and graspable"
    }
  ]
}
```

### Layer 3: Semantic Constraints - Detailed Specification

```json
{
  "layer_3_semantic_constraints": {
    "environment_context": {
      "internal_obstacles": [
        {
          "obstacle_id": "shelf_1",
          "type": "shelf",
          "location": [0.1, 1.5, 0.0],
          "dimensions": [0.3, 0.2, 0.5]
        },
        {
          "obstacle_id": "shelf_2",
          "type": "shelf",
          "location": [0.1, 1.0, 0.0],
          "dimensions": [0.3, 0.2, 0.5]
        }
      ],
      "external_obstacles": [],
      "intended_behavior": {
        "purpose": "store_dishes",
        "direction": "outward",
        "description": "Cabinet door should open outward to access shelves"
      },
      "safety_limits": {
        "max_torque": 10.0,
        "max_force": 100.0,
        "max_velocity": 1.0
      }
    },
    "valid_behaviors": [
      {
        "behavior_id": "rotate_outward",
        "description": "Rotate door outward (0-110°)",
        "valid": true,
        "constraints_satisfied": [
          {
            "domain": 1,
            "name": "Directional",
            "status": "SATISFIED",
            "reason": "Rotation matches intended outward direction"
          },
          {
            "domain": 10,
            "name": "Internal Volume",
            "status": "SATISFIED",
            "reason": "Rotation clears internal shelves (limited to 110°)"
          },
          {
            "domain": 14,
            "name": "Safety",
            "status": "SATISFIED",
            "reason": "Required torque (5 Nm) within safety limit (10 Nm)"
          }
        ],
        "rotation_range": [0, 1.92],
        "rotation_range_degrees": [0, 110],
        "required_torque": 5.0,
        "required_force": 0.0
      },
      {
        "behavior_id": "grasp_and_rotate",
        "description": "Grasp handle and rotate door outward",
        "valid": true,
        "constraints_satisfied": [
          {
            "domain": 5,
            "name": "Sequential",
            "status": "SATISFIED",
            "reason": "Grasp must precede rotation"
          },
          {
            "domain": 6,
            "name": "Force/Torque",
            "status": "SATISFIED",
            "reason": "Grip force (5 N) sufficient to hold door"
          }
        ],
        "required_grip_force": 5.0,
        "required_torque": 5.0
      }
    ],
    "invalid_behaviors": [
      {
        "behavior_id": "rotate_inward",
        "description": "Rotate door inward",
        "valid": false,
        "constraints_violated": [
          {
            "domain": 10,
            "name": "Internal Volume",
            "reason": "Would collide with internal shelves"
          },
          {
            "domain": 14,
            "name": "Safety",
            "reason": "Would crush contents"
          }
        ]
      }
    ]
  }
}
```

### Layer 4: Robot Interaction - Detailed Specification

```json
{
  "layer_4_robot_interaction": {
    "robot_metadata": {
      "robot_name": "Franka Emika Panda",
      "gripper_type": "Parallel Gripper",
      "dof": 7,
      "payload_capacity": 3.0
    },
    "gripper_specifications": {
      "gripper_id": "panda_gripper",
      "type": "parallel_gripper",
      "finger_width": 0.04,
      "max_grip_force": 170,
      "min_grip_force_with_control": 0.1,
      "has_force_feedback": true,
      "has_tactile_sensing": false,
      "workspace_reach": 0.85,
      "has_wrist_ft_sensor": true,
      "wrist_ft_sensor_range": {
        "force": [-330, 330],
        "torque": [-15, 15]
      }
    },
    "executable_behaviors": [
      {
        "behavior_id": "grasp_and_rotate_outward",
        "executable": true,
        "interaction_checks": [
          {
            "check_id": "gripper_geometry",
            "check_name": "Gripper Geometry Compatibility",
            "status": "PASS",
            "details": "Handle diameter (0.05m) fits within gripper width (0.04m)",
            "critical": true
          },
          {
            "check_id": "force_requirement",
            "check_name": "Force Requirement",
            "status": "PASS",
            "details": "Required grip force (5 N) achievable with Panda (0.1-170 N range)",
            "critical": true
          },
          {
            "check_id": "torque_requirement",
            "check_name": "Torque Requirement",
            "status": "PASS",
            "details": "Required torque (5 Nm) easily achievable via Panda arm",
            "critical": true
          },
          {
            "check_id": "workspace_reach",
            "check_name": "Workspace Reachability",
            "status": "PASS",
            "details": "Handle location within Panda workspace (0.85m reach)",
            "critical": true
          },
          {
            "check_id": "sensor_capability",
            "check_name": "Sensor Capability",
            "status": "PASS",
            "details": "Force feedback available for precise control",
            "critical": false
          }
        ],
        "recommended_approach": {
          "gripper_configuration": "parallel_grip",
          "grip_force": 5.0,
          "grip_force_unit": "N",
          "approach_velocity": 0.1,
          "approach_velocity_unit": "m/s",
          "rotation_velocity": 0.5,
          "rotation_velocity_unit": "rad/s",
          "force_control_enabled": true,
          "collision_detection_enabled": true
        }
      },
      {
        "behavior_id": "rotate_inward",
        "executable": false,
        "reason": "Semantically invalid (Layer 3 constraint violation)",
        "cannot_execute_reason": "Behavior violates semantic constraints; robot cannot execute invalid behaviors"
      }
    ]
  }
}
```

---

## Implementation Guide

### Prerequisites

- Python 3.8+
- Blender with MCP support
- Libraries: `json`, `numpy`, `trimesh` (for geometry processing)

### Step-by-Step Implementation

#### Step 1: Define Natural Language Input

```python
object_description = """
Create a wooden cabinet with:
- Dimensions: 0.4m wide, 0.6m tall, 0.3m deep
- Internal shelves at 1.5m and 1.0m height
- Hinged door on left side with metal hinge
- Door handle at center
- Purpose: store dishes
"""
```

#### Step 2: Call Blender MCP to Generate Asset

```python
import subprocess
import json

def generate_blender_asset(description):
    """Call Blender MCP with natural language instruction"""
    
    prompt = f"""
    {description}
    
    Export the model with:
    1. Joint metadata (hinge location, axis, type)
    2. Geometry (mesh, dimensions, mass)
    3. Material properties (friction, elasticity)
    4. Attachment points (handles, grasping surfaces)
    """
    
    # Call Blender MCP (implementation depends on MCP interface)
    result = call_blender_mcp(prompt)
    
    return result['model_file'], result['metadata']
```

#### Step 3: Extract Layer 1 - Mechanical Constraints

```python
def extract_mechanical_constraints(model_file, metadata):
    """Extract mechanical constraints from Blender model"""
    
    constraints = {
        'object_metadata': {
            'name': metadata['name'],
            'description': metadata['description']
        },
        'joints': [],
        'geometry': {},
        'attachment_points': []
    }
    
    # Parse joint definitions
    for joint in metadata['joints']:
        constraints['joints'].append({
            'joint_id': joint['id'],
            'type': joint['type'],
            'axis': joint['axis'],
            'location': joint['location'],
            'dof': joint['dof'],
            'material': joint['material'],
            'friction_coefficient': joint['friction']
        })
    
    # Extract geometry
    constraints['geometry'] = {
        'type': 'rigid_body',
        'mesh_file': model_file,
        'dimensions': metadata['dimensions'],
        'mass': metadata['mass'],
        'material': metadata['material']
    }
    
    # Extract attachment points
    for point in metadata['attachment_points']:
        constraints['attachment_points'].append({
            'point_id': point['id'],
            'type': point['type'],
            'location': point['location'],
            'diameter': point['diameter']
        })
    
    return constraints
```

#### Step 4: Compute Layer 2 - Plausible Actions

```python
def compute_plausible_actions(mechanical_constraints):
    """Generate all mechanically feasible actions"""
    
    plausible_actions = []
    
    # For each joint, generate rotation actions
    for joint in mechanical_constraints['joints']:
        if joint['type'] == 'revolute':
            plausible_actions.append({
                'action_id': f"rotate_cw_{joint['joint_id']}",
                'type': 'rotation',
                'joint': joint['joint_id'],
                'range': [0, 2*3.14159],
                'torque_range': [0, 50],
                'feasibility': 'MECHANICALLY_PLAUSIBLE'
            })
            plausible_actions.append({
                'action_id': f"rotate_ccw_{joint['joint_id']}",
                'type': 'rotation',
                'joint': joint['joint_id'],
                'range': [-2*3.14159, 0],
                'torque_range': [0, 50],
                'feasibility': 'MECHANICALLY_PLAUSIBLE'
            })
    
    # For each attachment point, generate grasping actions
    for point in mechanical_constraints['attachment_points']:
        plausible_actions.append({
            'action_id': f"grasp_{point['point_id']}",
            'type': 'grasping',
            'attachment_point': point['point_id'],
            'grip_force_range': [0.1, 500],
            'feasibility': 'MECHANICALLY_PLAUSIBLE'
        })
    
    return plausible_actions
```

#### Step 5: Apply Layer 3 - Semantic Constraints

```python
def apply_semantic_constraints(plausible_actions, environment_context):
    """Filter actions through semantic constraints"""
    
    valid_behaviors = []
    invalid_behaviors = []
    
    for action in plausible_actions:
        validity = {
            'action_id': action['action_id'],
            'valid': True,
            'constraints_satisfied': [],
            'constraints_violated': []
        }
        
        # Check Domain 1: Directional
        if action['type'] == 'rotation':
            intended_direction = environment_context['intended_behavior']['direction']
            if intended_direction == 'outward' and is_outward_rotation(action):
                validity['constraints_satisfied'].append({
                    'domain': 1,
                    'name': 'Directional',
                    'status': 'SATISFIED'
                })
            else:
                validity['valid'] = False
                validity['constraints_violated'].append({
                    'domain': 1,
                    'name': 'Directional',
                    'reason': 'Does not match intended direction'
                })
        
        # Check Domain 10: Internal Volume
        if action['type'] == 'rotation':
            if check_internal_volume_collision(action, environment_context):
                validity['valid'] = False
                validity['constraints_violated'].append({
                    'domain': 10,
                    'name': 'Internal Volume',
                    'reason': 'Would collide with internal obstacles'
                })
            else:
                validity['constraints_satisfied'].append({
                    'domain': 10,
                    'name': 'Internal Volume',
                    'status': 'SATISFIED'
                })
        
        # Check Domain 14: Safety
        required_torque = action.get('torque_range', [0, 0])[1]
        max_torque = environment_context['safety_limits']['max_torque']
        if required_torque <= max_torque:
            validity['constraints_satisfied'].append({
                'domain': 14,
                'name': 'Safety',
                'status': 'SATISFIED'
            })
        else:
            validity['valid'] = False
            validity['constraints_violated'].append({
                'domain': 14,
                'name': 'Safety',
                'reason': 'Exceeds safety torque limit'
            })
        
        # Classify as valid or invalid
        if validity['valid']:
            valid_behaviors.append(validity)
        else:
            invalid_behaviors.append(validity)
    
    return valid_behaviors, invalid_behaviors
```

#### Step 6: Filter Through Layer 4 - Robot Interaction

```python
def filter_robot_interaction(valid_behaviors, robot_specs):
    """Filter through robot capabilities"""
    
    executable_behaviors = []
    non_executable_behaviors = []
    
    for behavior in valid_behaviors:
        interaction = {
            'behavior_id': behavior['action_id'],
            'executable': True,
            'interaction_checks': []
        }
        
        # Check 1: Gripper geometry
        if behavior['type'] == 'grasping':
            gripper_width = robot_specs['gripper_specifications']['finger_width']
            object_size = get_object_size(behavior)
            if object_size <= gripper_width:
                interaction['interaction_checks'].append({
                    'check_name': 'Gripper Geometry',
                    'status': 'PASS'
                })
            else:
                interaction['executable'] = False
                interaction['interaction_checks'].append({
                    'check_name': 'Gripper Geometry',
                    'status': 'FAIL',
                    'reason': 'Object too large for gripper'
                })
        
        # Check 2: Force requirement
        required_force = behavior.get('required_force', 0)
        max_force = robot_specs['gripper_specifications']['max_grip_force']
        if required_force <= max_force:
            interaction['interaction_checks'].append({
                'check_name': 'Force Requirement',
                'status': 'PASS'
            })
        else:
            interaction['executable'] = False
            interaction['interaction_checks'].append({
                'check_name': 'Force Requirement',
                'status': 'FAIL'
            })
        
        # Check 3: Workspace reach
        object_location = get_object_location(behavior)
        workspace_reach = robot_specs['gripper_specifications']['workspace_reach']
        if distance(object_location) <= workspace_reach:
            interaction['interaction_checks'].append({
                'check_name': 'Workspace Reach',
                'status': 'PASS'
            })
        else:
            interaction['executable'] = False
            interaction['interaction_checks'].append({
                'check_name': 'Workspace Reach',
                'status': 'FAIL'
            })
        
        # Classify
        if interaction['executable']:
            executable_behaviors.append(interaction)
        else:
            non_executable_behaviors.append(interaction)
    
    return executable_behaviors, non_executable_behaviors
```

#### Step 7: Generate Comprehensive Output

```python
def generate_output_specification(
    mechanical_constraints,
    plausible_actions,
    valid_behaviors,
    invalid_behaviors,
    executable_behaviors,
    non_executable_behaviors
):
    """Generate comprehensive 4-layer specification"""
    
    specification = {
        'layer_1_mechanical_constraints': mechanical_constraints,
        'layer_2_plausible_actions': plausible_actions,
        'layer_3_semantic_constraints': {
            'valid_behaviors': valid_behaviors,
            'invalid_behaviors': invalid_behaviors
        },
        'layer_4_robot_interaction': {
            'executable_behaviors': executable_behaviors,
            'non_executable_behaviors': non_executable_behaviors
        }
    }
    
    # Save to JSON
    with open('semantic_behavior_specification.json', 'w') as f:
        json.dump(specification, f, indent=2)
    
    return specification
```

---

## Example: Cabinet Door

### Input

```
Create a wooden cabinet with:
- Dimensions: 0.4m wide, 0.6m tall, 0.3m deep
- Internal shelves at 1.5m and 1.0m height
- Hinged door on left side with metal hinge
- Door handle at center
- Purpose: store dishes
```

### Layer 1 Output: Mechanical Constraints

```
Cabinet Door Mechanical Specification:
- Joint: Hinge (revolute, Z-axis, location [0.4, 2.0, 0.0])
- Geometry: Rigid body, 0.4m × 0.6m × 0.02m, 5.0 kg
- Material: Wood
- Attachment: Handle at [0.2, 0.3, 0.0]
```

### Layer 2 Output: Plausible Actions

```
Plausible Actions:
1. Rotate CW: [0, 360°], 0-50 Nm torque
2. Rotate CCW: [0, 360°], 0-50 Nm torque
3. Grasp handle: 0.1-500 N grip force
```

### Layer 3 Output: Semantic Constraints

```
Valid Behaviors:
✓ Rotate outward (0-110°): Clears shelves, matches intent, safe
✓ Grasp and rotate: Proper sequence, sufficient grip force

Invalid Behaviors:
✗ Rotate inward: Collides with shelves, unsafe
```

### Layer 4 Output: Robot Interaction

```
Franka Panda Execution:
✓ Grasp and rotate outward: EXECUTABLE
  - Gripper fits handle: PASS
  - Force achievable: PASS (5 N < 170 N)
  - Torque achievable: PASS (5 Nm easily done)
  - Within workspace: PASS
  - Recommended grip: 5.0 N, velocity: 0.5 rad/s
```

---

## Summary

This 4-layer system provides a comprehensive framework for modeling robot-object interactions:

1. **Layer 1**: Extracts what the object CAN do (mechanical properties)
2. **Layer 2**: Computes what the object COULD do (plausible actions)
3. **Layer 3**: Determines what the object SHOULD do (semantic validity)
4. **Layer 4**: Filters what the robot CAN execute (robot capabilities)

Together, these layers enable intelligent, context-aware robotic behavior that respects both physical constraints and semantic meaning.
