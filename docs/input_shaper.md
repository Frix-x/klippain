# Tuning Klipper's Input Shaper system

As more and more people use my macros, questions about interpreting the resonnance testing results arise. This document aims to provide some guidance on how to interpret them. Keep in mind that there is no universal method: different people may interpret the results differently or could have other opinions. It's important to experiment and find what works best for your own 3D printer.


## Understanding ringing
When a 3D printer moves, the motors apply some force to move the toolhead along a precise path. This force is transmitted from the motor shaft to the toolhead through the entire printer motion system. When the toolhead reaches a sharp corner and needs to change direction, its inertia makes it want to continue the movement in a straight line. The motors force the toolhead to turn, but the belts act like springs, allowing the toolhead to oscillate in the perpendicular direction. These oscillations produce visible artifacts on the printed parts, known as ringing or ghosting.

![](./images/IS_docs/ghosting.png)


## Reading the graphs

When tuning Input Shaper, keep the following in mind:
  1. **Focus on the shape of the graphs, not the exact numbers**. There could be differences between ADXL boards or even printers, so there is no specific "target" value. This means that you shouldn't expect to get the same graphs between different printers, even if they are similar in term of brand, parts, size and assembly.
  1. Small differences between consecutive test runs are normal, as ADXL quality and sensitivity is quite variable between boards.
  1. Perform the tests when the machine is heat-soaked and close to printing conditions, as belt tension can change with temperature.
  1. Avoid running the toolhead fans during the tests, as they introduce unnecessary noise to the graphs, making them harder to interpret. This means that even if you should heatsoak the printer, you should also refrain from activating the hotend heater during the test, as it will also trigger the hotend fan. However, as a bad fan can introduce some vibrations, feel free to use the test to diagnose an unbalanced fan as seen in the [Examples of Input Shaper graphs](#examples-of-input-shaper-graphs) section.
  1. Ensure the accuracy of your ADXL measurements by running a `MEASURE_AXES_NOISE` test and checking that the result is below 100 for all axes. If it's not, check your ADXL and wiring before continuing.
  1. The graphs can only show symptoms of possible problems and in different ways. Those symptoms can sometimes suggest causes, but they rarely pinpoint issues.
  1. Remember why you're running these tests (clean prints) and **don't become too obsessive over perfect graphs.** 

[Belt Shaper Graphs](./belt_shaper.md) 

[Input Shaper Graphs](./input_shaper_graphs.md)

[vibrations Graphs] coming soon


## Theory behind it

### Modeling the motion system
The motion system of a 3D printer can be described as a spring and mass system, best modeled as a [harmonic oscillator](https://en.wikipedia.org/wiki/Harmonic_oscillator). This type of system has two key parameters:

| Schematics | Undamped resonnant frequency<br />(natural frequency) | Damping ratio ζ |
| --- | --- | --- |
| ![](./images/IS_docs/harmonic_oscillator.png) | $$\frac{1}{2\pi}\sqrt{\frac{k}{m}}$$ | $$\frac{c}{2}\sqrt{\frac{1}{km}}$$ |
| See [here for examples](https://beltoforion.de/en/harmonic_oscillator/) | `k` [N/m]: spring constant<br />`m` [g]: moving mass | `c` [N·s/m]: viscous damping coefficient<br />`k` [N/m]: spring constant<br />`m` [g]: moving mass |

When an oscillating input force is applied at a resonant frequency (or a Fourier component of it) on a dynamic system, the system will oscillate at a higher amplitude than when the same force is applied at other, non-resonant frequencies. This is called a resonance and can be dangerous for some systems but on our printers this will mainly lead to vibrations and oscillations of the toolhead.

On the other hand, the damping ratio (ζ) is a dimensionless measure describing how oscillations in a system decay after a perturbation. It can vary from underdamped (ζ < 1), through critically damped (ζ = 1) to overdamped (ζ > 1).

In 3D printers, it's quite challenging to measure the spring constant `k` and even more challenging to measure the viscous damping coefficient `c`, as they are affected by various factors such as belts, plastic parts, frame rigidity, rails, friction, grease, and motor control. Furthermore, a 3D printer is made up of many subsystems, each with its own behavior. Some subsystems, such as the toolhead/belts system, have a bigger impact on ringing than others, such as the motor shaft resonance for example.

### How Input Shaping helps
The rapid movement of machines is a challenging control problem because it often results in high levels of vibration. As a result, machines are typically moved relatively slowly. Input shaping is an open-loop control method that allows for higher speeds of motion by limiting vibration induced by the reference command. It can also improve the reliability of the stealthChop mode of Trinamic stepper drivers.

It works by creating a command signal that cancels its own vibration, achieved by [convoluting](https://en.wikipedia.org/wiki/Convolution) specifically crafted impulse signals (A2) with the original system control signal (A1). The resulting shaped signal is then used to drive the system (Total Response). To craft these impulses, the system's undamped resonant frequency and damping ratio are used.

![](./images/IS_docs/how_IS_works.png)

Klipper measures these parameters by exciting the printer with a series of input commands and recording the response behavior using an accelerometer. Resonances can be identified on the resulting graphs by large spikes indicating their frequency and energy. Additionnaly, the damping ratio is usually unknown and hard to estimate without a special equipment, so Klipper uses 0.1 value by default, which is a good all-round value that works well for most 3D printers.
