#!/usr/bin/env python3

##########################################
###### BASIC SERVICE RESTART SCRIPT ######
##########################################

# Be sure to make this script executable using SSH: type 'chmod +x ./service_restart.py' when in the folder !

# List of services to be checked/restarted
services = ['KlipperScreen']

#####################################################################
################ !!! DO NOT EDIT BELOW THIS LINE !!! ################
#####################################################################

import subprocess

def check_service(service_name):
    # Command to check if the service is active
    cmd = ['systemctl', 'is-active', service_name]
    
    # Run the command and capture the output
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
        return True  # Service is active
    except subprocess.CalledProcessError:
        return False  # Service is not active or doesn't exist

def restart_service(service_name):
    # Command to restart the service
    cmd = ['systemctl', 'restart', service_name]
    
    # Run the command
    subprocess.run(cmd, check=True)

for service_name in services:
    # Check if service(s) exist and restart
    if check_service(service_name):
        restart_service(service_name)
        print(f"{service_name} service successfully restarted.")
    else:
        print(f"{service_name} service doen't exist.")
