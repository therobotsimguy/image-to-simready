# Exhaustive Physics & Mathematics Equation Reference for Robotics Simulation

**A Complete Toolkit for 3D Asset Creation, Physics Simulation, and Robot Control**

This comprehensive reference compiles all essential mathematical and physics equations required for robotics simulation environments (NVIDIA Isaac Sim, IsaacLab, Newton physics engine, and similar platforms). It covers forces, constraints, limits, control systems, and advanced dynamics with complete descriptions, mathematical formulas, and production-ready Python implementations.

---

## Table of Contents

1. [Classical Mechanics: Kinematics & Dynamics](#1-classical-mechanics-kinematics--dynamics)
2. [Rigid Body Dynamics & Rotational Mechanics](#2-rigid-body-dynamics--rotational-mechanics)
3. [Friction Models & Contact Forces](#3-friction-models--contact-forces)
4. [Electromechanical Systems (Motors & Actuators)](#4-electromechanical-systems-motors--actuators)
5. [Joint Mechanics, Springs, & Damping](#5-joint-mechanics-springs--damping)
6. [Collisions & Energy](#6-collisions--energy)
7. [Sensors & IMU Physics](#7-sensors--imu-physics)
8. [Drag Forces & Aerodynamics](#8-drag-forces--aerodynamics)
9. [Centripetal & Centrifugal Forces](#9-centripetal--centrifugal-forces)
10. [Robot Kinematics & Jacobian Matrices](#10-robot-kinematics--jacobian-matrices)
11. [Control Systems (PID, Impedance, Force Control)](#11-control-systems-pid-impedance-force-control)
12. [Lagrangian Mechanics & Constraint Forces](#12-lagrangian-mechanics--constraint-forces)
13. [Advanced Friction Models](#13-advanced-friction-models)
14. [Contact Mechanics (Hertzian & Penalty Methods)](#14-contact-mechanics-hertzian--penalty-methods)
15. [Cable Tension & Rope Mechanics](#15-cable-tension--rope-mechanics)
16. [Magnetic Forces](#16-magnetic-forces)
17. [Joint Constraints & Workspace Limits](#17-joint-constraints--workspace-limits)
18. [Energy, Power, & Work](#18-energy-power--work)

---

## 1. Classical Mechanics: Kinematics & Dynamics

### 1.1 Kinematic Equations (Constant Acceleration)
**Description:** Fundamental equations describing motion under constant acceleration. Essential for predicting trajectories of end-effectors, falling objects, and projectiles in simulation.

**Mathematical Equations:**
- $v_f = v_i + at$
- $d = v_i t + \frac{1}{2}at^2$
- $v_f^2 = v_i^2 + 2ad$
- $d = \frac{v_i + v_f}{2}t$

**Python Code:**
```python
def kinematic_equations(v_i, a, t=None, d=None):
    """Calculate kinematic variables under constant acceleration.
    Fixed: guard against negative sqrt, handle t+d ambiguity.
    """
    results = {}
    if t is not None:
        results['v_f'] = v_i + a * t
        results['displacement'] = v_i * t + 0.5 * a * (t**2)
        results['avg_velocity'] = (v_i + results['v_f']) / 2
    if d is not None:
        discriminant = v_i**2 + 2 * a * d
        results['v_f_squared'] = discriminant
        if discriminant >= 0:
            results['v_f_from_d'] = discriminant**0.5
        else:
            results['v_f_from_d'] = None  # physically impossible (decelerated to stop before d)
    return results
```

### 1.2 Newton's Second Law of Motion
**Description:** Fundamental law relating force, mass, and acceleration. Critical for determining required forces and accelerations in robot simulations.

**Mathematical Equation:**
$F = ma$

**Python Code:**
```python
def newtons_second_law(mass, acceleration=None, force=None):
    """Calculate force or acceleration using Newton's Second Law.
    Fixed: guard against division by zero when mass=0.
    """
    if acceleration is not None:
        return mass * acceleration
    elif force is not None:
        if mass == 0:
            return float('inf') if force != 0 else 0
        return force / mass
    return None
```

### 1.3 Weight (Gravitational Force)
**Description:** The force exerted on an object due to gravity. Essential for all simulations involving falling objects, hanging loads, or gravitational effects.

**Mathematical Equation:**
$W = mg$

*(Where $W$ = weight, $m$ = mass, $g$ = gravitational acceleration ≈ 9.81 m/s²)*

**Python Code:**
```python
def weight_force(mass, gravity=9.81):
    """Calculate the weight of an object."""
    return mass * gravity
```

### 1.4 Momentum and Impulse
**Description:** Momentum is the product of mass and velocity. Impulse is the change in momentum caused by a force over time. Important for collision simulations and impact analysis.

**Mathematical Equations:**
- **Momentum:** $p = mv$
- **Impulse:** $J = F \Delta t = \Delta p$

**Python Code:**
```python
def momentum_and_impulse(mass, velocity=None, force=None, time=None):
    """Calculate momentum or impulse."""
    results = {}
    if velocity is not None:
        results['momentum'] = mass * velocity
    if force is not None and time is not None:
        results['impulse'] = force * time
        results['velocity_change'] = (force * time) / mass
    return results
```

---

## 2. Rigid Body Dynamics & Rotational Mechanics

### 2.1 Torque and Angular Acceleration
**Description:** The rotational equivalent of Newton's Second Law. Defines how torque applied to a body with moment of inertia causes angular acceleration. Essential for joint motors and rotating components.

**Mathematical Equation:**
$\tau = I \alpha$

*(Where $\tau$ = torque, $I$ = moment of inertia, $\alpha$ = angular acceleration)*

**Python Code:**
```python
def rotational_dynamics(moment_of_inertia, angular_acceleration=None, torque=None):
    """Calculate torque or angular acceleration."""
    if angular_acceleration is not None:
        return moment_of_inertia * angular_acceleration
    elif torque is not None:
        return torque / moment_of_inertia
    return None
```

### 2.2 Moment of Inertia (Common Shapes)
**Description:** Resistance to rotational acceleration. Different shapes have different inertia tensors. Critical for accurate rotational dynamics in simulation.

**Mathematical Equations:**
- **Solid Sphere:** $I = \frac{2}{5}mr^2$
- **Solid Cylinder:** $I = \frac{1}{2}mr^2$
- **Hollow Sphere:** $I = \frac{2}{3}mr^2$
- **Rectangular Block (about center):** $I = \frac{1}{12}m(a^2 + b^2)$
- **Point Mass at distance r:** $I = mr^2$

**Python Code:**
```python
import math

def moment_of_inertia(shape, mass, *dimensions):
    """Calculate moment of inertia for common shapes.
    Fixed: validate dimensions length before unpacking.
    """
    if not dimensions or mass <= 0:
        return None
    if shape == "sphere":
        r = dimensions[0]
        return (2/5) * mass * r**2
    elif shape == "cylinder":
        r = dimensions[0]
        return 0.5 * mass * r**2
    elif shape == "hollow_sphere":
        r = dimensions[0]
        return (2/3) * mass * r**2
    elif shape == "rectangular_block":
        if len(dimensions) < 2:
            return None  # need width and height
        a, b = dimensions[0], dimensions[1]
        return (1/12) * mass * (a**2 + b**2)
    elif shape == "thin_rod":
        L = dimensions[0]
        return (1/3) * mass * L**2  # hinged at end (door)
    elif shape == "point_mass":
        r = dimensions[0]
        return mass * r**2
    return None
```

### 2.3 Angular Momentum
**Description:** Rotational momentum of a body. Conserved in closed systems. Important for gyroscopic effects and stability analysis.

**Mathematical Equation:**
$L = I \omega$

*(Where $L$ = angular momentum, $I$ = moment of inertia, $\omega$ = angular velocity)*

**Python Code:**
```python
def angular_momentum(moment_of_inertia, angular_velocity):
    """Calculate angular momentum."""
    return moment_of_inertia * angular_velocity

def angular_velocity_from_momentum(angular_momentum, moment_of_inertia):
    """Calculate angular velocity from angular momentum."""
    return angular_momentum / moment_of_inertia
```

### 2.4 Rotational Kinetic Energy
**Description:** Energy associated with rotation. Used in energy conservation calculations and power analysis.

**Mathematical Equation:**
$KE_{rot} = \frac{1}{2}I\omega^2$

**Python Code:**
```python
def rotational_kinetic_energy(moment_of_inertia, angular_velocity):
    """Calculate rotational kinetic energy."""
    return 0.5 * moment_of_inertia * (angular_velocity**2)
```

---

## 3. Friction Models & Contact Forces

### 3.1 Static and Kinetic Friction
**Description:** Friction opposes relative motion. Static friction prevents motion until overcome; kinetic friction acts during motion. Critical for grasping, locomotion, and sliding simulations.

**Mathematical Equations:**
- **Maximum Static Friction:** $f_{s(max)} = \mu_s N$
- **Kinetic Friction:** $f_k = \mu_k N$

*(Where $\mu_s$ = coefficient of static friction, $\mu_k$ = coefficient of kinetic friction, $N$ = normal force)*

**Python Code:**
```python
def friction_force(normal_force, mu_s, mu_k, applied_force, is_moving=False):
    """Calculate friction force on an object."""
    max_static_friction = mu_s * normal_force
    kinetic_friction = mu_k * normal_force
    
    if is_moving:
        return kinetic_friction
    else:
        if applied_force <= max_static_friction:
            return applied_force  # Static friction matches applied force
        else:
            return kinetic_friction  # Object starts moving
```

### 3.2 Friction Direction
**Description:** Friction always opposes the direction of motion or potential motion.

**Mathematical Equation:**
$\vec{f} = -\mu N \hat{v}$

*(Where $\hat{v}$ = unit vector in direction of motion)*

**Python Code:**
```python
import numpy as np

def friction_force_vector(normal_force, mu, velocity_vector):
    """Calculate friction force as a vector."""
    v_magnitude = np.linalg.norm(velocity_vector)
    if v_magnitude < 1e-10:  # No motion
        return np.array([0, 0, 0])
    v_unit = velocity_vector / v_magnitude
    friction_magnitude = mu * normal_force
    return -friction_magnitude * v_unit
```

---

## 4. Electromechanical Systems (Motors & Actuators)

### 4.1 DC Motor Voltage and Back EMF
**Description:** Models electrical behavior of DC motors. Back EMF opposes applied voltage and increases with motor speed. Essential for accurate actuator simulation.

**Mathematical Equations:**
- **Voltage Equation:** $V = E + I_a R_a$
- **Back EMF:** $E = k_e \omega$

*(Where $V$ = terminal voltage, $E$ = back EMF, $I_a$ = armature current, $R_a$ = armature resistance, $k_e$ = back EMF constant, $\omega$ = angular velocity)*

**Python Code:**
```python
def dc_motor_electrical(voltage, resistance, ke_constant, angular_velocity):
    """Calculate DC motor electrical parameters."""
    back_emf = ke_constant * angular_velocity
    armature_current = (voltage - back_emf) / resistance if resistance != 0 else 0
    return {
        "back_emf": back_emf,
        "current": armature_current,
        "power_input": voltage * armature_current,
        "power_loss": armature_current**2 * resistance
    }
```

### 4.2 DC Motor Torque
**Description:** Mechanical torque generated by motor is proportional to armature current.

**Mathematical Equation:**
$\tau = k_t I_a$

*(Where $\tau$ = torque, $k_t$ = torque constant, $I_a$ = armature current)*

**Python Code:**
```python
def dc_motor_torque(kt_constant, armature_current):
    """Calculate DC motor torque."""
    return kt_constant * armature_current
```

### 4.3 Motor Power and Efficiency
**Description:** Relates electrical input power to mechanical output power and losses.

**Mathematical Equations:**
- **Input Power:** $P_{in} = VI$
- **Mechanical Power:** $P_{mech} = \tau \omega$
- **Power Loss:** $P_{loss} = I^2 R$
- **Efficiency:** $\eta = \frac{P_{mech}}{P_{in}} = \frac{\tau \omega}{VI}$

**Python Code:**
```python
def motor_power_efficiency(voltage, current, torque, angular_velocity, resistance):
    """Calculate motor power and efficiency."""
    input_power = voltage * current
    mechanical_power = torque * angular_velocity
    power_loss = current**2 * resistance
    efficiency = mechanical_power / input_power if input_power > 0 else 0
    return {
        "input_power": input_power,
        "mechanical_power": mechanical_power,
        "power_loss": power_loss,
        "efficiency": efficiency
    }
```

---

## 5. Joint Mechanics, Springs, & Damping

### 5.1 Hooke's Law (Spring Force)
**Description:** Restoring force of a spring proportional to displacement. Used for compliant joints, soft robotics, and suspension systems.

**Mathematical Equation:**
$F_s = -kx$

*(Where $F_s$ = spring force, $k$ = spring constant, $x$ = displacement from equilibrium)*

**Python Code:**
```python
def spring_force(spring_constant, displacement):
    """Calculate spring restoring force."""
    return -spring_constant * displacement

def spring_potential_energy(spring_constant, displacement):
    """Calculate elastic potential energy stored in spring."""
    return 0.5 * spring_constant * (displacement**2)
```

### 5.2 Damped Harmonic Oscillator
**Description:** Models spring-mass system with energy dissipation. Ensures joints reach stable state without infinite oscillation.

**Mathematical Equation:**
$m \frac{d^2x}{dt^2} + c \frac{dx}{dt} + kx = F_{ext}$

*(Where $m$ = mass, $c$ = damping coefficient, $k$ = spring constant, $x$ = position, $F_{ext}$ = external force)*

**Python Code:**
```python
def damped_oscillator(mass, damping_coeff, spring_constant, position, velocity, external_force=0):
    """Calculate forces and acceleration in damped oscillator."""
    spring_force = -spring_constant * position
    damping_force = -damping_coeff * velocity
    net_force = spring_force + damping_force + external_force
    acceleration = net_force / mass if mass > 0 else 0
    return {
        "spring_force": spring_force,
        "damping_force": damping_force,
        "net_force": net_force,
        "acceleration": acceleration
    }
```

### 5.3 Damping Ratio and Natural Frequency
**Description:** Characterizes oscillatory behavior of damped systems. Critical for tuning joint controllers.

**Mathematical Equations:**
- **Natural Frequency:** $\omega_n = \sqrt{\frac{k}{m}}$
- **Damping Ratio:** $\zeta = \frac{c}{2\sqrt{km}}$
- **Damped Frequency:** $\omega_d = \omega_n\sqrt{1-\zeta^2}$ (for $\zeta < 1$)

**Python Code:**
```python
import math

def oscillator_characteristics(mass, spring_constant, damping_coeff):
    """Calculate natural frequency and damping ratio."""
    omega_n = math.sqrt(spring_constant / mass) if mass > 0 else 0
    zeta = damping_coeff / (2 * math.sqrt(spring_constant * mass))
    
    if zeta < 1:
        omega_d = omega_n * math.sqrt(1 - zeta**2)
        regime = "underdamped"
    elif zeta == 1:
        omega_d = 0
        regime = "critically_damped"
    else:
        omega_d = 0
        regime = "overdamped"
    
    return {
        "natural_frequency": omega_n,
        "damping_ratio": zeta,
        "damped_frequency": omega_d,
        "regime": regime
    }
```

---

## 6. Collisions & Energy

### 6.1 Coefficient of Restitution (Elasticity)
**Description:** Ratio of relative speeds after and before collision. Defines bounciness (1 = perfectly elastic, 0 = perfectly inelastic).

**Mathematical Equation:**
$e = \frac{v_{2f} - v_{1f}}{v_{1i} - v_{2i}}$

*(Where $e$ = coefficient of restitution, $v_{1i}, v_{2i}$ = initial velocities, $v_{1f}, v_{2f}$ = final velocities)*

**Python Code:**
```python
def collision_final_velocities(m1, m2, v1_i, v2_i, e):
    """Calculate final velocities after 1D collision using coefficient of restitution."""
    denominator = m1 + m2
    if denominator == 0:
        return v1_i, v2_i
    
    v1_f = ((m1 - e*m2)*v1_i + m2*(1 + e)*v2_i) / denominator
    v2_f = ((m2 - e*m1)*v2_i + m1*(1 + e)*v1_i) / denominator
    return v1_f, v2_f

def coefficient_of_restitution(v1_i, v2_i, v1_f, v2_f):
    """Calculate coefficient of restitution from velocities."""
    denominator = v1_i - v2_i
    if abs(denominator) < 1e-10:
        return 0
    return (v2_f - v1_f) / denominator
```

### 6.2 Conservation of Momentum
**Description:** In closed systems, total momentum is conserved during collisions.

**Mathematical Equation:**
$m_1 v_{1i} + m_2 v_{2i} = m_1 v_{1f} + m_2 v_{2f}$

**Python Code:**
```python
def momentum_conservation(m1, v1_i, m2, v2_i, v1_f):
    """Calculate final velocity of second object using momentum conservation.
    Fixed: guard against m2=0 (massless object can't conserve momentum).
    """
    total_initial_momentum = m1 * v1_i + m2 * v2_i
    if m2 == 0:
        return float('inf') if total_initial_momentum != m1 * v1_f else 0
    v2_f = (total_initial_momentum - m1 * v1_f) / m2
    return v2_f
```

---

## 7. Sensors & IMU Physics

### 7.1 Accelerometer Equation
**Description:** Accelerometers measure specific force (proper acceleration), which includes kinematic acceleration minus gravity. Essential for state estimation.

**Mathematical Equation:**
$a_{meas} = a_{true} - g$

*(Where $a_{meas}$ = measured acceleration, $a_{true}$ = true kinematic acceleration, $g$ = gravity vector)*

**Python Code:**
```python
import numpy as np

def simulate_accelerometer(true_acceleration, gravity_vector=np.array([0, 0, -9.81]), noise_std=0.01):
    """Simulate accelerometer reading with noise."""
    measured_accel = true_acceleration - gravity_vector
    noise = np.random.normal(0, noise_std, 3)
    return measured_accel + noise
```

### 7.2 Gyroscope (Angular Velocity Measurement)
**Description:** Gyroscopes measure angular velocity directly. Integration gives orientation.

**Mathematical Equation:**
$\omega_{meas} = \omega_{true} + \text{bias} + \text{noise}$

**Python Code:**
```python
import numpy as np

def simulate_gyroscope(true_angular_velocity, bias=np.array([0, 0, 0]), noise_std=0.01):
    """Simulate gyroscope reading with bias and noise."""
    noise = np.random.normal(0, noise_std, 3)
    return true_angular_velocity + bias + noise

def integrate_angular_velocity(angular_velocity, dt, previous_orientation=np.array([0, 0, 0])):
    """Integrate angular velocity to get orientation (Euler angles approximation)."""
    return previous_orientation + angular_velocity * dt
```

### 7.3 IMU Orientation Estimation
**Description:** Combines accelerometer and gyroscope data to estimate orientation.

**Mathematical Equation:**
$\theta = \arctan2(a_y, a_z)$ (roll from accelerometer)
$\phi = \arcsin(-a_x / g)$ (pitch from accelerometer)

**Python Code:**
```python
import numpy as np
import math

def estimate_orientation_from_accel(accel_vector, gravity=9.81):
    """Estimate roll and pitch from accelerometer data."""
    ax, ay, az = accel_vector
    
    # Roll (rotation around x-axis)
    roll = math.atan2(ay, az)
    
    # Pitch (rotation around y-axis)
    pitch = math.asin(-ax / gravity) if abs(ax) <= gravity else 0
    
    return roll, pitch
```

---

## 8. Drag Forces & Aerodynamics

### 8.1 Drag Force (Quadratic Drag)
**Description:** Air resistance proportional to velocity squared. Important for high-speed simulations and aerial robots.

**Mathematical Equation:**
$F_D = \frac{1}{2} \rho C_D A v^2$

*(Where $\rho$ = fluid density, $C_D$ = drag coefficient, $A$ = reference area, $v$ = velocity)*

**Python Code:**
```python
def drag_force(fluid_density, drag_coefficient, reference_area, velocity):
    """Calculate quadratic drag force."""
    return 0.5 * fluid_density * drag_coefficient * reference_area * (velocity**2)

def drag_force_vector(fluid_density, drag_coefficient, reference_area, velocity_vector):
    """Calculate drag force as a vector (opposes motion)."""
    import numpy as np
    v_magnitude = np.linalg.norm(velocity_vector)
    if v_magnitude < 1e-10:
        return np.array([0, 0, 0])
    
    v_unit = velocity_vector / v_magnitude
    drag_magnitude = 0.5 * fluid_density * drag_coefficient * reference_area * (v_magnitude**2)
    return -drag_magnitude * v_unit
```

### 8.2 Linear Drag (Low Reynolds Number)
**Description:** For low-speed flow, drag is proportional to velocity (Stokes drag).

**Mathematical Equation:**
$F_D = 6\pi \eta r v$

*(Where $\eta$ = dynamic viscosity, $r$ = object radius, $v$ = velocity)*

**Python Code:**
```python
def stokes_drag(viscosity, radius, velocity):
    """Calculate Stokes drag for low-speed flow."""
    import math
    return 6 * math.pi * viscosity * radius * velocity
```

### 8.3 Drag Coefficient for Common Shapes
**Description:** Empirical values for different object geometries.

| Shape | Drag Coefficient |
|-------|------------------|
| Sphere | 0.47 |
| Cylinder (axis parallel to flow) | 0.1 |
| Cylinder (axis perpendicular to flow) | 1.1 |
| Flat plate (perpendicular to flow) | 1.28 |
| Streamlined body | 0.04 |

**Python Code:**
```python
def get_drag_coefficient(shape):
    """Get typical drag coefficient for common shapes."""
    coefficients = {
        "sphere": 0.47,
        "cylinder_parallel": 0.1,
        "cylinder_perpendicular": 1.1,
        "flat_plate": 1.28,
        "streamlined": 0.04
    }
    return coefficients.get(shape, 0.5)
```

---

## 9. Centripetal & Centrifugal Forces

### 9.1 Centripetal Force and Acceleration
**Description:** Net force directed toward center of circular path. Causes circular motion. Important for rotating components and curved trajectories.

**Mathematical Equations:**
- **Centripetal Force:** $F_c = \frac{mv^2}{r} = m\omega^2 r$
- **Centripetal Acceleration:** $a_c = \frac{v^2}{r} = \omega^2 r$

*(Where $m$ = mass, $v$ = tangential velocity, $r$ = radius, $\omega$ = angular velocity)*

**Python Code:**
```python
def centripetal_force(mass, velocity=None, radius=None, angular_velocity=None):
    """Calculate centripetal force."""
    if velocity is not None and radius is not None:
        return mass * (velocity**2) / radius
    elif angular_velocity is not None and radius is not None:
        return mass * (angular_velocity**2) * radius
    return None

def centripetal_acceleration(velocity=None, radius=None, angular_velocity=None):
    """Calculate centripetal acceleration."""
    if velocity is not None and radius is not None:
        return (velocity**2) / radius
    elif angular_velocity is not None and radius is not None:
        return (angular_velocity**2) * radius
    return None
```

### 9.2 Centrifugal Force (Fictitious Force in Rotating Frame)
**Description:** Apparent outward force in rotating reference frame. Useful for analyzing forces in rotating systems.

**Mathematical Equation:**
$F_{centrifugal} = m\omega^2 r$ (outward from center)

**Python Code:**
```python
def centrifugal_force(mass, angular_velocity, radius):
    """Calculate centrifugal force (fictitious force in rotating frame)."""
    return mass * (angular_velocity**2) * radius
```

---

## 10. Robot Kinematics & Jacobian Matrices

### 10.1 Forward Kinematics
**Description:** Calculates end-effector position and orientation given joint angles. Foundation for robot control and trajectory planning.

**Mathematical Equation:**
$T = T_1(\theta_1) \cdot T_2(\theta_2) \cdot ... \cdot T_n(\theta_n)$

*(Where $T$ = transformation matrix, $\theta_i$ = joint angles)*

**Python Code:**
```python
import numpy as np
import math

def forward_kinematics_2d_planar(link_lengths, joint_angles):
    """Calculate end-effector position for 2D planar robot."""
    x, y = 0, 0
    angle = 0
    
    for length, joint_angle in zip(link_lengths, joint_angles):
        angle += joint_angle
        x += length * math.cos(angle)
        y += length * math.sin(angle)
    
    return x, y, angle

def homogeneous_transform(rotation_matrix, position_vector):
    """Create 4x4 homogeneous transformation matrix."""
    T = np.eye(4)
    T[:3, :3] = rotation_matrix
    T[:3, 3] = position_vector
    return T
```

### 10.2 Jacobian Matrix (Geometric Jacobian)
**Description:** Relates joint velocities to end-effector velocities. Essential for velocity control and singularity analysis.

**Mathematical Equation:**
$\dot{x} = J(\theta) \dot{\theta}$

*(Where $\dot{x}$ = end-effector velocity, $J$ = Jacobian matrix, $\dot{\theta}$ = joint velocities)*

**Python Code:**
```python
import numpy as np

def compute_jacobian_2d_planar(link_lengths, joint_angles):
    """Compute Jacobian for 2D planar robot."""
    n = len(link_lengths)
    J = np.zeros((2, n))
    
    # Position of end-effector
    x, y = 0, 0
    angle = 0
    
    for i in range(n):
        angle += joint_angles[i]
        x += link_lengths[i] * np.cos(angle)
        y += link_lengths[i] * np.sin(angle)
    
    # Jacobian columns
    angle = 0
    for j in range(n):
        # Partial derivatives
        J[0, j] = -sum(link_lengths[i] * np.sin(sum(joint_angles[:i+1])) 
                      for i in range(j, n))
        J[1, j] = sum(link_lengths[i] * np.cos(sum(joint_angles[:i+1])) 
                     for i in range(j, n))
    
    return J

def end_effector_velocity(jacobian, joint_velocities):
    """Calculate end-effector velocity from joint velocities."""
    return np.dot(jacobian, joint_velocities)
```

### 10.3 Inverse Kinematics (Numerical)
**Description:** Calculates joint angles to reach desired end-effector position. Uses iterative methods.

**Python Code:**
```python
import numpy as np
from scipy.optimize import minimize

def inverse_kinematics_numerical(forward_kinematics_func, target_position, initial_guess, 
                                  link_lengths, max_iterations=1000, tolerance=1e-6):
    """Solve inverse kinematics using numerical optimization."""
    
    def error_function(joint_angles):
        ee_pos = forward_kinematics_func(link_lengths, joint_angles)[:2]
        error = np.linalg.norm(np.array(ee_pos) - np.array(target_position))
        return error
    
    result = minimize(error_function, initial_guess, method='BFGS', 
                     options={'maxiter': max_iterations, 'ftol': tolerance})
    
    return result.x, result.fun
```

---

## 11. Control Systems (PID, Impedance, Force Control)

### 11.1 PID Controller
**Description:** Proportional-Integral-Derivative controller. Most common feedback control method for robots.

**Mathematical Equation:**
$u(t) = K_p e(t) + K_i \int_0^t e(\tau) d\tau + K_d \frac{de(t)}{dt}$

*(Where $e(t)$ = error, $K_p, K_i, K_d$ = gains)*

**Python Code:**
```python
class PIDController:
    def __init__(self, kp, ki, kd, dt=0.01):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.dt = dt
        self.integral = 0
        self.prev_error = 0
    
    def update(self, error):
        """Calculate PID control output."""
        self.integral += error * self.dt
        derivative = (error - self.prev_error) / self.dt
        
        output = (self.kp * error + 
                 self.ki * self.integral + 
                 self.kd * derivative)
        
        self.prev_error = error
        return output
    
    def reset(self):
        """Reset controller state."""
        self.integral = 0
        self.prev_error = 0
```

### 11.2 Impedance Control
**Description:** Controls dynamic interaction between robot and environment. Emulates spring-damper behavior.

**Mathematical Equation:**
$F = M(\ddot{x}_{ref} - \ddot{x}) + B(\dot{x}_{ref} - \dot{x}) + K(x_{ref} - x)$

*(Where $M$ = desired mass, $B$ = desired damping, $K$ = desired stiffness)*

**Python Code:**
```python
def impedance_control(desired_mass, desired_damping, desired_stiffness,
                     ref_position, ref_velocity, ref_acceleration,
                     actual_position, actual_velocity, actual_acceleration=0):
    """Calculate impedance control force.
    Fixed: mass term acts on acceleration ERROR, not just ref_acceleration.
    F = M(ẍ_ref - ẍ) + B(ẋ_ref - ẋ) + K(x_ref - x)
    """
    position_error = ref_position - actual_position
    velocity_error = ref_velocity - actual_velocity
    acceleration_error = ref_acceleration - actual_acceleration
    
    force = (desired_mass * acceleration_error +
            desired_damping * velocity_error +
            desired_stiffness * position_error)
    
    return force
```

### 11.3 Force Control
**Description:** Directly controls force applied by end-effector to environment.

**Mathematical Equation:**
$F_{cmd} = F_{desired} + K_f (F_{meas} - F_{desired})$

*(Where $F_{cmd}$ = commanded force, $F_{meas}$ = measured force, $K_f$ = force gain)*

**Python Code:**
```python
def force_control(desired_force, measured_force, force_gain):
    """Calculate force control command.
    Fixed: gain should be 0 < K_f < 1 for negative feedback (stable).
    K_f > 1 causes positive feedback (unstable).
    """
    if force_gain > 1.0:
        force_gain = min(force_gain, 1.0)  # cap for stability
    force_error = measured_force - desired_force
    command_force = desired_force + force_gain * force_error
    return command_force
```

---

## 12. Lagrangian Mechanics & Constraint Forces

### 12.1 Lagrangian and Euler-Lagrange Equations
**Description:** Powerful formulation for deriving equations of motion for complex systems. Alternative to Newton's laws.

**Mathematical Equations:**
- **Lagrangian:** $L = T - V$ (kinetic energy minus potential energy)
- **Euler-Lagrange Equation:** $\frac{d}{dt}\left(\frac{\partial L}{\partial \dot{q}_i}\right) - \frac{\partial L}{\partial q_i} = Q_i$

*(Where $q_i$ = generalized coordinates, $Q_i$ = generalized forces)*

**Python Code:**
```python
import sympy as sp
import numpy as np

def lagrangian_mechanics_example():
    """Example: Lagrangian for simple pendulum.
    Fixed: theta must be a function of t for proper time derivative.
    """
    t = sp.Symbol('t')
    m_val, L_val, g_val = sp.symbols('m L g')
    theta = sp.Function('theta')(t)
    theta_dot = sp.diff(theta, t)
    
    # Kinetic energy
    T = sp.Rational(1, 2) * m_val * (L_val * theta_dot)**2
    
    # Potential energy
    V = m_val * g_val * L_val * (1 - sp.cos(theta))
    
    # Lagrangian
    Lagrangian = T - V
    
    # Euler-Lagrange equation (proper time derivative)
    dL_dtheta_dot = sp.diff(Lagrangian, theta_dot)
    d_dt_dL_dtheta_dot = sp.diff(dL_dtheta_dot, t)
    dL_dtheta = sp.diff(Lagrangian, theta)
    
    equation_of_motion = d_dt_dL_dtheta_dot - dL_dtheta
    
    return sp.simplify(equation_of_motion)
```

### 12.2 Constraint Forces (Lagrange Multipliers)
**Description:** Forces that enforce constraints in a system. Used in multi-body dynamics solvers.

**Mathematical Equation:**
$F_{constraint} = \lambda \nabla g(x)$

*(Where $\lambda$ = Lagrange multiplier, $g(x)$ = constraint equation)*

**Python Code:**
```python
import numpy as np
from scipy.optimize import fsolve

def solve_constrained_system(mass_matrix, force_vector, constraint_jacobian, constraint_rhs):
    """Solve for accelerations and constraint forces using Lagrange multipliers."""
    # System: M*a + J^T*lambda = F
    #         J*a = rhs
    
    n_dof = mass_matrix.shape[0]
    n_constraints = constraint_jacobian.shape[0]
    
    # Augmented system matrix
    A = np.vstack([
        np.hstack([mass_matrix, constraint_jacobian.T]),
        np.hstack([constraint_jacobian, np.zeros((n_constraints, n_constraints))])
    ])
    
    # Augmented RHS
    b = np.hstack([force_vector, constraint_rhs])
    
    # Solve
    solution = np.linalg.solve(A, b)
    
    accelerations = solution[:n_dof]
    multipliers = solution[n_dof:]
    
    return accelerations, multipliers
```

---

## 13. Advanced Friction Models

### 13.1 Stribeck Friction Model
**Description:** Captures transition from static to kinetic friction at low velocities. More realistic than simple Coulomb model.

**Mathematical Equation:**
$f = (\mu_s - (\mu_s - \mu_k) e^{-|v|/v_s}) \cdot \text{sgn}(v) \cdot N + b v$

*(Where $\mu_s$ = static friction coefficient, $\mu_k$ = kinetic friction coefficient, $v_s$ = Stribeck velocity, $b$ = viscous damping)*

**Python Code:**
```python
import numpy as np

def stribeck_friction(velocity, normal_force, mu_s, mu_k, stribeck_velocity, viscous_damping=0):
    """Calculate Stribeck friction force."""
    if abs(velocity) < 1e-10:
        return 0
    
    # Friction coefficient transitions from mu_s to mu_k
    mu = mu_k + (mu_s - mu_k) * np.exp(-abs(velocity) / stribeck_velocity)
    
    # Friction force with viscous component
    friction = mu * normal_force * np.sign(velocity) + viscous_damping * velocity
    
    return friction
```

### 13.2 Viscous Friction (Damping)
**Description:** Friction proportional to velocity. Models air resistance and fluid damping.

**Mathematical Equation:**
$f = -c v$

*(Where $c$ = damping coefficient, $v$ = velocity)*

**Python Code:**
```python
def viscous_friction(velocity, damping_coefficient):
    """Calculate viscous friction force."""
    return -damping_coefficient * velocity
```

### 13.3 Combined Friction Model
**Description:** Combines Coulomb, viscous, and Stribeck effects for realistic simulation.

**Python Code:**
```python
def combined_friction_model(velocity, normal_force, mu_s, mu_k, stribeck_velocity, 
                           viscous_damping, coulomb_damping=0):
    """Calculate combined friction with Coulomb, Stribeck, and viscous components."""
    if abs(velocity) < 1e-10:
        return coulomb_damping * 0  # No motion
    
    # Stribeck component
    mu = mu_k + (mu_s - mu_k) * np.exp(-abs(velocity) / stribeck_velocity)
    coulomb_friction = mu * normal_force * np.sign(velocity)
    
    # Viscous component
    viscous = viscous_damping * velocity
    
    # Total friction
    total_friction = coulomb_friction + viscous
    
    return total_friction
```

---

## 14. Contact Mechanics (Hertzian & Penalty Methods)

### 14.1 Hertzian Contact Stress (Sphere-Plane)
**Description:** Calculates contact stress when two curved surfaces touch. Important for accurate contact force modeling.

**Mathematical Equations:**
- **Contact Pressure:** $p_{max} = \frac{3F}{2\pi a^2}$
- **Contact Radius:** $a = \sqrt[3]{\frac{3FR}{4E^*}}$

*(Where $F$ = normal force, $R$ = effective radius, $E^*$ = effective Young's modulus)*

**Python Code:**
```python
import math

def hertzian_contact_sphere_plane(normal_force, radius1, radius2, youngs_modulus1, youngs_modulus2, poisson1=0.3, poisson2=0.3):
    """Calculate Hertzian contact parameters for sphere-plane contact."""
    
    # Effective radius
    R_eff = 1 / (1/radius1 + 1/radius2) if radius2 != float('inf') else radius1
    
    # Effective Young's modulus
    E_eff = 1 / ((1 - poisson1**2)/youngs_modulus1 + (1 - poisson2**2)/youngs_modulus2)
    
    # Contact radius
    a = (3 * normal_force * R_eff / (4 * E_eff))**(1/3)
    
    # Maximum contact pressure
    p_max = 3 * normal_force / (2 * math.pi * a**2)
    
    # Contact depth
    d = a**2 / R_eff
    
    return {
        "contact_radius": a,
        "max_pressure": p_max,
        "contact_depth": d
    }
```

### 14.2 Penalty-Based Contact Force
**Description:** Simulates contact by applying force proportional to penetration depth. Common in physics engines.

**Mathematical Equation:**
$F_{contact} = k_{penalty} \cdot \text{penetration\_depth}$

*(Where $k_{penalty}$ = penalty stiffness)*

**Python Code:**
```python
def penalty_contact_force(penetration_depth, penalty_stiffness, damping_coefficient=0, relative_velocity=0):
    """Calculate contact force using penalty method."""
    if penetration_depth <= 0:
        return 0
    
    # Spring force from penetration
    spring_force = penalty_stiffness * penetration_depth
    
    # Damping force from relative velocity
    damping_force = damping_coefficient * relative_velocity
    
    # Total contact force
    contact_force = spring_force + damping_force
    
    return contact_force
```

---

## 15. Cable Tension & Rope Mechanics

### 15.1 Cable Tension in Static Equilibrium
**Description:** Calculates tension in cables supporting loads at angles.

**Mathematical Equations:**
- **Vertical Load:** $T_1 \sin(\alpha_1) + T_2 \sin(\alpha_2) = W$
- **Horizontal Equilibrium:** $T_1 \cos(\alpha_1) = T_2 \cos(\alpha_2)$

*(Where $T_i$ = tension in cable $i$, $\alpha_i$ = angle from horizontal, $W$ = weight)*

**Python Code:**
```python
import numpy as np

def cable_tension_two_supports(weight, angle1, angle2):
    """Calculate cable tensions for weight suspended by two cables at angles."""
    # Convert angles to radians
    a1 = np.radians(angle1)
    a2 = np.radians(angle2)
    
    # System of equations: T1*sin(a1) + T2*sin(a2) = W
    #                      T1*cos(a1) = T2*cos(a2)
    
    A = np.array([
        [np.sin(a1), np.sin(a2)],
        [np.cos(a1), -np.cos(a2)]
    ])
    b = np.array([weight, 0])
    
    tensions = np.linalg.solve(A, b)
    return tensions[0], tensions[1]
```

### 15.2 Pulley System Mechanical Advantage
**Description:** Calculates force reduction in pulley systems.

**Mathematical Equation:**
$F_{load} = F_{effort} \times n$

*(Where $n$ = number of supporting rope segments. More segments = more load lifted.)*
*(Equivalently: $F_{effort} = \frac{F_{load}}{n}$ — less effort needed with more pulleys.)*

**Python Code:**
```python
def pulley_mechanical_advantage(effort_force, num_supporting_segments):
    """Calculate load that can be lifted with pulley system.
    Fixed: F_load = F_effort × n (not / n). More pulleys = more load.
    """
    if num_supporting_segments <= 0:
        return 0
    load_force = effort_force * num_supporting_segments
    return load_force
```

---

## 16. Magnetic Forces

### 16.1 Lorentz Force
**Description:** Force on a charged particle moving in magnetic field. Important for electromagnetic actuators.

**Mathematical Equation:**
$\vec{F} = q(\vec{E} + \vec{v} \times \vec{B})$

*(Where $q$ = charge, $\vec{E}$ = electric field, $\vec{v}$ = velocity, $\vec{B}$ = magnetic field)*

**Python Code:**
```python
import numpy as np

def lorentz_force(charge, electric_field, velocity, magnetic_field):
    """Calculate Lorentz force on a charged particle."""
    electric_force = charge * electric_field
    magnetic_force = charge * np.cross(velocity, magnetic_field)
    total_force = electric_force + magnetic_force
    return total_force

def magnetic_force_on_current(current, length_vector, magnetic_field):
    """Calculate force on current-carrying conductor in magnetic field."""
    return current * np.cross(length_vector, magnetic_field)
```

### 16.2 Magnetic Field Force Between Magnets
**Description:** Approximate force between two magnetic dipoles.

**Mathematical Equation:**
$F \approx \frac{6\mu_0 m_1 m_2}{4\pi r^4}$

*(Where $\mu_0$ = permeability of free space, $m_i$ = magnetic moments, $r$ = distance)*

**Python Code:**
```python
import math

def magnetic_dipole_force(magnetic_moment1, magnetic_moment2, distance):
    """Calculate approximate force between two magnetic dipoles."""
    mu_0 = 4 * math.pi * 1e-7  # Permeability of free space
    
    force = (6 * mu_0 * magnetic_moment1 * magnetic_moment2) / (4 * math.pi * (distance**4))
    return force
```

---

## 17. Joint Constraints & Workspace Limits

### 17.1 Revolute Joint Constraint
**Description:** Constrains relative motion between two bodies to rotation about a single axis.

**Mathematical Equation:**
$\vec{r}_{joint,1} = \vec{r}_{joint,2}$ (position constraint)
$\vec{v}_{rel} \cdot \hat{n} = 0$ (velocity constraint for non-rotation axes)

**Python Code:**
```python
import numpy as np

def revolute_joint_constraint(body1_position, body2_position, joint_axis, joint_position):
    """Check revolute joint constraints.
    Fixed: checks both position coincidence AND axis alignment.
    Returns dict with position_error and axis_constraint.
    """
    body1_position = np.array(body1_position)
    body2_position = np.array(body2_position)
    joint_axis = np.array(joint_axis)
    
    # Position constraint: joint attachment points must coincide
    position_error = np.linalg.norm(body1_position - body2_position)
    
    # Axis constraint: relative displacement must be along joint axis only
    relative = body2_position - body1_position
    axis_norm = joint_axis / np.linalg.norm(joint_axis) if np.linalg.norm(joint_axis) > 0 else joint_axis
    perpendicular = relative - np.dot(relative, axis_norm) * axis_norm
    axis_error = np.linalg.norm(perpendicular)
    
    return {"position_error": position_error, "axis_error": axis_error,
            "satisfied": position_error < 1e-6 and axis_error < 1e-6}
```

### 17.2 Prismatic Joint Constraint
**Description:** Constrains relative motion to translation along a single axis.

**Mathematical Equation:**
$\vec{r}_{rel} \cdot \hat{n}_{\perp} = 0$ (perpendicular to motion axis)
$\theta_{rel} = 0$ (no rotation)

**Python Code:**
```python
def prismatic_joint_constraint(body1_position, body2_position, motion_axis):
    """Check prismatic joint constraints.
    Fixed: guard against zero motion_axis, check both translation and rotation.
    """
    body1_position = np.array(body1_position, dtype=float)
    body2_position = np.array(body2_position, dtype=float)
    motion_axis = np.array(motion_axis, dtype=float)
    
    axis_norm = np.linalg.norm(motion_axis)
    if axis_norm < 1e-10:
        return {"perpendicular_error": 0, "satisfied": False, "error": "zero motion axis"}
    
    motion_axis_normalized = motion_axis / axis_norm
    relative_position = body2_position - body1_position
    
    # Component perpendicular to motion axis should be zero
    perpendicular = relative_position - np.dot(relative_position, motion_axis_normalized) * motion_axis_normalized
    perp_error = np.linalg.norm(perpendicular)
    
    # Slide distance along axis
    slide_distance = np.dot(relative_position, motion_axis_normalized)
    
    return {"perpendicular_error": perp_error, "slide_distance": slide_distance,
            "satisfied": perp_error < 1e-6}
```

### 17.3 Workspace Boundary Check
**Description:** Determines if end-effector position is within robot workspace.

**Python Code:**
```python
def check_workspace_boundary(end_effector_position, workspace_bounds):
    """Check if end-effector is within workspace bounds."""
    x, y, z = end_effector_position
    x_min, x_max, y_min, y_max, z_min, z_max = workspace_bounds
    
    in_workspace = (x_min <= x <= x_max and 
                   y_min <= y <= y_max and 
                   z_min <= z <= z_max)
    
    return in_workspace
```

### 17.4 Joint Limit Enforcement
**Description:** Prevents joints from exceeding their mechanical limits.

**Python Code:**
```python
def enforce_joint_limits(joint_angles, joint_limits):
    """Enforce joint angle limits."""
    limited_angles = []
    for angle, (min_angle, max_angle) in zip(joint_angles, joint_limits):
        limited_angle = max(min_angle, min(angle, max_angle))
        limited_angles.append(limited_angle)
    return limited_angles
```

---

## 18. Energy, Power, & Work

### 18.1 Work Done by a Force
**Description:** Energy transferred by a force acting over a distance.

**Mathematical Equation:**
$W = \int F \cdot dx = F \cdot d \cdot \cos(\theta)$

*(Where $\theta$ = angle between force and displacement)*

**Python Code:**
```python
import numpy as np

def work_done(force_vector, displacement_vector):
    """Calculate work done by a force."""
    return np.dot(force_vector, displacement_vector)
```

### 18.2 Power
**Description:** Rate of energy transfer or work done per unit time.

**Mathematical Equations:**
- **Mechanical Power:** $P = F \cdot v = \tau \cdot \omega$
- **Electrical Power:** $P = V \cdot I$

**Python Code:**
```python
def mechanical_power(force, velocity):
    """Calculate mechanical power (force-velocity)."""
    return force * velocity

def rotational_power(torque, angular_velocity):
    """Calculate rotational power (torque-angular velocity)."""
    return torque * angular_velocity

def electrical_power(voltage, current):
    """Calculate electrical power."""
    return voltage * current
```

### 18.3 Kinetic Energy
**Description:** Energy of motion.

**Mathematical Equations:**
- **Translational:** $KE = \frac{1}{2}mv^2$
- **Rotational:** $KE = \frac{1}{2}I\omega^2$
- **Combined:** $KE = \frac{1}{2}mv_{cm}^2 + \frac{1}{2}I_{cm}\omega^2$

**Python Code:**
```python
def kinetic_energy_translational(mass, velocity):
    """Calculate translational kinetic energy."""
    return 0.5 * mass * (velocity**2)

def kinetic_energy_rotational(moment_of_inertia, angular_velocity):
    """Calculate rotational kinetic energy."""
    return 0.5 * moment_of_inertia * (angular_velocity**2)

def kinetic_energy_combined(mass, velocity_cm, moment_of_inertia, angular_velocity):
    """Calculate total kinetic energy (translation + rotation)."""
    translational = 0.5 * mass * (velocity_cm**2)
    rotational = 0.5 * moment_of_inertia * (angular_velocity**2)
    return translational + rotational
```

### 18.4 Potential Energy
**Description:** Energy stored due to position or configuration.

**Mathematical Equations:**
- **Gravitational:** $PE = mgh$
- **Elastic (Spring):** $PE = \frac{1}{2}kx^2$

**Python Code:**
```python
def gravitational_potential_energy(mass, height, gravity=9.81):
    """Calculate gravitational potential energy."""
    return mass * gravity * height

def elastic_potential_energy(spring_constant, displacement):
    """Calculate elastic potential energy stored in spring."""
    return 0.5 * spring_constant * (displacement**2)
```

### 18.5 Energy Conservation
**Description:** In closed systems without friction, total mechanical energy is conserved.

**Mathematical Equation:**
$E_{total} = KE + PE = \text{constant}$

**Python Code:**
```python
def total_mechanical_energy(kinetic_energy, potential_energy):
    """Calculate total mechanical energy."""
    return kinetic_energy + potential_energy

def energy_conservation_check(initial_energy, final_energy, tolerance=1e-6):
    """Check if energy is conserved within tolerance."""
    energy_loss = abs(initial_energy - final_energy)
    is_conserved = energy_loss < tolerance
    return is_conserved, energy_loss
```

---

## References

[1] Physics Classroom. "Kinematic Equations." https://www.physicsclassroom.com/class/1dkin/Lesson-6/Kinematic-Equations

[2] OpenStax. "Newton's Second Law." https://openstax.org/books/university-physics-volume-1/pages/5-3-newtons-second-law

[3] LibreTexts. "Torque and Angular Acceleration." https://phys.libretexts.org/Bookshelves/Classical_Mechanics/Classical_Mechanics_(Dourmashkin)/17%3A_Two-Dimensional_Rotational_Dynamics/17.04%3A_Torque_Angular_Acceleration_and_Moment_of_Inertia

[4] LibreTexts. "Angular Momentum." https://phys.libretexts.org/Bookshelves/University_Physics/Radically_Modern_Introductory_Physics_Text_I_(Raymond)/11%3A_Rotational_Dynamics/11.02%3A_Torque_and_Angular_Momentum

[5] OpenStax. "Friction." https://openstax.org/books/university-physics-volume-1/pages/6-2-friction

[6] Monolithic Power Systems. "DC Motor Fundamentals." https://www.monolithicpower.com/en/learning/mpscholar/electric-motors/dc-motors/fundamentals

[7] LibreTexts. "Hooke's Law." https://phys.libretexts.org/Bookshelves/Conceptual_Physics/Introduction_to_Physics_(Park)/02%3A_Mechanics_I_-_Motion_and_Forces/02%3A_Dynamics/2.07%3A_Spring_Force-_Hookes_Law

[8] LibreTexts. "Damped Harmonic Oscillation." https://phys.libretexts.org/Bookshelves/University_Physics/University_Physics_I_-_Mechanics_Sound_Oscillations_and_Waves_(OpenStax)/15%3A_Oscillations/15.06%3A_Damped_Oscillations

[9] LibreTexts. "Coefficient of Restitution." https://phys.libretexts.org/Courses/Gettysburg_College/Gettysburg_College_Physics_for_Physics_Majors/08%3A_C8)_Conservation_of_Energy-_Kinetic_and_Gravitational/8.08%3A_Relative_Velocity_and_the_Coefficient_of_Restitution

[10] All About Circuits. "Accelerometer Sensing." https://www.allaboutcircuits.com/technical-articles/introduction-to-capacitive-accelerometer-measure-acceleration-capacitive-sensing/

[11] NASA. "Drag Equation." https://www.grc.nasa.gov/www/k-12/VirtualAero/BottleRocket/airplane/drageq.html

[12] OpenStax. "Centripetal Force." https://openstax.org/books/physics/pages/6-2-uniform-circular-motion

[13] Automatic Addison. "Jacobian Matrices for Robotics." https://automaticaddison.com/the-ultimate-guide-to-jacobian-matrices-for-robotics/

[14] National Instruments. "PID Control Theory." https://www.ni.com/en/shop/labview/pid-theory-explained.html

[15] LibreTexts. "Lagrangian Mechanics." https://phys.libretexts.org/Bookshelves/Classical_Mechanics/Classical_Mechanics_(Tatum)/13%3A_Lagrangian_Mechanics/13.04%3A_The_Lagrangian_Equations_of_Motion

[16] Tribonet. "Stribeck Curve." https://www.tribonet.org/wiki/stribeck-curve/

[17] Tribonet. "Hertz Contact Equations." https://www.tribonet.org/wiki/hertz-contact-equations-for-elliptical-spherical-and-cylindrical-contacts/

[18] Khan Academy. "Work-Energy Theorem." https://www.khanacademy.org/science/in-in-class11th-physics/in-in-class11th-physics-work-energy-and-power/in-in-class11-work-energy-theorem/a/work-energy-theorem-ap1

---

## Quick Reference Table

| Concept | Key Equation | Use Case |
|---------|-------------|----------|
| Force | $F = ma$ | Any dynamic simulation |
| Torque | $\tau = I\alpha$ | Rotational motion, motors |
| Friction | $f = \mu N$ | Grasping, locomotion, sliding |
| Spring Force | $F = -kx$ | Compliant joints, springs |
| Drag | $F_D = \frac{1}{2}\rho C_D A v^2$ | Aerial/aquatic robots |
| Centripetal | $F_c = \frac{mv^2}{r}$ | Curved trajectories |
| DC Motor | $\tau = k_t I$ | Motor control |
| PID Control | $u = K_p e + K_i \int e + K_d \dot{e}$ | Joint control |
| Jacobian | $\dot{x} = J\dot{\theta}$ | Velocity control |
| Energy | $E = KE + PE$ | Energy analysis |

---

## Implementation Tips for Physics Engines

1. **Always check for singularities** in Jacobian calculations
2. **Use Lagrange multipliers** for constraint forces in multi-body systems
3. **Apply penalty method** for contact forces with appropriate stiffness
4. **Implement Stribeck friction** for realistic stick-slip behavior
5. **Use quaternions** for rotation representation to avoid gimbal lock
6. **Normalize vectors** before cross products
7. **Check energy conservation** as a validation metric
8. **Use implicit integration** for stiff systems (springs, dampers)
9. **Clamp velocities** to prevent numerical instability
10. **Validate against analytical solutions** whenever possible

---

**Document Version:** 1.0  
**Last Updated:** April 2026  
**For Use With:** NVIDIA Isaac Sim, IsaacLab, Newton Physics Engine, and similar robotics simulation platforms


---

## PRODUCTION CALCULATOR - Complete Function Reference

This section provides the complete, production-ready calculator implementation with all 50+ calculation functions organized by category. These functions can be used directly in Python or through the interactive CLI interface.

### Calculator Core Engine

```python
#!/usr/bin/env python3
"""
Robotics Physics Calculator - Production Grade
Complete implementation with all equation categories
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class CalculationResult:
    """Store calculation results with metadata"""
    equation_name: str
    category: str
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    timestamp: str
    notes: str = ""
    
    def to_dict(self):
        return asdict(self)


class RoboticsCalculator:
    """Main calculator engine with all physics equations"""
    
    def __init__(self):
        self.history: List[CalculationResult] = []
        self.cache: Dict[str, Any] = {}
        self.material_db = self._init_material_database()
        
    def _init_material_database(self) -> Dict[str, Dict[str, float]]:
        """Initialize material properties database"""
        return {
            "steel_mild": {
                "density": 7850,
                "youngs_modulus": 200e9,
                "yield_strength": 250e6,
                "shear_strength": 150e6,
                "friction_coefficient": 0.6,
                "thermal_expansion": 11e-6
            },
            "steel_stainless": {
                "density": 8000,
                "youngs_modulus": 193e9,
                "yield_strength": 310e6,
                "shear_strength": 186e6,
                "friction_coefficient": 0.5,
                "thermal_expansion": 16e-6
            },
            "aluminum": {
                "density": 2700,
                "youngs_modulus": 69e9,
                "yield_strength": 110e6,
                "shear_strength": 66e6,
                "friction_coefficient": 0.4,
                "thermal_expansion": 23e-6
            },
            "brass": {
                "density": 8500,
                "youngs_modulus": 100e9,
                "yield_strength": 200e6,
                "shear_strength": 120e6,
                "friction_coefficient": 0.4,
                "thermal_expansion": 19e-6
            },
            "glass": {
                "density": 2500,
                "youngs_modulus": 70e9,
                "yield_strength": 50e6,
                "shear_strength": 30e6,
                "friction_coefficient": 0.4,
                "thermal_expansion": 9e-6
            },
            "plastic_acrylic": {
                "density": 1190,
                "youngs_modulus": 3.2e9,
                "yield_strength": 72e6,
                "shear_strength": 43e6,
                "friction_coefficient": 0.3,
                "thermal_expansion": 70e-6
            }
        }
    
    def _record_calculation(self, result: CalculationResult):
        """Record calculation to history"""
        self.history.append(result)
    
    # ==================== GEOMETRY ====================
    
    def wall_thickness_from_width(self, body_width: float, thickness_ratio: float = 15) -> Dict[str, float]:
        """Calculate wall thickness from body width"""
        thickness = body_width / thickness_ratio
        return {
            "wall_thickness": thickness,
            "body_width": body_width,
            "thickness_ratio": thickness_ratio
        }
    
    def door_zone_heights(self, door_height: float) -> Dict[str, Dict[str, float]]:
        """Calculate door zone heights based on ergonomic proportions"""
        return {
            "handle_zone": {
                "start": door_height * 0.35,
                "end": door_height * 0.45,
                "center": door_height * 0.40
            },
            "lock_zone": {
                "start": door_height * 0.45,
                "end": door_height * 0.55,
                "center": door_height * 0.50
            },
            "vision_zone": {
                "start": door_height * 0.60,
                "end": door_height * 0.80,
                "center": door_height * 0.70
            }
        }
    
    def frame_width_from_door(self, door_width: float, frame_thickness: float = 0.04, 
                             clearance_gap: float = 0.004) -> Dict[str, float]:
        """Calculate frame width from door width"""
        frame_width = door_width + 2 * (clearance_gap + frame_thickness)
        return {
            "frame_width": frame_width,
            "door_width": door_width,
            "frame_thickness": frame_thickness,
            "clearance_gap": clearance_gap
        }
    
    def handle_standoff_from_door_depth(self, door_depth: float, grip_clearance: float = 0.04) -> Dict[str, float]:
        """Calculate handle standoff distance from door surface"""
        standoff = door_depth + grip_clearance
        return {
            "standoff": standoff,
            "door_depth": door_depth,
            "grip_clearance": grip_clearance
        }
    
    def knob_spacing(self, body_width: float, knob_count: int, knob_diameter: float) -> Dict[str, Any]:
        """Calculate knob spacing on body"""
        total_knob_width = knob_count * knob_diameter
        available_space = body_width - total_knob_width
        spacing = available_space / (knob_count + 1)
        
        positions = []
        for i in range(knob_count):
            x = spacing + i * (knob_diameter + spacing) + knob_diameter / 2
            positions.append(x)
        
        return {
            "spacing": spacing,
            "positions": positions,
            "body_width": body_width,
            "knob_count": knob_count,
            "knob_diameter": knob_diameter
        }
    
    def glass_area_from_door_dimensions(self, door_inner_width: float, door_inner_height: float, 
                                       frame_margin: float = 0.025) -> Dict[str, float]:
        """Calculate glass panel area from door inner dimensions"""
        glass_width = door_inner_width - 2 * frame_margin
        glass_height = door_inner_height - 2 * frame_margin
        glass_area = glass_width * glass_height
        
        return {
            "glass_width": glass_width,
            "glass_height": glass_height,
            "glass_area": glass_area,
            "frame_margin": frame_margin
        }
    
    def divider_positions(self, zone_start: float, zone_end: float, divider_count: int) -> Dict[str, Any]:
        """Calculate divider positions within zone"""
        zone_width = zone_end - zone_start
        positions = []
        
        for i in range(1, divider_count + 1):
            x = zone_start + (i * zone_width / (divider_count + 1))
            positions.append(x)
        
        return {
            "positions": positions,
            "zone_start": zone_start,
            "zone_end": zone_end,
            "divider_count": divider_count
        }
    
    # ==================== PHYSICS - DOOR MECHANISMS ====================
    
    def mass_from_volume_density(self, volume: float, density: float) -> Dict[str, float]:
        """Calculate mass from volume and density"""
        mass = volume * density
        return {
            "mass": mass,
            "volume": volume,
            "density": density
        }
    
    def gravity_torque_on_door(self, mass: float, distance_to_cm: float, angle_degrees: float, 
                              gravity: float = 9.81) -> Dict[str, float]:
        """Calculate gravity torque at given angle"""
        angle_rad = math.radians(angle_degrees)
        torque = mass * gravity * distance_to_cm * math.sin(angle_rad)
        
        return {
            "torque": torque,
            "mass": mass,
            "distance_to_cm": distance_to_cm,
            "angle_degrees": angle_degrees,
            "angle_radians": angle_rad
        }
    
    def gravity_torque_profile(self, mass: float, distance_to_cm: float, gravity: float = 9.81) -> Dict[str, Any]:
        """Generate gravity torque profile from 0 to 90 degrees"""
        angles_deg = list(range(0, 91, 5))
        torques = []
        
        for angle_deg in angles_deg:
            angle_rad = math.radians(angle_deg)
            torque = mass * gravity * distance_to_cm * math.sin(angle_rad)
            torques.append(torque)
        
        return {
            "angles_degrees": angles_deg,
            "torques": torques,
            "max_torque": max(torques),
            "max_torque_angle": 90
        }
    
    def counterbalance_spring_stiffness(self, mass: float, distance_to_cm: float, 
                                       spring_extension: float, gravity: float = 9.81) -> Dict[str, float]:
        """Calculate spring stiffness to counterbalance door"""
        max_torque = mass * gravity * distance_to_cm
        stiffness = max_torque / spring_extension
        
        return {
            "spring_stiffness": stiffness,
            "max_torque": max_torque,
            "spring_extension": spring_extension
        }
    
    def damping_coefficient_from_close_time(self, mass: float, distance_to_cm: float, 
                                           desired_close_time: float, gravity: float = 9.81) -> Dict[str, float]:
        """Calculate damping coefficient for desired close time"""
        damping = (2 * mass * gravity * distance_to_cm) / desired_close_time
        
        return {
            "damping_coefficient": damping,
            "desired_close_time": desired_close_time,
            "mass": mass
        }
    
    def max_spring_stiffness_robot_can_overcome(self, robot_max_force: float, 
                                               expected_deflection: float) -> Dict[str, float]:
        """Calculate max spring stiffness robot can overcome"""
        max_stiffness = robot_max_force / expected_deflection
        
        return {
            "max_spring_stiffness": max_stiffness,
            "robot_max_force": robot_max_force,
            "expected_deflection": expected_deflection
        }
    
    def pin_diameter_from_shear_load(self, shear_force: float, shear_stress_limit: float) -> Dict[str, float]:
        """Calculate minimum pin diameter from shear load"""
        diameter = math.sqrt((4 * shear_force) / (math.pi * shear_stress_limit))
        
        return {
            "pin_diameter": diameter,
            "shear_force": shear_force,
            "shear_stress_limit": shear_stress_limit
        }
    
    def bracket_width_from_load(self, hinge_load: float, bracket_length: float, 
                               bracket_thickness: float, allowable_stress: float) -> Dict[str, float]:
        """Calculate bracket width from load"""
        width = (hinge_load * bracket_length) / (bracket_thickness * allowable_stress)
        
        return {
            "bracket_width": width,
            "hinge_load": hinge_load,
            "bracket_length": bracket_length,
            "bracket_thickness": bracket_thickness
        }
    
    def moment_of_inertia_rectangular_door(self, mass: float, door_width: float, 
                                          door_height: float) -> Dict[str, float]:
        """Calculate moment of inertia for rectangular door"""
        I = (1/3) * mass * (door_width**2 + door_height**2)
        
        return {
            "moment_of_inertia": I,
            "mass": mass,
            "door_width": door_width,
            "door_height": door_height
        }
    
    # ==================== PERCEPTION ====================
    
    def real_dimension_from_pixels(self, pixel_distance: float, depth_meters: float, 
                                  focal_length_pixels: float, sensor_scale: float = 1.0) -> Dict[str, float]:
        """Convert pixel measurement to real-world dimension"""
        real_dimension = (pixel_distance * depth_meters * sensor_scale) / focal_length_pixels
        
        return {
            "real_dimension": real_dimension,
            "pixel_distance": pixel_distance,
            "depth_meters": depth_meters,
            "focal_length_pixels": focal_length_pixels
        }
    
    def pixel_to_3d_point(self, pixel_x: float, pixel_y: float, depth_meters: float, 
                         focal_length_x: float, focal_length_y: float, 
                         principal_point_x: float, principal_point_y: float) -> Dict[str, Any]:
        """Convert pixel coordinates to 3D world coordinates"""
        x_norm = (pixel_x - principal_point_x) / focal_length_x
        y_norm = (pixel_y - principal_point_y) / focal_length_y
        
        x_3d = x_norm * depth_meters
        y_3d = y_norm * depth_meters
        z_3d = depth_meters
        
        return {
            "x_3d": x_3d,
            "y_3d": y_3d,
            "z_3d": z_3d,
            "point_3d": (x_3d, y_3d, z_3d)
        }
    
    def fuse_depth_measurements(self, depth1: float, depth2: float, 
                               confidence1: float = 1.0, confidence2: float = 1.0) -> Dict[str, float]:
        """Fuse two depth measurements"""
        fused_depth = (confidence1 * depth1 + confidence2 * depth2) / (confidence1 + confidence2)
        
        return {
            "fused_depth": fused_depth,
            "depth1": depth1,
            "depth2": depth2,
            "confidence1": confidence1,
            "confidence2": confidence2
        }
    
    # ==================== VALIDATION & UNIT CONVERSIONS ====================
    
    def convert_units(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """Convert between units"""
        conversions = {
            ("degrees", "radians"): lambda x: x * math.pi / 180,
            ("radians", "degrees"): lambda x: x * 180 / math.pi,
            ("inches", "meters"): lambda x: x * 0.0254,
            ("meters", "inches"): lambda x: x / 0.0254,
            ("mm", "meters"): lambda x: x / 1000,
            ("meters", "mm"): lambda x: x * 1000,
            ("pounds", "kg"): lambda x: x * 0.453592,
            ("kg", "pounds"): lambda x: x / 0.453592,
            ("newtons", "lbf"): lambda x: x * 0.224809,
            ("lbf", "newtons"): lambda x: x * 4.44822,
            ("nm", "ft_lbs"): lambda x: x * 0.737562,
            ("ft_lbs", "nm"): lambda x: x * 1.35582,
        }
        
        key = (from_unit.lower(), to_unit.lower())
        if key in conversions:
            converted = conversions[key](value)
            return {
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": converted,
                "converted_unit": to_unit
            }
        
        return {"error": f"Conversion from {from_unit} to {to_unit} not supported"}
    
    def reachability_score(self, distance_to_target: float, robot_max_reach: float) -> Dict[str, float]:
        """Calculate reachability score"""
        if distance_to_target > robot_max_reach:
            score = 0.0
        else:
            score = 1.0 - (distance_to_target / robot_max_reach)
        
        score = max(0.0, min(1.0, score))
        
        return {
            "reachability_score": score,
            "distance_to_target": distance_to_target,
            "robot_max_reach": robot_max_reach,
            "reachable": score > 0
        }
    
    def friction_coefficient_lookup(self, material1: str, material2: str, 
                                   joint_type: str = "sliding", lubricated: bool = False) -> Dict[str, Any]:
        """Look up friction coefficient"""
        friction_db = {
            ("steel", "steel"): {"sliding": 0.6, "rolling": 0.002},
            ("steel", "aluminum"): {"sliding": 0.5, "rolling": 0.002},
            ("steel", "rubber"): {"sliding": 0.7, "rolling": 0.015},
            ("aluminum", "aluminum"): {"sliding": 0.4, "rolling": 0.001},
            ("plastic", "steel"): {"sliding": 0.3, "rolling": 0.01},
            ("glass", "glass"): {"sliding": 0.4, "rolling": 0.01},
        }
        
        key = tuple(sorted([material1.lower(), material2.lower()]))
        
        if key in friction_db:
            mu = friction_db[key].get(joint_type.lower(), 0.5)
            if lubricated:
                mu *= 0.5
            
            return {
                "friction_coefficient": mu,
                "material1": material1,
                "material2": material2,
                "joint_type": joint_type,
                "lubricated": lubricated
            }
        
        return {"error": f"Material pair {material1}-{material2} not in database"}
    
    def bboxes_overlap_2d(self, bbox1: Tuple, bbox2: Tuple) -> Dict[str, Any]:
        """Check if two 2D bounding boxes overlap"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        overlap_x = x1_max >= x2_min and x2_max >= x1_min
        overlap_y = y1_max >= y2_min and y2_max >= y1_min
        overlap = overlap_x and overlap_y
        
        return {
            "overlap": overlap,
            "bbox1": bbox1,
            "bbox2": bbox2,
            "overlap_x": overlap_x,
            "overlap_y": overlap_y
        }
    
    def iou_2d(self, bbox1: Tuple, bbox2: Tuple) -> Dict[str, float]:
        """Calculate Intersection over Union for 2D bboxes"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        
        intersection_width = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        intersection_height = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        intersection = intersection_width * intersection_height
        
        union = area1 + area2 - intersection
        
        iou = intersection / union if union > 0 else 0.0
        
        return {
            "iou": iou,
            "intersection_area": intersection,
            "union_area": union,
            "area1": area1,
            "area2": area2
        }
    
    # ==================== STRUCTURAL ENGINEERING ====================
    
    def cantilever_beam_deflection(self, load_force: float, beam_length: float, 
                                  youngs_modulus: float, moment_of_inertia: float) -> Dict[str, float]:
        """Calculate cantilever beam deflection"""
        deflection = (load_force * (beam_length ** 3)) / (3 * youngs_modulus * moment_of_inertia)
        
        return {
            "deflection": deflection,
            "load_force": load_force,
            "beam_length": beam_length,
            "youngs_modulus": youngs_modulus,
            "moment_of_inertia": moment_of_inertia
        }
    
    def rectangular_beam_moment_of_inertia(self, width: float, height: float) -> Dict[str, float]:
        """Calculate second moment of inertia for rectangular cross-section"""
        I = (width * (height ** 3)) / 12
        
        return {
            "moment_of_inertia": I,
            "width": width,
            "height": height
        }
    
    def euler_buckling_load(self, youngs_modulus: float, moment_of_inertia: float, 
                           unsupported_length: float, boundary_condition: str = "pinned") -> Dict[str, float]:
        """Calculate Euler buckling load"""
        k_factors = {
            "pinned": 1.0,
            "fixed": 0.5,
            "fixed_free": 2.0,
            "fixed_pinned": 0.7
        }
        
        k = k_factors.get(boundary_condition.lower(), 1.0)
        effective_length = k * unsupported_length
        
        buckling_load = (math.pi ** 2 * youngs_modulus * moment_of_inertia) / (effective_length ** 2)
        
        return {
            "buckling_load": buckling_load,
            "youngs_modulus": youngs_modulus,
            "moment_of_inertia": moment_of_inertia,
            "effective_length": effective_length,
            "boundary_condition": boundary_condition
        }
    
    def stress_concentration_factor_hole(self, hole_diameter: float, plate_width: float) -> Dict[str, float]:
        """Calculate stress concentration factor for hole"""
        ratio = hole_diameter / plate_width
        
        if ratio < 0.1:
            Kt = 3.0 - 3.13 * ratio + 3.66 * (ratio ** 2) - 1.53 * (ratio ** 3)
        else:
            Kt = 2.5
        
        return {
            "stress_concentration_factor": Kt,
            "hole_diameter": hole_diameter,
            "plate_width": plate_width,
            "ratio": ratio
        }
    
    # ==================== ADVANCED DYNAMICS ====================
    
    def angular_velocity_from_torque(self, torque: float, moment_of_inertia: float, 
                                    time: float) -> Dict[str, float]:
        """Calculate angular velocity from constant torque"""
        alpha = torque / moment_of_inertia
        omega = alpha * time
        
        return {
            "angular_velocity": omega,
            "angular_acceleration": alpha,
            "torque": torque,
            "moment_of_inertia": moment_of_inertia,
            "time": time
        }
    
    def impact_energy_from_angular_velocity(self, moment_of_inertia: float, 
                                           angular_velocity: float) -> Dict[str, float]:
        """Calculate rotational kinetic energy"""
        energy = 0.5 * moment_of_inertia * (angular_velocity ** 2)
        
        return {
            "impact_energy": energy,
            "moment_of_inertia": moment_of_inertia,
            "angular_velocity": angular_velocity
        }
    
    def natural_frequency_spring_mass(self, spring_stiffness: float, mass: float) -> Dict[str, float]:
        """Calculate natural frequency of spring-mass system"""
        omega_n = math.sqrt(spring_stiffness / mass)
        f_n = omega_n / (2 * math.pi)
        
        return {
            "natural_frequency": f_n,
            "angular_frequency": omega_n,
            "spring_stiffness": spring_stiffness,
            "mass": mass
        }
    
    def centripetal_force_on_knob(self, knob_mass: float, angular_velocity: float, 
                                 knob_radius: float) -> Dict[str, float]:
        """Calculate centripetal force on rotating knob"""
        force = knob_mass * (angular_velocity ** 2) * knob_radius
        
        return {
            "centripetal_force": force,
            "knob_mass": knob_mass,
            "angular_velocity": angular_velocity,
            "knob_radius": knob_radius
        }
    
    # ==================== FLUID & THERMAL ====================
    
    def air_resistance_on_door(self, air_density: float, drag_coefficient: float, 
                              door_area: float, velocity: float) -> Dict[str, float]:
        """Calculate air resistance (drag) on door"""
        drag_force = 0.5 * air_density * drag_coefficient * door_area * (velocity ** 2)
        
        return {
            "drag_force": drag_force,
            "air_density": air_density,
            "drag_coefficient": drag_coefficient,
            "door_area": door_area,
            "velocity": velocity
        }
    
    def thermal_expansion(self, original_dimension: float, thermal_expansion_coefficient: float, 
                         temperature_change: float) -> Dict[str, float]:
        """Calculate dimensional change due to thermal expansion"""
        delta_dimension = thermal_expansion_coefficient * original_dimension * temperature_change
        
        return {
            "delta_dimension": delta_dimension,
            "new_dimension": original_dimension + delta_dimension,
            "original_dimension": original_dimension,
            "temperature_change": temperature_change
        }
    
    # ==================== CONTACT MECHANICS ====================
    
    def hertzian_contact_stress_cylinder_plane(self, force: float, effective_youngs_modulus: float, 
                                              contact_length: float, radius: float) -> Dict[str, float]:
        """Calculate Hertzian contact stress"""
        pressure_max = math.sqrt((force * effective_youngs_modulus) / (math.pi * contact_length * radius))
        
        return {
            "max_pressure": pressure_max,
            "force": force,
            "effective_youngs_modulus": effective_youngs_modulus,
            "contact_length": contact_length,
            "radius": radius
        }
    
    def bearing_friction_torque(self, friction_coefficient: float, preload_force: float, 
                               bearing_radius: float) -> Dict[str, float]:
        """Calculate friction torque in preloaded bearing"""
        torque = friction_coefficient * preload_force * bearing_radius
        
        return {
            "friction_torque": torque,
            "friction_coefficient": friction_coefficient,
            "preload_force": preload_force,
            "bearing_radius": bearing_radius
        }
    
    def seal_compression_force(self, gasket_stiffness: float, compression_distance: float, 
                              gasket_area: float) -> Dict[str, float]:
        """Calculate force needed to compress gasket seal"""
        force = gasket_stiffness * compression_distance * gasket_area
        
        return {
            "compression_force": force,
            "gasket_stiffness": gasket_stiffness,
            "compression_distance": compression_distance,
            "gasket_area": gasket_area
        }
    
    def magnetic_force_distance(self, distance: float, magnetic_constant: float = 1.0, 
                               distance_offset: float = 0.001) -> Dict[str, float]:
        """Calculate magnetic force as function of distance"""
        if distance < 0:
            force = 0
        else:
            force = magnetic_constant / ((distance + distance_offset) ** 4)
        
        return {
            "magnetic_force": force,
            "distance": distance,
            "magnetic_constant": magnetic_constant
        }
    
    # ==================== ROBOT INTERACTION ====================
    
    def breakaway_force(self, friction_coefficient_static: float, normal_force: float) -> Dict[str, float]:
        """Calculate force to overcome static friction"""
        force = friction_coefficient_static * normal_force
        
        return {
            "breakaway_force": force,
            "friction_coefficient": friction_coefficient_static,
            "normal_force": normal_force
        }
    
    def knob_rotation_torque(self, grip_force: float, knob_radius: float) -> Dict[str, float]:
        """Calculate torque to rotate knob"""
        torque = grip_force * knob_radius
        
        return {
            "rotation_torque": torque,
            "grip_force": grip_force,
            "knob_radius": knob_radius
        }
    
    def gripper_width_for_handle(self, handle_diameter: float, clearance: float = 0.005) -> Dict[str, float]:
        """Calculate gripper width needed for handle"""
        gripper_width = handle_diameter + 2 * clearance
        
        return {
            "gripper_width": gripper_width,
            "handle_diameter": handle_diameter,
            "clearance": clearance
        }
    
    # ==================== COLLISION GEOMETRY ====================
    
    def door_swept_volume(self, door_width: float, door_height: float, 
                         rotation_angle_radians: float) -> Dict[str, float]:
        """Calculate volume swept by rotating door"""
        volume = (rotation_angle_radians / (2 * math.pi)) * math.pi * (door_width ** 2) * door_height
        
        return {
            "swept_volume": volume,
            "door_width": door_width,
            "door_height": door_height,
            "rotation_angle_radians": rotation_angle_radians
        }
    
    def minimum_clearance_two_doors(self, door1_width: float, door2_width: float, 
                                   safety_clearance: float = 0.05) -> Dict[str, float]:
        """Calculate minimum clearance between two swinging doors"""
        min_clearance = door1_width + door2_width + safety_clearance
        
        return {
            "minimum_clearance": min_clearance,
            "door1_width": door1_width,
            "door2_width": door2_width,
            "safety_clearance": safety_clearance
        }
    
    # ==================== MATERIALS ====================
    
    def get_material_properties(self, material_name: str) -> Dict[str, Any]:
        """Get material properties from database"""
        material = material_name.lower()
        if material in self.material_db:
            return {
                "material": material_name,
                "properties": self.material_db[material]
            }
        
        available = list(self.material_db.keys())
        return {"error": f"Material not found. Available: {available}"}
    
    def composite_material_properties(self, material1_name: str, material2_name: str, 
                                     volume_fraction1: float) -> Dict[str, Any]:
        """Calculate composite material properties"""
        props1 = self.material_db.get(material1_name.lower())
        props2 = self.material_db.get(material2_name.lower())
        
        if not props1 or not props2:
            return {"error": "One or both materials not found"}
        
        f1 = volume_fraction1
        f2 = 1.0 - volume_fraction1
        
        composite = {
            "density": f1 * props1["density"] + f2 * props2["density"],
            "youngs_modulus": f1 * props1["youngs_modulus"] + f2 * props2["youngs_modulus"],
            "yield_strength": f1 * props1["yield_strength"] + f2 * props2["yield_strength"],
            "friction_coefficient": f1 * props1["friction_coefficient"] + f2 * props2["friction_coefficient"],
        }
        
        return {
            "material1": material1_name,
            "material2": material2_name,
            "volume_fraction1": volume_fraction1,
            "volume_fraction2": f2,
            "composite_properties": composite
        }
    
    # ==================== OPTICS ====================
    
    def reflectance_from_roughness(self, base_reflectance: float, roughness: float, 
                                  roughness_factor: float = 0.5) -> Dict[str, float]:
        """Calculate reflectance from surface roughness"""
        reflectance = base_reflectance * (1 - roughness_factor * roughness)
        reflectance = max(0.0, min(1.0, reflectance))
        
        return {
            "reflectance": reflectance,
            "base_reflectance": base_reflectance,
            "roughness": roughness,
            "roughness_factor": roughness_factor
        }
    
    def refractive_index_glass(self, glass_type: str = "standard") -> Dict[str, Any]:
        """Get refractive index for glass type"""
        indices = {
            "standard": 1.52,
            "crown": 1.52,
            "flint": 1.65,
            "dense_flint": 1.72,
            "borosilicate": 1.47,
            "quartz": 1.46,
            "sapphire": 1.77
        }
        
        index = indices.get(glass_type.lower(), 1.52)
        
        return {
            "glass_type": glass_type,
            "refractive_index": index
        }
    
    def color_temperature_to_rgb(self, temperature_kelvin: float) -> Dict[str, Any]:
        """Convert color temperature to RGB"""
        temp = temperature_kelvin / 100
        
        # Red
        if temp <= 66:
            r = 255
        else:
            r = temp - 60
            r = 329.698727446 * (r ** -0.1332047592)
        
        # Green
        if temp <= 66:
            g = temp
            g = 99.4708025861 * math.log(g) - 161.1195681661
        else:
            g = temp - 60
            g = 288.1221695283 * (g ** -0.0755148492)
        
        # Blue
        if temp >= 66:
            b = 255
        else:
            if temp <= 19:
                b = 0
            else:
                b = temp - 10
                b = 138.5177312231 * math.log(b) - 305.0447927307
        
        r = int(max(0, min(255, r)))
        g = int(max(0, min(255, g)))
        b = int(max(0, min(255, b)))
        
        return {
            "temperature_kelvin": temperature_kelvin,
            "rgb": (r, g, b),
            "hex": f"#{r:02x}{g:02x}{b:02x}"
        }
```

### Usage Examples

```python
# Create calculator instance
calc = RoboticsCalculator()

# Example 1: Calculate door mass
result = calc.mass_from_volume_density(volume=0.5, density=7850)
print(result)
# {'mass': 3925.0, 'volume': 0.5, 'density': 7850}

# Example 2: Calculate gravity torque profile
result = calc.gravity_torque_profile(mass=50, distance_to_cm=0.5)
print(result['max_torque'])
# 245.25

# Example 3: Unit conversion
result = calc.convert_units(value=45, from_unit="degrees", to_unit="radians")
print(result['converted_value'])
# 0.7853981633974483

# Example 4: Material properties
result = calc.get_material_properties("steel_mild")
print(result['properties']['density'])
# 7850

# Example 5: Composite materials
result = calc.composite_material_properties("steel_mild", "glass", volume_fraction1=0.7)
print(result['composite_properties']['density'])
# 6595.0
```

---

**Calculator Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** April 2026
