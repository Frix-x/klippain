#!/usr/bin/env bash

#################################################
######## AUTOMATED UNINSTALL SCRIPT #############
#################################################
# Written by Frix_x
# @version: 1.0

# CHANGELOG:
#   v1.0: first version of the script to allow an user to revert to his old config
#         in case the install script was called by error... ;)


# Where the user Klipper config is located (ie. the one used by Klipper to work)
USER_CONFIG_PATH="${HOME}/printer_data/config"
# Where Frix-x repository config files are stored (Klippain read-only files that are untouched)
FRIX_CONFIG_PATH="${HOME}/klippain_config"
# Path used to store backups when updating (backups are automatically dated when saved inside)
BACKUP_PATH="${HOME}/klippain_config_backups"
# Where the Klipper folder is located (ie. the internal Klipper firmware machinery)
KLIPPER_PATH="${HOME}/klipper"


set -eu
export LC_ALL=C

# Step 1: Verify that the script is not run as root and Klipper is installed.
#         Then warn and ask the user if he is sure to proceed to revert to his old config
function preflight_checks {
    if [ "$EUID" -eq 0 ]; then
        echo "[PRE-CHECK] This script must not be run as root!"
        exit -1
    fi

    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F 'klipper.service')" ]; then
        printf "[PRE-CHECK] Klipper service found! Continuing...\n\n"
    else
        echo "[ERROR] Klipper service not found, Klippain is unlikely to be installed! Exiting..."
        exit -1
    fi

    local uninstall_klippain_answer
    if [ ! -f "${USER_CONFIG_PATH}/.VERSION" ]; then
        echo "[PRE-CHECK] This uninstall script will fully remove Klippain"
        echo "[PRE-CHECK] If a backup from your old configuration (before using Klippain) is found, it will be restored"
        echo "[PRE-CHECK] Be sure that the printer is idle before continuing!"
        
        read < /dev/tty -rp "[PRE-CHECK] Are you sure want to proceed and uninstall Klippain? (y/N) " uninstall_klippain_answer
        if [[ -z "$uninstall_klippain_answer" ]]; then
            uninstall_klippain_answer="n"
        fi
        uninstall_klippain_answer="${uninstall_klippain_answer,,}"

        if [[ "$uninstall_klippain_answer" =~ ^(yes|y)$ ]]; then
            printf "[PRE-CHECK] Klippain will be uninstalled...\n\n"
        else
            echo "[PRE-CHECK] Klippain uninstall script was canceled!"
            exit -1
        fi
    fi
}

# Step 2: Delete everything in ~/printer_data/config and the Klippain repository
function delete_current_klippain {
    if [ -d "${USER_CONFIG_PATH}" ]; then
        rm -rf ${USER_CONFIG_PATH}
        mkdir ${USER_CONFIG_PATH}
        printf "[UNINSTALL] Klippain user files deleted!\n\n"
    else
        echo "[WARNING] User config path not found! Nothing to delete here. Continuing..."
    fi

    if [ -d "${FRIX_CONFIG_PATH}" ]; then
        rm -rf ${FRIX_CONFIG_PATH}
        printf "[UNINSTALL] Klippain read-only files deleted!\n\n"
    else
        echo "[WARNING] Klippain path not found! Nothing to delete here. Continuing..."
    fi
}

# Step 3: Find the latest backup without a .VERSION file and restore it if needed
function restore_latest_backup {
    local restore_backup latest_backup 

    if [[ ! -e "${BACKUP_PATH}" ]]; then
        printf "[RESTORE] No backup folder found! Skipping...\n\n"
        return
    fi

    read < /dev/tty -rp "[RESTORE] Would you like to restore your last config backup? This script will look for the last one before running Klippain (Y/n) " restore_backup
    if [[ -z "$restore_backup" ]]; then
        restore_backup="y"
    fi
    restore_backup="${restore_backup,,}"

    # Check and exit if the user do not wants to restore a backup
    if [[ "$restore_backup" =~ ^(no|n)$ ]]; then
        printf "[RESTORE] Skipping... No backup will be restored and you will need to manually populate your own printer.cfg file!\n\n"
        return
    fi

    latest_backup=$(find ${BACKUP_PATH} -maxdepth 1 -type d -not -path "${BACKUP_PATH}" -exec sh -c 'if [ ! -f "$1/.VERSION" ]; then echo "$1"; fi' sh {} \; | sort -r | head -n 1)
    if [ -n "${latest_backup}" ]; then
        cp -fa ${latest_backup}/. ${USER_CONFIG_PATH} 2>/dev/null || :
        printf "[RESTORE] Latest backup restored from: ${latest_backup}\n\n"
    else
        echo "[WARNING] No valid backup found in the Klippain backup folder... The restore process was skipped!"
    fi
}

# Step 5: Restart Klipper
function restart_klipper {
    echo "[RESTART] Restarting Klipper..."
    sudo systemctl restart klipper
}

printf "\n=============================\n"
echo "- Klippain uninstall script -"
printf "=============================\n\n"

# Run steps
preflight_checks
delete_current_klippain
restore_latest_backup
restart_klipper

echo "[POST-UNINSTALL] Klippain was uninstalled!"
echo "[POST-UNINSTALL] Do not hesitate to give me your feedback, why you uninstalled Klippain and if there is something I can improve :)"
echo "[POST-UNINSTALL] Maybe see you again in the future..."
printf "\nPS: If a backup has been restored, check that everything is working and then you can safely delete the Klippain backup folder\n"
