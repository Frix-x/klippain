#!/usr/bin/env python3
############################################
###### INPUT SHAPER KLIPPAIN WORKFLOW ######
############################################
# Written by Frix_x#0161 #
# @version: 2.0

# CHANGELOG:
#   v2.0: new version of this as a Python script (to replace the old bash script) and implement the newer and improved shaper plotting scripts
#   v1.7: updated the handling of shaper files to account for the new analysis scripts as we are now using raw data directly
#   v1.6: - updated the handling of shaper graph files to be able to optionnaly account for added positions in the filenames and remove them
#         - fixed a bug in the belt graph on slow SD card or Pi clones (Klipper was still writing in the file while we were already reading it)
#   v1.5: fixed klipper unnexpected fail at the end of the execution, even if graphs were correctly generated (unicode decode error fixed)
#   v1.4: added the ~/klipper dir parameter to the call of graph_vibrations.py for a better user handling (in case user is not "pi")
#   v1.3: some documentation improvement regarding the line endings that needs to be LF for this file
#   v1.2: added the movement name to be transfered to the Python script in vibration calibration (to print it on the result graphs)
#   v1.1: multiple fixes and tweaks (mainly to avoid having empty files read by the python scripts after the mv command)
#   v1.0: first version of the script based on a Zellneralex script

# Usage:
#   This script was designed to be used with gcode_shell_commands directly from Klipper
#   Parameters availables:
#      BELTS       - To generate belts diagrams after calling the Klipper TEST_RESONANCES AXIS=1,(-)1 OUTPUT=raw_data
#      SHAPER      - To generate input shaper diagrams after calling the Klipper TEST_RESONANCES AXIS=X/Y OUTPUT=raw_data
#      VIBRATIONS  - To generate vibration diagram after calling the custom (Frix_x#0161) VIBRATIONS_CALIBRATION macro



import os
import time
import glob
import sys
import shutil
import tarfile
from datetime import datetime

#################################################################################################################
RESULTS_FOLDER = os.path.expanduser('~/printer_data/config/adxl_results')
SCRIPTS_FOLDER = os.path.expanduser('~/printer_data/config/scripts')
KLIPPER_FOLDER = os.path.expanduser('~/klipper')
STORE_RESULTS = 3
#################################################################################################################

from graph_belts import belts_calibration
from graph_shaper import shaper_calibration
from graph_vibrations import vibrations_calibration

RESULTS_SUBFOLDERS = ['belts', 'inputshaper', 'vibrations']


def is_file_open(filepath):
    for proc in os.listdir('/proc'):
        if proc.isdigit():
            for fd in glob.glob(f'/proc/{proc}/fd/*'):
                try:
                    if os.path.samefile(fd, filepath):
                        return True
                except FileNotFoundError:
                    pass
    return False


def get_belts_graph():
    current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    lognames = []

    for filename in glob.glob('/tmp/raw_data_axis*.csv'):
        # Wait for the file handler to be released by Klipper
        while is_file_open(filename):
            time.sleep(3)
        
        # Extract the tested belt from the filename and rename/move the CSV file to the result folder
        belt = os.path.basename(filename).split('_')[3].split('.')[0].upper()
        new_file = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[0], f'belt_{current_date}_{belt}.csv')
        shutil.move(filename, new_file)

        # Save the file path for later
        lognames.append(new_file)
    
    # Generate the belts graph and its name
    fig = belts_calibration(lognames, KLIPPER_FOLDER)
    png_filename = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[0], f'belts_{current_date}.png')
    
    return fig, png_filename


def get_shaper_graph():
    current_date = datetime.now().strftime('%Y%m%d_%H%M%S')

    globbed_files = glob.glob('/tmp/raw_data*.csv')
    if len(globbed_files) > 1:
        print("There is more than 1 measurement.csv found in the /tmp folder. Unable to plot the shaper graphs!")
        print("Please clean the files in the /tmp folder and start again.")
        sys.exit(1)

    filename = globbed_files[0]

    # Wait for the file handler to be released by Klipper
    while is_file_open(filename):
        time.sleep(3)
    
    # Extract the tested axis from the filename and rename/move the CSV file to the result folder
    axis = os.path.basename(filename).split('_')[3].split('.')[0].upper()
    new_file = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[1], f'resonances_{current_date}_{axis}.csv')
    shutil.move(filename, new_file)
    
    # Generate the shaper graph and its name
    fig = shaper_calibration([new_file], KLIPPER_FOLDER)
    png_filename = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[1], f'resonances_{current_date}_{axis}.png')
    
    return fig, png_filename


def get_vibrations_graph(axis_name):
    current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    lognames = []

    for filename in glob.glob('/tmp/adxl345-*.csv'):
        # Wait for the file handler to be released by Klipper
        while is_file_open(filename):
            time.sleep(3)

        # Cleanup of the filename and moving it in the result folder
        cleanfilename = os.path.basename(filename).replace('adxl345', f'vibr_{current_date}')
        new_file = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[2], cleanfilename)
        shutil.move(filename, new_file)

        # Save the file path for later
        lognames.append(new_file)

    # Sync filesystem to avoid problems as there is a lot of file copied
    os.sync()

    # Generate the vibration graph and its name
    fig = vibrations_calibration(lognames, KLIPPER_FOLDER, axis_name)
    png_filename = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[2], f'vibrations_{current_date}_{axis_name}.png')
    
    # Archive all the csv files in a tarball and remove them to clean up the results folder
    with tarfile.open(os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[2], f'vibrations_{current_date}_{axis_name}.tar.gz'), 'w:gz') as tar:
        for csv_file in glob.glob(os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[2], f'vibr_{current_date}*.csv')):
            tar.add(csv_file, recursive=False)
            os.remove(csv_file)

    return fig, png_filename


# Utility function to get old files based on their modification time
def get_old_files(folder, extension, limit):
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(extension)]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files[limit:]

def clean_files():
    # Define limits based on STORE_RESULTS
    keep1 = STORE_RESULTS + 1
    keep2 = 2 * STORE_RESULTS + 1

    # Find old files in each directory
    old_belts_files = get_old_files(os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[0]), '.png', keep1)
    old_inputshaper_files = get_old_files(os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[1]), '.png', keep2)
    old_vibrations_files = get_old_files(os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[2]), '.png', keep1)

    # Remove the old belt files
    for old_file in old_belts_files:
        file_date = "_".join(os.path.splitext(os.path.basename(old_file))[0].split('_')[1:3])
        for suffix in ['A', 'B']:
            csv_file = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[0], f'belt_{file_date}_{suffix}.csv')
            if os.path.exists(csv_file):
                os.remove(csv_file)
        os.remove(old_file)
    
    # Remove the old shaper files
    for old_file in old_inputshaper_files:
        csv_file = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[1], os.path.splitext(os.path.basename(old_file))[0] + ".csv")
        if os.path.exists(csv_file):
            os.remove(csv_file)
        os.remove(old_file)

    # Remove the old vibrations files
    for old_file in old_vibrations_files:
        os.remove(old_file)
        tar_file = os.path.join(RESULTS_FOLDER, RESULTS_SUBFOLDERS[2], os.path.splitext(os.path.basename(old_file))[0] + ".tar.gz")
        if os.path.exists(tar_file):
            os.remove(tar_file)


def main():
    # Check if results folders are there or create them
    for result_subfolder in RESULTS_SUBFOLDERS:
        folder = os.path.join(RESULTS_FOLDER, result_subfolder)
        if not os.path.exists(folder):
            os.makedirs(folder)

    if len(sys.argv) < 2:
        print("Usage: plot_graphs.py [SHAPER|BELTS|VIBRATIONS]")
        sys.exit(1)

    if sys.argv[1].lower() == 'belts':
        fig, png_filename = get_belts_graph()
    elif sys.argv[1].lower() == 'shaper':
        fig, png_filename = get_shaper_graph()
    elif sys.argv[1].lower() == 'vibrations':
        fig, png_filename = get_vibrations_graph(axis_name=sys.argv[2])
    else:
        print("Usage: plot_graphs.py [SHAPER|BELTS|VIBRATIONS]")
        sys.exit(1)

    fig.savefig(png_filename)

    clean_files()
    print(f"Graphs created. You will find the results in {RESULTS_FOLDER}")


if __name__ == '__main__':
    main()
