# <u>mmu details for correct install</u>
before installing Happy-Hare V2 you must

Uninstall the old ercf ERCF-Software-V3 (if you already have it):
1. backup your old ercf_***.cfg files for future reference,
1. Cleanly REMOVE ERCF-Software-V3:
```
~/ERCF-Software-V3/install.sh -u
rm -rf ~/ERCF-Software-V3
```

and install the "new" Happy Hare V2 by following instructions in https://github.com/moggieuk/Happy-Hare:
```
cd ~
git clone https://github.com/moggieuk/Happy-Hare.git
cd Happy-Hare

./install.sh -i
```

Finally, Klippain requires a few simple steps to configure and customize it for your printer: please follow the [configuration guide](./configuration.md).

----
‎ 
# <u>Some loose details:</u>

- <u>MMU check Gates on Start Print:</u>

I recommend to set your `variable_mmu_check_gates_on_start_print` to `True` in your Klippain `variables.cfg` file.  
But take in mind that you also must add in your slicer start g_code the parameter `TOOLS_USED=!referenced_tools!` used by the [HHv2 moonraker gcode preprocessor](https://github.com/moggieuk/Happy-Hare/blob/main/doc/gcode_preprocessing.md). Otherwise, only the INITIAL TOOL will be checked and if the gates used have previously been marked as empty an error may occur during printing!!!

- <u>some exemple of HHv2 errors:</u>

![img](images/mmu/HHv2emptygate.PNG)  
<details>
<summary><sub>🔹 Read more about this error...</sub></summary>

If the gate is "correctly" loaded and this error appears, this is generally due to the fact that the gate was previously marked as empty and its state has not been updated.
To correct during print for example you can use the command: `MMU_GATE_MAP GATE=1 AVAILABLE=1` (adapt for your GATE number...)

a good practice is to check the gates state after make changes in filaments with the command `MMU_GATE_MAP` to be sure all your setup is correct.  
The command `MMU_CHECK_GATES` can update the MAP for all MMU gates. But you can also use for exemple `MMU__CHECK_GATES GATE="0 2 5"` to check only gates 0, 2 and 5