The purpose of this document is to explain the purpose of the brush center offset variable in variables.cfg.

The brush center offset takes the brush center and moves it in the direction of the brush normal by the specified amount. 
This is useful for avoiding brush strokes that would cause the toolhead to crash into something or otherwise cause undesired affects. 
One example (and the impetus for this feature) is the case in which one has a brush and a gantry-mounted depressor for a filament cutter on the same side of the gantry. If nozzle cleaning is perform with filament loaded and the brush strokes occur in the same space as the depressor, then the filament cutter is actuated (repeatedly) which results in unnecessary wear and unwanted filament cutting.
One could simply move the center of the brush away from the depressor, but this would cause the nozzle to leave the brush and be wasted motion.

How it works:
The brush center should be set as normal in the variables.cfg file. The brush center offset should be set to a value (in mm) that will prevent the toolhead from crashing into anything.
The brush size is provided to accomodate different brush sizes and is used to calculate the brush stroke distance.

For example, if the variable_brush_xyz is set to (40, 250, 2) and the variable_brush_center_offset is set to 10, then the new brush center will be (50, 250, 2). 
This will create the following brush action:

	|-----------------------------|---------------|--------------|
       left			    center     center + offset     right
	    					      ^ nozzle starts here
					              ---------------> first brush stroke direction {(brush size/2) - brush center offset}
		         <-------------------------------------------- n brush stroke direction {(brush size/2)}
		         --------------------------------------------> n+1 brush stroke direction {(brush size/2)}

If variable_brush_center_offset is set to -10, then the new brush center will be (30, 250, 2) and the nozzle will start to the left of the center and do the mirror of the above brush action.

Therefore, this allows the nozzle brushing action to occur entirely with the brush with no wasted motion or unwanted interactions with other components.
