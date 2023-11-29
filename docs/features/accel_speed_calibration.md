made by fragmon@crydteam https://www.youtube.com/@Crydteam

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/LIaPKYyOujQ/0.jpg)](https://www.youtube.com/watch?v=LIaPKYyOujQ)

# Introduction:
The macros MAX_VELOCITY_TEST, MAX_ACCEL_TEST, and BENCHMARK have been developed to test the maximum acceleration and velocity of the 3D printer along the X and Y axes. They perform a series of test movements at different acceleration and velocity values to examine the printer's performance under different settings.

## CAUTION:
Only the physical properties are being tested. These can be used, for example, for travel movements. Whether these values can be realized by the hotend must be determined separately. 

# Preparation:
- Ensure that the 3D printer is correctly set up and all axes are free to move.

# Explanation of the Macros:
## CAUTION -- The macros can only be stopped by emergency stop

## The MAX_VELOCITY_TEST 
is designed to test the maximum velocity of a 3D printer along the X and Y axes. It performs a series of test movements at different velocities, allowing you to examine the printer's performance at various speeds.

The macro uses several parameters to customize the test:

- MIN_VELOCITY: The minimum velocity at which the test should start (default: 10 mm/s).
- MAX_VELOCITY: The maximum velocity at which the test should be performed (default: 300 mm/s).
- VELOCITY_INCREMENT: The increment in velocity for each step of the test (default: 10 mm/s).
- AXIS: The axis along which the test should be performed (default: "X").
- ACCEL: The acceleration value to be used during the test (default: the printer's maximum acceleration setting).
- DISTANCE: Specifies the distance for the test movements, either "full" (default) or "short". If set to "full", the macro will use the maximum available distance on the axis; if set to "short", it will use a random distance for each test movement that ensures the specified velocity is reached.
- REPEAT: The number of back and forth movements to be performed at each velocity step (default: 5 for "DISTANCE=full", 50 for "short").

## The MAX_ACCEL_TEST 
has been developed to test the maximum acceleration of a 3D printer along the X and Y axes. It performs a series of test movements with different acceleration values, allowing you to examine the printer's performance at different acceleration rates. 

The macro uses several parameters to customize the test:

- MIN_ACCEL: The minimum acceleration at which the test should start (default: 100 mm/s^2).
- MAX_ACCEL: The maximum acceleration at which the test should be performed (default: 1000 mm/s^2).
- ACCEL_INCREMENT: The increment in acceleration for each step of the test (default: 100 mm/s^2).
- AXIS: The axis along which the test should be performed (default: "X").
- SPEED: The velocity to be used during the test (default: the printer's maximum velocity setting).
- REPEAT: The number of back and forth movements to be performed at each velocity step (50).

##  The BENCHMARK macro 
is intended to test the performance behavior of a 3D printer using a series of short and long movements. The macro allows for an extensive analysis of the printer's behavior regarding different acceleration and velocity parameters.

The macro uses the following parameters to customize the test:
- MAX_ACCEL: The maximum acceleration at which the test should be performed (default: the printer's maximum acceleration setting).
- MAX_VELOCITY: The maximum velocity at which the test should be performed (default: the printer's maximum velocity setting).
- MOVEMENTS_SHORT: The number of short movements to be performed (default: 200).
- MOVEMENTS_LONG: The number of long movements to be performed (default: 200).
- RANDOM_SEED: A seed value for random number generation to determine the positions of the movements (default: 42).
The macro starts by homing the axes and setting the Z-axis to 20. It then adjusts the printer's acceleration and velocity limits according to the given or default parameters.

After that, the macro performs the specified number of short movements. For each movement, the macro calculates a random position along the X and Y axes, ensuring that the movement stays within the valid range of each axis. It uses the given or default seed value for random generation to determine the positions. Similarly, the macro then performs the specified number of long movements, again with randomly calculated positions based on the seed value. At the end of the test, the macro performs homing of the X and Y axes again and resets the printer's velocity and acceleration limits to their original values. This macro is very useful for analyzing and optimizing the printer's behavior under different conditions, especially regarding velocity and acceleration settings. It can also be used to identify potential issues with the printer's hardware by monitoring its behavior at different velocity and acceleration parameters.

# Recommended Testing Procedure
1. Maximum Velocity
The MAX_VELOCITY_TEST macro should be executed on the X-axis. Gradually approach the maximum velocity step by step. The full distance should be used. If the printer produces "unfavorable" noises, the macro should be stopped by activating the emergency stop.
!!Caution!! Despite high noises, there may be no step loss. In case of doubt, action should be taken by listening in addition to technical detection.
The velocity that does not produce noises should be validated using the short distance. This test should then be performed analogously on the Y-axis. Note that bed-slinger printers on the Y-axis may achieve a lower velocity. The determined maximum velocity should be reduced by 20% for safety and material protection.

2. Maximum Acceleration
The MAX_ACCEL_TEST macro should be executed on the X-axis. Gradually approach the maximum acceleration step by step. This macro has an automatic self-shutdown in case of step loss. However, if the printer produces "unfavorable" noises, it should be stopped by activating the emergency stop. The acceleration that does not produce noises should be validated with a REPEAT of 200. This test should then be performed analogously on the Y-axis. Note that bed-slinger printers on the Y-axis may achieve a lower acceleration. The determined maximum acceleration should be reduced by 30% for safety and material protection.

3. Final Steps:
The values should be validated with the BENCHMARK macro. The maximum acceleration and velocity values that the printer could achieve without step loss or vibrations should be noted. The printer's settings should be updated accordingly, and the changes should be saved. Final test prints should be performed to verify print quality and performance at the determined maximum values.