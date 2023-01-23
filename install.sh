#!/bin/bash

set -eu

CONFIG_PATH="$(realpath -e ${HOME}/printer_data/config)"
BACKUP_PATH="${HOME}/.klipper_config_backup_$(date +'%Y%m%d%H%M%S')"

# Step 1: Verify Klipper installation
check_klipper()
{
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F 'klipper.service')" ]; then
        echo "Klipper service found."
    else
        echo "Klipper service not found, please install Klipper first!"
        exit -1
    fi
}

# Step 2: backup current Klipper configuration
backup_config()
{
    echo "Backup current Klipper configuration..."
    mv -f ${CONFIG_PATH} ${BACKUP_PATH}
}

# Step 3: install the new configuration files
install_new_config()
{
    echo "Install new Klipper configuration..."
    mkdir -p ${CONFIG_PATH}

    for name in config macros scripts; do
        ln -fsv ${SRCDIR}/$name ${CONFIG_PATH}/$name
    done
    cp -frv ${SRCDIR}/adxl_results ${CONFIG_PATH}/

    for name in mcus.cfg overrides.cfg printer.cfg moonraker.conf variables.cfg save_variables.cfg; do
        if [ -f "${BACKUP_PATH}/$name" ]; then
            cp -fav ${BACKUP_PATH}/$name ${CONFIG_PATH}/$name
        else
            cp -fav ${SRCDIR}/$name ${CONFIG_PATH}/$name
        fi
    done
}

# Step 4: restarting Klipper
restart_klipper()
{
    echo "Restarting Klipper..."
    sudo systemctl restart klipper
}

# Helper functions
verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

# Find SRCDIR from the pathname of this script
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

# Run steps
verify_ready
backup_config
install_new_config
restart_klipper
