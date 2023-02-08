#!/usr/bin/env bash
#################################################
###### AUTOMATED INSTALL AND UPDATE SCRIPT ######
#################################################
# Written by yomgui1 & Frix_x
# @version: 1.0

# CHANGELOG:
#   v1.0: first version of the script to allow a peaceful install and update ;)


# Where the user Klipper config is located (ie. the one used by Klipper to work)
USER_CONFIG_PATH="$(realpath -e ${HOME}/printer_data/config)"
# Where to clone Frix-x repository config files (read-only and keep untouched)
FRIX_CONFIG_PATH="${HOME}/frix-x_config"
# Path used to store backups when updating (backups are automatically dated when saved inside)
BACKUP_PATH="${HOME}/frix-x_config_backups"


set -eu

# Step 1: Verify that the script is not run as root and Klipper is installed
function preflight_checks {
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not be run as root"
        exit -1
    fi

    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F 'klipper.service')" ]; then
        echo "Klipper service found! Continuing..."
    else
        echo "Klipper service not found, please install Klipper first!"
        exit -1
    fi
}

# Step 2: Check if the git config folder exist (or download it)
function check_download {
    local frixtemppath frixreponame
    frixtemppath="$(dirname ${FRIX_CONFIG_PATH})"
    frixreponame="$(basename ${FRIX_CONFIG_PATH})"

    if [ ! -d "${FRIX_CONFIG_PATH}" ]; then
        echo "Downloading Frix-x configuration folder..."
        
        if git -C $frixtemppath clone https://github.com/Frix-x/klipper-voron-V2.git $frixreponame; then
            chmod +x ${FRIX_CONFIG_PATH}/install.sh
            echo "Download complete!"
        else
            echo "Download of Frix-x configuration folder from https://github.com/Frix-x/klipper-voron-V2.git failed!"
            exit -1
        fi 
    else
        echo "Frix-x configuration folder found!"
    fi
}

# Step 3: Backup the old Klipper configuration
function backup_config {
    echo "Backup your old configuration files... You will find them in: ${BACKUP_DIR}"
    if [ ! -d "${BACKUP_PATH}" ]; then
        mkdir ${BACKUP_PATH}
    fi
    mv -f ${USER_CONFIG_PATH}/*.cfg ${BACKUP_DIR}
    mv -f ${USER_CONFIG_PATH}/*.conf ${BACKUP_DIR}
    mv -f ${USER_CONFIG_PATH}/.VERSION ${BACKUP_DIR}
}

# Step 4: Put the new configuration files in place to be ready to start
function install_config {
    echo "Installing the new Frix-x Klipper configuration..."
    mkdir -p ${USER_CONFIG_PATH}

    # Symlink Frix-x config folders (read-only repository) to the user's config directory
    for dir in config macros scripts moonraker; do
        ln -fs ${FRIX_CONFIG_PATH}/$dir ${USER_CONFIG_PATH}/$dir
    done

    # Copy the ADXL results from the last backup to restore them to the user's config directory
    if [ -d "${BACKUP_DIR}/adxl_results" ]; then
        cp -fa ${BACKUP_DIR}/adxl_results ${USER_CONFIG_PATH}/
    fi

    # Copy custom user's config files from the last backup to restore them to their config directory (or install templates)
    cp -fa ${BACKUP_DIR}/*.cfg ${USER_CONFIG_PATH}
    cp -fa ${BACKUP_DIR}/*.conf ${USER_CONFIG_PATH}
    for file in mcus.cfg overrides.cfg printer.cfg moonraker.conf variables.cfg save_variables.cfg; do
        if [ ! -f "${USER_CONFIG_PATH}/$file" ]; then
            cp -fa ${FRIX_CONFIG_PATH}/user_templates/$file ${USER_CONFIG_PATH}/$file
        fi
    done

    # CHMOD the scripts to be sure they are all executables (Git should keep the modes on files but it's to be sure)
    chmod +x ${FRIX_CONFIG_PATH}/install.sh
    for file in graph_vibrations.py plot_graphs.sh; do
        chmod +x ${FRIX_CONFIG_PATH}/scripts/$file
    done

    # Create or update the config version tracking file
    cd ${FRIX_CONFIG_PATH}
    git rev-parse HEAD > ${FRIX_CONFIG_PATH}/.VERSION
}

# Step 5: restarting Klipper
function restart_klipper {
    echo "Restarting Klipper..."
    sudo systemctl restart klipper
}


BACKUP_DIR="${BACKUP_PATH}/config_$(date +'%Y%m%d%H%M%S')"

# Run steps
preflight_checks
check_download
backup_config
install_config
restart_klipper
