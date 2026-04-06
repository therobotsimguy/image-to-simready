# Blender Asset Requirements — Geometry, Collision, Materials, and Validation Protocols

> This document covers Blender geometry preparation and validation protocols. For behavior definitions see BEHAVIOR_DEFINITIONS.md. For Isaac Sim/PhysX parameters see ISAAC_SIM_PHYSICS_REFERENCE.md.

---

# BEHAVIOR: SLIDING/FRICTION-BASED MOTION — Blender Requirements

## SECTION 6: Blender Asset Requirements

For the SLIDING/FRICTION-BASED MOTION behavior to function correctly and realistically within Isaac Sim, the 3D assets modeled in Blender must adhere to specific requirements, particularly concerning collision meshes, pivot placement, and overall geometry. These requirements ensure accurate physical simulation and interaction.

*   **Collision Meshes**: Every object involved in the pushing interaction (the pushed object, the surface, and the robot end-effector) **MUST** have a well-defined and accurate collision mesh. This mesh should be a simplified representation of the visual mesh, optimized for physics calculations. Using a convex hull or a set of convex decomposition shapes is generally preferred over complex concave meshes for performance and stability in physics engines. If the collision mesh is too complex, it can lead to performance bottlenecks; if it is too simple or inaccurate, it can result in objects interpenetrating or unrealistic contact responses. For instance, a box should have a simple box collider, while a more complex object might require multiple convex shapes. The collision mesh **MUST** be watertight and free of self-intersections to prevent physics engine errors.

*   **Pivot Placement**: While the pushed object itself is free-floating and does not have a fixed pivot in the traditional sense, the origin of the object in Blender (its pivot point) **MUST** be set to its geometric center or center of mass. This is crucial because Isaac Sim often uses this origin as the reference point for applying forces, calculating inertia, and setting initial poses. If the pivot is arbitrarily placed (e.g., at a corner or far from the object), applying a force at the object's reported center of mass might result in unexpected rotational behavior or an incorrect application point. This ensures that physical properties are correctly associated with the object's geometry.

*   **Special Geometry Considerations**: 
    *   **Flat Contact Surfaces**: For the pushed object and the surface it slides on, the contact surfaces **MUST** be modeled as flat and smooth as possible. Irregularities, small bumps, or highly detailed textures in the geometry can lead to noisy contact points and unstable sliding behavior in the physics engine. While visual detail can be high, the collision mesh should abstract these details for stability. This is critical for accurate friction modeling.
    *   **Consistent Scale and Units**: All assets **MUST** be modeled in a consistent unit system (e.g., meters) and scale within Blender. Discrepancies in scale between assets or between Blender and Isaac Sim can lead to incorrect physical properties (e.g., mass, inertia) and visual misalignment. Isaac Sim typically operates in meters, so Blender models should reflect this.
    *   **Material Assignment**: Although material properties like friction are often defined in Isaac Sim via `PhysicsMaterialAPI`, it is good practice to assign distinct materials to different parts of the object or surface in Blender. This helps in easily identifying and assigning the correct `PhysicsMaterialAPI` properties in Isaac Sim later. For example, the bottom face of the box and the top face of the table should have clearly identifiable material groups.
    *   **Normals and Winding Order**: All faces in the mesh **MUST** have correctly oriented normals and consistent winding order. Incorrect normals can lead to issues with collision detection, lighting, and rendering within Isaac Sim, potentially causing physics anomalies where surfaces are not detected as solid. This ensures that the physics engine correctly perceives the surface boundaries for collision detection.

## SECTION 7: Validation Protocol

Validating the SLIDING/FRICTION-BASED MOTION behavior is crucial to ensure its fidelity and robustness in Isaac Sim before deployment to a real Franka Panda robot. The validation protocol will leverage Isaac Teleop for interactive testing and systematic evaluation of key performance indicators and failure modes.

### Test Setup

1.  **Environment**: Load the Isaac Sim environment containing the Franka Panda robot, a flat surface (e.g., a table), and the target object (e.g., a box, book, or plate) with the properties defined in the valid behavior specification (Section 4). Ensure all physics parameters (friction, mass, damping, solver iterations) are correctly configured.
2.  **Isaac Teleop**: Launch Isaac Teleop and connect it to the simulated Franka Panda. Configure the control interface to allow for precise end-effector force control, enabling the operator to command pushing forces and velocities.
3.  **Logging**: Enable comprehensive logging of robot state (joint positions, velocities, efforts), end-effector pose, applied forces, object pose, object linear and angular velocities, and contact forces between the end-effector and object, and between the object and the surface.

### Specific Tests to be Run

1.  **Static Push Test**: 
    *   **Objective**: Verify that the robot can apply a controlled force to the object without causing unintended motion or instability when the applied force is below the static friction threshold.
    *   **Procedure**: Position the end-effector in contact with the object. Gradually increase the applied force from 0 N up to a value just below the calculated static friction threshold (e.g., 0.8 * static_friction * normal_force). Maintain the force for a set duration (e.g., 2 seconds).
    *   **Success Criteria**: The object remains stationary, and the applied force is stable and matches the commanded force within a small tolerance (e.g., +/-0.5 N). No unexpected robot joint movements or oscillations.
    *   **Failure Modes**: Object slides prematurely, robot oscillates, or commanded force cannot be maintained.

2.  **Dynamic Push Test (Linear)**:
    *   **Objective**: Validate the object's linear sliding motion under a constant pushing force, observing its acceleration, velocity, and deceleration.
    *   **Procedure**: Apply a constant pushing force (e.g., 10 N) to the object, exceeding the static friction threshold. Maintain the force until the object travels a specified distance (e.g., 0.3 meters) or for a set duration (e.g., 5 seconds). Record the object's trajectory and velocity profile.
    *   **Success Criteria**: The object moves smoothly in the intended direction, achieving a stable velocity. The observed acceleration and deceleration profiles match theoretical predictions based on dynamic friction. The object comes to rest within a reasonable distance after the force is removed.
    *   **Failure Modes**: Object tumbles, rotates unexpectedly, deviates significantly from the linear path, exhibits jerky motion, or fails to stop within expected parameters.

3.  **Dynamic Push Test (Rotational Control)**:
    *   **Objective**: Assess the robot's ability to induce controlled rotation in the object by applying an offset force.
    *   **Procedure**: Apply a pushing force with a deliberate offset from the object's center of mass (e.g., 0.02 m offset along the y-axis). Observe the object's combined linear and angular motion.
    *   **Success Criteria**: The object exhibits a predictable combination of linear translation and rotation, consistent with the applied force vector and offset. The rotational speed is stable and controllable.
    *   **Failure Modes**: Object spins uncontrollably, fails to rotate, or exhibits unstable combined motion.

4.  **Obstacle Avoidance/Clearance Test**: 
    *   **Objective**: Verify that the robot can push the object past obstacles while maintaining specified clearance constraints.
    *   **Procedure**: Place small, static obstacles (e.g., small blocks) along the intended pushing path. Command the robot to push the object, requiring it to navigate around the obstacles. Monitor for collisions.
    *   **Success Criteria**: The robot successfully pushes the object past all obstacles without any collisions between the robot, object, or obstacles, maintaining the minimum specified clearance.
    *   **Failure Modes**: Collisions occur, the object gets stuck, or the robot fails to complete the path.

### Success Criteria (General)

*   **Physical Plausibility**: The simulated behavior visually appears realistic, consistent with real-world physics.
*   **Quantitative Accuracy**: Key metrics (object displacement, velocity, applied force, contact force) match expected values within defined tolerances (e.g., +/-5% for displacement, +/-10% for forces).
*   **Stability**: The simulation runs without numerical instability, jittering, or unexpected discontinuities in motion or forces.
*   **Repeatability**: The behavior can be consistently reproduced across multiple simulation runs with the same input parameters.

### Failure Modes

*   **Object Interpenetration**: The object or robot links pass through other objects or the surface, indicating collision detection or resolution issues.
*   **Unstable Dynamics**: Object jittering, excessive bouncing, or uncontrolled spinning, often due to incorrect physics parameters (e.g., friction, restitution, solver iterations) or unstable control.
*   **Loss of Contact**: The end-effector loses contact with the object prematurely or unintentionally, preventing effective pushing.
*   **Deviation from Path**: The object deviates significantly from the commanded trajectory, indicating issues with force application, friction modeling, or control accuracy.
*   **Robot Instability/Collision**: The robot exhibits unstable joint movements, self-collisions, or collisions with the environment, indicating issues with robot control, joint limits, or safety constraints.
*   **Unrealistic Acceleration/Deceleration**: The object accelerates or decelerates too quickly or too slowly, suggesting incorrect mass, damping, or friction parameters.

---

# WIPING/SWEEPING BEHAVIOR SPECIFICATION — Blender Requirements

## SECTION 6: Blender Asset Requirements

For the Wiping/Sweeping behavior to function correctly and realistically within Isaac Sim, several aspects of the 3D assets, particularly the end-effector tool and the target surface, must be meticulously modeled in Blender. These requirements extend beyond visual representation to encompass physical properties crucial for accurate simulation.

### Collision Mesh Requirements

*   **End-Effector Tool (e.g., Sponge):** The collision mesh for the wiping tool must accurately represent its physical contact surface. For a compliant tool like a sponge, a convex decomposition or a simplified mesh that captures the general shape is often sufficient. However, if fine-grained contact interactions are critical (e.g., simulating individual bristles), a more detailed mesh or even multiple collision primitives might be necessary. The collision mesh should be distinct from the visual mesh to optimize physics calculations. It is crucial that the collision mesh is watertight and free of self-intersections to prevent simulation artifacts. **Justification:** An inaccurate collision mesh will lead to unrealistic contact points, incorrect force distribution, and potentially unstable physics simulations. If the collision mesh is too coarse, it might miss contact with surface irregularities; if too complex, it can significantly increase computational load. **What breaks:** The robot might appear to float above the surface, interpenetrate it, or experience sudden, inexplicable forces.

*   **Target Surface (e.g., Table):** The collision mesh for the target surface must be precise, especially in the areas where the wiping action occurs. For flat surfaces, a simple planar mesh is adequate. For surfaces with contours or features, the collision mesh must accurately reflect these geometries. Similar to the end-effector, the collision mesh should be optimized for physics performance. **Justification:** An imprecise surface collision mesh will result in the end-effector losing contact or applying inconsistent force as it traverses the surface. This directly impacts the effectiveness of the wiping behavior. **What breaks:** The wiping action will be uneven, with areas being missed or excessive force applied in others.

### Pivot Placement

*   **End-Effector Tool:** The pivot point (origin) of the end-effector tool in Blender should be placed at a logical point relative to its geometry, typically at its geometric center or the point of attachment to the robot flange. This pivot defines the local coordinate system of the tool. **Justification:** Correct pivot placement is essential for accurate kinematic transformations and for applying forces and torques correctly in Isaac Sim. If the pivot is misplaced, the tool's pose in simulation will be offset, leading to incorrect contact points and trajectories. **What breaks:** The end-effector will not align correctly with the robot's flange, and commanded poses will result in unexpected tool positions.

*   **Robot Base and Joints:** While the Franka Panda model is typically pre-defined, understanding that each joint and link in the robot's kinematic chain has a precisely defined pivot (origin) is important. These pivots determine the axes of rotation for each joint. **Justification:** The accuracy of the robot's kinematics and dynamics in Isaac Sim relies entirely on the correct definition of these pivots. **What breaks:** Inaccurate joint pivots will lead to incorrect forward and inverse kinematics solutions, causing the robot to move unpredictably or fail to reach target poses.

### Special Geometry Considerations

*   **Compliant Tool Deformation:** If the wiping tool is designed to be compliant (e.g., a sponge), its material properties (stiffness, damping) will be defined in Isaac Sim (as mapped in Section 3). However, the visual mesh in Blender should ideally support potential deformation. This might involve a higher polygon count in areas expected to deform or the use of blend shapes if visual deformation is to be explicitly animated. While the physics engine handles the collision mesh deformation based on material properties, the visual representation can enhance realism. **Justification:** A visually rigid tool that is physically compliant can create a disconnect in user perception. Supporting visual deformation enhances the realism of the simulation. **What breaks:** The tool might appear to interpenetrate the surface visually even if the physics is correct, reducing fidelity.

*   **Surface Features:** Any significant features on the target surface (e.g., grooves, raised patterns) that are intended to interact with the wiping tool must be accurately modeled in both the visual and collision meshes. Small details that do not significantly affect contact can be omitted from the collision mesh for performance. **Justification:** These features will influence the path and forces experienced by the end-effector. Accurate modeling ensures realistic interaction. **What breaks:** The robot might snag on unmodeled features or fail to clean recessed areas.

*   **Mass Distribution:** While mass and density are defined in Isaac Sim, the distribution of mass within the end-effector tool can be influenced by its geometry. For complex tools, ensuring that the Blender model's geometry reflects the intended mass distribution can help in setting more accurate inertial properties in Isaac Sim. **Justification:** The center of mass and moments of inertia are derived from the geometry and density. Accurate representation in Blender aids in setting these physical properties correctly. **What breaks:** Incorrect mass distribution can lead to unrealistic dynamic responses, affecting the robot's stability and control during high-speed movements or sudden changes in direction.

## SECTION 7: Validation Protocol

Validating the Wiping/Sweeping behavior in Isaac Sim with the Franka Emika Panda requires a systematic approach to ensure that the simulated robot accurately reflects the desired physical interactions and control performance. Isaac Teleop provides a valuable interface for real-time control and observation, making it suitable for interactive testing and parameter tuning. The validation protocol focuses on verifying contact stability, force control accuracy, trajectory adherence, and overall task effectiveness.

### Test Setup

The validation environment should include a flat, rigid surface with known material properties (friction, restitution) within the Isaac Sim scene. For evaluating sweeping effectiveness, small, lightweight debris (e.g., spheres or cubes) can be optionally introduced onto the surface. The Franka Emika Panda robot, equipped with the compliant end-effector (e.g., a sponge model), must be present, and its force-torque sensor should be correctly configured and accessible for feedback. The robot should operate in an impedance or admittance control mode to facilitate compliant interaction and force regulation, as position control alone is insufficient for this behavior. Isaac Teleop must be configured to provide real-time control over the end-effector's pose (position and orientation) and to display sensor feedback, including force-torque data and joint states.

### Specific Tests

| Test Name | Procedure | Success Criteria | Failure Modes |
| :--- | :--- | :--- | :--- |
| **Contact Establishment Test** | Command the end-effector to approach the surface along its normal vector until a predefined contact force threshold (e.g., 5-10 N) is met. Maintain this force for 2-3 seconds. | The force-torque sensor reading consistently matches the target normal force within +/-1 N. The end-effector should not visibly bounce or interpenetrate the surface. Joint torques must remain within safe limits. | Inconsistent contact force (oscillations, drops), visible bouncing, excessive penetration, or joint torques exceeding limits. This indicates issues with impedance control gains, collision parameters (`contactOffset`, `restOffset`), or material properties. |
| **Linear Wiping Stroke Test** | Once stable contact is established, command the end-effector to execute a straight-line wiping motion across the surface at a constant speed while maintaining the target normal force. Repeat for different speeds and force levels. | The end-effector follows the commanded linear path accurately. The normal contact force remains consistent throughout the stroke. Lateral forces should be present, indicating effective friction, and should be within expected ranges. If debris is present, it should be effectively swept. | Deviation from the linear path, inconsistent normal force (too high/low), excessive slipping (if debris is not moved), or robot getting stuck. This points to issues with control gains, friction coefficients, or kinematic accuracy. |
| **Raster Wiping Pattern Test** | Implement a complete raster pattern (e.g., back-and-forth strokes with overlaps) over a defined area of the surface, maintaining constant contact force and wiping speed. | The entire target area is covered by the wiping path. Contact force and speed are maintained consistently across all strokes. The robot avoids self-collisions and singular configurations. If debris is present, the area should be cleared effectively. | Uncovered areas, inconsistent force/speed, robot entering singular configurations, or collisions. This suggests problems with path planning, IK solver robustness, or overall control stability. |
| **Force Adaptation Test (Surface Irregularity)** | Introduce a minor surface irregularity (e.g., a small bump or depression) into the wiping path. Command the robot to perform a linear wiping stroke over this irregularity while maintaining target normal force. | The robot's end-effector compliantly adapts to the surface change, maintaining the target normal force without significant deviations. The end-effector should conform to the irregularity without losing contact or applying excessive force. | Loss of contact, sudden spikes in force, or inability to conform to the surface. This highlights issues with the compliance and damping parameters of the end-effector tool, or the responsiveness of the impedance control. |

### What Success Looks Like

Successful validation of the Wiping/Sweeping behavior is characterized by several key observations. Firstly, the end-effector must maintain **stable and consistent contact** with the surface, applying the desired normal force within a tight tolerance, without any signs of bouncing, chattering, or excessive penetration. Secondly, the robot should demonstrate **accurate trajectory following**, precisely adhering to the commanded wiping path with smooth and controlled motion. Finally, the behavior should result in **effective wiping/sweeping**, meaning that if debris is present, it is consistently moved or cleared from the surface. If the task is cleaning, the visual representation should reflect a clean surface, indicating the successful removal of simulated contaminants. The robot's joint efforts and velocities should remain within safe operating limits throughout the entire process, and no unexpected collisions or simulation instabilities should occur.

---

# STACKING/PLACEMENT BEHAVIOR — Blender Requirements

## SECTION 6: Blender Asset Requirements

For the STACKING/PLACEMENT behavior to function correctly and realistically within Isaac Sim, the 3D assets modeled in Blender must adhere to specific requirements, particularly concerning collision meshes, pivot placement, and overall geometry. These considerations are crucial for accurate physics simulation and stable robot interaction.

**Collision Mesh Requirements:**

Accurate collision meshes are paramount for realistic physical interactions, especially in stacking scenarios where objects come into close contact and stability is critical. Each object involved in the stacking operation (both the object being manipulated and the surface it's placed upon) must have a well-defined collision mesh. 

*   **Watertight Meshes:** All collision meshes should be **watertight** (i.e., fully enclosed without holes or gaps). Non-watertight meshes can lead to unpredictable physics behavior, such as objects falling through surfaces or incorrect contact point calculations. This is because the physics engine relies on a closed volume to determine collisions and apply forces accurately. If a mesh is not watertight, the simulation may interpret it as an open boundary, leading to penetration or instability.
*   **Convex Decomposition:** For complex geometries, using **convex decomposition** is highly recommended. While a single, concave mesh can be used as a collider, it is computationally more expensive and can sometimes lead to less stable simulations. Decomposing a complex concave mesh into several simpler convex hulls allows the PhysX engine to perform collision detection more efficiently and robustly. For instance, a hollow object like a cup should be represented by multiple convex shapes to accurately capture its internal and external collision boundaries. Failure to use appropriate collision approximations can result in objects passing through each other or exhibiting jittery behavior, breaking the realism of the stacking task.
*   **Level of Detail (LOD):** Consider creating simplified collision meshes (lower polygon count) for performance optimization, especially for objects that are far from the robot or not directly involved in fine manipulation. The visual mesh can retain high detail, but the collision mesh should be optimized for physics calculations. If collision meshes are overly complex, the simulation can become slow and unstable, particularly when many objects are present or when continuous collision detection (CCD) is enabled.

**Pivot Placement:**

The pivot point of an object, often represented by its origin or `xformOp:translate` in USD, is fundamental for stable grasping and accurate placement. 

*   **Center of Mass Alignment:** Ideally, the pivot point of the object being manipulated should coincide with its **center of mass**. When the robot grasps an object, the control algorithms often assume the grasp point is relative to the object's origin. If the pivot is significantly offset from the center of mass, the robot's inverse kinematics (IK) solver may struggle to find a stable grasp, leading to an unbalanced object that topples or rotates unexpectedly upon release. This misalignment can introduce unwanted torques, making precise placement extremely difficult or impossible.
*   **Logical Grasp Points:** For objects with specific features, the pivot can also be aligned with a **logical grasp point** that facilitates stable manipulation. For example, a handle on a mug might be a more appropriate pivot for grasping than the geometric center of the mug itself. However, for stacking, the primary concern is the stability of the object once released, which heavily relies on the center of mass.

**Special Geometry Considerations:**

*   **Scaling:** Ensure that all assets are modeled to their **real-world scale** in Blender. Incorrect scaling can lead to discrepancies between the visual representation and the physics properties (e.g., mass, inertia), resulting in unrealistic behavior. Isaac Sim operates in meters, so Blender units should be configured accordingly. If an object is modeled at 10x its actual size, its perceived mass and inertia in the simulation will be disproportionately large, making it impossible for the robot to manipulate it correctly.
*   **Thin Features:** For objects with **thin features** (e.g., paper, thin plates), special attention is required for collision detection. Very thin colliders can sometimes be missed by the physics engine during fast movements, leading to penetration. In such cases, increasing the collision margin or using a slightly thicker collision mesh than the visual mesh might be necessary to ensure robust contact. If thin features are not handled correctly, objects might pass through each other, invalidating the stacking operation.
*   **Static vs. Dynamic Objects:** Clearly distinguish between static and dynamic objects in Blender. Static objects (e.g., the table, the base object for stacking) should have their rigid body properties set to fixed or static in Isaac Sim to prevent them from moving. Dynamic objects (e.g., the object being stacked) require full rigid body simulation. This distinction is crucial for computational efficiency and physical accuracy. Treating a static object as dynamic will introduce unnecessary computational overhead and potential instability, while treating a dynamic object as static will prevent it from interacting physically with the environment.

## SECTION 7: Validation Protocol

Validating the STACKING/PLACEMENT behavior in Isaac Sim with the Franka Emika Panda robot is crucial to ensure that the simulated environment accurately reflects real-world physics and robot capabilities. This protocol outlines a series of tests using Isaac Teleop, defining success criteria and identifying potential failure modes.

**Validation Methodology:**

Isaac Teleop provides a direct interface to control the Franka Panda in Isaac Sim, allowing for real-time manipulation and observation of the robot's interaction with objects. This hands-on approach is essential for verifying the fidelity of the physics simulation and the effectiveness of the defined behavior parameters. The validation process will involve manually guiding the robot through the stacking task and observing the outcomes against predefined criteria.

**Specific Tests:**

| Test Case | Description | Expected Outcome (Success) | Failure Modes |
| :--- | :--- | :--- | :--- |
| **Single Object Stacking (Cube on Cube)** | The robot picks up a small cube and places it stably on a larger cube. | The small cube is released and settles without falling or sliding off the larger cube. The final position is within a defined tolerance (e.g., +/-2mm from the center). | Object falls off, slides excessively, or bounces upon release. Robot fails to grasp or approach the target. |
| **Single Object Stacking (Cylinder on Cylinder)** | The robot picks up a cylinder and places it stably on another cylinder. This tests stability with curved surfaces. | The cylinder is released and settles stably on the base cylinder, maintaining its upright orientation. | Object rolls off, topples, or exhibits unstable oscillations after placement. |
| **Stacked Object Stability (Multiple Objects)** | After successfully stacking one object, the robot attempts to stack a second object on top of the first. This tests cumulative stability. | Each subsequent object is placed stably, and the entire stack remains upright and balanced. | The stack collapses during or after the placement of a new object. The robot disturbs the existing stack. |
| **Payload Limit Test** | The robot attempts to stack an object at or near its maximum payload capacity (e.g., 2.9 kg). | The robot successfully lifts and places the heavy object, albeit with potentially slower movements due to inertia. The object remains stable. | Robot fails to lift the object, struggles with excessive joint torques, or drops the object due to insufficient grip force. |
| **Friction Variation Test** | The robot stacks an object on surfaces with varying friction coefficients (e.g., low friction, high friction). | On high-friction surfaces, the object settles quickly. On low-friction surfaces, the object may slide slightly but eventually stabilizes if the placement is precise. | On low-friction surfaces, the object slides off uncontrollably. On high-friction surfaces, the object sticks unnaturally. |
| **Off-Center Placement Test** | The robot intentionally places an object slightly off-center on the target surface. | The object either slides to a more stable position or topples, depending on the degree of off-center placement and friction. This validates realistic instability. | The object remains perfectly stable despite significant off-center placement, indicating unrealistic physics. |

**Success Criteria:**

1.  **Stable Placement:** The manipulated object must come to rest stably on the target surface or object without falling, sliding excessively, or exhibiting prolonged oscillations after release. The object should remain within a predefined positional and orientational tolerance (e.g., +/-2mm position, +/-2 degrees orientation) relative to the intended placement. 
2.  **Robot Capability Adherence:** The robot must operate within its physical limits (payload, joint torques, gripper force) throughout the task. No excessive joint torques or unexpected robot movements should occur. 
3.  **Realistic Interaction:** All physical interactions (grasping, contact, release) must appear visually and physically plausible, consistent with real-world expectations for the given material properties and forces. 

**Failure Modes:**

1.  **Object Instability:** The most common failure mode is the object falling, sliding, or toppling after release. This indicates issues with friction, restitution, center of mass, or imprecise placement. 
2.  **Robot Incapacity:** The robot may fail to lift the object (exceeding payload), drop it during transport (insufficient grip force), or exhibit jerky/unstable movements (incorrect joint control or torque limits). 
3.  **Collision/Penetration:** Unintended collisions or penetration between objects or the robot and the environment indicate problems with collision meshes, continuous collision detection (CCD) settings, or incorrect path planning. 
4.  **Unrealistic Physics:** The object might bounce excessively (high restitution), stick unnaturally (high friction), or defy gravity, suggesting incorrect material properties or physics scene configurations. 
5.  **Grasping Failure:** The robot may fail to establish a stable grasp on the object, leading to drops or an inability to lift. This could be due to incorrect gripper parameters, object geometry, or grasp pose definition. 

---

# TWISTING/TORQUE-BASED ROTATION — Blender Requirements

## SECTION 6: Blender Asset Requirements

To ensure this behavior works correctly in Isaac Sim, the asset must be prepared in Blender with the following strict requirements:

1. **Hierarchical Separation:** The rotating part (e.g., the lid) MUST be a separate mesh object from the static base (e.g., the jar). They cannot be a single combined mesh.
2. **Pivot Point (Origin) Placement:** The origin of the rotating object MUST be placed exactly at the geometric center of its intended axis of rotation. In Blender, select the object, snap the 3D cursor to the center of the cylindrical geometry, and use `Object > Set Origin > Origin to 3D Cursor`. If the origin is off-center, the `UsdPhysics.RevoluteJoint` will cause eccentric rotation in Isaac Sim.
3. **Axis Alignment:** Align the local Z-axis of the rotating object with the axis of rotation. This simplifies the USD setup, allowing you to simply specify "Z" as the rotation axis without complex quaternion offsets.
4. **Collision Meshes:** Use simple, convex collision meshes. For a cylindrical lid, a cylinder primitive is ideal. Avoid complex concave colliders (like the internal threads), as they are computationally expensive and prone to physics glitches. The threads should be simulated via the `UsdPhysics.DriveAPI` damping, not actual geometry.
5. **Scale:** Apply all transforms (`Ctrl+A > All Transforms`) so the scale is exactly (1.0, 1.0, 1.0). Unapplied scales will cause unpredictable physics behavior and incorrect torque calculations in Isaac Sim.

## SECTION 7: Validation Protocol

Validation of this behavior should be conducted using Isaac Teleop with the Franka Panda, employing a human-in-the-loop approach to gather realistic grasp and torque data.

**Test Setup:**
1. Spawn the Franka Panda and the target asset (e.g., a jar with a lid) in Isaac Sim.
2. Configure the asset with the specified `UsdPhysics.RevoluteJoint` and `DriveAPI` parameters.
3. Connect a VR controller or a 6-DOF space mouse via Isaac Teleop to control the Franka's end-effector.

**Specific Tests to Run:**
1. **Grasp Stability Test:** Approach the object, close the gripper with a specified force (e.g., 40N), and attempt to rotate the wrist.
2. **Torque Limit Test:** Gradually increase the `damping` on the object's joint until the robot can no longer turn it, verifying that the failure occurs near the Franka's 12 Nm wrist limit.
3. **Eccentricity Test:** Verify that the object rotates smoothly around its center without lateral wobbling.

**Success Criteria:**
- The gripper maintains a stable hold on the object without slipping during rotation.
- The object rotates smoothly around its intended axis.
- The joint limits (if applicable) are respected, and the robot stops rotating when the limit is reached.

---

# COMPLIANT/FORCE-CONTROLLED MOTION — Blender Requirements

## SECTION 6: Blender Asset Requirements

To ensure the compliant and force-controlled motion behavior functions correctly in Isaac Sim, the target objects, such as the table or workpiece, and the robot's end-effector tool must be modeled in Blender with specific requirements. The collision meshes for the interaction surfaces must be highly accurate and preferably convex decompositions. You must avoid using low-poly proxy meshes for curved surfaces, like a car door being polished. This is required because smooth continuous normals are necessary for stable force feedback; if you get this wrong, faceted collisions will cause the contact normal to jump abruptly, making the robot stutter and bounce as it slides across polygon edges. The origin or pivot placement of the target object should be placed at a logical reference point, such as the center of the interaction surface or the base of the object. This is required because it simplifies the definition of the task frame for the impedance controller; if you place the origin far outside the object, calculating the surface normal and relative position becomes prone to floating-point errors and complex transformations. Furthermore, all assets must be modeled in meters with a scale of 1.0 to match Isaac Sim's default unit system. This is required because physics parameters like mass, inertia, and stiffness are scale-dependent; if you import assets in centimeters without scaling, a 10 N force might be interpreted as 1000 N, launching the object across the room. Finally, separate material slots should be assigned to the interaction surfaces. This is required because it allows specific physics materials, such as friction and restitution, to be bound only to the areas where the robot makes contact; if the whole object shares one material, adjusting friction for the scrubbing surface might inadvertently make the object slide off its supports.

## SECTION 7: Validation Protocol

To validate the compliant and force-controlled motion behavior using Isaac Teleop with the Franka Panda, a structured protocol must be executed. First, load the Franka Panda and a rigid table asset into the Isaac Sim environment, attach a rigid probe or polishing tool to the Franka Hand, and implement a Cartesian impedance controller that maps teleoperation inputs to the X-Y planar position while autonomously regulating a 15 N downward force along the Z-axis. The first test is the approach phase, where you command the robot to move downwards towards the table. Success in this phase looks like the robot stopping smoothly upon detecting a contact force greater than 2 N without penetrating the table deeply or bouncing. The second test is force regulation, where you command the robot to hold its position. Success is achieved when the measured contact force stabilizes at 15 N within a 1 N margin over 0.5 seconds. A failure mode here is the robot oscillating or chattering, or the force diverging, which indicates incorrect damping or stiffness tuning. The third test is sliding or scrubbing, where you use the teleop device to move the end-effector in a figure-eight pattern across the table surface. Success looks like the robot tracking the X-Y trajectory smoothly while maintaining the 15 N Z-axis force, with the visualizer showing continuous contact. A failure mode occurs if the robot gets stuck due to excessive friction, or if the Z-axis force drops to zero, indicating a loss of contact when moving quickly. The final test is disturbance rejection, where you dynamically spawn a small bump, such as a 1 cm thick box, in the robot's path while it is sliding. Success looks like the robot's end-effector complying, riding up and over the bump while maintaining the 15 N force, without exceeding joint torque limits. A failure mode is the robot crashing into the bump and triggering a protective stop due to a massive torque spike, which indicates insufficient compliance.

---

# IMPACT/STRIKING BEHAVIOR — Blender Requirements

## SECTION 6: Blender Asset Requirements

Accurate 3D models are fundamental for realistic simulation of the IMPACT/STRIKING BEHAVIOR in Isaac Sim. The following requirements specify what must be meticulously modeled in Blender to ensure correct physics interactions, visual fidelity, and functional integrity.

1.  **Collision Mesh Requirements:**
    *   **Accurate Representation:** The collision meshes for both the Franka Panda's end-effector (specifically the gripper fingers) and the target object (e.g., nail, bell) must be highly accurate and closely match their visual meshes. This is crucial because the collision mesh defines the physical boundaries for contact detection and force application. If the collision mesh is too coarse or deviates significantly from the visual mesh, impacts will occur at incorrect locations or with incorrect contact normals, leading to unrealistic force transfer and visual discrepancies. For instance, if the end-effector's collision mesh is too large, it might register a hit before visual contact, or if too small, it might interpenetrate the target object.
    *   **Convex Decomposition:** For complex geometries, collision meshes should be decomposed into multiple convex hulls. PhysX, the physics engine in Isaac Sim, performs optimally with convex shapes. Using a single concave mesh for collision can lead to unstable or inaccurate collision detection, especially during high-speed impacts where precise contact points are vital. Without proper convex decomposition, the simulation might exhibit unpredictable bouncing or penetration. Tools like Blender's built-in convex hull generation or external add-ons can assist in this process.
    *   **Watertight Meshes:** All collision meshes must be watertight (closed volumes) to ensure consistent and reliable collision detection. Open meshes can lead to ambiguous contact points and unreliable physics calculations, especially during high-speed interactions. This is particularly important for the end-effector and the target object, as their precise interaction dictates the success of the impact behavior.
    *   **Simplified Geometry for Performance:** While accuracy is important, collision meshes should be as simple as possible while maintaining fidelity. Excessive polygon counts in collision meshes can significantly impact simulation performance, especially when multiple objects are involved or during complex contact scenarios. A balance must be struck between accuracy and computational efficiency; often, a lower-polygon collision mesh that captures the essential shape is sufficient.

2.  **Pivot Placement:**
    *   **Origin at Center of Mass:** For all rigid bodies (robot links, end-effector, target object), the origin (pivot point) in Blender should ideally be placed at the object's center of mass. This ensures that rotational dynamics are correctly calculated in Isaac Sim. If the pivot is offset from the center of mass, applying forces will result in incorrect torques, leading to unrealistic rotational behavior during and after impact. This is particularly critical for objects that are expected to rotate or tumble after being struck.
    *   **Joint Origins for Robot:** For the Franka Panda, the joint origins in Blender must precisely align with the actual rotational axes of the physical robot's joints. This ensures that the kinematic and dynamic models in Isaac Sim accurately reflect the real robot's movements. Incorrect joint origins will lead to discrepancies between commanded and actual robot poses, making precise impact control impossible and potentially causing instability.

3.  **Special Geometry Considerations:**
    *   **End-Effector Contact Surface:** The specific surface of the end-effector intended for impact (e.g., the face of a hammer, the tip of a gripper finger) should be clearly defined and have a well-modeled collision geometry. This ensures that the impact force is applied precisely where intended. Any irregularities or poorly defined surfaces can lead to glancing blows or inaccurate force distribution.
    *   **Target Object Stability:** For objects that are meant to be struck, ensure their base or mounting points are modeled to allow for stable placement before impact, but also permit realistic movement or deformation upon impact. For example, a nail should have a sharp tip to penetrate, and a bell should have a stable base but be free to resonate. If the target object is not stable, it might move prematurely, making the impact unpredictable. If it's overly constrained, it might not react realistically to the impact force.
    *   **Material Assignment:** While material properties are primarily defined in Isaac Sim, it's good practice to assign distinct materials in Blender to different parts of the model (e.g., metal for the hammerhead, wood for the handle). This aids in organizing the model and can simplify the process of assigning PhysX materials in Isaac Sim, ensuring that the correct physical properties are applied to the correct surfaces.

## SECTION 7: Validation Protocol

Validating the IMPACT/STRIKING BEHAVIOR is crucial to ensure that the simulation accurately reflects real-world physics and robot capabilities. This protocol outlines specific tests using Isaac Teleop with the Franka Panda, defining success criteria, and identifying potential failure modes.

### Test Setup

1.  **Robot Configuration:** Load the Franka Emika Panda robot model with the Franka Hand gripper into Isaac Sim. Ensure all joints are correctly configured and the robot is in a known home position.
2.  **Target Object Placement:** Place the target object (e.g., a nail, a bell) at a precise, repeatable location within the robot's workspace. The object's initial pose should be well-defined and consistent across test runs.
3.  **Environment:** Ensure the simulation environment is free of extraneous objects that could interfere with the impact. Gravity should be enabled, and the ground plane should have appropriate friction and restitution properties.
4.  **Isaac Teleop:** Initialize Isaac Teleop for the Franka Panda. This allows for real-time control and monitoring of the robot's state.

### Test Cases

**Test Case 1: Single Impact Force Verification**

*   **Objective:** Verify that the robot can execute a single, controlled impact with the target object, transferring kinetic energy as expected.
*   **Procedure:**
    1.  Command the Franka Panda to move its end-effector to a pre-impact position, a short distance away from the target object.
    2.  Execute a high-speed linear motion of the end-effector towards the target object, aiming for a direct impact with the designated contact surface.
    3.  Immediately after impact, command the robot to retract its end-effector to a safe, post-impact position.
    4.  Monitor the target object's reaction (e.g., nail penetration, bell ringing, object displacement) and the force/torque feedback from the robot's wrist.
*   **Success Criteria:**
    *   The end-effector makes clear, distinct contact with the target object at the intended location.
    *   The target object exhibits a realistic physical response consistent with the applied force (e.g., nail penetrates wood by a measurable amount, bell produces an audible sound, object moves a predictable distance).
    *   Force/torque sensors on the robot wrist register a sharp, transient force spike at the moment of impact, consistent with the expected kinetic energy transfer.
    *   No excessive bouncing or unstable behavior of the end-effector after impact.
*   **Failure Modes:**
    *   **No Impact Detected:** The end-effector misses the target object, or the contact is too weak to register. This could indicate issues with trajectory planning, robot pose accuracy, or insufficient impact velocity.
    *   **Unrealistic Object Reaction:** The target object does not move, moves too little, or moves excessively/unpredictably. This points to incorrect physics parameters (e.g., mass, friction, restitution of the object or environment), or insufficient impact force.
    *   **Robot Instability:** The robot arm exhibits oscillations, unexpected joint movements, or errors during or after impact. This could be due to unstable control, incorrect joint damping, or issues with the physics solver iterations.
    *   **Interpenetration:** The end-effector or target object interpenetrates, indicating issues with collision mesh accuracy, `maxDepenetrationVelocity`, or general physics engine stability.

**Test Case 2: Repetitive Impact Consistency**

*   **Objective:** Assess the consistency and repeatability of the impact behavior over multiple strikes.
*   **Procedure:**
    1.  Execute Test Case 1 multiple times (e.g., 10-20 repetitions) with the same initial conditions.
    2.  Record quantitative metrics for each impact, such as peak impact force, object displacement, and end-effector retraction time.
*   **Success Criteria:**
    *   The measured metrics (peak force, displacement) should be consistent across repetitions within an acceptable tolerance (e.g., +/-5%).
    *   The robot should return to its pre-impact state reliably after each strike.
*   **Failure Modes:**
    *   **Inconsistent Impacts:** Significant variation in impact force or object reaction across repetitions. This could indicate non-deterministic physics, sensor noise, or subtle inaccuracies in robot control.
    *   **Accumulated Error:** The robot's position or the target object's state drifts over multiple impacts, leading to eventual failure to strike correctly. This might be due to minor errors accumulating in the robot's odometry or object's physics.

**Test Case 3: Impact with Varying Target Properties**

*   **Objective:** Evaluate the robustness of the impact behavior when interacting with objects of different material properties (e.g., density, restitution, friction).
*   **Procedure:**
    1.  Repeat Test Case 1 with different target objects, each having distinct physical properties (e.g., a soft foam block, a hard wooden block, a metallic object).
    2.  Observe and record the qualitative and quantitative differences in impact response.
*   **Success Criteria:**
    *   The robot successfully executes the impact behavior on all tested objects.
    *   The observed physical reactions of the objects (e.g., deformation, bounce, sound) are qualitatively consistent with their material properties.
    *   The force/torque feedback reflects the expected interaction with different materials (e.g., higher peak force for harder objects, longer contact duration for softer objects).
*   **Failure Modes:**
    *   **Inability to Adapt:** The robot fails to perform the impact correctly on certain materials, or the object reactions are unrealistic for their properties. This suggests that the physics parameters for materials are not correctly configured or that the control strategy is not robust enough to handle variations.
    *   **Simulation Breakdowns:** The simulation becomes unstable or crashes when interacting with specific material combinations, indicating fundamental issues with physics engine stability or parameter limits.

---

# PULLING/TENSION-BASED MOTION — Blender Requirements

## SECTION 6: Blender Asset Requirements

For the PULLING/TENSION-BASED MOTION behavior to function correctly and realistically within Isaac Sim, the 3D assets modeled in Blender must adhere to specific requirements, particularly concerning collision meshes, pivot placement, and geometric features. These requirements ensure accurate physics simulation and proper interaction with the Franka Emika Panda robot.

### Collision Mesh Requirements

Each object involved in the pulling interaction—the object being pulled, the environment it's pulled from, and the robot's gripper—must possess a collision mesh that accurately represents its physical boundaries. These meshes should be as simple as possible to minimize computational overhead. While complex visual meshes are suitable for rendering, simplified convex hull or primitive shape collision meshes are preferred for physics calculations. An overly complex collision mesh increases simulation time and can introduce numerical instability. Conversely, an inaccurate collision mesh leads to unrealistic interpenetration or premature contact detection, thereby compromising the physical realism of the pull. For instance, if a drawer's collision mesh is excessively large, it might prematurely collide with the cabinet frame, preventing it from reaching its visual limit. Conversely, if it is too small, it might pass through the frame unrealistically. Furthermore, all collision meshes must be watertight and manifold (i.e., without holes or intersecting faces) to ensure consistent collision detection by the PhysX engine. Non-manifold or open meshes can cause unpredictable behavior in the physics engine, leading to objects passing through each other or generating spurious contact forces, which would render the pulling behavior unreliable and non-deterministic. For articulated objects, such as a drawer within a cabinet, each moving part (e.g., the drawer body, the cabinet frame) should be defined with its own distinct collision primitive. This enables Isaac Sim to correctly identify and simulate collisions between individual components, facilitating realistic drawer movement and preventing the entire assembly from being treated as a single rigid body.

### Pivot Placement

For objects that are part of an articulated system, such as a drawer sliding on rails, the pivot point (origin) of the joint connecting the moving part to its base must be precisely defined in Blender. In the case of a prismatic joint, like that of a drawer, this origin explicitly defines the axis of translation. Incorrect joint origins will result in the object moving along an unintended path or rotating instead of translating, fundamentally breaking the intended pulling behavior. For example, an offset drawer pivot might cause the drawer to wobble or detach when pulled. Additionally, while not a traditional pivot, the intended grasping point on the object—such as a drawer handle or a peg's head—should be clearly identifiable and accessible for the robot's gripper. The robot requires a stable and well-defined point to apply the pulling force; an ambiguous or unstable grasping point will lead to gripper slippage or an inability to initiate the pull.

### Special Geometry Considerations

Objects designed for pulling must incorporate geometry that facilitates a stable grasp by the Franka Hand. This includes features such as handles, knobs, or sufficient surface area to enable friction-based gripping. Without suitable graspable features, the robot may struggle to establish a secure hold, leading to repeated task failures due to slippage. For example, attempting to pull a perfectly smooth sphere would be challenging. Furthermore, the design of the object and its surrounding environment should inherently provide adequate clearance for the robot's gripper and end-effector to approach and engage the object without collision. This is a critical design consideration in Blender, not merely a simulation parameter. If the physical geometry of the scene does not allow the robot to reach and grasp the object without self-collision or collision with the environment, the behavior cannot be executed, irrespective of simulation parameters. For instance, a deeply recessed handle might be unreachable by the Franka Hand.

## SECTION 7: Validation Protocol

Validation of the PULLING/TENSION-BASED MOTION behavior for the Franka Emika Panda in Isaac Sim will involve a series of structured tests using Isaac Teleop. This protocol aims to verify the robot's ability to execute the pulling motion reliably, safely, and in accordance with the defined semantic constraints. Success will be measured by consistent object extraction, adherence to force limits, and absence of unintended collisions or slippage. Failure modes will be identified and analyzed to refine the behavior specification.

### Test Setup

The testing environment will consist of an Isaac Sim simulation featuring a Franka Emika Panda robot, a designated target object (e.g., a drawer, a peg-in-hole assembly, or an electrical plug in a socket), and all relevant surrounding geometry. The target object will be meticulously configured with realistic physics properties, including mass, friction, and damping, as detailed in the Isaac Sim API Mapping section. For control, the Franka Panda will be operated via Isaac Teleop, enabling real-time human intervention and precise manipulation throughout the tests. This human-in-the-loop approach is crucial for qualitative assessment and rapid iteration of the behavior. Furthermore, Isaac Sim's integrated logging capabilities will be utilized to record essential metrics such as joint positions, velocities, applied forces/torques, gripper state, and contact events. This quantitative data is indispensable for comprehensive post-test analysis.

### Specific Tests

#### Grasping Stability Test

**Procedure:** The robot will be positioned to grasp the target object, such as a drawer handle. The grasp will be initiated using Isaac Teleop, followed by the application of a small, controlled pulling force. The grasp position will be varied slightly to assess the robustness of the grip.

**Success Criteria:** The gripper must maintain a secure hold on the object without any slippage. Force sensors on the gripper should register consistent contact forces within the expected operational ranges. Crucially, the object must remain stationary and not exhibit any unintentional movement prior to the commencement of the main pulling action.

**Failure Modes:** Failure in this test is characterized by gripper slippage, where force sensor readings drop and the object remains stationary while the gripper moves. Other failure modes include an unstable grasp, indicated by excessive object wobbling, or a complete inability to achieve a secure grasp due to unsuitable geometry or insufficient gripper force.

#### Directional Pull Test

**Procedure:** Following a stable grasp, a pulling force will be applied precisely along the intended extraction axis. For instance, this could be perpendicular to a drawer face or axial to a peg. The pulling force will be gradually increased while continuously monitoring the object's movement and the robot's overall stability.

**Success Criteria:** The object is expected to move smoothly and linearly along the predetermined path. The robot must maintain its pose and stability throughout the motion, with no binding or jamming occurring. The applied pulling force must consistently remain within the robot's operational capabilities and the object's structural integrity limits.

**Failure Modes:** This test fails if the object binds or jams, meaning movement ceases despite increasing force. Other failure indicators include the object deviating from its intended path, robot instability manifested as excessive joint movement or unexpected vibrations, or damage to the object resulting from excessive force. An inability to overcome the object's resistance also constitutes a failure.

#### Release and Retraction Test

**Procedure:** Upon complete extraction of the object, the robot will release its grasp and retract its arm to a predefined safe home position. The behavior of the object immediately after release will be carefully observed.

**Success Criteria:** The object must detach cleanly from the robot. Its post-release motion should be controlled, such as a drawer stopping at its end-stop or a plug falling gently. The robot's retraction must occur without any collisions with the environment or other objects.

**Failure Modes:** Failure occurs if the object flies off uncontrollably due to insufficient damping, or if it collides with the environment or the robot upon release. Any collision involving the robot during its retraction phase also signifies a failure.

#### Force Threshold Test (Feedback Validation)

**Procedure:** The behavior will be configured to cease pulling when a specific force threshold is met, typically indicating a significant drop in resistance upon extraction. The pull will be executed, and the robot's response to the force feedback will be observed.

**Success Criteria:** The robot must immediately stop pulling once the object is extracted, as evidenced by force sensor readings crossing the defined threshold.

**Failure Modes:** This test fails if the robot continues pulling after extraction, suggesting the threshold is too high or feedback is not being processed correctly. Conversely, premature stopping due to a threshold that is too low or a false positive also indicates a failure.

### Success and Failure Modes

**Success:** A successful validation confirms that the Franka Panda can consistently execute the PULLING/TENSION-BASED MOTION behavior. This includes extracting objects along the intended vector, operating within specified force and range limits, and performing without slippage, collisions, or instability. Quantitative metrics derived from data logs, such as smooth force profiles and consistent trajectory tracking, must align precisely with expected physical behavior.

**Failure:** Failure is indicated by any deviation from the aforementioned success criteria. This encompasses, but is not limited to:

| Failure Type | Description |
| :--- | :--- |
| **Grasp Failure** | Object slips from the gripper, an unstable grasp is achieved, or the robot is unable to grasp the object at all. |
| **Extraction Failure** | The object binds, jams, deviates from its intended path, or cannot be extracted due to insufficient force. |
| **Robot Instability** | The robot exhibits excessive vibrations, unexpected joint movements, or a loss of balance during the operation. |
| **Collisions** | The robot collides with the environment, the target object, or itself. |
| **Uncontrolled Release** | The object flies off uncontrollably or causes secondary collisions upon release. |
| **Exceeding Limits** | The robot or the object experiences forces/torques that surpass safe operating limits. |
| **Feedback Misinterpretation** | The robot fails to react correctly to force/torque feedback, leading to incorrect task execution. |

---

# ROLLING BEHAVIOR — Blender Requirements

## SECTION 6: Blender Asset Requirements

For the ROLLING BEHAVIOR to function correctly and realistically within Isaac Sim, the 3D assets, particularly the rolling object, must be meticulously modeled in Blender with specific considerations:

*   **Collision Mesh Requirements:** The collision mesh for the rolling object must be a simplified, convex representation of its visual mesh. Complex, concave meshes can lead to unstable physics simulations, increased computational cost, and inaccurate contact responses. For a sphere, a simple sphere collider is ideal. For a cylinder, a capsule or cylinder collider is appropriate. The collision mesh should accurately reflect the object's physical boundaries to ensure proper contact detection with the robot's end-effector and the ground plane. If the collision mesh is too coarse, the robot might 'pass through' the object or experience incorrect contact points, leading to failed rolling. Conversely, an overly complex collision mesh can introduce jitter and performance issues.

*   **Pivot Placement:** The origin (pivot point) of the rolling object in Blender should be set at its geometric center. This is crucial because Isaac Sim's physics engine uses this origin as the center of mass by default, especially if no explicit center of mass is defined. For a uniformly dense, symmetrical object like a ball or cylinder, the geometric center coincides with the center of mass. Incorrect pivot placement will result in an inaccurate center of mass, leading to unrealistic rotational dynamics and an inability to maintain the $v = \omega \cdot r$ rolling constraint. The object might wobble, slide, or rotate unexpectedly.

*   **Special Geometry Considerations:**
    *   **Roundness and Smoothness:** The rolling surface of the object must be perfectly round and smooth. Any irregularities, facets, or sharp edges on the rolling surface will cause the object to bounce, snag, or deviate from a smooth rolling path. This is particularly important for objects like bottles, where the main body should be cylindrical. The mesh should have sufficient tessellation to appear smooth, even if the collision mesh is simplified.
    *   **Scale and Units:** Ensure that the object is modeled to real-world scale in Blender, typically using meters as the unit. Isaac Sim interprets units directly, and incorrect scaling will lead to physics simulations that are either too fast/slow or objects that are disproportionately heavy/light, breaking the realism and expected behavior.
    *   **Material Assignment:** While detailed material properties (like friction) are defined in Isaac Sim, assigning basic material slots in Blender can help organize the asset and ensure that different parts of the object can have distinct physical properties if needed (e.g., a bottle with a glass body and a plastic cap).

## SECTION 7: Validation Protocol

Validating the ROLLING BEHAVIOR with the Franka Panda in Isaac Sim using Isaac Teleop involves a series of structured tests to ensure the behavior is robust, repeatable, and adheres to the specified kinematic and physical constraints. Success is defined by consistent, controlled rolling without slipping, while failure modes include slipping, uncontrolled motion, or inability to initiate the roll.

**Specific Tests to be Run:**

1.  **Static Contact Test:**
    *   **Procedure:** Position the Franka Panda's end-effector in contact with the object on a flat surface, applying a small, controlled normal force. Do not initiate rolling. Observe the stability of the contact.
    *   **Success:** The object remains stationary, and the robot maintains stable contact without jitter or unexpected movement. This validates initial contact and friction properties.
    *   **Failure Modes:** Object slides or jitters, indicating insufficient static friction or unstable contact force application.

2.  **Initiation of Roll Test:**
    *   **Procedure:** From a static contact, gradually apply a tangential force to the object while simultaneously initiating a controlled angular velocity. The force application point should be carefully chosen to induce rolling. Increase force and angular velocity until rolling begins.
    *   **Success:** The object smoothly transitions from static to rolling motion, maintaining the $v = \omega \cdot r$ constraint. The robot's end-effector maintains consistent contact and guides the object.
    *   **Failure Modes:** Object slips excessively, fails to roll, or rolls erratically. This could indicate incorrect force application, insufficient friction, or an improperly calculated angular velocity for the given linear velocity.

3.  **Sustained Rolling Test (Straight Line):**
    *   **Procedure:** Once rolling is initiated, maintain a constant linear and angular velocity for the object, guiding it in a straight line across a predefined distance (e.g., 0.5 meters). The robot's end-effector should move along with the object, applying the necessary forces.
    *   **Success:** The object rolls smoothly in a straight line without significant deviation or slipping. The robot's joint torques and forces remain within specified limits.
    *   **Failure Modes:** Object deviates from the path, slips, or stops rolling. This may point to issues with dynamic friction, force control stability, or kinematic tracking errors.

4.  **Direction Change Test:**
    *   **Procedure:** While the object is rolling, introduce a gradual change in the desired rolling direction (e.g., a gentle curve or a 45-degree turn). The robot must adjust its end-effector trajectory and applied forces to guide the object through the turn.
    *   **Success:** The object smoothly changes direction while maintaining the rolling constraint. The robot's movements are fluid and controlled.
    *   **Failure Modes:** Object loses rolling contact, slips during the turn, or tumbles. This indicates challenges in dynamic force control during complex trajectories or issues with the robot's ability to adapt to changing contact points.

5.  **Obstacle Negotiation Test (Small Obstacle):**
    *   **Procedure:** Place a small, low-profile obstacle (e.g., a thin strip) in the rolling path. Guide the object to roll over the obstacle.
    *   **Success:** The object successfully navigates the obstacle, potentially with a slight perturbation, but quickly re-establishes stable rolling.
    *   **Failure Modes:** Object gets stuck, flips over, or loses rolling behavior due to the obstacle. This highlights limitations in the behavior's robustness to environmental variations.

**Success Criteria:**

*   **Kinematic Constraint Adherence:** The ratio of linear velocity to angular velocity ($v/\omega$) should remain approximately equal to the object's radius ($r$) throughout the rolling motion, with a tolerance of +/- 5%.
*   **No Slipping:** Visual inspection and velocity data should confirm minimal to no slipping between the object and the surface. The contact point should continuously change.
*   **Stable Contact:** The robot's end-effector maintains consistent and stable contact with the object, applying forces within its operational limits.
*   **Repeatability:** The behavior can be initiated and executed successfully multiple times under identical conditions.
*   **Smooth Trajectory:** The object follows the intended path smoothly without erratic movements or excessive oscillations.

**Failure Modes:**

*   **Excessive Slipping:** The object slides significantly instead of rolling, indicating insufficient friction or improper force/torque application.
*   **Loss of Contact:** The robot loses contact with the object, causing it to stop or move uncontrollably.
*   **Object Tumble/Flip:** The object loses stability and tumbles or flips over, often due to excessive or improperly directed forces.
*   **Uncontrolled Deviation:** The object deviates significantly from the desired path, suggesting issues with force control or trajectory tracking.
*   **Robot Overload/Joint Limits:** The robot attempts to apply forces or move in ways that exceed its joint torque or velocity limits, leading to errors or unstable behavior.
*   **Jitter/Instability:** The object or robot exhibits high-frequency oscillations, indicating numerical instability in the physics simulation or control loop.
