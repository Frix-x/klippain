#!/usr/bin/env python3

##################################################
###### SPEED AND VIBRATIONS PLOTTING SCRIPT ######
##################################################
# Written by Frix_x#0161 #
# @version: 2.0

# CHANGELOG:
#   v2.0: - updated the script to align it to the new K-Shake&Tune module
#         - new features for peaks detection and advised speed zones
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
import matplotlib.ticker, matplotlib.gridspec
import locale
from datetime import datetime

matplotlib.use('Agg')


PEAKS_DETECTION_THRESHOLD = 0.05
PEAKS_RELATIVE_HEIGHT_THRESHOLD = 0.04
VALLEY_DETECTION_THRESHOLD = 0.1 # Lower is more sensitive

KLIPPAIN_COLORS = {
    "purple": "#70088C",
    "dark_purple": "#150140",
    "dark_orange": "#F24130"
}


# Set the best locale for time and date formating (generation of the titles)
try:
    locale.setlocale(locale.LC_TIME, locale.getdefaultlocale())
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'C')

# Override the built-in print function to avoid problem in Klipper due to locale settings
original_print = print
def print_with_c_locale(*args, **kwargs):
    original_locale = locale.setlocale(locale.LC_ALL, None)
    locale.setlocale(locale.LC_ALL, 'C')
    original_print(*args, **kwargs)
    locale.setlocale(locale.LC_ALL, original_locale)
print = print_with_c_locale


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


# This find all the peaks in a curve by looking at when the derivative term goes from positive to negative
# Then only the peaks found above a threshold are kept to avoid capturing peaks in the low amplitude noise of a signal
# Additionaly, we validate that a peak is a real peak based of its neighbors as we can have pretty flat zones in vibration
# graphs with a lot of false positive due to small "noise" in these flat zones
def detect_peaks(power_total, speeds, window_size=10, vicinity=10):
    # Smooth the curve using a moving average to avoid catching peaks everywhere in noisy signals
    kernel = np.ones(window_size) / window_size
    smoothed_psd = np.convolve(power_total, kernel, mode='valid')
    mean_pad = [np.mean(power_total[:window_size])] * (window_size // 2)
    smoothed_psd = np.concatenate((mean_pad, smoothed_psd))

    # Find peaks on the smoothed curve (and excluding the last value of the serie often detected when in a flat zone)
    smoothed_peaks = np.where((smoothed_psd[:-3] < smoothed_psd[1:-2]) & (smoothed_psd[1:-2] > smoothed_psd[2:-1]))[0] + 1
    detection_threshold = PEAKS_DETECTION_THRESHOLD * power_total.max()
    
    valid_peaks = []
    for peak in smoothed_peaks:
        peak_height = smoothed_psd[peak] - np.min(smoothed_psd[max(0, peak-vicinity):min(len(smoothed_psd), peak+vicinity+1)])
        if peak_height > PEAKS_RELATIVE_HEIGHT_THRESHOLD * smoothed_psd[peak] and smoothed_psd[peak] > detection_threshold:
            valid_peaks.append(peak)
 
    # Refine peak positions on the original curve
    refined_peaks = []
    for peak in valid_peaks:
        local_max = peak + np.argmax(power_total[max(0, peak-vicinity):min(len(power_total), peak+vicinity+1)]) - vicinity
        refined_peaks.append(local_max)

    peak_speeds = ["{:.1f}".format(speeds[i]) for i in refined_peaks]
    num_peaks = len(refined_peaks)
    print("Vibrations peaks detected: %d @ %s mm/s (avoid running these speeds in your slicer profile)" % (num_peaks, ", ".join(map(str, peak_speeds))))

    return np.array(refined_peaks), num_peaks


# The goal is to find zone outside of peaks (flat low energy zones) to advise them as good speeds range to use in the slicer
def identify_low_energy_zones(power_total):
    valleys = []

    # Calculate the mean and standard deviation of the entire power_total
    mean_energy = np.mean(power_total)
    std_energy = np.std(power_total)

    # Define a threshold value as mean minus a certain number of standard deviations
    threshold_value = mean_energy - VALLEY_DETECTION_THRESHOLD * std_energy

    # Find valleys in power_total based on the threshold
    in_valley = False
    start_idx = 0
    for i, value in enumerate(power_total):
        if not in_valley and value < threshold_value:
            in_valley = True
            start_idx = i
        elif in_valley and value >= threshold_value:
            in_valley = False
            valleys.append((start_idx, i))

    # If the last point is still in a valley, close the valley
    if in_valley:
        valleys.append((start_idx, len(power_total) - 1))

    max_signal = np.max(power_total)

    # Calculate mean energy for each valley as a percentage of the maximum of the signal
    valley_means_percentage = []
    for start, end in valleys:
        if not np.isnan(np.mean(power_total[start:end])):
            valley_means_percentage.append((start, end, (np.mean(power_total[start:end]) / max_signal) * 100))

    # Sort valleys based on mean percentage values
    sorted_valleys = sorted(valley_means_percentage, key=lambda x: x[2])

    return sorted_valleys


# Resample the signal to achieve denser data points in order to get more precise valley placing and
# avoid having to use the original sampling of the signal (that is equal to the speed increment used for the test)
def resample_signal(speeds, power_total, new_spacing=0.1):
    new_speeds = np.arange(speeds[0], speeds[-1] + new_spacing, new_spacing)
    new_power_total = np.interp(new_speeds, speeds, power_total)
    return new_speeds, new_power_total


######################################################################
# Graphing
######################################################################

def plot_total_power(ax, speeds, power_total):
    resampled_speeds, resampled_power_total = resample_signal(speeds, power_total[0])

    ax.set_title("Vibrations decomposition", fontsize=14, color=KLIPPAIN_COLORS['dark_orange'], weight='bold')
    ax.set_xlabel('Speed (mm/s)')
    ax.set_ylabel('Energy')
    
    ax2 = ax.twinx()
    ax2.yaxis.set_visible(False)
    
    power_total_sum = np.array(resampled_power_total)
    speed_array = np.array(resampled_speeds)
    max_y = power_total_sum.max() + power_total_sum.max() * 0.05
    ax.set_xlim([speed_array.min(), speed_array.max()])
    ax.set_ylim([0, max_y])
    ax2.set_ylim([0, max_y])

    ax.plot(resampled_speeds, resampled_power_total, label="X+Y+Z", color='purple')
    ax.plot(speeds, power_total[1], label="X", color='red')
    ax.plot(speeds, power_total[2], label="Y", color='green')
    ax.plot(speeds, power_total[3], label="Z", color='blue')

    peaks, num_peaks = detect_peaks(resampled_power_total, resampled_speeds)
    low_energy_zones = identify_low_energy_zones(resampled_power_total)

    if peaks.size:
        ax.plot(speed_array[peaks], power_total_sum[peaks], "x", color='black', markersize=8)
        for idx, peak in enumerate(peaks):
            fontcolor = 'red'
            fontweight = 'bold'
            ax.annotate(f"{idx+1}", (speed_array[peak], power_total_sum[peak]), 
                        textcoords="offset points", xytext=(8, 5), 
                        ha='left', fontsize=13, color=fontcolor, weight=fontweight)
        ax2.plot([], [], ' ', label=f'Number of peaks: {num_peaks}')
    else:
        ax2.plot([], [], ' ', label=f'No peaks detected')

    for idx, (start, end, energy) in enumerate(low_energy_zones):
        ax.axvline(speed_array[start], color='red', linestyle='dotted', linewidth=1.5)
        ax.axvline(speed_array[end], color='red', linestyle='dotted', linewidth=1.5)
        ax2.fill_between(speed_array[start:end], 0, power_total_sum[start:end], color='green', alpha=0.2, label=f'Zone {idx+1}: {speed_array[start]:.1f} to {speed_array[end]:.1f} mm/s (mean energy: {energy:.2f}%)')

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.grid(which='major', color='grey')
    ax.grid(which='minor', color='lightgrey')
    fontP = matplotlib.font_manager.FontProperties()
    fontP.set_size('small')
    ax.legend(loc='upper left', prop=fontP)
    ax2.legend(loc='upper right', prop=fontP)

    if peaks.size:
        return speed_array[peaks]
    else:
        return None


def plot_spectrogram(ax, speeds, freqs, power_spectral_densities, peaks, max_freq):
    spectrum = np.empty([len(freqs), len(speeds)])

    for i in range(len(speeds)):
        for j in range(len(freqs)):
            spectrum[j, i] = power_spectral_densities[i][0][j]

    ax.set_title("Vibrations spectrogram", fontsize=14, color=KLIPPAIN_COLORS['dark_orange'], weight='bold')
    ax.pcolormesh(speeds, freqs, spectrum, norm=matplotlib.colors.LogNorm(),
            cmap='inferno', shading='gouraud')

    # Add peaks lines in the spectrogram to get hint from peaks found in the first graph
    if peaks is not None:
        for idx, peak in enumerate(peaks):
            ax.axvline(peak, color='cyan', linestyle='dotted', linewidth=0.75)
            ax.annotate(f"Peak {idx+1}", (peak, freqs[-1]*0.9), 
                        textcoords="data", color='cyan', rotation=90, fontsize=10,
                        verticalalignment='top', horizontalalignment='right')
    
    ax.set_ylim([0., max_freq])
    ax.set_ylabel('Frequency (hz)')
    ax.set_xlabel('Speed (mm/s)')

    return


######################################################################
# Startup and main routines
######################################################################

def parse_log(logname):
    with open(logname) as f:
        for header in f:
            if not header.startswith('#'):
                break
        if not header.startswith('freq,psd_x,psd_y,psd_z,psd_xyz'):
            # Raw accelerometer data
            return np.loadtxt(logname, comments='#', delimiter=',')
    # Power spectral density data or shaper calibration data
    raise ValueError("File %s does not contain raw accelerometer data and therefore "
               "is not supported by graph_vibrations.py script. Please use "
               "calibrate_shaper.py script to process it instead." % (logname,))


def extract_speed(logname):
    try:
        speed = re.search('sp(.+?)n', os.path.basename(logname)).group(1).replace('_','.')
    except AttributeError:
        raise ValueError("File %s does not contain speed in its name and therefore "
               "is not supported by graph_vibrations.py script." % (logname,))
    return float(speed)


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
    kdir = os.path.expanduser(kdir)
    sys.path.append(os.path.join(kdir, 'klippy'))
    shaper_calibrate = importlib.import_module('.shaper_calibrate', 'extras')


def vibrations_calibration(lognames, klipperdir="~/klipper", axisname=None, max_freq=1000., remove=0):
    setup_klipper_import(klipperdir)

    # Parse the raw data and get them ready for analysis
    raw_datas = [parse_log(filename) for filename in lognames]
    raw_speeds = [extract_speed(filename) for filename in lognames]
    speeds, datas = sort_and_slice(raw_speeds, raw_datas, remove)

    # As we assume that we have the same number of file for each speeds. We can group
    # the PSD results by this number (to combine vibrations at given speed on all movements)
    group_by = speeds.count(speeds[0])
    # Compute psd and total power of the signal
    freqs, power_spectral_densities = calc_psd(datas, group_by, max_freq)
    power_total = calc_powertot(power_spectral_densities, freqs)

    fig = matplotlib.pyplot.figure()
    gs = matplotlib.gridspec.GridSpec(2, 1, height_ratios=[4, 3])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    title_line1 = "VIBRATIONS MEASUREMENT TOOL"
    fig.text(0.12, 0.965, title_line1, ha='left', va='bottom', fontsize=20, color=KLIPPAIN_COLORS['purple'], weight='bold')
    try:
        filename_parts = (lognames[0].split('/')[-1]).split('_')
        dt = datetime.strptime(f"{filename_parts[1]} {filename_parts[2].split('-')[0]}", "%Y%m%d %H%M%S")
        title_line2 = dt.strftime('%x %X') + ' -- ' + axisname.upper() + ' axis'
    except:
        print("Warning: CSV filename look to be different than expected (%s)" % (lognames[0]))
        title_line2 = lognames[0].split('/')[-1]
    fig.text(0.12, 0.957, title_line2, ha='left', va='top', fontsize=16, color=KLIPPAIN_COLORS['dark_purple'])

    # Remove speeds duplicates and graph the processed datas
    speeds = list(OrderedDict((x, True) for x in speeds).keys())

    peaks = plot_total_power(ax1, speeds, power_total)
    plot_spectrogram(ax2, speeds, freqs, power_spectral_densities, peaks, max_freq)

    fig.set_size_inches(8.3, 11.6)
    fig.tight_layout()
    fig.subplots_adjust(top=0.89)

    # Adding a small Klippain logo to the top left corner of the figure
    ax_logo = fig.add_axes([0.001, 0.899, 0.1, 0.1], anchor='NW', zorder=-1)
    ax_logo.imshow(matplotlib.pyplot.imread(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'klippain.png')))
    ax_logo.axis('off')

    return fig


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
                    default="~/klipper", help="main klipper directory")
    options, args = opts.parse_args()
    if len(args) < 1:
        opts.error("No CSV file(s) to analyse")
    if options.output is None:
        opts.error("You must specify an output file.png to use the script (option -o)")
    if options.remove > 50 or options.remove < 0:
        opts.error("You must specify a correct percentage (option -r) in the 0-50 range")

    fig = vibrations_calibration(args, options.klipperdir, options.axisname, options.max_freq, options.remove)
    fig.savefig(options.output)


if __name__ == '__main__':
    main()
