#!/usr/bin/env python3

######################################
###### BASIC SYSTEM INFO SCRIPT ######
######################################
# Written by Frix_x#0161 #
# @version: 1.0

# CHANGELOG:
#   v1.0: first version of the script to get some system info printed in the klippy.log


# Be sure to make this script executable using SSH: type 'chmod +x ./system_info.py' when in the folder !

#####################################################################
################ !!! DO NOT EDIT BELOW THIS LINE !!! ################
#####################################################################

import subprocess
import os
import platform
from datetime import datetime
import concurrent.futures

def get_date_time():
    # Special note for power-user running Klipper inside a docker container: usually the timezone
    # is not set and this result in a print of the UTC time (instead of local). Consider running
    # the container like: "docker run -e TZ=America/New_York klipper_image"
    # in order to get a proper timezone set and get the correct time read by this script
    return datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

def check_docker():
    return os.path.exists('/.dockerenv')

def check_wsl():
    try:
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower():
                return True
    except Exception:
        pass
    return False

def get_pi_model():
    try:
        model_info = subprocess.check_output(['cat', '/sys/firmware/devicetree/base/model'], universal_newlines=True)
        if 'raspberry pi' in model_info.lower(): return model_info
    except subprocess.CalledProcessError:
        return None
    else:
        return None

def get_unknown_board_info():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Hardware') or line.startswith('Model'):
                    return line.split(':')[1].strip()
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME') or line.startswith('NAME'):
                    return line.split('=')[1].strip().strip('"')
    except Exception:
        pass

    return "no additional info..."

def get_os_kernel_info():
    uname = os.uname()
    return uname.sysname, uname.release, uname.machine

def get_ram_info():
    try:
        total_ram = subprocess.check_output(['free', '-m'], universal_newlines=True).split('\n')[1].split()[1]
        available_ram = subprocess.check_output(['free', '-m'], universal_newlines=True).split('\n')[1].split()[6]
        return total_ram, available_ram
    except subprocess.CalledProcessError:
        return None, None


def print_system_info():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_date_time = executor.submit(get_date_time)
        future_docker = executor.submit(check_docker)
        future_pi_model = executor.submit(get_pi_model)
        future_wsl = executor.submit(check_wsl)
        future_os_kernel = executor.submit(get_os_kernel_info)
        future_ram_info = executor.submit(get_ram_info)


    date_time = future_date_time.result()
    print(f"Klippain started ({date_time})")

    sysname, release, machine = future_os_kernel.result()
    print(f"Operating System: {sysname} - {release}")


    is_docker = future_docker.result()
    is_wsl = future_wsl.result()
    pi_model = future_pi_model.result()

    if is_docker:
        print(f"Machine: {machine} - in a docker container")
    elif is_wsl:
        print(f"Machine: {machine} - in Windows Subsystem for Linux")
    elif pi_model is not None:
        print(f"Machine: {machine} - in a {pi_model}")
    else:
        # This is the case where it is running on a unknown machine type
        # so we use the specific function to try to gather more info...
        print(f"Machine: {machine}")
        print(f"System information: {get_unknown_board_info()}")


    total_ram, available_ram = future_ram_info.result()
    if total_ram is None or available_ram is None:
        print("RAM information not found...")
    else:
        print(f"Used RAM: {available_ram}/{total_ram} MB")


if __name__ == "__main__":
    print_system_info()
