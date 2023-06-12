#!/usr/bin/env python3

##################################################
###### SPEED AND VIBRATIONS PLOTTING SCRIPT ######
##################################################
# Written by Frix_x#0161 #
# @version: 1.2

# CHANGELOG:
#   v1.2: fixed a bug that could happen when username is not "pi" (thanks @spikeygg)
#   v1.1: better graph formatting
#   v1.0: first version of the script


# Be sure to make this script executable using SSH: type 'chmod +x ./graph_vibrations.py' when in the folder !

#####################################################################
################ !!! DO NOT EDIT BELOW THIS LINE !!! ################
#####################################################################

import optparse, matplotlib, re, sys, importlib, os, operator
from collections import OrderedDict
import numpy as np
import matplotlib.pyplot, matplotlib.dates, matplotlib.font_manager
import matplotlib.ticker

matplotlib.use('Agg')


######################################################################
# Computation
######################################################################

def calc_freq_response(data):
    # Use Klipper standard input shaper objects to do the computation
    helper = shaper_calibrate.ShaperCalibrate(printer=None)
    return helper.process_accelerometer_data(data)


def calc_psd(datas, group, max_freq):
    psd_list = []
    first_freqs = None
    signal_axes = ['x', 'y', 'z', 'all']

    for i in range(0, len(datas), group):
        
        # Round up to the nearest power of 2 for faster FFT
        N = datas[i].shape[0]
        T = datas[i][-1,0] - datas[i][0,0]
        M = 1 << int((N/T) * 0.5 - 1).bit_length()
        if N <= M:
            # If there is not enough lines in the array to be able to round up to the
            # nearest power of 2, we need to pad some zeros at the end of the array to
            # avoid entering a blocking state from Klipper shaper_calibrate.py
            datas[i] = np.pad(datas[i], [(0, (M-N)+1), (0, 0)], mode='constant', constant_values=0)

        freqrsp = calc_freq_response(datas[i])
        for n in range(group - 1):
            data = datas[i + n + 1]

            # Round up to the nearest power of 2 for faster FFT
            N = data.shape[0]
            T = data[-1,0] - data[0,0]
            M = 1 << int((N/T) * 0.5 - 1).bit_length()
            if N <= M:
                # If there is not enough lines in the array to be able to round up to the
                # nearest power of 2, we need to pad some zeros at the end of the array to
                # avoid entering a blocking state from Klipper shaper_calibrate.py
                data = np.pad(data, [(0, (M-N)+1), (0, 0)], mode='constant', constant_values=0)

            freqrsp.add_data(calc_freq_response(data))

        if not psd_list:
            # First group, just put it in the result list
            first_freqs = freqrsp.freq_bins
            psd = freqrsp.psd_sum[first_freqs <= max_freq]
            px = freqrsp.psd_x[first_freqs <= max_freq]
            py = freqrsp.psd_y[first_freqs <= max_freq]
            pz = freqrsp.psd_z[first_freqs <= max_freq]
            psd_list.append([psd, px, py, pz])
        else:
            # Not the first group, we need to interpolate every new signals
            # to the first one to equalize the frequency_bins between them
            signal_normalized = dict()
            freqs = freqrsp.freq_bins
            for axe in signal_axes:
                signal = freqrsp.get_psd(axe)
                signal_normalized[axe] = np.interp(first_freqs, freqs, signal)

            # Remove data above max_freq on all axes and add to the result list
            psd = signal_normalized['all'][first_freqs <= max_freq]
            px = signal_normalized['x'][first_freqs <= max_freq]
            py = signal_normalized['y'][first_freqs <= max_freq]
            pz = signal_normalized['z'][first_freqs <= max_freq]
            psd_list.append([psd, px, py, pz])

    return first_freqs[first_freqs <= max_freq], psd_list


def calc_powertot(psd_list, freqs):
    pwrtot_sum = []
    pwrtot_x = []
    pwrtot_y = []
    pwrtot_z = []

    for psd in psd_list:
        pwrtot_sum.append(np.trapz(psd[0], freqs))
        pwrtot_x.append(np.trapz(psd[1], freqs))
        pwrtot_y.append(np.trapz(psd[2], freqs))
        pwrtot_z.append(np.trapz(psd[3], freqs))

    return [pwrtot_sum, pwrtot_x, pwrtot_y, pwrtot_z]


######################################################################
# Graphing
######################################################################

def plot_total_power(ax, speeds, power_total):
    ax.set_title('Vibrations decomposition')
    ax.set_xlabel('Speed (mm/s)')
    ax.set_ylabel('Energy')

    ax.plot(speeds, power_total[0], label="X+Y+Z", alpha=0.6)
    ax.plot(speeds, power_total[1], label="X", alpha=0.6)
    ax.plot(speeds, power_total[2], label="Y", alpha=0.6)
    ax.plot(speeds, power_total[3], label="Z", alpha=0.6)

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.grid(which='major', color='grey')
    ax.grid(which='minor', color='lightgrey')
    fontP = matplotlib.font_manager.FontProperties()
    fontP.set_size('medium')
    ax.legend(loc='best', prop=fontP)

    return


def plot_spectrogram(ax, speeds, freqs, power_spectral_densities, max_freq):
    spectrum = np.empty([len(freqs), len(speeds)])

    for i in range(len(speeds)):
        for j in range(len(freqs)):
            spectrum[j, i] = power_spectral_densities[i][0][j]

    ax.set_title("Summed vibrations spectrogram")
    ax.pcolormesh(speeds, freqs, spectrum, norm=matplotlib.colors.LogNorm(),
            cmap='inferno', shading='gouraud')
    ax.set_ylim([0., max_freq])
    ax.set_ylabel('Frequency (hz)')
    ax.set_xlabel('Speed (mm/s)')

    return


######################################################################
# Startup and main routines
######################################################################

def parse_log(logname, opts):
    with open(logname) as f:
        for header in f:
            if not header.startswith('#'):
                break
        if not header.startswith('freq,psd_x,psd_y,psd_z,psd_xyz'):
            # Raw accelerometer data
            return np.loadtxt(logname, comments='#', delimiter=',')
    # Power spectral density data or shaper calibration data
    opts.error("File %s does not contain raw accelerometer data and therefore "
               "is not supported by graph_vibrations.py script. Please use "
               "calibrate_shaper.py script to process it instead." % (logname,))


def extract_speed(logname, opts):
    try:
        speed = re.search('sp(.+?)n', os.path.basename(logname)).group(1)
    except AttributeError:
        opts.error("File %s does not contain speed in its name and therefore "
               "is not supported by graph_vibrations.py script." % (logname,))
    return int(speed)


def sort_and_slice(raw_speeds, raw_datas, remove):
    # Sort to get the speeds and their datas aligned and in ascending order
    raw_speeds, raw_datas = zip(*sorted(zip(raw_speeds, raw_datas), key=operator.itemgetter(0)))

    # Remove beginning and end of the datas for each file to get only
    # constant speed data and remove the start/stop phase of the movements
    datas = []
    for data in raw_datas:
        sliced = round((len(data) * remove / 100) / 2)
        datas.append(data[sliced:len(data)-sliced])

    return raw_speeds, datas


def setup_klipper_import(kdir):
    global shaper_calibrate
    sys.path.append(os.path.join(kdir, 'klippy'))
    shaper_calibrate = importlib.import_module('.shaper_calibrate', 'extras')


def main():
    # Parse command-line arguments
    usage = "%prog [options] <raw logs>"
    opts = optparse.OptionParser(usage)
    opts.add_option("-o", "--output", type="string", dest="output",
                    default=None, help="filename of output graph")
    opts.add_option("-a", "--axis", type="string", dest="axisname",
                    default=None, help="axis name to be shown on the side of the graph")
    opts.add_option("-f", "--max_freq", type="float", default=1000.,
                    help="maximum frequency to graph")
    opts.add_option("-r", "--remove", type="int", default=0,
                    help="percentage of data removed at start/end of each files")
    opts.add_option("-k", "--klipper_dir", type="string", dest="klipperdir",
                    default="/home/pi/klipper", help="main klipper directory")
    options, args = opts.parse_args()
    if len(args) < 1:
        opts.error("No CSV file(s) to analyse")
    if options.output is None:
        opts.error("You must specify an output file.png to use the script (option -o)")
    if options.remove > 50 or options.remove < 0:
        opts.error("You must specify a correct percentage (option -r) in the 0-50 range")

    setup_klipper_import(options.klipperdir)

    # Parse the raw data and get them ready for analysis
    raw_datas = [parse_log(filename, opts) for filename in args]
    raw_speeds = [extract_speed(filename, opts) for filename in args]
    speeds, datas = sort_and_slice(raw_speeds, raw_datas, options.remove)

    # As we assume that we have the same number of file for each speeds. We can group
    # the PSD results by this number (to combine vibrations at given speed on all movements)
    group_by = speeds.count(speeds[0])
    # Compute psd and total power of the signal
    freqs, power_spectral_densities = calc_psd(datas, group_by, options.max_freq)
    power_total = calc_powertot(power_spectral_densities, freqs)

    fig, axs = matplotlib.pyplot.subplots(2, 1, sharex=True)
    fig.suptitle("Machine vibrations - " + options.axisname + " moves", fontsize=16)

    # Remove speeds duplicates and graph the processed datas
    speeds = list(OrderedDict((x, True) for x in speeds).keys())
    plot_total_power(axs[0], speeds, power_total)
    plot_spectrogram(axs[1], speeds, freqs, power_spectral_densities, options.max_freq)

    fig.set_size_inches(10, 10)
    fig.tight_layout()
    fig.subplots_adjust(top=0.92)

    fig.savefig(options.output)

if __name__ == '__main__':
    main()
