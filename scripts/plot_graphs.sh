#!/bin/bash
###################################
###### GRAPH PLOTTING SCRIPT ######
###################################
# Written by Frix_x#0161 #
# @version: 1.1

# CHANGELOG:
#   v1.1: multiple fixes and tweaks (mainly to avoid having empty files read by the python scripts after the mv command)
#   v1.0: first version of the script based on a Zellneralex script

# Installation:
#   1. Copy this file somewhere in your config folder and edit the parameters below if needed
#   2bis. Make it executable using SSH: type 'chmod +x ./plot_graphs.sh' when in the folder.
#   2. Be sure to have the gcode_shell_command.py Klipper extension installed (easiest way to install it is to use KIAUH in the Advanced section)
#   3. Create a gcode_shell_command to be able to start it from a macro (see my shell_commands.cfg file)

# Usage:
#   This script was designed to be used with gcode_shell_commands. Use it to call it.
#   Parameters availables:
#      SHAPER      - To generate input shaper diagrams after calling the Klipper TEST_RESONANCES AXIS=X/Y
#      BELTS       - To generate belts diagrams after calling the Klipper TEST_RESONANCES AXIS=1,(-)1 OUTPUT=raw_data
#      VIBRATIONS  - To generate vibration diagram after calling the custom (Frix_x#0161) VIBRATIONS_CALIBRATION macro


#################################################################################################################
RESULTS_FOLDER=~/klipper_config/adxl_results # Path to the folder where storing the results files
SCRIPTS_FOLDER=~/klipper_config/scripts # Path to the folder where the graph_vibrations.py is located
KLIPPER_FOLDER=~/klipper # Path of the klipper main folder
STORE_RESULTS=3 # Number of results to keep (older files are automatically cleaned). 0 to keep them indefinitely
#################################################################################################################


#####################################################################
################ !!! DO NOT EDIT BELOW THIS LINE !!! ################
#####################################################################

function plot_shaper_graph {
  local generator filename newfilename date axis
  generator="${KLIPPER_FOLDER}/scripts/calibrate_shaper.py"
  
  while read filename; do
    newfilename="$(echo ${filename} | sed -e "s/\\/tmp\///")"
    date="$(basename "${newfilename}" | cut -d '.' -f1 | awk -F'_' '{print $3"_"$4}')"
    axis="$(basename "${newfilename}" | cut -d '_' -f2)"
    mv "${filename}" "${isf}"/inputshaper/"${newfilename}"
    
    sync && sleep 2
    "${generator}" "${isf}"/inputshaper/"${newfilename}" -o "${isf}"/inputshaper/resonances_"${axis}"_"${date}".png
  done <<< "$(find /tmp -type f -name "resonances_*.csv" 2>&1 | grep -v "Permission")"
}

function plot_belts_graph {
  local date_ext generator filename belt
  date_ext="$(date +%Y%m%d_%H%M%S)"
  generator="${KLIPPER_FOLDER}/scripts/graph_accelerometer.py"
  
  while read filename; do
    belt="$(basename "${filename}" | cut -d '_' -f4 | cut -d '.' -f1 | sed -e 's/\(.*\)/\U\1/')"
    mv "${filename}" "${isf}"/belts/belt_"${date_ext}"_"${belt}".csv
  done <<< "$(find /tmp -type f -name "raw_data_axis*.csv" 2>&1 | grep -v "Permission")"
  
  sync && sleep 2
  "${generator}" -c "${isf}"/belts/belt_"${date_ext}"_*.csv -o "${isf}"/belts/belts_"${date_ext}".png
}

function plot_vibr_graph {
  local date_ext generator filename newfilename
  date_ext="$(date +%Y%m%d_%H%M%S)"
  generator="${SCRIPTS_FOLDER}/graph_vibrations.py"
  
  while read filename; do
    newfilename="$(echo ${filename} | sed -e "s/\\/tmp\/adxl345/vibr_${date_ext}/")"
    mv "${filename}" "${isf}"/vibrations/"${newfilename}"
  done <<< "$(find /tmp -type f -name "adxl345-*.csv" 2>&1 | grep -v "Permission")"
  
  sync && sleep 2
  "${generator}" "${isf}"/vibrations/vibr_"${date_ext}"*.csv -o "${isf}"/vibrations/vibrations_"${date_ext}".png
  
  tar cfz "${isf}"/vibrations/vibrations_"${date_ext}".tar.gz "${isf}"/vibrations/vibr_"${date_ext}"*.csv
  rm "${isf}"/vibrations/vibr_"${date_ext}"*.csv
}

function clean_files {
  local filename keep1 keep2 old csv date
  keep1=$(( ${STORE_RESULTS} + 1 ))
  keep2=$(( ${STORE_RESULTS} * 2 + 1))

  while read filename; do
    if [ ! -z "${filename}" ]; then
      old+=("${filename}")
      csv="$(basename "${filename}" | cut -d '.' -f1)"
      old+=("${isf}"/inputshaper/"${csv}".csv)
    fi
  done <<< "$(find "${isf}"/inputshaper/ -type f -name '*.png' -printf '%T@ %p\n' | sort -k 1 -n -r | sed 's/^[^ ]* //' | tail -n +"${keep2}")"
  
  while read filename; do
    if [ ! -z "${filename}" ]; then
      old+=("${filename}")
      date="$(basename "${filename}" | cut -d '.' -f1 | awk -F'_' '{print $2"_"$3}')"
      old+=("${isf}"/belts/belt_"${date}"_A.csv)
      old+=("${isf}"/belts/belt_"${date}"_B.csv)
    fi
  done <<< "$(find "${isf}"/belts/ -type f -name '*.png' -printf '%T@ %p\n' | sort -k 1 -n -r | sed 's/^[^ ]* //' | tail -n +"${keep1}")"

  while read filename; do
    if [ ! -z "${filename}" ]; then
      old+=("${filename}")
      csv="$(basename "${filename}" | cut -d '.' -f1)"
      old+=("${isf}"/vibrations/"${csv}".tar.gz)
    fi
  done <<< "$(find "${isf}"/vibrations/ -type f -name '*.png' -printf '%T@ %p\n' | sort -k 1 -n -r | sed 's/^[^ ]* //' | tail -n +"${keep1}")"

  if [ "${#old[@]}" -ne 0 -a "${STORE_RESULTS}" -ne 0 ]; then
    for rmv in "${old[@]}"; do
      rm "${rmv}"
    done
  fi
}

#############################
### MAIN ####################
#############################

if [ ! -d "${RESULTS_FOLDER}/inputshaper" ]; then
  mkdir -p "${RESULTS_FOLDER}/inputshaper"
fi
if [ ! -d "${RESULTS_FOLDER}/belts" ]; then
  mkdir -p "${RESULTS_FOLDER}/belts"
fi
if [ ! -d "${RESULTS_FOLDER}/vibrations" ]; then
  mkdir -p "${RESULTS_FOLDER}/vibrations"
fi

isf="${RESULTS_FOLDER//\~/${HOME}}"

case ${@} in
  SHAPER|shaper)
    plot_shaper_graph
  ;;
  BELTS|belts)
    plot_belts_graph
  ;;
  VIBRATIONS|vibrations)
    plot_vibr_graph
  ;;
  *)
  echo -e "\nUsage:"
  echo -e "\t${0} SHAPER|BELTS|VIBRATIONS"
  echo -e "\t\tSHAPER\tGenerate input shaper diagram"
  echo -e "\t\tBELT\tGenerate belt tension diagram\n"
  echo -e "\t\tVIBRATIONS\tGenerate vibration response diagram\n"
  exit 1
esac

clean_files

echo "Graphs created. You will find the results in ${isf}"
