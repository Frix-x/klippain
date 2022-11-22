# Adaptive bed mesh

The adaptive bed mesh is one of the most known macro of this config. It's almost like a normal bed mesh, but only "where" and "when" it's necessary.


## Description

Sometime I print small parts, sometime I print full plates and I like to get a precise bed_mesh (like 9x9 or more). However, it take a lot of time and it's useless to probe all the plate for only a small part in the middle. This is where the adaptive bed mesh is helping.

Here is how the magic happen:
  1. The coordinates of the first layer corners are extracted from the slicer (currently work with SuperSlicer, PrusaSlicer and Cura)
  2. On this area, a new set of points is computed to get at least the same precision (or better) as the original `[bed_mesh]` section. For example, if the `[bed_mesh]` section is set to 9×9 for a 300mm² bed, then it will compute for a 100mm² first layer surface a 3×3 mesh. Also if for whatever reason your parts are not in the center of the build plate (like when using a damaged PEI center), it will follow them to probe this exact area.
  3. The computed set of probed points is always odd: this allow the algorithm to compute a `relative_reference_index` point exactly in the center of the area. This point coordinates are saved in a variable if you need to use it somewhere else (like for example with the [klipper_z_calibration](https://github.com/protoloft/klipper_z_calibration) plugin and its `BED_POSITION` parameter).
  4. To go further, the adaptive bed mesh macro has also some smart features:
     - The shape of the computed mesh is not always a square and is always adapted to fit the first layer: for example, it can be something like 3×9 in case of an elongated part.
     - In case of a very small part, the algorithm can choose automatically to not do any bed mesh at all if there is less than 3×3 points to probe.
     - The macro can also choose and change automatically the interpolation algorithm between bicubic and lagrange depending of the size and shape of the mesh computed (like 3×3 vs 3×9) to always get the best precision.


## Installation

If you installed and use the full config folder of this github repository, this is already enabled by default and should work out of the box.

If you want to install it to your own custom config, here is the way to go:
  1. Copy the [adaptive_bed_mesh.cfg](./../../macros/addons/adaptive_bed_mesh.cfg) macro file directly into your own config.
  2. You need to change some settings in your slicer:
    
     - **SuperSlicer** is easy. Just change your custom g_code PRINT_START macro to add the SIZE argument like this (everything should be on one line !):

       ```
       PRINT_START [all your own things..] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]}
       ```

     - **Cura** is a bit more tricky as you need to install the post process plugin by frankbags called MeshPrintSize.py.
     
       In Cura menu, click `Help` > `Show configuration folder`. Then, copy [this python script](https://gist.github.com/frankbags/c85d37d9faff7bce67b6d18ec4e716ff#file-meshprintsize-py) into the plugins folder. Some users reported problems with newer versions of Cura, so if it's not working, try placing the script manually here: `C:\Program Files\Ultimaker Cura 5.0.0\share\cura\plugins\PostProcessingPlugin\scripts`.
     
       Then restart Cura and select in the menu: `Extensions` > `Post processing` > select `Mesh Print Size`.
     
       At the end, change your custom g_code PRINT_START macro to add the SIZE argument like this (everything should be on one line !):
     
       ```
       PRINT_START [all your own things...] SIZE=%MINX%_%MINY%_%MAXX%_%MAXY%
       ```

  3. In klipper, if it's not already the case, add and configure a `[bed_mesh]` for your machine. This will be the base on which my macro compute the new adaptive bed mesh. Keep in mind that you can (and should) push the precision a little bit further: do not hesistate to go with a mesh of 9x9 (or even more) as with my adaptive bed mesh, not all the points will be probed for smaller parts.

  4. **VERY IMPORTANT CHECKS**:
     - Check that the `BED_MESH_CALIBRATE` command is working correctly now or fix your `[bed_mesh]` section.
     - Check that the `mesh_min`, `mesh_max`, `probe_count` and `mesh_pps` config entries in your `[bed_mesh]` section are specified using **TWO numbers** as my macro is waiting for  it and will fail if there is only one specified. Something like this is ok:
     
       ```
       probe_count: 9,9
       ```

  5. My macro is using the `RESPOND` command of Klipper for debugging purposes. So, you need to: either be sure there is a `[respond]` section in your config (or add it). Or, if you don't want to see the messages, delete all the `RESPOND msg=...` lines in my macro.


## Usage

There is two way to use this set of macros and do an adaptive bed mesh. Choose between the two points the one that is best for you:
    
  1. First way is the normal and easy way adapted for most of the users: in your klipper config, modify your `PRINT_START` macro definition by adding two lines of gcode. The first one is to get the `SIZE` parameter from the slicer, and the second one is to call the `ADAPTIVE_BED_MESH` macro to start the probing. Something like that will do the trick:
     
     ```
     {% set FL_SIZE = params.SIZE|default("0_0_0_0")|string %}
     ADAPTIVE_BED_MESH SIZE={FL_SIZE}
     ```

  2. Second way is for power users that also use the [klipper_z_calibration](https://github.com/protoloft/klipper_z_calibration) plugin and want to do the bed mesh **after** the Z calibration procedure: in your klipper config, modify your `PRINT_START` macro definition by adding some gcode lines. First you need to get the `SIZE` parameter from the slicer and then call the `COMPUTE_MESH_PARAMETERS` macro with it like so:

     ```
     {% set FL_SIZE = params.SIZE|default("0_0_0_0")|string %}
     COMPUTE_MESH_PARAMETERS SIZE={FL_SIZE}
     ```
             
     Then you need to call **in an another macro** the `CALIBRATE_Z` command with the computed mesh center point:

     ```
     {% set mesh_center = printer["gcode_macro _ADAPTIVE_MESH_VARIABLES"].mesh_center %}
     CALIBRATE_Z BED_POSITION={mesh_center}
     ```

     Finally, do a simple call to `ADAPTIVE_BED_MESH` whenever you want to effectively do the mesh.

     The *in an another macro* point is very important due to the way klipper is working and you will have troubles if you do not do this. For example, you can do it directly like me in the [CALIBRATE_Z overide](./../../macros/base/homing/z_calibration.cfg).


## FAQ

#### Error: !! Malformed command 'CALIBRATE_Z BED_POSITION=(0, 0)'
This is the most common issue and is in fact due to the way Klipper and the Jinja templates are working: the templates are evaluated at the beginning of every macro call to "generate" raw gcode. Then, this generated gcode is read and executed directly as-is by Klipper. This means that after the template is evaluated and the gcode generated, no more computation and/or memory access is done during the gcode execution.

So basically, when you start a macro (like your `START_PRINT`), Klipper is rendering the Jinja template by accessing all the variables and so on and replace everything with their current value. If we speak about the `mesh_center`, this variable is not already computed at this time and the result will be `(0, 0)`. Then if you do some computation in the macro like `COMPUTE_MESH_PARAMETERS`, the gecode already generated will not be replaced (but will be in a next macro call). So in order to access it, you need to start a new macro that will render the template and generate gcode **after** having computed the mesh parameters. 

I don't know if I managed to explain clearly what happens in Klipper, but here is how to solve the issue: move the following two lines in another macro that is called **after** `COMPUTE_MESH_PARAMETERS`. You can also integrate this logic directly in the `CALIBRATE_Z` overide as I've done: [see here](./../../macros/base/homing/z_calibration.cfg).

```
{% set mesh_center = printer["gcode_macro _ADAPTIVE_MESH_VARIABLES"].mesh_center %}
CALIBRATE_Z BED_POSITION={mesh_center}
```


## Partnerships

I've got some youtube coverage on that topic:
  - From Tom's Basement in french: [Votre Bed Mesh plus RAPIDE et plus PRECIS avec Klipper ? La macro qu'il vous faut absolument !](https://youtu.be/fhfAhPH-y7M)
