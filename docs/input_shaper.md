# Input shaper first aid

For a few months now, my macros have been used by a lot of people. But the more people use them, the more questions I get about how to interpret the results. So here is my take on how to interpret the graphs.

Disclaimer: there is no universal method. What is written in this documentation is my own take on the subject. Other people may think differently, and that's fine, it doesn't mean they're wrong, nor that I'm the only one who knows the truth. So think about it, try it by yourself, and use what works for you.

<!-- add to discussion GH: ironhalik and SinisterRj -->


## Basic theory

### What is ringing?
When a printer moves, the motors apply some force to move the toolhead along a precise path. This force is transmitted from the motor shaft to the toolhead through the entire printer motion system. When the toolhead reaches a sharp corner and need to change direction, its inertia makes it want to continue the movement in a straight line. The motors will force the toolhead to turn because they have enough force to do it, but the belts will act as springs and will allow the toolhead to oscillate in the perpendicular direction. These oscillations produce visible artifacts on the printed parts, known as ringing or ghosting.

![](./images/IS_docs/ghosting.png)

### How to model it?
Your printer's motion system is basically a spring and mass system, best described as an [harmonic oscillator](https://en.wikipedia.org/wiki/Harmonic_oscillator). No need to go into much detail, the only thing you need to know is that this type of system has two important physical parameters:

| Schematics | The undamped resonnant frequency<br />or natural frequency | The damping ratio ζ |
| --- | --- | --- |
| ![](./images/IS_docs/harmonic_oscillator.png) | $$\frac{1}{2\pi}\sqrt{\frac{k}{m}}$$ | $$\frac{c}{2}\sqrt{\frac{1}{km}}$$ |
| Please have a look [here for some examples](https://beltoforion.de/en/harmonic_oscillator/) | `k` [N/m]: spring constant<br />`m` [g]: moving mass | `c` [N·s/m]: viscous damping coefficient<br />`k` [N/m]: spring constant<br />`m` [g]: moving mass |

When an oscillating input force is applied at a resonant frequency (or a Fourier component of it) on a dynamic system, the system will oscillate at a higher amplitude than when the same force is applied at other, non-resonant frequencies. This is called a resonance and can be dangerous for some systems but on our printers this will mainly lead to vibrations and oscillations of the toolhead.

On the other hand, the damping ratio (ζ) is a dimensionless measure that describes how oscillations in a system decay after a perturbation. It can vary from underdamped (ζ < 1) or undamped (ζ = 0), through critically damped (ζ = 1) or even overdamped (ζ > 1).

Let's get back to our printers: the toolhead mass can be measured as `m`, but it's difficult to measure the spring constant `k` because there are many factors that contribute to it such as belts, plastic parts, and rigidity of the frame. The viscous damping coefficient `c` is even harder to measure because it's affected by multiple factors such as the rails, friction, quantity of grease, motor control, ... Furthermore, a printer is made up of many subsystems, each with its own behavior. Some subsystems, such as the toolhead/belts system, have a bigger impact on ringing than others, such as the motor shaft resonance for example.

### How Input Shaping can help?
The rapid movement of machines is a challenging control problem because it often results in high levels of vibration. As a result, machines are typically moved relatively slowly. Input shaping is an open-loop control method that allows much higher speeds of motion by limiting vibration induced by the reference command. It can also improve the reliability of the stealthChop mode of Trinamic stepper drivers.

It works by creating a command signal that cancels its own vibration: a vibration caused by earlier parts of the command signal is cancelled by a vibration intentionally created by latter parts of the command. To do that, the algorithm is [convoluting](https://en.wikipedia.org/wiki/Convolution) specificaly crafted impulses signals (A2) with the original system control signal (A1). The resulting shaped signal is then used to drive the system (Total Response). To "craft" this impulses, we have to use the system undamped resonant frequency and damping ratio.

![](./images/IS_docs/how_IS_works.png)

Klipper has a special feature that measures these parameters by exciting the printer with a series of input commands and recording the response behavior using an accelerometer. Resonances can be identified on resulting graphs by big spikes that indicate their frequency and energy. Additionnaly, the damping ratio is usually unknown and hard to estimate without a special equipment, so Klipper uses 0.1 value by default, which is a good all-round value that works "ok" for most printers.

To use input shaper, you will need to keep a few things in mind:
  1. When interpreting the results, **don't focus too much on the numbers, but look at the shape of the graphs instead**. Indeed, there could be difference between ADXL boards and even printers, so there is no "target" value.
  2. This also means there may be small differences between consecutive runs of the test, but if they are within 1-5Hz, the results are still usable.
  3. As belt tension can change with temperature, it's best to perform the tests when the machine is heatsoaked and close to printing conditions.
  4. Don't run the toolhead fans during the test as they can add noise to the graphs and make them a little bit more difficult to read.
  5. Before starting, make sure your ADXL measurements are accurate by running a `MEASURE_AXES_NOISE` test and checking that the result is below 100 for all axes. If it's not, check your ADXL and wiring.

<details>
<summary>Special note on ADXL mounting point</summary><br />

TODO...

<!-- You need to note that Klipper input shaper algorithms works by suppressing **only one** resonnant frequency (or a range around one resonnant frequency). So we will need to select the one that has the biggest impact on the prints: the fundamental frequency or main harmonic of the toolhead/belts system. 

Yes in fact with IS we want to suppress the main harmonic. The one that have the highest amplitude and that is visible on the print. All the higher frequency things are not that much a problem on a print and doesn't need to be filtered.
However that doesn't means they are not a problem as they usually hide something else...

Be careful with this assumption. While this sentence is perfectly true, the problem is that input shaping algorithms are "dumb" and can only filter 1 resonant frequency (or two with 2_hump_ei, ...). This is done by convolving the selected filter model to the sequence of impulses fed to the X and Y stepper drivers.
So to be able to do it properly, we want to measure the main resonant frequency, the one that make the ghosting appears while printing. This one is mainly due to the moving mass (whole toolhead + aluminium extrusion in case of Y movement on our machines) and the dampening system (belts and their elasticity). So if you put the accelerometer on the toolhead center of gravity, you will measure this very precisely. However, if you put the accelerometer on the nozzle, I agree that you will have a more precise measurement (that include the main resonant frequency but also all the other vibrations due to the toolhead rotation around X, etc...). This will lead to a much more noiser graph (that basic input shaping cannot filter) and it will be more hard to see and select the correct filter.
That's why I think it's more simpler to put the accelerometer on the toolhead near its center of gravity, as it's easier to select the filter at the end for the main frequency, the one that cause the ghosting. IMHO, all the other vibrations measured at the nozzle are almost negligible compared to the ghosting 

For my part, I do not recommend the nozzle mount. However, that's my personal opinion, but here's why:
The Input Shaper system is here to suppress ringing. To do this, we use a static filter that is able to work on a very precise frequency range to directly influence the motor step control. The main frequency responsible for the ringing must therefore be found and selected in the filter config section. This specific frequency is the one corresponding to the first mode of resonance of the harmonic oscillator composed of the toolhead (mass) and the belts (spring/damper). It can be seen as follows: in a corner movement, the inertia of the toolhead at the change of direction will want to continue the movement in a straight line, then the belts will act as dampers and allow the toolhead to make some oscillations perpendicular to the second branch of the movement (this is seen as ringing/ghosting on the printed part). Then, in a second time, on top of that, there are also other resonant frequencies that can appear in the system, like the toolhead giggling on the X carriage, some loosened screws, etc.... However, all these secondary frequencies don't contribute as much to the ringing (lower amplitude) and/or are completely uncorrelated and centred on a different frequency.
Problem: With Klipper's input shaper, you need to select only one frequency to filter. Also, the resonance testing algorithms work by looking at the main and highest peak to do the automatic filter selection. This means that you want to find a way to measure just the main ringing frequency, and this is best measured at the center of gravity of the toolhead to avoid measuring everything else as well. I have to agree that measuring at the nozzle tip will get you everything on the graph and be more accurate, but it will also lead to a much noisier graph and can cause problems with the auto-selection of the algorithm or just "human interpretation". 
That's why you get cleaner curves when using the SB mount also
So here is my workflow: when I build a machine, I use the nozzle mount first to diagnose if there is some problems (like a bad X carriage, untightened screws, rattling, etc...). When the mechanics is sane and ready to go, I switch to a much closer mount to the toolhead center of gravity and use only this one to set my input shaper config settings.

Doesn't agree with that. As I already said here: nozzle mount measure everything so you get the main harmonic that you want to suppress but also all the "noise" and other smaller movements happening at this spot (that exists but doesn't influence that much on ringing).
When using the SB mount, you're closer to the center of gravity of the SB and only the main harmonic is measured. The other smaller movements are not measured and this lead to a cleaner graph.
IS can dampen only one harmonic. So you want to measure and select the heaviest

I do not say that motion at the nozzle doesn't matter. What I'm saying is that most IS algorithms are band-pass filters centered on only one frequency (ok, this is not really true for x_hump_ei filters but you don't want to use them). So it basically focus on only one harmonic -> you want to select the one that produce the most ringing on the part. This is the first harmonic of the toolhead/belts oscillator. All the other harmonics of the system have waaayyy less impact on the ringing (they do still exist and are indeed best measured at the nozzle tip). 
So my workflow is basically:
  - Measure at the nozzle tip when you wants to diagnose and solve all the mechanical problems and see exactly what happens in your machine mechanics. Try to get the graphs as best as you can from here.
  - Then, put the accelerometer as close as you can to the toolhead center of gravity to be able to measure only the main harmonic and get a clean graph with only this one (without the noise of the other that have low to no impact on the ringing). This will allow an easier reading of the graph by the automatic selection algorithm

kmobs: If the mechanical issues are solved, then they should be the same. The COG measurement doesn't matter because you don't print from cog.
Frix_x — 01/03/2023 16:42
No, you cannot suppress the second, third, etc... mode of vibration of the system. Those will stay, but again, with no real impact on the ringing. So it doesn't matter that much to get them on the graph. They will just make it more difficult to read it and the automatic selection algorithm could be lost in some case and do some mistakes. So better to avoid that IMHO 
On the other hand, I do agree that if you understand the graph well, you can find out by yourself and figure out that the frequency advice is wrong. But this is not the case for everyone here, and that's why I prefer to do this advice of COG measurement: it make things easier for them -->

</details>


## Tuning Klipper's Input Shaper

<details>
<summary>Checking belt tension</summary><br />

**First, make sure that the belts are properly tensioned before starting**. For example, you can follow the [Voron belt tensioning documentation](https://docs.vorondesign.com/tuning/secondary_printer_tuning.html#belt-tension). This is very important!

Then you can generate the belt graphs using my `BELTS_SHAPER_CALIBRATION` macro. You can have a look at the [IS workflow documentation](./features/is_workflow.md) for more info. 

On this graph, you want both curves to look similar and overlap to form only one curve. Try to make them fit as best as possible. It's not a problem if you have "noise" around the main peak, but it should be present on both curves with a similar amplitude. As you proceed, keep in mind that when you tighten a belt, its main peak should move diagonally to the upper right corner, moving "a lot" in amplitude and "a little" in frequency. Also, you can check the magnitude order of the main peaks as they *usually* range from ~100k to ~1M on most machines.

The resonant frequency/amplitude of the curves will depend mainly on three parameters (and the actual tension):
  - the *mass of the toolhead*, which is the same for both belts, so this has no effect here
  - the *belt "elasticity"*, which evolve over time as the belt wears. You must use the **same belt brand and type** for both A and B belts and have them **installed at the same time**
  - the *belt path length*, that's why they must have the **exact same number of teeth** so that one belt path is not longer than the other when tightened at the same tension

**If these three parameters are met, there is no way that the curves could be different** or you can be sure that there is an underlying problem in at least one of the belt paths. Also, if the belt graphs have low amplitude curves (no nice peaks) and a lot of noise, you will probably also have bad input shaper graphs. So before you continue, be sure to get good belt graphs or fix your belt paths. You can start by checking the belt tension, bearings, gantry screws, alignment of the belts on the idlers, etc...

Here are some examples of belt graphs:

| Comment | Belt graphs examples 1 | Belt graphs examples 2 |
| --- | --- | --- |
| **Both of these two graphs are considered good**. As you can see, the main peak doesn't have to be perfect if you can get both curves to stack | ![](./images/IS_docs/belt_graphs/perfect%20graph.png) | ![](./images/resonances_belts_example.png) |
| **These two graphs show a bad belt tension**: each time, one of the belts has not enough tension (first is B belt, second is A belt). You can start by tightening it half a turn and measure again | ![](./images/IS_docs/belt_graphs/different_tensions.png) | ![](./images/IS_docs/belt_graphs/different_tensions2.png) |
| **These two graphs show a belt path problem**: the belt tension could be OK, but something else is happening in the belt paths. You can start by checking the bearings and belt wear, or belt alignement | ![](./images/IS_docs/belt_graphs/belts_problem.png) | ![](./images/IS_docs/belt_graphs/belts_problem2.png) |

</details>


<details>
<summary>"Shaper" graphs</summary><br />

TODO...

<!-- No universal way:
Yes, this would be a good starting point to be able to compare it more easily.
But this would need to include also:
  - if using Z chains, which brand (Igus is known to provide better IS graph that AliE chains)
  - if using TAP or not (more mass but also TAP is known to add some giggling to the toolhead)
  - Which extruder ? For example the LGX normal is quite heavy and add mass
  - If using CAN bus as there is then probably an ombilical configuration. Then ombilical from where ? Top following the bowden or from the A motor plate ?
  - etc...
  - Motor type and voltage used
  - Klipper motor configuration (ie. microstepping, etc...)
  - TMC drivers used ?
This is just to say that with the market growing and the way the Voron ecosystem started to become a renown printer brand, there is everyday new products coming and it will be very difficult to get this kind of database effective and universal... 

I don't think so in fact. As their signature is mixed with the rest of the machine behavior...
But some can be seen: like the TAP giggling is something we can see clearly on the graphs

accels is not what matter, but more the shape of the graph. Basically you want a single peak, very thin and that's it.
Thing is that the max accel will depend a lot of the "rigidity" of the system and the way the toolhead will be able to follow closely the IS motor input. So this means that for that to happens, you want more rigid belts (ie. more tension and/or less length ), lower toolhead inertia (ie. lower toolhead mass), and better motor control of this (ie. beefy motor but with the less rotor inertia possible, or even switch to 48V). 
So this all depends a lot on the machine configuration and not only on the "sane mechanics" as we all have different motor, different stepping configuration, different belts and bearing brands, etc...

Insane number accel but very bad graph
Because your graph is bad so it can't give you a good suggestion
Accel numbers are worthless if you have remaining vibrations

Note on Voron TAP You're not the first one to experience this kind of trouble with the TAP (especially the first revisions). Try to reseat your magnets and validate that everything is mounted correctly to avoid any movements. Also verify that the TAP MGN is of good quality with a correct preload.
At the end, TAP is also more heavy than the standard carriage and there is some tradeoffs to use it while it makes you able to get very easy and good Z offset calibration (modifié)
120Hz on X with TAP, do not look any further. TAP is adding significant wobbling and this can be seen especially on the X graph.
Try to reseat your TAP magnets and make sure that they are proper and strong N52. And check your TAP MGN rail preload also, it's very important to have something stiff here. This can help, but keep in mind that TAP is more heavy and less rigid than a standard SB and this will definitely lead to less clean graphs

Note on extra light X Beam > bad

DON'T DO : First thing's first. Delete all the old data in your /tmp folder before making graphs. Old data can do this. Second, you should limit your data to 100Hz (anything above that point doesn't matter). You can open the .csv file in a text editor and delete lines starting with anything above 100.
> I doesn't agree with the data above 100Hz. While I agree that their effect on ringing is marginal, it can still show a mechanical issue on the machine. Do you have a specific reason to say this ? Maybe you have something specific in mind that I'm not aware of
> No, you should avoid doing that. This will not do anything beside "hiding" the problem. The second peak is still here, just not shown. 
I think it's better to work on the mechanics of the machine to solve it instead of hiding it
I do however agree that the ringing is more from the main lower frequency peak. This higher frequency bump will mostly add noise and wear to the mechanical parts: its contribution to the ringing is not so high though
But you should not ignore it > solve it

Additional point as I've seen this a couple time: Each axis have it's own properties like it's own mass (only the toolhead mass for X, but there is the aluminium extrusion additional mass for Y for example on our Voron printers). So this will lead to a different behavior of each axis and thus you will need a different filter.
Having the same input shaping value for both axis is valid only if both axis are similar mechanically. This could be true on some machines like on a H-bot configuration (Ultimaker) but it's certainly not a generality

Per the formula above, mass differences will play a role in your values, so if you have a corexy machine with identical X/Y peaks, you likely have an issue in either your machine or your measurement setup. 
  * Always measure the noise in your system with the `MEASURE_AXES_NOISE` command. If it's too high, then you need to track that down in order to ensure your measurements are accurate.  -->

</details>


<details>
<summary>"Vibrations" graphs</summary><br />

TODO...

</details>
