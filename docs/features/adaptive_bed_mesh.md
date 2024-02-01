# Adaptive bed mesh

The adaptive bed mesh is one of the most known macro of this config. It's almost like a normal bed mesh, but only "where" and "when" it's necessary.


## Description

Sometime I print small parts, sometime I print full plates and I like to get a precise bed_mesh (like 9x9 or more). However, it take a lot of time and it's useless to probe all the plate for only a small part in the middle. This is where the adaptive bed mesh is helping.

Here is how the magic happen:
  1. The coordinates of the first layer corners are extracted either from the slicer (currently work with SuperSlicer, PrusaSlicer and Cura) or (since v3.0) directly from the `[exclude_object]` tags of Klipper
  2. On this area, a new set of points is computed to get at least the same precision (or better) as the original `[bed_mesh]` section. For example, if the `[bed_mesh]` section is set to 9×9 for a 300mm² bed, then it will compute for a 100mm² first layer surface a 3×3 mesh. Also if for whatever reason your parts are not in the center of the build plate (like when using a damaged PEI center), it will follow them to probe this exact area.
  3. To go further, the adaptive bed mesh macro has also some smart features:
     - The shape of the computed mesh is not always a square and is always adapted to fit the first layer: for example, it can be something like 3×9 in case of an elongated part.
     - In case of a very small part, the algorithm can choose automatically to not do any bed mesh at all if there is less than 3×3 points to probe. If this behavior is not wanted because of a very bad bed, a mesh can still be forced using the `FORCE_MESH=1` parameter.
     - The macro can also choose and change automatically the interpolation algorithm between bicubic and lagrange depending of the size and shape of the mesh computed (like 3×3 vs 3×9) to always get the best precision.


## Installation

If you installed and use the full config folder of this github repository, this is already enabled by default and should work out of the box.

If you want to install it to your own custom config, here is the way to go:
  1. Copy the [adaptive_bed_mesh.cfg](./../../macros/calibration/adaptive_bed_mesh.cfg) macro file directly into your own config and include it.
  2. The macro needs the bounding box of the first layer to be able to compute a mesh on this surface. There is now two way to get it. Choose the one you prefer for your setup:

      - **Method 1. It's the most easy way** as you have nothing to do beside activating the `[exclude_object]` mechanisms of Moonraker and Klipper. To proceed, you can follow the excellent [Exclude Objects guide from the Mainsail team](https://docs.mainsail.xyz/overview/features/exclude-objects). Then you can go to step 3.

        This method of extracting data was derived from [Kyleisah KAMP repository](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging). Many thanks to him for the idea!
      
        Please note that only G-Code files that have been prepared accordingly will be able to use the adaptive mesh feature. For old and unprocessed files, a normal bed mesh will be automatically applied instead.

      - **Method 2. If you want to do it the manual way**, you will need to change some settings in your slicer:

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

> Please note that using the `[exclude_object]` tags (method 1) is a little bit less precise than using the original "SIZE" parameter (method 2) as the `[exclude_object]` tags are using the full parts sizes (not only the first layer). So if you do a part with large overhangs, it will do a large mesh using the tags but will only mesh the base of the part with the SIZE parameter. Also, if you add a skirt around the parts or use a purge tower (like MMU/ERCF users), there is no tags associated to this and the mesh can be a little bit smaller and lead to bad adhesion of these objects. So my advice is: use the [exclude_object] tags method for a new installation as it's much more easier to install. But if you are updating from an older version of the macro or use an MMU, use the SIZE parameter!

  3. In klipper, if it's not already the case, add and configure a `[bed_mesh]` for your machine. This will be the base on which my macro compute the new adaptive bed mesh. Keep in mind that you can (and should) push the precision a little bit further: do not hesistate to go with a mesh of 9x9 (or even more) as with my adaptive bed mesh, not all the points will be probed for smaller parts.

  4. **VERY IMPORTANT CHECKS**:
     - Check that the `BED_MESH_CALIBRATE` command is working correctly now or fix your `[bed_mesh]` section.
     - Check that the `mesh_min`, `mesh_max`, `probe_count` and `mesh_pps` config entries in your `[bed_mesh]` section are specified using **TWO numbers** as my macro is waiting for it and will fail if there is only one specified. Something like this is ok:

       ```
       probe_count: 9,9
       ```

  5. My macro is using the `RESPOND` command of Klipper for debugging purposes. So, you need to: either be sure there is a `[respond]` section in your config (or add it). Or, if you don't want to see the messages, delete all the `RESPOND msg=...` lines.


## Usage


<details>
<summary>Using Exclude Objects</summary>
In your klipper config, modify your `PRINT_START` macro definition by calling the `ADAPTIVE_BED_MESH` macro when you want to start the probing:

     ```
     ADAPTIVE_BED_MESH
     ```

</details>

<details>
<summary>Using the SIZE parameter from the slicer</summary>
In your klipper config, modify your `PRINT_START` macro definition by adding two lines of gcode. The first one is to get the `SIZE` parameter from the slicer, and the second one is to call the `ADAPTIVE_BED_MESH` macro to start the probing. Something like that will do the trick:

     ```
     {% set FL_SIZE = params.SIZE|default("0_0_0_0")|string %}
     ADAPTIVE_BED_MESH SIZE={FL_SIZE}
     ```

</details>


Regarding the parameters availables, you can use them either when calling the `ADAPTIVE_BED_MESH` macro or the `COMPUTE_MESH_PARAMETERS` macro. Please see this table for details:

| parameters | default value | description |
|-----------:|---------------|-------------|
|SIZE||"xMin_yMin_xMax_yMax" of the zone you want to do the mesh. Usually this is coming automatically from the slicer but this can still be used mannually when you want to call the adaptive mesh macro by hand (not during a print)|
|MARGIN|5|margin in mm to add around the first layer for the probing area|
|FORCE_MESH|0|force a 3×3 mesh even for very small parts (when less than 3×3 points are computed)|


## Partnerships

I've got some youtube coverage on that topic:
  - From Tom's Basement in french: [Votre Bed Mesh plus RAPIDE et plus PRECIS avec Klipper ? La macro qu'il vous faut absolument !](https://youtu.be/fhfAhPH-y7M)
