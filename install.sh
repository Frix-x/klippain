#!/usr/bin/env bash
#################################################
###### AUTOMATED INSTALL AND UPDATE SCRIPT ######
#################################################
# Written by yomgui1 & Frix_x
# @version: 1.0

# CHANGELOG:
#   v1.0: first version of the script to allow a peaceful install and update ;)


# Where the user Klipper config is located (ie. the one used by Klipper to work)
KLIPPER_PATH="${HOME}/klipper"
KLIPPER_CONFIG_PATH="${HOME}/klipper_config"
USER_CONFIG_PATH="$(realpath -e ${HOME}/printer_data/config)"
# Where to clone Frix-x repository config files (read-only and keep untouched)
FRIX_CONFIG_PATH="${HOME}/frix-x_config"
# Where to clone ERCF-Software-V3 repository config files (read-only and keep untouched)
ERCF_SOFTWARE_V3 _PATH="${HOME}/ERCF-Software-V3"
# Path used to store backups when updating (backups are automatically dated when saved inside)
BACKUP_PATH="${HOME}/frix-x_config_backups"


set -eu
export LC_ALL=C

prompt_yn() {
    while true; do
        read -p "$@ (y/n)?" yn
        case "${yn}" in
            Y|y|Yes|yes)
        echo "y" 
                break;;
            N|n|No|no)
        echo "n" 
                break;;
            *)
        ;;
        esac
    done
}

INSTALL_OPTIONS=0
while getopts "e" arg; do
    case $arg in
        e) INSTALL_ERCF=1;;
    esac
done

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
    if [ ! -d "${KLIPPER_PATH}" ]; then
        echo -e "${ERROR}Klipper home directory (${KLIPPER_PATH}) not found."
        exit -1
    fi
    if [ ! -d "${KLIPPER_CONFIG_PATH}" ]; then
        if [ ! -d "${PRINTER_DATA_CONFIG_PATH}" ]; then
            echo -e "${ERROR}Klipper config directory (${KLIPPER_CONFIG_PATH} or ${USER_CONFIG_PATH}) not found."
            exit -1
        fi
        KLIPPER_CONFIG_PATH="${USER_CONFIG_PATH}"
    fi
}

# Step 2: Check if the git configs folders exist (or download it) if necessary
function check_download {
    local frixtemppath frixreponame ercfrepopath ercfreponame
    frixtemppath="$(dirname ${FRIX_CONFIG_PATH})"
    frixreponame="$(basename ${FRIX_CONFIG_PATH})"
    ercfrepopath="$(dirname ${ERCF_SOFTWARE_V3 _PATH})"
    ercfreponame="$(basename ${ERCF_SOFTWARE_V3 _PATH})"

    if [ ! -d "${FRIX_CONFIG_PATH}" ]; then
        echo "Downloading Frix-x configuration folder..."
        if git -C $frixtemppath clone https://github.com/Frix-x/klipper-voron-V2.git $frixreponame; then
            chmod +x ${FRIX_CONFIG_PATH}/install.sh
            echo "Download complete!"
        else
            echo "Download of Frix-x configuration git repository failed!"
            exit -1
        fi
    else
        echo "Frix-x git repository folder found locally!"
    fi

    echo
    echo -e "Do you use an ERCF and do you want to use ERCF Software V3...${INPUT}"
    echo
    case $yn in
        y)
            if [ ! -d "${ERCF_SOFTWARE_V3 _PATH}" ]; then
                echo "Downloading ERCF Software V3 configuration folder..."
                if git -C $ercfrepopath clone https://github.com/moggieuk/ERCF-Software-V3.git $ercfreponame;
                    echo "Download complete!"
                else
                    echo "Download of ERCF Software V3 configuration git repository failed!"
                    exit -1
                fi
            else
                echo "ERCF Software V3 git repository folder found locally!"
            fi
            ;;
        n)
            exit -1
    esac
}

# Step 3: Backup the old Klipper configuration
function backup_config {
    mkdir -p ${BACKUP_DIR}

    if [ -f "${USER_CONFIG_PATH}/.VERSION" ]; then
        echo "Frix-x configuration already in use: only a backup of the custom user cfg files is needed"
        find ${USER_CONFIG_PATH} -type f -regex '.*\.\(cfg\|conf\|VERSION\)' | xargs mv -t ${BACKUP_DIR}/ 2>/dev/null
    else
        echo "New installation detected: a full backup of the user config folder is needed"
        cp -fa ${USER_CONFIG_PATH} ${BACKUP_DIR}
    fi

    echo "Backup done in: ${BACKUP_DIR}"
}

# Step 4: Put the new configuration files in place to be ready to start
function install_config {
    echo "Installation of the last Frix-x Klipper configuration files"
    mkdir -p ${USER_CONFIG_PATH}

    # Symlink Frix-x config folders (read-only git repository) to the user's config directory
    for dir in config macros scripts moonraker; do
        ln -fsn ${FRIX_CONFIG_PATH}/$dir ${USER_CONFIG_PATH}/$dir
    done

    # Copy custom user's config files from the last backup to restore them to their config directory (or install templates if it's a first install)
    if [ -f "${BACKUP_DIR}/.VERSION" ]; then
        echo "Update done: restoring user config files now!"
        find ${BACKUP_DIR} -type f -regex '.*\.\(cfg\|conf\)' | xargs cp -ft ${USER_CONFIG_PATH}/
    else
        echo "New installation detected: default config templates will be set in place!"
        cp -fa ${FRIX_CONFIG_PATH}/user_templates/* ${USER_CONFIG_PATH}/
    fi

    # CHMOD the scripts to be sure they are all executables (Git should keep the modes on files but it's to be sure)
    chmod +x ${FRIX_CONFIG_PATH}/install.sh
    for file in graph_vibrations.py plot_graphs.sh; do
        chmod +x ${FRIX_CONFIG_PATH}/scripts/$file
    done

    # Create the config version tracking file in the user config directory
    git -C ${FRIX_CONFIG_PATH} rev-parse HEAD > ${USER_CONFIG_PATH}/.VERSION
}

# Step 5: Put the ercf plugin files in place to be ready to use if ERCF Software V3
function link_ercf_plugin() {
    if [ "${INSTALL_ERCF}" -eq 1 ]; then
        if [ -d "${ERCF_SOFTWARE_V3 _PATH}" ]; then
            echo -e "Linking ercf extension to Klipper..."
            if [ -d "${KLIPPER_HOME}/klippy/extras" ]; then
                for file in `cd ${ERCF_SOFTWARE_V3 _PATH}/extras ; ls *.py`; do
                    ln -sf "${ERCF_SOFTWARE_V3 _PATH}/extras/${file}" "${KLIPPER_HOME}/klippy/extras/${file}"
                done
            else
                echo -e "ERCF modules not installed because Klipper 'extras' directory not found!"
            fi
        fi
    fi
}

# Step 6: restarting Klipper
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
link_ercf_plugin
restart_klipper

echo "Everything is ok, Frix-x config installed and up to date!"